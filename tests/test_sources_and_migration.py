"""Prevent a migration from weakening scientific and source provenance."""
from pathlib import Path
import json
import hashlib
from icu_liaison.schemas import Scenario

ROOT=Path(__file__).resolve().parents[1]


def test_public_anizcs_benchmark_not_confused_with_early_return() -> None:
    doc=json.loads((ROOT/'conductor/evidence/source-register.json').read_text())
    ccr=next(s for s in doc['sources'] if s['id']=='ANZICS-CCR-2024-25')
    apd=next(s for s in doc['sources'] if s['id']=='ANZICS-CORE-2024')
    rates={x['name']:x for x in ccr['outcomes']}
    assert rates['live_ward_home_discharge_delay_ge12h']['value']==0.204
    assert rates['live_ward_home_discharge_delay_ge12h']['contributors']==162
    assert rates['live_ward_home_discharge_delay_ge12h']['denominator']=='live ward/home discharges'
    assert rates['return_icu_hdu_admission_episodes']['value']==0.045
    assert rates['return_icu_hdu_admission_episodes']['denominator']=='all ICU/HDU admissions'
    assert next(x for x in apd['outcomes'] if x['name']=='adult_readmitted_patients')['value']==0.04
    scenario=Scenario.model_validate_json((ROOT/'model-inputs/illustrative.json').read_text())
    assert scenario.inputs.unplanned_72h_readmission_risk.value != rates['return_icu_hdu_admission_episodes']['value']


def test_initial_repository_import_preserves_original_provenance_and_external_workbook() -> None:
    doc=json.loads((ROOT/'conductor/evidence/migration-manifest.json').read_text())
    assert doc['status']=='dedicated_repository_initial_import'
    assert doc['prior_implementation']['status_at_inspection']=='open_draft_unmerged'
    assert doc['workbook']['not_a_local_chhhs_data_source'] is True
    assert doc['workbook']['sha256']=='da9699f36affef4fdbd444f40ce5d8b138c576fde3bf33363b4bebe908a44844'
    assert not list(ROOT.glob('**/*.xlsx'))
    assert not list(ROOT.glob('**/*.xlsm'))
    assert (ROOT/'conductor/tracks/P0-portable-consolidation/metadata.json').is_file()


def test_conductor_plan_retains_outstanding_native_and_review_obligations() -> None:
    m=json.loads((ROOT/'conductor/tracks/P0-portable-consolidation/metadata.json').read_text())
    assert m['status']=='in_progress'
    assert 'P0.4' in m['blocked_phases']
    assert m['external_dependencies']


def test_no_disconnected_source_records() -> None:
    doc=json.loads((ROOT/'conductor/evidence/source-register.json').read_text())
    ids=[s['id'] for s in doc['sources']]
    assert len(ids)==len(set(ids))
    assert all(s['url'].startswith('https://') for s in doc['sources'])
