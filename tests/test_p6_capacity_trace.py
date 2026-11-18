"""P6 RED: independent time-aware capacity trace acceptance, not a new DES."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import subprocess
import sys

import pytest

from icu_liaison.p6_capacity import TraceBundle, audit_trace_bundle

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'model-inputs/p6/synthetic-trace.json'


def sample() -> dict:
    return json.loads(FIXTURE.read_text(encoding='utf-8'))


def test_trace_integrates_half_open_occupancy_and_admission_wait():
    report = audit_trace_bundle(TraceBundle.model_validate(sample()))
    assert report['status'] == 'synthetic_trace_admitted_not_a_DES_run'
    assert report['trace_source'] == 'synthetic_fixture'
    assert report['horizon_minutes'] == 240
    assert report['strategies']['current_care']['occupied_bed_minutes'] == 180
    assert report['strategies']['liaison_service']['occupied_bed_minutes'] == 150
    assert report['strategies']['current_care']['mean_admission_wait_minutes'] == 60
    assert report['strategies']['liaison_service']['mean_admission_wait_minutes'] == 30
    assert report['paired_comparisons']['liaison_service']['occupied_bed_days_change'] == pytest.approx(-30 / 1440)
    assert report['paired_comparisons']['liaison_service']['mean_wait_minutes_change'] == -30
    assert report['investment_ready'] is False
    assert report['capacity_is_cash_saving'] is False


def test_staffed_bed_hours_and_time_varying_capacity_are_integrated():
    v = sample()
    v['capacity'] = [
        {'start_minute': 0, 'end_minute': 120, 'staffed_beds': 1},
        {'start_minute': 120, 'end_minute': 240, 'staffed_beds': 2},
    ]
    report = audit_trace_bundle(TraceBundle.model_validate(v))
    assert report['staffed_bed_minutes'] == 360
    assert report['strategies']['current_care']['spare_staffed_bed_minutes'] == 180
    assert report['strategies']['liaison_service']['spare_staffed_bed_minutes'] == 210
    assert report['paired_comparisons']['liaison_service']['staffed_capacity_changed'] is False


def test_missing_capacity_calendar_and_overbooking_rejected():
    v = sample()
    v['capacity'][0]['end_minute'] = 239
    with pytest.raises(ValueError, match='capacity'):
        audit_trace_bundle(TraceBundle.model_validate(v))
    v = sample()
    v['strategies'][0]['occupancies'].append({
        'episode_id': 'syn-other', 'start_minute': 0, 'end_minute': 30,
    })
    with pytest.raises(ValueError, match='overbook'):
        audit_trace_bundle(TraceBundle.model_validate(v))


def test_admission_must_link_to_actual_occupancy_without_ghost_beds():
    v = sample()
    v['strategies'][1]['requests'][0]['admitted_minute'] = 80
    with pytest.raises(ValueError, match='matching occupancy'):
        audit_trace_bundle(TraceBundle.model_validate(v))
    v = sample()
    v['strategies'][1]['requests'][0]['disposition'] = 'declined'
    v['strategies'][1]['requests'][0]['admitted_minute'] = None
    with pytest.raises(ValueError, match='declined.*occupancy'):
        audit_trace_bundle(TraceBundle.model_validate(v))


def test_paired_demand_provenance_must_match_across_strategies():
    v = sample()
    v['strategies'][1]['requests'][0]['request_minute'] = 61
    with pytest.raises(ValueError, match='paired demand'):
        audit_trace_bundle(TraceBundle.model_validate(v))


def test_individual_episode_cannot_overlap_or_end_at_horizon_without_provenance():
    v = sample()
    v['strategies'][0]['occupancies'].append({
        'episode_id':'syn-index-1','start_minute':0,'end_minute':10
    })
    with pytest.raises(ValueError,match='duplicate'):
        audit_trace_bundle(TraceBundle.model_validate(v))
    v=sample()
    v['strategies'][0]['occupancies'][0]['end_minute']=241
    with pytest.raises(ValueError,match='horizon'):
        audit_trace_bundle(TraceBundle.model_validate(v))


def test_physical_capacity_does_not_infer_cost_or_safety_evidence():
    report = audit_trace_bundle(TraceBundle.model_validate(sample()))
    assert report['independent_empirical_calibration'] is False
    assert report['kairos_native_execution_verified'] is False
    assert 'avoided_readmissions' not in report['paired_comparisons']['liaison_service']
    assert 'estimated_financial_savings' not in report['paired_comparisons']['liaison_service']
    assert report['clinical_safety_evaluated'] is False


def test_direct_kairos_claim_rejected_until_native_adapter_qualified():
    v = sample()
    v['source_engine'] = 'kairos'
    with pytest.raises(ValueError):
        TraceBundle.model_validate(v)


def test_unknown_request_disposition_preserved_not_counted_as_decline():
    v = sample()
    for arm in v['strategies']:
        arm['occupancies'] = [x for x in arm['occupancies'] if x['episode_id'] != 'syn-demand-1']
        arm['requests'][0]['disposition'] = 'censored'
        arm['requests'][0]['admitted_minute'] = None
    report = audit_trace_bundle(TraceBundle.model_validate(v))
    assert report['strategies']['current_care']['censored_requests'] == 1
    assert report['strategies']['current_care']['declined_requests'] == 0
    assert report['strategies']['current_care']['mean_admission_wait_minutes'] is None


def test_cli_reports_only_aggregate_results(tmp_path):
    result = subprocess.run(
        [sys.executable, '-m', 'icu_liaison.p6_cli', str(FIXTURE)],
        env={'PYTHONPATH':str(ROOT/'src')},cwd=ROOT,capture_output=True,text=True,
    )
    assert result.returncode == 0,result.stderr
    report=json.loads(result.stdout)
    assert 'syn-index' not in result.stdout
    assert report['status']=='synthetic_trace_admitted_not_a_DES_run'
    assert report['trace_sha256']


def test_committed_schema_matches_native_pydantic_contract():
    from jsonschema import Draft202012Validator
    schema = json.loads((ROOT/'model-inputs/p6/trace-schema.json').read_text())
    assert schema == TraceBundle.model_json_schema()
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(sample())


def test_real_or_restricted_patient_trace_rejected_even_with_synthetic_looking_ids():
    v=sample();v['data_class']='restricted'
    with pytest.raises(ValueError):TraceBundle.model_validate(v)
    v=sample();v['strategies'][0]['occupancies'][0]['episode_id']='patient-1049'
    with pytest.raises(ValueError):TraceBundle.model_validate(v)
