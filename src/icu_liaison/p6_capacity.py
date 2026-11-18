"""P6 synthetic trace acceptance: time-aware ICU occupancy and access auditing.

This is NOT a DES, event scheduler, counterfactual estimator, or Kairos runtime.
It checks already-emitted synthetic events against physical/staffed capacity
using NumPy's interval-search primitives; Kairos-native trace production remains
an independent unqualified consumer contract.
"""
from __future__ import annotations

from collections import Counter
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class CapacityWindow(_Strict):
    start_minute: int = Field(ge=0)
    end_minute: int = Field(gt=0)
    staffed_beds: int = Field(ge=0, le=1000)


class Occupancy(_Strict):
    episode_id: str = Field(pattern=r'^syn-[a-z0-9_-]{1,80}$')
    start_minute: int = Field(ge=0)
    end_minute: int = Field(gt=0)


class AdmissionRequest(_Strict):
    request_id: str = Field(pattern=r'^syn-[a-z0-9_-]{1,80}$')
    request_minute: int = Field(ge=0)
    disposition: Literal['admitted', 'declined', 'censored']
    admitted_minute: int | None

    @model_validator(mode='after')
    def disposition_is_consistent(self) -> 'AdmissionRequest':
        if self.disposition == 'admitted':
            if self.admitted_minute is None or self.admitted_minute < self.request_minute:
                raise ValueError('admitted request needs a non-earlier admission minute')
        elif self.admitted_minute is not None:
            raise ValueError('declined/censored request must not have admission timestamp')
        return self


class ArmTrace(_Strict):
    strategy_id: str = Field(pattern=r'^[a-z][a-z0-9_]{1,48}$')
    occupancies: list[Occupancy] = Field(max_length=100_000)
    requests: list[AdmissionRequest] = Field(max_length=100_000)


class TraceBundle(_Strict):
    schema_version: Literal[1]
    data_class: Literal['synthetic']
    source_engine: Literal['not_kairos']
    trace_source: Literal['synthetic_fixture']
    scenario_id: str = Field(min_length=1, max_length=128)
    horizon_minutes: int = Field(ge=1, le=525_600)
    capacity: list[CapacityWindow] = Field(min_length=1, max_length=10_000)
    strategies: list[ArmTrace] = Field(min_length=2, max_length=8)
    qualification: Literal['source_fixture_only_not_native_DES']
    notes: str = Field(min_length=1, max_length=1000)

    @model_validator(mode='after')
    def pair_contract(self) -> 'TraceBundle':
        names = [arm.strategy_id for arm in self.strategies]
        if names[0] != 'current_care' or len(names) != len(set(names)):
            raise ValueError('current-care strategy required first, with unique strategy IDs')
        return self


def _capacity(bundle: TraceBundle) -> tuple[int, np.ndarray]:
    windows = bundle.capacity
    if windows[0].start_minute != 0 or windows[-1].end_minute != bundle.horizon_minutes:
        raise ValueError('capacity calendar must cover the full horizon')
    for index, interval in enumerate(windows):
        if interval.start_minute >= interval.end_minute:
            raise ValueError('invalid capacity interval')
        if index > 0 and interval.start_minute != windows[index - 1].end_minute:
            raise ValueError('capacity calendar has a gap or overlap')
    total = sum((w.end_minute - w.start_minute) * w.staffed_beds for w in windows)
    return total, np.asarray([w.start_minute for w in windows], dtype=np.int64)


