"""Source tables for the seven supplementary synthetic P9 figures."""
from __future__ import annotations

import csv
from math import isclose
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from .local_data import DatasetManifest, load_and_audit
from .p4_model import nominal_counterfactual, one_way_sensitivity
from .p6_capacity import TraceBundle, audit_trace_bundle

SUPPLEMENT_IDS = ('F05', 'F06', 'F07', 'F08', 'F09', 'F13', 'F18')
ROOT = Path(__file__).resolve().parents[2]
TRACE = ROOT / 'model-inputs/p6/synthetic-trace.json'
DESIGN = ROOT / 'model-inputs/p9/event-study.json'
DICTIONARY = ROOT / 'model-inputs/clinical-data-dictionary.json'


def _table(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def economic_rows(run, p5, paired_liaison):
    reference = run.strategies['current_care']
    consequences = {(row['strategy_id'], row['measure']): float(row['mean'])
                    for row in _table(p5 / 'cost-consequence.csv')}
    comparisons = {(row['strategy_id'], row['measure']): row
                   for row in _table(p5 / 'paired-comparisons.csv')}
    amounts, signs = [], []
    for arm, result in run.strategies.items():
        if arm == 'current_care':
            continue
        for name in ('net_resource_benefit_aud', 'net_budget_impact_aud'):
            mean = float(np.mean(getattr(result, name) - getattr(reference, name)))
            expected = consequences[arm, name] - consequences['current_care', name]
            if not isclose(mean, expected, abs_tol=1e-7, rel_tol=1e-12):
                raise ValueError('P5 accounting mean differs from paired source')
            amounts.append({'strategy': arm, 'measure': name, 'mean_aud': mean})
        delta = result.net_resource_benefit_aud - reference.net_resource_benefit_aud
        for sign, mask in [('positive', delta > 0), ('zero', delta == 0), ('negative', delta < 0)]:
            count = int(np.count_nonzero(mask))
            signs.append({'strategy': arm, 'sign': sign, 'count': count,
                          'draws': len(delta), 'fraction': count / len(delta)})
        published = comparisons[arm, 'net_resource_benefit_aud']
        if any(not isclose(signs[idx]['fraction'], float(published[field]), abs_tol=1e-12)
               for idx, field in [(-3, 'probability_strictly_better'), (-2, 'probability_equal')]):
            raise ValueError('paired sign fractions differ from P5 comparison')

    scenario = run.scenario
    arm = 'liaison_service'
    pivot = nominal_counterfactual(scenario)[arm]['net_resource_benefit_aud']
    published = [r for r in _table(p5 / 'one-way-sensitivity.csv') if r['strategy_id'] == arm]
    sensitivity = []
    for r, p in zip(one_way_sensitivity(scenario, arm), published, strict=True):
        fields = ('low_net_resource_aud', 'high_net_resource_aud')
        if p['parameter'] != r['parameter'] or any(
            not isclose(float(p[k]), r[k], abs_tol=1e-7, rel_tol=1e-12) for k in fields
        ):
            raise ValueError('P5 tornado bounds differ from P4 sensitivity')
        sensitivity.append({'parameter': r['parameter'], 'pivot_aud': pivot,
                            'lower_aud': r[fields[0]], 'upper_aud': r[fields[1]]})
    if not sensitivity:
        sensitivity = [{'parameter': 'All priors fixed', 'pivot_aud': pivot,
                        'lower_aud': pivot, 'upper_aud': pivot}]
    values = [r['net_resource_aud'] for r in paired_liaison]
    counts, edges = np.histogram(values, bins=min(20, max(1, int(np.sqrt(len(values))))))
    hist = [{'lower_aud': float(lo), 'upper_aud': float(hi), 'count': int(n)}
            for lo, hi, n in zip(edges[:-1], edges[1:], counts, strict=True)]
    return {'F05': amounts, 'F06': signs, 'F07': sensitivity, 'F08': hist}


def capacity_rows(trace_file):
    trace = TraceBundle.model_validate_json(trace_file.read_bytes())
    audit = audit_trace_bundle(trace)
    rows = []
    for arm in trace.strategies:
        bounds = sorted({0, trace.horizon_minutes,
                         *(n for w in trace.capacity for n in (w.start_minute, w.end_minute)),
                         *(n for o in arm.occupancies for n in (o.start_minute, o.end_minute)),
                         *(r.request_minute for r in arm.requests),
                         *(r.admitted_minute for r in arm.requests if r.admitted_minute is not None)})
        total = 0
        for lo, hi in zip(bounds, bounds[1:]):
            occupied = sum(o.start_minute <= lo < o.end_minute for o in arm.occupancies)
            staffed = next(w.staffed_beds for w in trace.capacity if w.start_minute <= lo < w.end_minute)
            # Only admitted requests have two known endpoints for a wait interval.
            waiting = sum(r.admitted_minute is not None and r.request_minute <= lo < r.admitted_minute
                          for r in arm.requests)
            rows.append({'strategy': arm.strategy_id, 'start_minute': lo, 'end_minute': hi,
                         'occupied_beds': occupied, 'staffed_beds': staffed, 'known_waiting': waiting})
            total += occupied * (hi - lo)
        if total != audit['strategies'][arm.strategy_id]['occupied_bed_minutes']:
            raise ValueError('trace plot does not conserve occupied bed-minutes')
    return rows


def flow_rows(p3_manifest):
    if DatasetManifest.model_validate_json(p3_manifest.read_bytes()).data_class != 'synthetic':
        raise ValueError('flow figure requires a synthetic P3 cohort')
    audit = load_and_audit(p3_manifest, data_dictionary_path=DICTIONARY)
    c = audit['cohort']
    death = c['competing_death_before_return']
    counts = {'Unplanned return': c['unplanned_return_within_72h'],
              'Observed without return': c['early_return_observed_no_event'],
              'Competing death': death, 'Unknown': c['early_return_unknown'] - death}
    if min(counts.values()) < 0 or sum(counts.values()) != c['eligible_index_discharges']:
        raise ValueError('index discharge flow does not conserve its denominator')
    return [{'outcome': name, 'count': n, 'eligible_indices': c['eligible_index_discharges']}
            for name, n in counts.items()]


class Period(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid', allow_inf_nan=False)
    week: int
    intervention_hours: float = Field(ge=0)
    control_hours: float = Field(ge=0)


class Design(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    schema_version: Literal[1]
    data_class: Literal['synthetic_design']
    reference_week: Literal[-1]
    rollout_week: Literal[0]
    periods: list[Period] = Field(min_length=4, max_length=104)


def event_rows(design_file):
    design = Design.model_validate_json(design_file.read_bytes())
    periods = design.periods
    weeks = [p.week for p in periods]
    if weeks != list(range(weeks[0], weeks[0] + len(weeks))) or weeks[0] > -2 or weeks[-1] < 1:
        raise ValueError('event study needs complete consecutive pre/post weeks and a reference')
    ref = next(p for p in periods if p.week == design.reference_week)
    gap = ref.intervention_hours - ref.control_hours
    return [dict(**p.model_dump(), gap_change_hours=p.intervention_hours - p.control_hours - gap)
            for p in periods]
