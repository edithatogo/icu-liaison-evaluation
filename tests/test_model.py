"""Independent model identities and fail-closed contracts."""
from icu_liaison.schemas import Parameter
from pytest import CaptureFixture
from pathlib import Path
import json
import math
import numpy as np
import pytest
from icu_liaison.schemas import Scenario
from icu_liaison.model import simulate, summarise

FIXTURE = Path(__file__).resolve().parents[1] / 'model-inputs' / 'illustrative.json'


def scenario() -> Scenario:
    return Scenario.model_validate_json(FIXTURE.read_text())


def lock(parameter: Parameter, value: float) -> None:
    parameter.low = parameter.value = parameter.high = value


def test_reproducible_draws_and_run_metadata() -> None:
    s = scenario()
    a = simulate(s)
    b = simulate(s)
    assert np.array_equal(a.net_resource_benefit_aud, b.net_resource_benefit_aud)
    assert np.array_equal(a.icu_bed_days_released, b.icu_bed_days_released)
    assert a.input_digest == b.input_digest
    assert len(a.net_resource_benefit_aud) == s.iterations


def test_nominal_annual_accounting_identity() -> None:
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


def test_no_effect_is_not_savings() -> None:
    s = scenario()
    lock(s.inputs.addressable_cases_improved_fraction, 0)
    lock(s.inputs.relative_readmission_reduction, 0)
    res = simulate(s)
    assert np.all(res.icu_bed_days_released == 0)
    assert np.all(res.readmissions_avoided == 0)
    assert np.all(res.gross_resource_benefit_aud == 0)
    assert np.all(res.net_resource_benefit_aud < 0)


def test_more_appropriate_early_returns_can_be_modelled() -> None:
    s = scenario()
    lock(s.inputs.relative_readmission_reduction, -.25)
    assert np.all(simulate(s).readmissions_avoided < 0)


def test_public_rate_is_not_an_early_unplanned_readmission_rate() -> None:
    s = scenario()
    assert s.inputs.delayed_discharge_ge12h_rate.value == .204
    assert s.inputs.unplanned_72h_readmission_risk.status == 'illustrative_assumption'
    assert s.inputs.unplanned_72h_readmission_risk.value == .03


def test_unknown_or_untraceable_public_input_fails() -> None:
    data = json.loads(FIXTURE.read_text())
    data['inputs']['delayed_discharge_ge12h_rate']['url'] = None
    with pytest.raises(ValueError): Scenario.model_validate(data)
    data = json.loads(FIXTURE.read_text())
    data['patient_record'] = {'mrn': '111111'}
    with pytest.raises(ValueError): Scenario.model_validate(data)
    data = json.loads(FIXTURE.read_text())
    data['inputs']['unplanned_72h_readmission_risk']['high'] = 1.2
    with pytest.raises(ValueError): Scenario.model_validate(data)


def test_nonfinite_and_nonmonotonic_parameters_fail() -> None:
    s = scenario().model_dump()
    s['inputs']['annual_incremental_service_cost_aud']['value'] = float('nan')
    with pytest.raises(ValueError): Scenario.model_validate(s)
    s = scenario().model_dump()
    s['inputs']['annual_incremental_service_cost_aud']['low'] = 400000
    with pytest.raises(ValueError): Scenario.model_validate(s)


def test_distinct_input_seed_changes_uncertainty_draws() -> None:
    s = scenario()
    a = simulate(s)
    s.seed += 1
    b = simulate(s)
    assert not np.array_equal(a.net_resource_benefit_aud, b.net_resource_benefit_aud)


def test_sensitivity_interval_is_ordered_and_probability_bounded() -> None:
    out = summarise(simulate(scenario()))
    assert out['net_resource_benefit_aud']['p05'] <= out['net_resource_benefit_aud']['p50'] <= out['net_resource_benefit_aud']['p95']
    assert 0 <= out['probability_net_resource_benefit_nonnegative'] <= 1
    assert out['result_class'] == 'illustrative_not_chhhs_observed'


@pytest.mark.parametrize(
    "parameter", ["net_avoidable_cost_per_icu_day_aud", "annual_incremental_service_cost_aud"]
)
def test_portable_cli_rejects_nonfinite_results(tmp_path: Path, capsys: CaptureFixture[str], parameter: str) -> None:
    from icu_liaison.cli import main

    s = scenario()
    lock(getattr(s.inputs, parameter), 1e308)
    path = tmp_path / "scenario.json"
    path.write_text(s.model_dump_json(), encoding="utf-8")

    with pytest.raises(ValueError, match="finite"):
        summarise(simulate(s))
    with pytest.raises(SystemExit) as error:
        main([str(path)])
    assert error.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "finite" in captured.err


def test_portable_cli_does_not_echo_rejected_input(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    from icu_liaison.cli import main

    data = json.loads(FIXTURE.read_text())
    marker = "FICTIONAL-REJECTED-RECORD"
    data[marker] = {"id": marker}
    path = tmp_path / "scenario.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(SystemExit) as error:
        main([str(path)])
    assert error.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "invalid synthetic scenario" in captured.err
    assert marker not in captured.err
