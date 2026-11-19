"""Independent model identities and fail-closed contracts."""
from pathlib import Path
import json
import math
import numpy as np
import pytest
from icu_liaison.schemas import Scenario
from icu_liaison.model import simulate, summarise

FIXTURE = Path(__file__).resolve().parents[1] / 'model-inputs' / 'illustrative.json'


def scenario():
    return Scenario.model_validate_json(FIXTURE.read_text())


def lock(parameter, value):
    parameter.low = parameter.value = parameter.high = value


def test_reproducible_draws_and_run_metadata():
    s = scenario()
    a = simulate(s)
    b = simulate(s)
    assert np.array_equal(a.net_resource_benefit_aud, b.net_resource_benefit_aud)
    assert np.array_equal(a.icu_bed_days_released, b.icu_bed_days_released)
    assert a.input_digest == b.input_digest
    assert len(a.net_resource_benefit_aud) == s.iterations


def test_nominal_annual_accounting_identity():
    s = scenario()
    for parameter in s.inputs.__dict__.values():
        lock(parameter, parameter.value)
    result = summarise(simulate(s))
    expected_days = 1_000 * .204 * .45 * .5 * 4 / 24
    expected_returns = 1_000 * .03 * .15
    expected_gross = expected_days * 1_800 + expected_returns * 15_000
    assert result['icu_bed_days_released']['mean'] == pytest.approx(expected_days)
    assert result['readmissions_avoided']['mean'] == pytest.approx(expected_returns)
    assert result['gross_resource_benefit_aud']['mean'] == pytest.approx(expected_gross)
    assert result['net_resource_benefit_aud']['mean'] == pytest.approx(expected_gross - 250_000)


def test_no_effect_is_not_savings():
    s = scenario()
    lock(s.inputs.addressable_cases_improved_fraction, 0)
    lock(s.inputs.relative_readmission_reduction, 0)
    res = simulate(s)
    assert np.all(res.icu_bed_days_released == 0)
    assert np.all(res.readmissions_avoided == 0)
    assert np.all(res.gross_resource_benefit_aud == 0)
    assert np.all(res.net_resource_benefit_aud < 0)


def test_more_appropriate_early_returns_can_be_modelled():
    s = scenario()
    lock(s.inputs.relative_readmission_reduction, -.25)
    assert np.all(simulate(s).readmissions_avoided < 0)


def test_public_rate_is_not_an_early_unplanned_readmission_rate():
    s = scenario()
    assert s.inputs.delayed_discharge_ge12h_rate.value == .204
    assert s.inputs.unplanned_72h_readmission_risk.status == 'illustrative_assumption'
    assert s.inputs.unplanned_72h_readmission_risk.value == .03


def test_unknown_or_untraceable_public_input_fails():
    data = json.loads(FIXTURE.read_text())
    data['inputs']['delayed_discharge_ge12h_rate']['url'] = None
    with pytest.raises(ValueError): Scenario.model_validate(data)
    data = json.loads(FIXTURE.read_text())
    data['patient_record'] = {'mrn': '111111'}
    with pytest.raises(ValueError): Scenario.model_validate(data)
    data = json.loads(FIXTURE.read_text())
    data['inputs']['unplanned_72h_readmission_risk']['high'] = 1.2
    with pytest.raises(ValueError): Scenario.model_validate(data)


def test_nonfinite_and_nonmonotonic_parameters_fail():
    s = scenario().model_dump()
    s['inputs']['annual_incremental_service_cost_aud']['value'] = float('nan')
    with pytest.raises(ValueError): Scenario.model_validate(s)
    s = scenario().model_dump()
    s['inputs']['annual_incremental_service_cost_aud']['low'] = 400000
    with pytest.raises(ValueError): Scenario.model_validate(s)


def test_distinct_input_seed_changes_uncertainty_draws():
    s = scenario()
    a = simulate(s)
    s.seed += 1
    b = simulate(s)
    assert not np.array_equal(a.net_resource_benefit_aud, b.net_resource_benefit_aud)


def test_sensitivity_interval_is_ordered_and_probability_bounded():
    out = summarise(simulate(scenario()))
    assert out['net_resource_benefit_aud']['p05'] <= out['net_resource_benefit_aud']['p50'] <= out['net_resource_benefit_aud']['p95']
    assert 0 <= out['probability_net_resource_benefit_nonnegative'] <= 1
    assert out['result_class'] == 'illustrative_not_chhhs_observed'
