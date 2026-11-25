"""P8.4 TDD: ICU economic, funding and workforce perspectives never conflate."""
from __future__ import annotations
from icu_liaison.p4_model import P4Run
from numpy import float64
from numpy.typing import NDArray
from typing import Any, Literal
from collections.abc import Callable

from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path

import pytest
import numpy as np
from jsonschema import Draft202012Validator

from icu_liaison.p4_model import EconomicScenario, evaluate_scenarios, summarise_p4
from icu_liaison.p8_composition import FictionalFundingPrice, P8Composition, compose_p8_shadow

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def run() -> P4Run:
    source = (ROOT / 'model-inputs/p4/illustrative.json').read_text()
    return evaluate_scenarios(EconomicScenario.model_validate_json(source))


def mchs_record() -> dict[str, Any]:
    return {
        'schema_version': 1, 'episode_id': 'synthetic-episode-001',
        'data_class': 'synthetic', 'provider': 'mchs', 'pricing_year': 2025,
        'drg_edition': 'v11.0', 'source_bundle_id': 'synthetic-bundle',
        'source_bundle_sha256_declared': '1' * 64, 'unit': 'NWAU',
        'current_nwau': '2.1000', 'proposed_nwau': '2.0000',
        'change_nwau': '-0.1000', 'actual_revenue_aud': None,
        'technical_modelled_aud': None, 'execution_evidence': 'injected_contract_test_only',
        'annual_calculator_parity': 'unverified',
        'clinical_case_mix_qualification': 'not_established',
    }


def roster_record() -> dict[str, Any]:
    return {
        'provider_evidence': 'injected_contract_test_only',
        'scenario_id': 'synthetic-nurse-roster',
        'financial_cost_status': 'not_valued',
        'annual_workforce_cost_aud': None,
        'classification_eligibility': 'unverified',
        'roster_completeness': 'partial',
        'request': {
            'schema_version': '0.1', 'run_id': 'synthetic-nurse-roster',
            'policy': {'basis': 'financial_cost', 'currency': 'AUD', 'price_year': 2026},
            'quotes': [{'id': 'q1', 'basis': 'financial_cost', 'currency': 'AUD',
                        'price_year': 2026, 'components': ['base_salary'], 'unit': 'hour'}],
            'usage': [{'id': 'u1', 'quote_id': 'q1', 'unit': 'hour',
                       'service_date': '2026-10-01'}],
        },
    }


def test_source_only_shadow_keeps_p4_draws_and_cash_claim_unchanged(run: P4Run) -> None:
    before = summarise_p4(run)
    out = compose_p8_shadow(run, strategy_id='liaison_service')
    assert out['p4_input_sha256'] == run.input_digest_sha256
    assert out['strategy_id'] == 'liaison_service'
    assert out['p4_illustrative_net_resource_benefit_aud_mean'] == before['strategies']['liaison_service']['net_resource_benefit_aud']['mean']
    assert out['p4_illustrative_net_budget_impact_aud_mean'] == before['strategies']['liaison_service']['net_budget_impact_aud']['mean']
    assert out['mchs']['case_change_nwau'] is None
    assert out['mchs']['actual_revenue_aud'] is None
    assert out['workforce']['annual_labour_cost_aud'] is None
    assert out['workforce']['reconciliation_to_p4_cost_prior'] == 'not_reconciled'
    assert out['admission'] == 'planning_only'
    assert out['clinical_investment_approval'] is False
    assert before == summarise_p4(run)


def test_mchs_case_level_shadow_remains_outside_financial_draws(run: P4Run) -> None:
    base = compose_p8_shadow(run, strategy_id='liaison_service')
    joined = compose_p8_shadow(run, strategy_id='liaison_service', mchs_result=mchs_record())
    assert joined['mchs']['case_change_nwau'] == '-0.1000'
    assert joined['mchs']['pricing_year'] == 2025
    assert joined['p4_price_year'] == 2026
    assert joined['mchs']['scope'] == 'one_synthetic_episode_not_programme_total'
    assert joined['mchs']['annual_calculator_parity'] == 'unverified'
    assert joined['mchs']['actual_revenue_aud'] is None
    assert joined['p4_illustrative_net_resource_benefit_aud_mean'] == base['p4_illustrative_net_resource_benefit_aud_mean']
    assert joined['p4_illustrative_net_budget_impact_aud_mean'] == base['p4_illustrative_net_budget_impact_aud_mean']


