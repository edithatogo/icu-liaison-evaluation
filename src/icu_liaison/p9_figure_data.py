"""Build source rows for the six priority fictional P9 figures."""
from __future__ import annotations

from dataclasses import replace
import csv
from decimal import Decimal
from math import isclose
from pathlib import Path
from typing import Annotated, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from .local_data import DatasetManifest, _read_feed
from .p4_model import (
    EconomicScenario, P4Run, _calculate_arrays, financial_decision_surface, nominal_counterfactual,
)
from .qualification_independent import _reference_one_draw, audit_p4_draws

ARM = 'liaison_service'
REFERENCE = 'current_care'
DAYS = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
FIGURE_IDS = ('F02', 'F10', 'F11', 'F15', 'F20', 'F24')


class _SyntheticInput(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


Minute = Annotated[int, Field(ge=0)]
Hour = Annotated[int, Field(ge=0, le=24)]
DailyDemand = Annotated[list[Annotated[int, Field(ge=0, le=10)]], Field(min_length=24, max_length=24)]


class Journey(_SyntheticInput):
    episode_id: str = Field(pattern=r'^SYNICU[0-9]+$')
    referral_minute: Minute | None
    ward_bed_minute: Minute | None


class Shift(_SyntheticInput):
    day: int = Field(ge=0, le=6)
    start: Hour
    end: Hour
    productive_start: Hour
    productive_end: Hour


class CoverageWeek(_SyntheticInput):
    shifts: list[Shift] = Field(max_length=168)
    demand_by_hour: list[DailyDemand] = Field(min_length=7, max_length=7)


class Fixtures(_SyntheticInput):
    schema_version: Literal[1]
    data_class: Literal['synthetic']
    journeys: list[Journey] = Field(min_length=1, max_length=6)
    week: CoverageWeek


def _intervention(scenario: EconomicScenario):
    for strategy in scenario.strategies:
        if strategy.id == ARM and strategy.role == 'proposed':
            return strategy
    raise ValueError('priority figures require the proposed liaison_service arm')


def resource_waterfall(scenario: EconomicScenario) -> list[dict]:
    """Separate nominal resource contributions and count programme staffing once."""
    arm = _intervention(scenario)
    nominal = nominal_counterfactual(scenario)[ARM]
    components = [
        ('icu_delay_resource', nominal['icu_bed_days_released']
         * scenario.resource.net_index_delay_cost_aud_per_day.nominal()),
        ('icu_return_resource', nominal['readmissions_avoided']
         * scenario.resource.incremental_return_cost_aud_per_return.nominal()),
        ('annual_service_cost', -arm.annual_incremental_cost_aud.nominal()),
    ]
    rows = []
    total = 0.
    for name, value in components:
        rows.append({'component': name, 'start_aud': total, 'end_aud': total + value, 'value_aud': value})
        total += value
    if not isclose(total, nominal['net_resource_benefit_aud'], abs_tol=1e-7, rel_tol=1e-12):
        raise ValueError('nominal resource components do not reconcile')
    rows.append({'component': 'net_resource_benefit', 'start_aud': 0., 'end_aud': total, 'value_aud': total})
    return rows


def break_even_grid(scenario: EconomicScenario) -> list[dict]:
    """Vary effectiveness and annual service cost over their finite P4 supports."""
    arm = _intervention(scenario)
    axes = []
    for prior in (arm.delay_success_fraction, arm.annual_incremental_cost_aud):
        low, high = prior.support()
        if not np.isfinite([low, high]).all() or low >= high:
            raise ValueError('break-even grid needs two nondegenerate bounded priors')
        axes.append(np.linspace(low, high, num=17))
    success, cost = (values.ravel() for values in np.meshgrid(*axes))
    sampled = {key: np.full(success.size, p.nominal()) for key, p in scenario.all_priors().items()}
    sampled[f'strategy.{ARM}.delay_success_fraction'] = success
    sampled[f'strategy.{ARM}.annual_incremental_cost_aud'] = cost
    net = _calculate_arrays(scenario.annual_eligible_discharges, sampled, ARM).net_resource_benefit_aud
    rows = []
    for idx, (x, y, value) in enumerate(zip(success, cost, net, strict=True)):
        decimal_sample = {key: Decimal(str(float(values[idx]))) for key, values in sampled.items()}
        expected = _reference_one_draw(scenario.annual_eligible_discharges, decimal_sample, ARM)
        if not isclose(value, float(expected['net_resource_benefit_aud']), abs_tol=1e-7, rel_tol=1e-12):
            raise ValueError('break-even grid failed independent resource reconciliation')
        rows.append({'delay_success': float(x), 'annual_cost_aud': float(y), 'net_resource_aud': float(value)})
    return rows


def paired_capacity(run: P4Run, decision_surface: Path) -> list[dict]:
    """Assign draw IDs only after matching each ordered export row to its P4 replay."""
    _intervention(run.scenario)
    expected, strategies = financial_decision_surface(run)
    with decision_surface.open(encoding='utf-8', newline='') as stream:
        reader = csv.reader(stream)
        if next(reader, None) != strategies:
            raise ValueError('P5 resource strategy columns differ from the replay')
        published = np.array(list(reader), dtype=float)
    if published.shape != expected.shape or not np.allclose(published, expected, rtol=1e-12, atol=1e-7):
        raise ValueError('P5 draw order or values differ from the seeded replay')
    baseline, liaison = run.strategies[REFERENCE], run.strategies[ARM]
    days = liaison.icu_bed_days_released - baseline.icu_bed_days_released
    net = published[:, strategies.index(ARM)] - published[:, strategies.index(REFERENCE)]
    return [
        {'draw_id': idx, 'strategy': ARM, 'reference': REFERENCE,
         'released_icu_bed_days': float(x), 'net_resource_aud': float(y)}
        for idx, (x, y) in enumerate(zip(days, net, strict=True), start=1)
    ]


def journey_rows(journeys: list[Journey], manifest_file: Path) -> list[dict]:
    """Link fictional milestones to audited P3 episode times; retain unknown stages."""
    manifest = DatasetManifest.model_validate_json(manifest_file.read_bytes())
    if manifest.data_class != 'synthetic':
        raise ValueError('journey requires the fictional P3 episode feed')
    records = _read_feed(manifest_file.parent, 'episodes', manifest.files['episodes'])
    episodes = {record.index_icu_episode_id: record for record in records}
    if len(episodes) != len(records) or len({row.episode_id for row in journeys}) != len(journeys):
        raise ValueError('duplicate episode in journey source')
    output = []
    for idx, journey in enumerate(journeys):
        episode = episodes.get(journey.episode_id)
        if episode is None or episode.destination_category != 'ward_same_hospital':
            raise ValueError('journey requires a known synthetic ICU-to-ward episode')
        label = chr(ord('A') + idx)
        referral, bed = journey.referral_minute, journey.ward_bed_minute
        if episode.icu_medically_ready_at is None:
            if referral is not None or bed is not None:
                raise ValueError('journey milestones cannot have offsets from unknown readiness')
            output.append({'episode': label, 'stage': 'readiness_unknown',
                           'start_minute': None, 'end_minute': None, 'duration_minutes': None})
            continue
        delta = episode.icu_actual_departure_at - episode.icu_medically_ready_at
        minutes = delta.total_seconds() / 60
        if not minutes.is_integer() or minutes < 0:
            raise ValueError('journey requires ordered whole-minute P3 fixture endpoints')
        departure = int(minutes)
        points = [0, *(minute for minute in (referral, bed) if minute is not None), departure]
        if points != sorted(points):
            raise ValueError('journey order overlaps or reverses a stage')
        if referral is None and bed is None:
            spans = [(0, departure, 'unresolved_stage')]
        elif referral is None:
            spans = [(0, bed, 'unresolved_stage'), (bed, departure, 'bed_to_departure')]
        elif bed is None:
            spans = [(0, referral, 'ready_to_referral'), (referral, departure, 'unresolved_stage')]
        else:
            spans = [(0, referral, 'ready_to_referral'), (referral, bed, 'referral_to_bed'),
                     (bed, departure, 'bed_to_departure')]
        for start, end, stage in spans:
            output.append({'episode': label, 'stage': stage, 'start_minute': start,
                           'end_minute': end, 'duration_minutes': end - start})
    return output


def coverage_rows(week: CoverageWeek) -> list[dict]:
    """Account for a single fictional nursing post in each complete weekly hour."""
    paid, productive = set(), set()
    for shift in week.shifts:
        if not shift.start < shift.end:
            raise ValueError('paid shift requires increasing endpoints')
        if not shift.start <= shift.productive_start <= shift.productive_end <= shift.end:
            raise ValueError('productive hours must fit within paid shift')
        rostered = {(shift.day, hour) for hour in range(shift.start, shift.end)}
        if paid & rostered:
            raise ValueError('paid shifts overlap for the same liaison post')
        paid |= rostered
        productive.update((shift.day, hr) for hr in range(shift.productive_start, shift.productive_end))
    return [
        {'day': day, 'weekday': DAYS[day], 'hour': hour, 'paid_staff_hours': int((day, hour) in paid),
         'productive_staff_hours': int((day, hour) in productive), 'eligible_readiness_cases': demand}
        for day, hours in enumerate(week.demand_by_hour) for hour, demand in enumerate(hours)
    ]


def sensitivity_grid(run: P4Run) -> list[dict]:
    """Stress shared P4 draws with fixed effect pairs, including joint null and harm."""
    scenario = run.scenario
    arm = _intervention(scenario)
    delay = arm.delay_success_fraction
    returns = arm.relative_return_effect
    delay_values = sorted({0., delay.nominal(), delay.support()[1]})
    ref_low, ref_high = returns.support()
    adverse = ref_low if ref_low < 0 else -0.10
    return_values = sorted({adverse, 0., returns.nominal(), ref_high})
    if not all(0 <= value <= 1 for value in delay_values) or not all(-1 <= value <= 1 for value in return_values):
        raise ValueError('clinical stress effects outside bounded risk support')
    rows = []
    for success in delay_values:
        for effect in return_values:
            sampled = {
                **run.sampled_inputs,
                f'strategy.{ARM}.delay_success_fraction': np.full(scenario.iterations, success),
                f'strategy.{ARM}.relative_return_effect': np.full(scenario.iterations, effect),
            }
            result = _calculate_arrays(scenario.annual_eligible_discharges, sampled, ARM)
            audit_p4_draws(replace(run, sampled_inputs=sampled, strategies={**run.strategies, ARM: result}))
            effect_class = 'more_returns' if effect < 0 else 'joint_null' if effect == 0 == success else 'scenario'
            rows.append({
                'delay_success': success, 'relative_return_reduction': effect, 'effect_class': effect_class,
                'draws': scenario.iterations, 'mean_bed_days': float(result.icu_bed_days_released.mean()),
                'mean_returns_avoided': float(result.readmissions_avoided.mean()),
                'mean_net_resource_aud': float(result.net_resource_benefit_aud.mean()),
            })
    return rows
