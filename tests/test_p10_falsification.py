"""P10 adversarial fixtures preserve scientific and accounting boundaries."""
from typing import Any
import json
import pytest

from tools.p10_falsification import MATRIX, _variant, run_suite
from icu_liaison.p4_model import EconomicScenario


@pytest.fixture(scope="module")
def receipt() -> dict[str, Any]:
    return run_suite(128)


def test_all_cases_run_with_safety_unmeasured(receipt: dict[str, Any]) -> None:
    assert receipt["status"] == "synthetic_falsification_passed_not_empirically_validated"
    assert len(receipt["cases"]) == 5
    assert receipt["investment_ready"] is False
    assert receipt["clinical_safety_measured"] is False
    assert all(case["invariants_passed"] for case in receipt["cases"])


def test_null_effect_yields_cost_without_benefit(receipt: dict[str, Any]) -> None:
    arms = receipt["cases"][0]["strategies"]
    assert all(abs(x["mean_bed_days_released"]) < 1e-8
               and abs(x["mean_returns_avoided"]) < 1e-8
               and x["mean_net_resource_benefit_aud"] < 0 for x in arms)


def test_harmful_effect_yields_additional_returns(receipt: dict[str, Any]) -> None:
    assert all(x["mean_returns_avoided"] < 0 for x in receipt["cases"][1]["strategies"])


def test_zero_capacity_is_not_same_as_zero_resource_benefit(receipt: dict[str, Any]) -> None:
    arms = receipt["cases"][3]["strategies"]
    assert all(x["mean_usable_bed_days"] == 0 and x["mean_bed_days_released"] > 0
               for x in arms)


def test_zero_cash_fractions_do_not_change_resource_perspective(receipt: dict[str, Any]) -> None:
    base = {x["strategy_id"]:x for x in receipt["cases"][3]["strategies"]}
    cash_zero = {x["strategy_id"]:x for x in receipt["cases"][4]["strategies"]}
    for arm in base:
        assert abs(base[arm]["mean_net_resource_benefit_aud"]
                   -cash_zero[arm]["mean_net_resource_benefit_aud"]) < 1e-8


def test_missing_or_unknown_falsification_case_rejected() -> None:
    raw=json.loads((MATRIX.parents[2]/"model-inputs/p4/illustrative.json").read_text())
    with pytest.raises(ValueError,match="unknown falsification"):
        _variant(raw,"assumed_clinical_noninferiority")


def test_invalid_negative_effect_magnitude_rejected_by_p4_schema() -> None:
    raw=json.loads((MATRIX.parents[2]/"model-inputs/p4/illustrative.json").read_text())
    raw["strategies"][1]["relative_return_effect"]["family"]="fixed"
    raw["strategies"][1]["relative_return_effect"]["params"]={"value":-2.0}
    with pytest.raises(ValueError,match="signed effect"):
        EconomicScenario.model_validate(raw)
