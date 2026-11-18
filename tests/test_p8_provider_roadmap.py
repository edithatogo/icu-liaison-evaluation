"""P8 red/green: the portable Conductor must preserve separated economic views."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
TRACK = ROOT / 'conductor/tracks/P8-abf-workforce-interop'
DATA = ROOT / 'model-inputs/p8'


def _load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def _schema():
    schema = _load(DATA / 'funding-workforce-shadow.schema.json')
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_p8_has_complete_conductor_contract_without_premature_acceptance():
    for name in ('index.md', 'spec.md', 'plan.md', 'metadata.json', 'agent-contract.md',
                 'test-matrix.md', 'risk-register.md', 'handoff.md'):
        assert (TRACK / name).is_file(), name
    meta = _load(TRACK / 'metadata.json')
    assert meta['track_id'] == 'P8-abf-workforce-interop'
    assert meta['status'] == 'in_progress'
    assert 'P7-technical-empirical-qualification' in meta['dependency_tracks']
    assert meta['native_integrations_qualified'] is False
    assert meta['clinical_validation'] is False
    assert 'P8-abf-workforce-interop/index.md' in (ROOT / 'conductor/tracks.md').read_text()


def test_provider_capability_register_separates_owners_and_does_not_claim_installed_parity():
    doc = _load(DATA / 'provider-capabilities.json')
    by_id = {p['id']: p for p in doc['providers']}
    assert len(by_id) == len(doc['providers'])
    assert {'mchs', 'microcosting_healthworkforce', 'dapane', 'voiage', 'kairos'} <= set(by_id)
    assert by_id['mchs']['ledger'] == 'weighted_activity_funding_shadow'
    assert by_id['microcosting_healthworkforce']['ledger'] == 'workforce_resource_input'
    assert by_id['dapane']['ledger'] == 'resource_valuation'
    assert by_id['voiage']['ledger'] == 'decision_uncertainty'
    assert by_id['kairos']['ledger'] == 'temporal_capacity_optional'
    for p in doc['providers']:
        assert len(p['source_revision']) == 40
        int(p['source_revision'], 16)
        assert p['installed_qualification'] == 'unverified'
        assert p['owner_reuses_existing_track']


def test_synthetic_null_shadow_admits_but_never_claims_hospital_revenue():
    doc = _load(DATA / 'synthetic-null-shadow.json')
    assert list(_schema().iter_errors(doc)) == []
    assert doc['data_class'] == 'synthetic'
    assert doc['admission'] == 'planning_only'
    assert doc['funding']['shadow_modelled_nwau_change'] is None
    assert doc['funding']['actual_incremental_revenue_aud'] is None
    assert doc['workforce']['incremental_annual_labour_cost_aud'] is None


@pytest.mark.parametrize('field,value', [
    ('data_class', 'clinical_records'),
    ('admission', 'investment_ready'),
])
def test_wrong_promotion_flags_are_rejected(field, value):
    doc = _load(DATA / 'synthetic-null-shadow.json')
    doc[field] = value
    assert list(_schema().iter_errors(doc))


def test_no_revenue_projection_without_actual_contract():
    doc = _load(DATA / 'synthetic-null-shadow.json')
    doc['funding']['actual_incremental_revenue_aud'] = '12000.00'
    assert list(_schema().iter_errors(doc))
    doc = _load(DATA / 'synthetic-null-shadow.json')
    doc['funding']['shadow_modelled_nwau_change'] = '0.5'
    assert list(_schema().iter_errors(doc))


def test_no_nursing_cost_without_classification_and_rate_approval():
    doc = _load(DATA / 'synthetic-null-shadow.json')
    doc['workforce']['incremental_annual_labour_cost_aud'] = '123000.00'
    assert list(_schema().iter_errors(doc))
    doc = _load(DATA / 'synthetic-null-shadow.json')
    doc['workforce']['classification_status'] = 'confirmed'
    assert list(_schema().iter_errors(doc))


def test_separate_resource_and_funding_units_and_no_unknown_fields():
    doc = _load(DATA / 'synthetic-null-shadow.json')
    doc['funding']['unit'] = 'AUD'
    assert list(_schema().iter_errors(doc))
    doc = _load(DATA / 'synthetic-null-shadow.json')
    doc['funding']['actual_cash_savings_aud'] = '5000.00'
    assert list(_schema().iter_errors(doc))
    doc = _load(DATA / 'synthetic-null-shadow.json')
    doc['resource_valuation']['basis'] = 'funding'
    assert list(_schema().iter_errors(doc))


def test_nwau_pay_year_edition_and_provider_are_required_for_any_calculation():
    doc = _load(DATA / 'synthetic-null-shadow.json')
    doc['funding']['qualification_status'] = 'calculated_paired'
    doc['funding']['shadow_modelled_nwau_change'] = '0.15'
    assert list(_schema().iter_errors(doc))  # no DRG edition, source validation or pair


def test_candidate_notes_identify_2026_27_as_not_parity_qualified():
    matrix = _load(DATA / 'provider-capabilities.json')
    m = next(x for x in matrix['providers'] if x['id'] == 'mchs')
    assert m['year_2026_27_full_parity'] is False
    assert 'nwau' in m['domain_scope'].lower()


def test_funding_calculator_and_financial_year_are_separate_from_cost_price_year():
    doc = _load(DATA / 'synthetic-null-shadow.json')
    assert doc['funding']['calculator_year'] is None
    assert doc['funding']['financial_year_label'] is None
    doc['funding']['calculator_year'] = 2025
    assert list(_schema().iter_errors(doc))  # unavailable route cannot imply accepted annual calculator
    doc = _load(DATA / 'synthetic-null-shadow.json')
    doc['funding']['financial_year_label'] = '2025-26'
    assert list(_schema().iter_errors(doc))
