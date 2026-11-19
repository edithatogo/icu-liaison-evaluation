"""P10 source-only clinical safety gate negative tests."""
from copy import deepcopy

import pytest
from tools.evaluate_safety_decision import evaluate_decision, validate_policy


def test_all_six_p2_endpoints_preserved():
    p = validate_policy()
    assert {x["id"] for x in p["required_endpoints"]} == {
        "delayed_escalation", "post_icu_death",
        "return_severity_and_appropriateness", "treatment_limitations",
        "ward_cardiac_arrest", "ward_workload",
    }


@pytest.mark.parametrize("value,sign", [
    ("1000000", "positive"), ("-25.10", "negative"),
    ("0", "zero"), (None, "unknown"),
])
def test_economic_sign_never_overrides_unknown_clinical_safety(value, sign):
    result = evaluate_decision(value)
    assert result["economic_sign"] == sign
    assert result["decision"] == "not_authorised"
    assert result["investment_ready"] is False
    assert result["safety_overrides_favourable_economics"] is True


def test_missing_endpoint_is_rejected():
    policy = deepcopy(validate_policy())
    policy["required_endpoints"].pop()
    with pytest.raises(ValueError, match="schema|incomplete"):
        validate_policy(policy)


def test_fake_margin_or_measurement_is_rejected():
    policy = deepcopy(validate_policy())
    policy["required_endpoints"][0]["approved_noninferiority_margin"] = 0.02
    with pytest.raises(ValueError, match="schema"):
        validate_policy(policy)
    policy = deepcopy(validate_policy())
    policy["required_endpoints"][0]["observed_effect"] = 0.01
    with pytest.raises(ValueError, match="schema"):
        validate_policy(policy)


def test_fake_authority_rejected():
    policy = deepcopy(validate_policy())
    policy["signoff_authority"] = {"approved": True}
    with pytest.raises(ValueError, match="schema"):
        validate_policy(policy)


def test_return_rate_not_a_surrogate_for_return_severity():
    mapped = {x["id"]: x["metric_id"] for x in validate_policy()["required_endpoints"]}
    assert mapped["return_severity_and_appropriateness"] is None
    assert mapped["delayed_escalation"] is None
    assert mapped["post_icu_death"] == "M15"
    assert mapped["ward_cardiac_arrest"] == "M14"


@pytest.mark.parametrize("bad", ["NaN", "Infinity", "-Infinity", "not-a-number"])
def test_nonfinite_or_invalid_economics_rejected(bad):
    with pytest.raises(ValueError, match="nonfinite|invalid"):
        evaluate_decision(bad)
