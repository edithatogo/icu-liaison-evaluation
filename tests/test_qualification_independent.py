"""Independent source and numerical controls for the portable qualification lane."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from shutil import copytree

import numpy as np
import pytest

from icu_liaison.local_data import load_and_audit
from icu_liaison.p4_model import EconomicScenario, evaluate_scenarios
from icu_liaison.qualification_independent import audit_local_aggregate, audit_p4_draws

ROOT = Path(__file__).resolve().parents[1]


def test_p3_aggregate_denominators_do_not_treat_missing_as_zero() -> None:
    data = load_and_audit(ROOT / 'tests/fixtures/p3_episodes/manifest.json')
    check = audit_local_aggregate(data)
    assert check['provenance_class'] == 'synthetic'
    assert check['eligible_index_discharges'] == 3
    assert check['readiness_completeness']['numerator'] == 2
    assert check['exit_block_ge12h']['observed_denominator'] == 2
    assert check['exit_block_ge12h']['observed_rate'] == 0.5
    assert check['exit_block_ge12h']['eligible_cohort_fraction_bounds'] == pytest.approx([1 / 3, 2 / 3])
    assert check['return_72h']['positive'] == 1
    assert check['return_72h']['unknown'] == 1
    assert check['return_72h']['no_event'] == 1
    assert check['return_72h']['complete_cohort_risk_estimable'] is False
    assert check['return_72h']['eligible_cohort_fraction_bounds'] == pytest.approx([1 / 3, 2 / 3])
    assert check['investment_ready'] is False


def test_missing_readiness_leaves_the_eligible_cohort_range_unidentified() -> None:
    data = load_and_audit(ROOT / 'tests/fixtures/p3_episodes/manifest.json')
    data['cohort'].update(index_with_readiness=0, index_exit_block_ge12h=0)
    result = audit_local_aggregate(data)['exit_block_ge12h']
    assert result['observed_rate'] is None
    assert result['exact_binomial_95_interval_observed_only'] is None
    assert result['eligible_cohort_fraction_bounds'] == [0, 1]


def test_complete_observation_collapses_the_missing_outcome_bounds() -> None:
    data = load_and_audit(ROOT / 'tests/fixtures/p3_episodes/manifest.json')
    data['cohort'].update(index_with_readiness=3, early_return_unknown=0,
                          early_return_observed_no_event=2, competing_death_before_return=0,
                          followup_complete_72h=3)
    result = audit_local_aggregate(data)
    assert result['exit_block_ge12h']['eligible_cohort_fraction_bounds'] == pytest.approx([1 / 3, 1 / 3])
    assert result['return_72h']['eligible_cohort_fraction_bounds'] == pytest.approx([1 / 3, 1 / 3])
    assert result['return_72h']['complete_cohort_risk_estimable'] is True


def test_complete_followup_can_include_a_return_with_unknown_planned_status(tmp_path: Path) -> None:
    fixture = ROOT / 'tests/fixtures/p3_episodes'
    directory = copytree(fixture, tmp_path / 'case')
    episodes = directory / 'episodes.csv'
    raw = episodes.read_bytes().replace(b',unplanned', b',unknown', 1)
    episodes.write_bytes(raw)
    path = directory / 'manifest.json'
    manifest = json.loads(path.read_bytes())
    manifest['files']['episodes']['sha256'] = hashlib.sha256(raw).hexdigest()
    path.write_text(json.dumps(manifest), encoding='utf-8')
    audit = load_and_audit(path)
    assert audit['cohort']['followup_complete_72h'] == 2
    assert audit['cohort']['early_return_unknown'] == 2
    result = audit_local_aggregate(audit)['return_72h']
    assert result['followup_complete_72h'] == 2
    assert result['no_event'] == 1
    assert result['eligible_cohort_fraction_bounds'] == pytest.approx([0, 2 / 3])
    assert result['complete_cohort_risk_estimable'] is False


@pytest.mark.parametrize('complete', [0, 3])
def test_aggregate_rejects_inconsistent_followup_and_outcome_counts(complete: int) -> None:
    audit = load_and_audit(ROOT / 'tests/fixtures/p3_episodes/manifest.json')
    audit['cohort']['followup_complete_72h'] = complete
    with pytest.raises(ValueError, match='follow-up conflicts'):
        audit_local_aggregate(audit)


@pytest.mark.parametrize(('field', 'value'), [
    ('manifest_sha256', 'unverified marker'),
    ('feed_sha256', 'unverified marker'),
    ('feed_sha256', {'episodes': '1' * 64}),
    ('feed_sha256', {'episodes': '1' * 64, 'followup': 'unverified marker'}),
])
def test_aggregate_rejects_incomplete_or_invalid_source_fingerprints(field: str, value: dict[str, str] | str) -> None:
    audit = load_and_audit(ROOT / 'tests/fixtures/p3_episodes/manifest.json')
    audit['input_provenance'][field] = value
    with pytest.raises(ValueError, match='provenance'):
        audit_local_aggregate(audit)


def test_aggregate_refuses_inconsistent_return_counts_and_readiness_overrun() -> None:
    data = load_and_audit(ROOT / 'tests/fixtures/p3_episodes/manifest.json')
    altered = deepcopy(data)
    altered['cohort']['unplanned_return_within_72h'] = 3
    with pytest.raises(ValueError, match='partition'):
        audit_local_aggregate(altered)
    altered = deepcopy(data)
    altered['cohort']['index_with_readiness'] = 5
    with pytest.raises(ValueError, match='readiness'):
        audit_local_aggregate(altered)


def test_aggregate_requires_audit_source_identity_and_will_not_promote_approval() -> None:
    data = load_and_audit(ROOT / 'tests/fixtures/p3_episodes/manifest.json')
    altered = deepcopy(data)
    altered.pop('input_provenance')
    with pytest.raises(ValueError, match='provenance'):
        audit_local_aggregate(altered)
    altered = deepcopy(data)
    altered['investment_ready'] = True
    with pytest.raises(ValueError, match='approval'):
        audit_local_aggregate(altered)


def test_independent_draw_oracle_and_denominator_coverage() -> None:
    scenario = EconomicScenario.model_validate_json((ROOT / 'model-inputs/p4/illustrative.json').read_text())
    run = evaluate_scenarios(scenario)
    check = audit_p4_draws(run, sampled_indices=[0, 7, 53, scenario.iterations - 1])
    assert check['status'] == 'independently_recalculated_draw_accounting'
    assert check['draws_checked'] == 4 * len(scenario.strategies)
    assert check['max_abs_difference_aud'] < 1e-6
    assert check['clinical_or_causal_validation'] is False


def test_independent_oracle_rejects_perturbed_budget_or_return_ledger() -> None:
    scenario = EconomicScenario.model_validate_json((ROOT / 'model-inputs/p4/illustrative.json').read_text())
    run = evaluate_scenarios(scenario)
    arm = scenario.strategies[1].id
    run.strategies[arm].net_budget_impact_aud[0] += 700
    with pytest.raises(ValueError, match='net_budget_impact_aud'):
        audit_p4_draws(run, sampled_indices=[0])


def test_2023_24_pdf_text_and_page_image_review_has_its_own_nonhash_status() -> None:
    from icu_liaison.public_evidence import load_benchmark_catalogue, select_external_benchmark
    data=load_benchmark_catalogue(ROOT/'model-inputs/anzics-benchmarks.json',
                                  ROOT/'conductor/evidence/source-register.json')
    record=select_external_benchmark(data,'CCR_2023_24_EXIT_BLOCK')
    assert record['verification_status'] == 'publisher_text_and_page_image_inspected_no_pdf_sha'
    with pytest.raises(ValueError, match='unverified'):
        select_external_benchmark(data,'CCR_2023_24_EXIT_BLOCK',require_document_verified=True)
