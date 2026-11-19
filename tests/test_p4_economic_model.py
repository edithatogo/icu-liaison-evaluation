"""P4 RED behavioural and boundary tests; no provider substitutions."""
import copy
import json
from pathlib import Path
import numpy as np
import pytest
from pydantic import ValidationError

from icu_liaison.p4_model import (EconomicScenario, evaluate_scenarios,
                                  summarise_p4, financial_decision_surface,
                                  nominal_counterfactual, make_p4_voiage_analysis)

SOURCE = Path(__file__).resolve().parents[1] / 'model-inputs/p4/illustrative.json'

def example():
    return json.loads(SOURCE.read_text(encoding='utf-8'))

def fixed(value, unit='proportion'):
    return {'family':'fixed','params':{'value':value},'unit':unit,'evidence_status':'illustrative_assumption','source_ref':'TEST-ILLUSTRATIVE'}

def deterministic(data):
    # Convert all probabilistic draws to their nominal modes/medians/beta means.
    for section in ('baseline','resource'):
        for key, prior in data[section].items():
            v = prior['params']
            mode = {'fixed':lambda:v['value'], 'triangular':lambda:v['mode'],
                    'beta':lambda:v['alpha']/(v['alpha']+v['beta']),
                    'lognormal':lambda:v['median']}[prior['family']]()
            data[section][key] = fixed(mode,prior['unit'])
    data['baseline']['exit_block_rate']['evidence_status']='public_proxy'
    data['baseline']['exit_block_rate']['source_ref']='CCR_2024_25_EXIT_BLOCK'
    for strategy in data['strategies']:
        for key,prior in strategy.items():
            if not isinstance(prior,dict) or 'family' not in prior: continue
            v=prior['params']; mode={'fixed':lambda:v['value'],'triangular':lambda:v['mode'],
                            'beta':lambda:v['alpha']/(v['alpha']+v['beta']),
                            'lognormal':lambda:v['median']}[prior['family']]()
            strategy[key]=fixed(mode,prior['unit'])
    data['dependence_groups']=[]
    return data


def test_scenario_requires_real_current_care_and_at_least_one_intervention():
    s=EconomicScenario.model_validate(example())
    assert [x.id for x in s.strategies]==['current_care','liaison_service','extended_cover']
    z=example();z['strategies']=z['strategies'][:1]
    with pytest.raises(ValidationError): EconomicScenario.model_validate(z)


def test_nominal_reproduces_existing_p1_accounting_without_cash_conflation():
    x=EconomicScenario.model_validate(deterministic(example()))
    r=nominal_counterfactual(x)['liaison_service']
    assert r['icu_bed_days_released']==pytest.approx(7.65)
    assert r['readmissions_avoided']==pytest.approx(4.5)
    assert r['gross_resource_benefit_aud']==pytest.approx(81270)
    assert r['net_resource_benefit_aud']==pytest.approx(-168730)
    assert r['usable_bed_days']==pytest.approx(6.12)
    assert r['net_budget_impact_aud']==pytest.approx(7.65*1800*.2+4.5*15000*.4-250000)


def test_current_care_is_zero_incremental_and_shared_draws_preserve_comparison():
    result=evaluate_scenarios(EconomicScenario.model_validate(example()))
    assert np.all(result.strategies['current_care'].net_resource_benefit_aud==0)
    assert len(result.strategies['extended_cover'].net_resource_benefit_aud)==5000
    matrix,labels=financial_decision_surface(result)
    assert labels==['current_care','liaison_service','extended_cover']
    assert matrix.shape==(5000,3)
    assert np.array_equal(matrix[:,1],result.strategies['liaison_service'].net_resource_benefit_aud)


def test_full_run_is_repeatable_and_safeguards_not_silent_success():
    scenario=EconomicScenario.model_validate(example())
    a=summarise_p4(evaluate_scenarios(scenario))
    b=summarise_p4(evaluate_scenarios(scenario))
    assert a==b
    assert a['investment_ready'] is False
    assert a['clinical_safety']=='unmeasured'
    assert a['cost_utility_evaluation_performed'] is False
    assert a['monetised_capacity_beyond_resource_cost'] is False


def test_no_service_effect_does_not_create_benefit():
    z=deterministic(example())
    arm=z['strategies'][1]
    arm['delay_success_fraction']=fixed(0)
    arm['relative_return_effect']=fixed(0,'signed_proportion')
    out=evaluate_scenarios(EconomicScenario.model_validate(z)).strategies['liaison_service']
    assert np.all(out.gross_resource_benefit_aud == 0)
    assert np.all(out.net_resource_benefit_aud == -250000)
    assert np.all(out.usable_bed_days==0)


def test_more_appropriate_returns_can_worsen_finances():
    z=deterministic(example())
    arm=z['strategies'][1]
    arm['relative_return_effect']=fixed(-.2,'signed_proportion')
    out=evaluate_scenarios(EconomicScenario.model_validate(z)).strategies['liaison_service']
    assert np.all(out.readmissions_avoided<0)
    assert np.all(out.net_resource_benefit_aud<0)


def test_independent_cash_fraction_does_not_change_resource_consequences():
    z=deterministic(example());s=EconomicScenario.model_validate(z)
    before=evaluate_scenarios(s).strategies['liaison_service']
    z['resource']['index_cash_realisability_fraction']=fixed(0)
    z['resource']['return_cash_realisability_fraction']=fixed(0)
    after=evaluate_scenarios(EconomicScenario.model_validate(z)).strategies['liaison_service']
    assert np.array_equal(before.net_resource_benefit_aud,after.net_resource_benefit_aud)
    assert np.all(after.net_budget_impact_aud==-250000)