def _arm(bundle: TraceBundle, arm: ArmTrace, staffed: int, cap_starts: np.ndarray) -> dict:
    horizon = bundle.horizon_minutes
    episodes = arm.occupancies
    requests = arm.requests
    if len({p.episode_id for p in episodes}) != len(episodes):
        raise ValueError('duplicate occupancy episode ID')
    if len({r.request_id for r in requests}) != len(requests):
        raise ValueError('duplicate admission request ID')
    if any(p.start_minute >= p.end_minute or p.end_minute > horizon for p in episodes):
        raise ValueError('occupancy duration outside horizon')
    if any(r.request_minute >= horizon or (r.admitted_minute is not None and
            r.admitted_minute >= horizon) for r in requests):
        raise ValueError('admission request outside horizon')
    occupied_by_id = {p.episode_id: p for p in episodes}
    requested = {r.request_id: r for r in requests}
    for r in requests:
        interval = occupied_by_id.get(r.request_id)
        if r.disposition == 'admitted':
            if interval is None or interval.start_minute != r.admitted_minute:
                raise ValueError('admission requires matching occupancy interval')
        elif interval is not None:
            raise ValueError('declined or censored request has a ghost occupancy')
    if any(p.start_minute > 0 and p.episode_id not in requested for p in episodes):
        raise ValueError('post-start occupancy without paired admission request')

    # Time-of-day capacity must be checked at every event boundary, including
    # capacity changes. This is vectorised *trace validation*, not scheduling.
    starts = np.asarray([p.start_minute for p in episodes], dtype=np.int64)
    ends = np.asarray([p.end_minute for p in episodes], dtype=np.int64)
    cap_ends = np.asarray([w.end_minute for w in bundle.capacity], dtype=np.int64)
    boundaries = np.unique(np.concatenate((
        np.asarray([0, horizon], dtype=np.int64),
        cap_starts, cap_ends, starts, ends,
    )))
    samples = boundaries[:-1]
    widths = np.diff(boundaries)
    active = (np.searchsorted(np.sort(starts), samples, side='right')
              - np.searchsorted(np.sort(ends), samples, side='right'))
    cap_index = np.searchsorted(cap_starts, samples, side='right') - 1
    capacity = np.asarray([bundle.capacity[i].staffed_beds for i in cap_index], dtype=np.int64)
    if (active > capacity).any():
        raise ValueError('ICU trace overbooked beyond staffed capacity')
    if (active < 0).any():
        raise ValueError('invalid occupancy conservation')
    occupied_bed_minutes = int(np.sum(active * widths, dtype=np.int64))
    literal_minutes = sum(p.end_minute - p.start_minute for p in episodes)
    if occupied_bed_minutes != literal_minutes:
        raise ValueError('occupied interval conservation failed')
    spare = int(np.sum((capacity - active) * widths, dtype=np.int64))
    if occupied_bed_minutes + spare != staffed:
        raise ValueError('staffed capacity conservation failed')

    count = Counter(r.disposition for r in requests)
    waits = [r.admitted_minute - r.request_minute for r in requests if r.disposition == 'admitted']
    mean_wait = sum(waits) / len(waits) if waits else None
    return {
        'occupied_bed_minutes': occupied_bed_minutes,
        'occupied_bed_days': occupied_bed_minutes / 1440,
        'spare_staffed_bed_minutes': spare,
        'staffed_capacity_conserved': True,
        'admitted_requests': count['admitted'],
        'declined_requests': count['declined'],
        'censored_requests': count['censored'],
        'mean_admission_wait_minutes': mean_wait,
    }


def audit_trace_bundle(bundle: TraceBundle) -> dict:
    """Admit a paired synthetic trace and report physical/access consequences.

    No admission decisions are generated. Outcomes and their causal validity
    remain wholly the responsibility of a future qualified Kairos producer.
    """
    b = TraceBundle.model_validate(bundle.model_dump())
    staffed, cap_starts = _capacity(b)
    for arm in b.strategies[1:]:
        baseline = {r.request_id: r.request_minute for r in b.strategies[0].requests}
        proposed = {r.request_id: r.request_minute for r in arm.requests}
        if proposed != baseline:
            raise ValueError('paired demand requests must be identical across strategies')
    arms = {arm.strategy_id: _arm(b, arm, staffed, cap_starts) for arm in b.strategies}
    base = arms['current_care']
    comparisons = {}
    for name, outcome in arms.items():
        if name == 'current_care':
            continue
        if base['mean_admission_wait_minutes'] is None or outcome['mean_admission_wait_minutes'] is None:
            delta_wait = None
        else:
            # If different requests are admitted in the arms, an unpaired mean
            # difference is not a causal same-patient wait effect.
            base_ids = {r.request_id for r in b.strategies[0].requests if r.disposition == 'admitted'}
            alt = next(x for x in b.strategies if x.strategy_id == name)
            alt_ids = {r.request_id for r in alt.requests if r.disposition == 'admitted'}
            delta_wait = (outcome['mean_admission_wait_minutes'] - base['mean_admission_wait_minutes']
                          if base_ids == alt_ids else None)
        comparisons[name] = {
            'occupied_bed_days_change': (outcome['occupied_bed_minutes'] - base['occupied_bed_minutes']) / 1440,
            'spare_staffed_bed_minutes_change': outcome['spare_staffed_bed_minutes'] - base['spare_staffed_bed_minutes'],
            'mean_wait_minutes_change': delta_wait,
            'admitted_requests_change': outcome['admitted_requests'] - base['admitted_requests'],
            'declined_requests_change': outcome['declined_requests'] - base['declined_requests'],
            'staffed_capacity_changed': False,
            'interpretation': 'given_paired_traces_not_causal_or_cash_savings',
        }
    return {
        'schema_version': 1,
        'status': 'synthetic_trace_admitted_not_a_DES_run',
        'scenario_id': b.scenario_id,
        'trace_source': b.trace_source,
        'horizon_minutes': b.horizon_minutes,
        'staffed_bed_minutes': staffed,
        'strategies': arms,
        'paired_comparisons': comparisons,
        'capacity_is_cash_saving': False,
        'investment_ready': False,
        'independent_empirical_calibration': False,
        'kairos_native_execution_verified': False,
        'clinical_safety_evaluated': False,
        'source_status': 'synthetic_fixture_only_no_native_runtime_or_CHHHS_data',
    }