@pytest.mark.parametrize('field,value', [
    ('actual_revenue_aud','100'), ('technical_modelled_aud', '100'),
    ('annual_calculator_parity','verified'), ('execution_evidence','native_verified'),
    ('data_class', 'patient_records'), ('unit','AUD'),
    ('source_bundle_sha256_declared','xyz'), ('provider','other')
])
def test_invalid_mchs_provider_result_is_rejected(run: P4Run, field: str, value: str) -> None:
    a=mchs_record();a[field]=value
    with pytest.raises(ValueError):
        compose_p8_shadow(run, strategy_id='liaison_service', mchs_result=a)


def test_inconsistent_nwau_difference_is_rejected(run: P4Run) -> None:
    a=mchs_record();a['change_nwau']='-0.09'
    with pytest.raises(ValueError, match='NWAU'):
        compose_p8_shadow(run, strategy_id='liaison_service', mchs_result=a)


def test_case_sensitivity_rejects_rounded_difference_even_at_high_precision(run: P4Run) -> None:
    provider = mchs_record()
    provider.update(current_nwau='0', proposed_nwau='1.123456789012345678901234567891',
                    change_nwau='1.123456789012345678901234568')
    with pytest.raises(ValueError, match='NWAU change'):
        compose_p8_shadow(run, strategy_id='liaison_service', mchs_result=provider,
                          fictional_funding_price=FictionalFundingPrice(pricing_year=2025, aud_per_nwau='1000'))


def test_fictional_episode_money_keeps_the_annual_cost_ledgers_unchanged(run: P4Run) -> None:
    base = compose_p8_shadow(run, strategy_id='liaison_service', mchs_result=mchs_record())
    priced = compose_p8_shadow(
        run, strategy_id='liaison_service', mchs_result=mchs_record(),
        fictional_funding_price=FictionalFundingPrice(pricing_year=2025, aud_per_nwau='1000.25'),
    )
    funding = priced.pop('episode_funding_sensitivity')
    assert Decimal(funding['case_change_aud']) == Decimal('-100.025')
    assert funding['actual_revenue_aud'] is None and funding['pricing_year'] == 2025
    assert priced == base
    assert base['net_modelled_nwau_aud'] is None


@pytest.mark.parametrize('result, year, rate', [
    (None, 2025, '1000'), (mchs_record(), 2024, '1000'),
    (mchs_record(), 2025, '-1'), (mchs_record(), 2025, 'NaN'),
])
def test_episode_price_requires_compatible_mchs_year_and_exact_assumption(run: P4Run, result: dict[str, Any] | None, year: Literal[2024, 2025], rate: str) -> None:
    with pytest.raises(ValueError, match='fictional'):
        compose_p8_shadow(
            run, strategy_id='liaison_service', mchs_result=result,
            fictional_funding_price=FictionalFundingPrice(pricing_year=year, aud_per_nwau=rate),
        )


@pytest.mark.parametrize('objective, field', [
    ('net_resource', 'net_resource_benefit_aud'), ('budget', 'net_budget_impact_aud'),
])
def test_voiage_only_sees_the_selected_pair_and_perspective(run: P4Run, objective: Literal["net_resource", "budget"], field: str) -> None:
    class ExampleAnalysis:
        def evpi(self) -> float:
            return 4.25

    def inspect_surface(values: NDArray[float64], labels: list[str]) -> ExampleAnalysis:
        assert labels == ['current_care', 'extended_cover']
        expected = np.column_stack([getattr(run.strategies[arm], field) for arm in labels])
        np.testing.assert_array_equal(values, expected)
        return ExampleAnalysis()

    out = compose_p8_shadow(
        run, strategy_id='extended_cover', mchs_result=mchs_record(),
        fictional_funding_price=FictionalFundingPrice(pricing_year=2025, aud_per_nwau='1000'),
        voiage_objective=objective, value_array_factory=inspect_surface, analysis_factory=lambda value: value,
    )
    assert out['voiage_comparison'] == {
        'objective': objective, 'strategy_ids': ['current_care', 'extended_cover'],
        'draws': len(run.strategies['current_care'].net_budget_impact_aud),
        'evpi_aud_per_annual_programme_decision': 4.25, 'provider_evidence': 'injected_contract_test_only',
    }
    assert out['actual_hospital_revenue_change_aud'] is None
    assert out['extra_workforce_cost_applied_to_p4'] is False