def test_capacity_reuse_is_not_double_counted_as_cash_or_resource():
    z=deterministic(example())
    z['resource']['usable_released_capacity_fraction']=fixed(0)
    a=evaluate_scenarios(EconomicScenario.model_validate(z)).strategies['liaison_service']
    assert np.all(a.usable_bed_days==0)
    assert a.net_resource_benefit_aud[0]==pytest.approx(-168730)


def test_gaussian_dependence_is_supported_and_rejects_non_psd():
    result=evaluate_scenarios(EconomicScenario.model_validate(example()))
    a=result.sampled_inputs['baseline.unplanned_72h_return_rate']
    b=result.sampled_inputs['resource.incremental_return_cost_aud_per_return']
    # Positive latent Gaussian correlation should induce positive rank association.
    assert np.corrcoef(np.argsort(np.argsort(a)),np.argsort(np.argsort(b)))[0,1]>0.15
    z=example();z['dependence_groups'][0]['gaussian_correlation']=[[1,1.5],[1.5,1]]
    with pytest.raises(ValidationError):EconomicScenario.model_validate(z)


def test_invalid_correlation_identifiers_overlapping_groups_or_matrix_rejected():
    z=example();z['dependence_groups'][0]['variables'][0]='absent.rate'
    with pytest.raises(ValidationError):EconomicScenario.model_validate(z)
    z=example();z['dependence_groups'].append(copy.deepcopy(z['dependence_groups'][0]))
    with pytest.raises(ValidationError):EconomicScenario.model_validate(z)
    z=example();z['dependence_groups'][0]['gaussian_correlation']=[[1,.3],[.1,1]]
    with pytest.raises(ValidationError):EconomicScenario.model_validate(z)


def test_semantic_input_units_and_public_72h_misuse_are_rejected():
    z=example();z['baseline']['unplanned_72h_return_rate']['evidence_status']='public_proxy'
    with pytest.raises(ValidationError):EconomicScenario.model_validate(z)
    z=example();z['resource']['hours_released_per_improved_case']['unit']='days_per_case'
    with pytest.raises(ValidationError):EconomicScenario.model_validate(z)
    z=example();z['baseline']['exit_block_rate']['params']['value']=.25
    with pytest.raises(ValidationError):EconomicScenario.model_validate(z)


def test_current_care_cannot_contain_nonzero_cost_or_effect():
    z=example();z['strategies'][0]['annual_incremental_cost_aud']=fixed(1000,'AUD_per_year')
    with pytest.raises(ValidationError):EconomicScenario.model_validate(z)
    z=example();z['strategies'][0]['coverage_fraction']=fixed(.25)
    with pytest.raises(ValidationError):EconomicScenario.model_validate(z)


def test_safety_missingness_cannot_be_mislabeled_as_noninferiority():
    z=example();z['safety']['assessment_status']='validated_safe'
    with pytest.raises(ValidationError):EconomicScenario.model_validate(z)
    z=example();z['safety']['required_outcomes']=['post_icu_death']
    with pytest.raises(ValidationError):EconomicScenario.model_validate(z)


def test_multiple_strategies_can_feed_voiage_but_only_via_provider():
    run=evaluate_scenarios(EconomicScenario.model_validate(example()))
    calls=[]
    class Stub:
        def __init__(self,v): self.v=v
    def value_factory(array,labels):calls.append((array.shape,labels));return Stub(array)
    def analysis_factory(value):return {'matrix':value.v}
    x=make_p4_voiage_analysis(run,value_array_factory=value_factory,analysis_factory=analysis_factory)
    assert x['matrix'].shape==(5000,3)
    assert calls[0][1]==['current_care','liaison_service','extended_cover']


def test_numerical_distributions_bounded_and_positive():
    run=evaluate_scenarios(EconomicScenario.model_validate(example()))
    x=run.sampled_inputs
    assert np.all((x['resource.addressable_delay_fraction']>=.2)&(x['resource.addressable_delay_fraction']<=.65))
    assert np.all(x['resource.incremental_return_cost_aud_per_return']>0)
    assert np.all((x['baseline.unplanned_72h_return_rate']>=0)&(x['baseline.unplanned_72h_return_rate']<=1))


def test_summary_reports_strategy_specific_threshold_without_recommendation():
    x=EconomicScenario.model_validate(deterministic(example()))
    s=summarise_p4(evaluate_scenarios(x))
    i=s['strategies']['liaison_service']
    assert i['threshold_annual_service_cost_aud'] == pytest.approx(81270)
    assert i['break_even_coverage_fraction']>1
    assert s['financially_best_mean_strategy_not_clinical_recommendation'] in {None,'current_care','liaison_service','extended_cover'}


def test_finite_inputs_cannot_overflow_into_invalid_financial_results():
    z=deterministic(example())
    z['resource']['net_index_delay_cost_aud_per_day']=fixed(1e308,'AUD_per_icu_day')
    with pytest.raises(ValueError,match='nonfinite model outcome'):
        evaluate_scenarios(EconomicScenario.model_validate(z))


def test_one_way_sensitivity_is_versioned_and_sorted_without_hidden_baseline_substitution():
    from icu_liaison.p4_model import one_way_sensitivity
    scenario=EconomicScenario.model_validate(example())
    rows=one_way_sensitivity(scenario,'liaison_service')
    assert len(rows)>5
    assert all(x['parameter'] in scenario.all_priors() for x in rows)
    assert all(x['low_net_resource_aud']<=x['high_net_resource_aud'] for x in rows)
    assert rows==sorted(rows,key=lambda x:x['absolute_net_resource_swing_aud'],reverse=True)
    assert not any(x['parameter']=='baseline.exit_block_rate' for x in rows)
    assert all(x['interpretation']=='one_at_a_time_prior_quantile_not_joint_posterior' for x in rows)
