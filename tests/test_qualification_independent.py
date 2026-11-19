"""Independent source and numerical controls for the portable qualification lane."""
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from icu_liaison.local_data import load_and_audit
from icu_liaison.p4_model import EconomicScenario, evaluate_scenarios
from icu_liaison.qualification_independent import audit_local_aggregate, audit_p4_draws

ROOT = Path(__file__).resolve().parents[1]


def test_p3_aggregate_denominators_do_not_treat_missing_as_zero():
    data = load_and_audit(ROOT / 'tests/fixtures/p3_episodes/manifest.json')
    check = audit_local_aggregate(data)
    assert check['provenance_class'] == 'synthetic'
    assert check['eligible_index_discharges'] == 3
    assert check['readiness_completeness']['numerator'] == 2
    assert check['exit_block_ge12h']['observed_denominator'] == 2
    assert check['exit_block_ge12h']['observed_rate'] == 0.5
    assert check['return_72h']['positive'] == 1
    assert check['return_72h']['unknown'] == 1
    assert check['return_72h']['no_event'] == 1
    assert check['return_72h']['complete_cohort_risk_estimable'] is False
    assert check['investment_ready'] is False


def test_aggregate_refuses_inconsistent_return_counts_and_readiness_overrun():
    data = load_and_audit(ROOT / 'tests/fixtures/p3_episodes/manifest.json')
    altered = deepcopy(data)
    altered['cohort']['unplanned_return_within_72h'] = 3
    with pytest.raises(ValueError, match='partition'):
        audit_local_aggregate(altered)
    altered = deepcopy(data)
    altered['cohort']['index_with_readiness'] = 5
    with pytest.raises(ValueError, match='readiness'):
        audit_local_aggregate(altered)


def test_aggregate_requires_audit_source_identity_and_will_not_promote_approval():
    data = load_and_audit(ROOT / 'tests/fixtures/p3_episodes/manifest.json')
    altered = deepcopy(data)
    altered.pop('input_provenance')
    with pytest.raises(ValueError, match='provenance'):
        audit_local_aggregate(altered)
    altered = deepcopy(data)
    altered['investment_ready'] = True
    with pytest.raises(ValueError, match='approval'):
        audit_local_aggregate(altered)


def test_independent_draw_oracle_and_denominator_coverage():
    scenario = EconomicScenario.model_validate_json((ROOT / 'model-inputs/p4/illustrative.json').read_text())
    run = evaluate_scenarios(scenario)
    check = audit_p4_draws(run, sampled_indices=[0, 7, 53, scenario.iterations - 1])
    assert check['status'] == 'independently_recalculated_draw_accounting'
    assert check['draws_checked'] == 4 * len(scenario.strategies)
    assert check['max_abs_difference_aud'] < 1e-6
    assert check['clinical_or_causal_validation'] is False


def test_independent_oracle_rejects_perturbed_budget_or_return_ledger():
    scenario = EconomicScenario.model_validate_json((ROOT / 'model-inputs/p4/illustrative.json').read_text())
    run = evaluate_scenarios(scenario)
    arm = scenario.strategies[1].id
    run.strategies[arm].net_budget_impact_aud[0] += 700
    with pytest.raises(ValueError, match='net_budget_impact_aud'):
        audit_p4_draws(run, sampled_indices=[0])


def test_2023_24_pdf_text_and_page_image_review_has_its_own_nonhash_status():
    from icu_liaison.public_evidence import load_benchmark_catalogue, select_external_benchmark
    data=load_benchmark_catalogue(ROOT/'model-inputs/anzics-benchmarks.json',
                                  ROOT/'conductor/evidence/source-register.json')
    record=select_external_benchmark(data,'CCR_2023_24_EXIT_BLOCK')
    assert record['verification_status'] == 'publisher_text_and_page_image_inspected_no_pdf_sha'
    with pytest.raises(ValueError, match='unverified'):
        select_external_benchmark(data,'CCR_2023_24_EXIT_BLOCK',require_document_verified=True)