def test_non_strategic_comparison_rejected(run: P4Run) -> None:
    with pytest.raises(ValueError):
        compose_p8_shadow(run, strategy_id='current_care')
    with pytest.raises(ValueError):
        compose_p8_shadow(run, strategy_id='unknown_strategy')


def test_workforce_request_requires_explicit_scenario_link_and_adds_no_cost(run: P4Run) -> None:
    workforce=roster_record()
    with pytest.raises(ValueError):
        compose_p8_shadow(run, strategy_id='liaison_service', workforce_result=workforce)
    out=compose_p8_shadow(run,strategy_id='liaison_service',workforce_result=workforce,
                          expected_roster_scenario_id='synthetic-nurse-roster')
    assert out['workforce']['financial_cost_status']=='not_valued'
    assert out['workforce']['annual_labour_cost_aud'] is None
    assert out['workforce']['request_line_count']==1
    assert out['workforce']['source_evidence']=='injected_contract_test_only'
    assert out['net_modelled_nwau_aud'] is None


@pytest.mark.parametrize('mutate', [
    lambda v:v.update({'annual_workforce_cost_aud': '120000.00'}),
    lambda v:v.update({'financial_cost_status': 'valued'}),
    lambda v:v.update({'scenario_id':'different'}),
    lambda v:v['request']['policy'].update({'basis':'funding'}),
    lambda v:v['request']['policy'].update({'price_year':2025}),
    lambda v:v['request']['policy'].update({'currency':'USD'}),
    lambda v:v['request']['usage'].append(deepcopy(v['request']['usage'][0])),
    lambda v:v['request']['usage'][0].update({'quote_id':'missing'}),
    lambda v:v['request']['quotes'].append(deepcopy(v['request']['quotes'][0])),
], ids=["unapproved-cost", "valued", "scenario", "basis", "year", "currency", "duplicate-use", "orphan-quote", "duplicate-quote"])
def test_unqualified_roster_or_corrupt_dapane_request_fails_closed(run: P4Run, mutate: Callable[[dict[str, Any]], object]) -> None:
    v=roster_record();mutate(v)
    with pytest.raises(ValueError):
        compose_p8_shadow(run,strategy_id='liaison_service',workforce_result=v,
                          expected_roster_scenario_id='synthetic-nurse-roster')


@pytest.mark.parametrize('change', ['none', 'quantity', 'observed', 'expired', 'missing_date'])
def test_installed_roster_trace_preserves_dated_synthetic_quantities(run: P4Run, change: str) -> None:
    workforce = roster_record()
    workforce['provider_evidence'] = 'unqualified_installed_workforce_source'
    request = workforce['request']
    request['knowledge_cutoff'] = '2026-11-18'
    quote = request['quotes'][0]
    quote.update(valid_from='2026-01-01', valid_to='2027-01-01', known_from='2026-01-01')
    usage = request['usage'][0]
    usage.update(quantity='8', source={'evidence': 'synthetic'})
    if change == 'quantity':
        usage['quantity'] = '-8'
    elif change == 'observed':
        usage['source'] = {'evidence': 'observed'}
    elif change == 'expired':
        quote['valid_to'] = usage['service_date']
    elif change == 'missing_date':
        del quote['valid_from']
    def compose() -> dict[str, Any]:
        return compose_p8_shadow(run, strategy_id='liaison_service', workforce_result=workforce,
                                 expected_roster_scenario_id='synthetic-nurse-roster')
    if change == 'none':
        assert compose()['workforce']['request_line_count'] == 1
    else:
        with pytest.raises(ValueError, match='workforce'):
            compose()


def test_generated_schema_matches_pydantic_and_fixture(run: P4Run) -> None:
    schema=P8Composition.model_json_schema()
    Draft202012Validator.check_schema(schema)
    fixture=compose_p8_shadow(run,strategy_id='liaison_service')
    assert not list(Draft202012Validator(schema).iter_errors(fixture))
    assert P8Composition.model_validate(fixture).strategy_id=='liaison_service'


def test_byte_identical_output_for_same_model_and_evidence(run: P4Run) -> None:
    a=compose_p8_shadow(run,strategy_id='liaison_service',mchs_result=mchs_record())
    b=compose_p8_shadow(run,strategy_id='liaison_service',mchs_result=mchs_record())
    assert json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)
