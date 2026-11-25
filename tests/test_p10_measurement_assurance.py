"""P10 metrics, denominators, provenance, claim and uncertainty admission tests."""
from __future__ import annotations
from typing import Any
import json
import pytest
from tools.validate_measurement_contracts import (
    CONTRACTS, validate_assurance, assess_claim, validate_provenance,
)

def load(name: str) -> dict[str, Any]:
    value = json.loads((CONTRACTS / name).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value

def test_all_seven_tables_and_24_figures_link_to_registered_metrics() -> None:
    result=validate_assurance()
    assert (result["tables"],result["figures"],result["metrics"],result["denominators"])==(7,24,31,14)
    assert result["authorities_verified"]==0 and result["visual_checks_executed"]==0

@pytest.mark.parametrize("id,wrong",[
    ("M02","D03"),("M03","D02"),("M06","D03"),
    ("M08","D02"),("M20","D08"),("M25","D08"),("M05","D14"),("M31","D04"),("M31","D03")
])
def test_denominator_drift_is_rejected(id: str,wrong: str) -> None:
    data=load("metrics.json")
    next(x for x in data["metrics"] if x["id"]==id)["denominator_id"]=wrong
    with pytest.raises(ValueError,match="denominator drift"):
        validate_assurance(registry=data)

def test_72_hour_return_cannot_become_24_hours() -> None:
    data=load("metrics.json")
    next(x for x in data["metrics"] if x["id"]=="M08")["followup_hours"]=24
    with pytest.raises(ValueError,match="72-hour"):
        validate_assurance(registry=data)

def test_metric_cannot_reference_nonexistent_source_dataset() -> None:
    data=load("metrics.json")
    data["metrics"][0]["source_datasets"]=["imaginary_hospital"]
    with pytest.raises(ValueError,match="unknown source"):
        validate_assurance(registry=data)

def test_figure_rejects_unknown_metric_and_wrong_source_table() -> None:
    c=load("catalogue.json")
    c["figures"][0]["metric_ids"]=["M99"]
    with pytest.raises(ValueError,match="unknown or duplicate metric"):
        validate_assurance(catalogue=c)
    c=load("catalogue.json")
    c["figures"][21]["metric_ids"]=["M30"]
    with pytest.raises(ValueError,match="no source-table metric"):
        validate_assurance(catalogue=c)

def test_cash_and_nwau_remain_different_units() -> None:
    data=load("metrics.json")
    next(x for x in data["metrics"] if x["id"]=="M20")["unit"]="AUD_2026"
    with pytest.raises(ValueError,match="NWAU and cash"):
        validate_assurance(registry=data)

def test_unqualified_empirical_figure_cannot_claim_psa_intervals() -> None:
    c=load("catalogue.json")
    c["figures"][16]["interval_semantics"]="psa_percentile_not_confidence_interval"
    with pytest.raises(ValueError,match="unqualified figure"):
        validate_assurance(catalogue=c)

def test_fake_finance_and_clinical_signatures_do_not_count() -> None:
    for claim in ("cash_savings","clinical_effectiveness","provider_qualified",
                  "investment_ready","nwau_activity","local_descriptive"):
        assert assess_claim(claim,{"approved":True,"signature":"fake"})=={
            "permitted":False,"reason":"trusted_external_verifier_not_connected"}
    assert assess_claim("synthetic_illustration",{"manifest_verified":True})=={
        "permitted":False,"reason":"requires_verified_p5_bundle_not_untrusted_receipts"}

def test_unknown_claim_rejected() -> None:
    assert assess_claim("unsupported_noninferiority")["reason"]=="unknown_claim"

def test_provenance_unproduced_and_forged_complete_outputs_fail_closed() -> None:
    p=load("provenance-template.json")
    assert validate_provenance(p)["admitted"] is False
    p["status"]="accepted_synthetic"
    with pytest.raises(ValueError,match="schema violation"):
        validate_provenance(p)
    p.update(source_input_sha256="a"*64,model_seed=7,
        renderer_version="fake",artifact_sha256="a"*64,
        numeric_receipt_sha256="a"*64,visual_receipt_sha256="a"*64)
    assert validate_provenance(p)["admitted"] is False

def test_visual_profiles_are_specified_not_executed() -> None:
    v=load("visual-review.json")
    assert {x["id"] for x in v["required_profiles"]}=={
        "mobile","tablet","desktop","print_a4"}
    v["status"]="passed"
    with pytest.raises(ValueError,match="visual review"):
        validate_assurance(visual=v)

def test_claim_policy_cannot_authorise_site_sources() -> None:
    p=load("claim-policy.json")
    next(x for x in p["claim_classes"] if x["id"]=="cash_savings")[
        "public_source_can_validate"]=True
    with pytest.raises(ValueError,match="external claim"):
        validate_assurance(policy=p)

def test_claim_policy_requires_all_registered_claim_classes() -> None:
    policy = load("claim-policy.json")
    policy["claim_classes"][-1]["id"] = "unrelated_class"
    with pytest.raises(ValueError, match="claim policy incomplete"):
        validate_assurance(policy=policy)

def test_claim_policy_requires_p5_evidence_for_synthetic_class() -> None:
    policy = load("claim-policy.json")
    policy["claim_classes"][0]["required_evidence"].remove("p5_numeric_review")
    with pytest.raises(ValueError, match="synthetic claim requirements"):
        validate_assurance(policy=policy)

def test_uncertainty_taxonomy_must_remain_unfitted() -> None:
    u=load("uncertainty-taxonomy.json")
    u["status"]="fitted_to_CHHHS"
    with pytest.raises(ValueError,match="uncertainty taxonomy"):
        validate_assurance(taxonomy=u)
