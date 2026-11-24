"""Tests for P2.5 CHHHS 32-to-115 field crosswalk and fail-closed governance sign-off pack."""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError
import pytest

from icu_liaison.p2_governance import audit_governance_signoff, validate_p2_chhhs_crosswalk

ROOT = Path(__file__).resolve().parents[1]
CROSSWALK = ROOT / "model-inputs/p2-chhhs-field-crosswalk.json"
DICTIONARY = ROOT / "model-inputs/clinical-data-dictionary.json"
REQUEST = ROOT / "model-inputs/chhhs-data-request.json"
SIGNOFF = ROOT / "model-inputs/p2-governance-signoff-TEMPLATE.json"
PROTOCOL = ROOT / "model-inputs/clinical-economic-protocol.json"


def test_committed_p2_chhhs_crosswalk_covers_all_32_fields() -> None:
    report = validate_p2_chhhs_crosswalk(CROSSWALK, DICTIONARY, REQUEST)
    assert report["status"] == "CROSSWALK_VERIFIED_NO_LOCAL_DATA"
    assert report["p2_field_count"] == 32
    assert report["exact_count"] == 9
    assert report["non_exact_count"] == 23
    assert len(report["crosswalk_sha256"]) == 64


def test_crosswalk_rejects_missing_duplicate_bad_target_and_exact_mismatch(tmp_path: Path) -> None:
    base = json.loads(CROSSWALK.read_text(encoding="utf-8"))

    missing = dict(base, mappings=base["mappings"][:-1])
    p = tmp_path / "missing.json"
    p.write_text(json.dumps(missing), encoding="utf-8")
    with pytest.raises(ValueError, match="coverage mismatch"):
        validate_p2_chhhs_crosswalk(p, DICTIONARY, REQUEST)

    duplicate = dict(base, mappings=base["mappings"] + [base["mappings"][0]])
    p.write_text(json.dumps(duplicate), encoding="utf-8")
    with pytest.raises(ValidationError, match="duplicate"):
        validate_p2_chhhs_crosswalk(p, DICTIONARY, REQUEST)

    bad_ds = json.loads(CROSSWALK.read_text(encoding="utf-8"))
    bad_ds["mappings"][0]["dataset_id"] = "nonexistent_dataset"
    p.write_text(json.dumps(bad_ds), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown CHHHS dataset_id"):
        validate_p2_chhhs_crosswalk(p, DICTIONARY, REQUEST)

    bad_field = json.loads(CROSSWALK.read_text(encoding="utf-8"))
    bad_field["mappings"][1]["target_fields"] = ["nonexistent_field"]
    p.write_text(json.dumps(bad_field), encoding="utf-8")
    with pytest.raises(ValueError, match="unknown target field"):
        validate_p2_chhhs_crosswalk(p, DICTIONARY, REQUEST)

    bad_exact = json.loads(CROSSWALK.read_text(encoding="utf-8"))
    bad_exact["mappings"][1]["mapping_kind"] = "exact"
    p.write_text(json.dumps(bad_exact), encoding="utf-8")
    with pytest.raises(ValidationError, match="exact mapping"):
        validate_p2_chhhs_crosswalk(p, DICTIONARY, REQUEST)

    no_note = json.loads(CROSSWALK.read_text(encoding="utf-8"))
    no_note["mappings"][1]["reconciliation_note"] = ""
    p.write_text(json.dumps(no_note), encoding="utf-8")
    with pytest.raises(ValidationError, match="reconciliation_note"):
        validate_p2_chhhs_crosswalk(p, DICTIONARY, REQUEST)


def test_committed_signoff_template_audits_and_stays_unapproved() -> None:
    report = audit_governance_signoff(SIGNOFF, PROTOCOL, DICTIONARY)
    assert report["status"] == "template_unapproved_no_site_signoff"
    assert report["protocol_sha256_verified"] is True
    assert report["data_dictionary_sha256_verified"] is True
    assert report["gate_count"] == 7
    assert report["approved_gate_count"] == 0
    assert report["pending_gate_count"] == 7
    assert report["ready_for_local_claims"] is False


def test_crosswalk_requires_a_valid_dictionary_even_if_field_names_match(tmp_path: Path) -> None:
    dictionary = json.loads(DICTIONARY.read_text(encoding="utf-8"))
    dictionary["fields"].append(dictionary["fields"][0])
    duplicate = tmp_path / "dictionary-with-duplicate.json"
    duplicate.write_text(json.dumps(dictionary), encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate dictionary field"):
        validate_p2_chhhs_crosswalk(CROSSWALK, duplicate, REQUEST)


def test_signoff_rejects_hash_tampering_missing_gate_and_false_approval(tmp_path: Path) -> None:
    p = tmp_path / "signoff.json"

    bad_proto_sha = json.loads(SIGNOFF.read_text(encoding="utf-8"))
    bad_proto_sha["protocol_sha256"] = "0" * 64
    p.write_text(json.dumps(bad_proto_sha), encoding="utf-8")
    with pytest.raises(ValueError, match="protocol_sha256 mismatch"):
        audit_governance_signoff(p, PROTOCOL, DICTIONARY)

    bad_dict_sha = json.loads(SIGNOFF.read_text(encoding="utf-8"))
    bad_dict_sha["data_dictionary_sha256"] = "f" * 64
    p.write_text(json.dumps(bad_dict_sha), encoding="utf-8")
    with pytest.raises(ValueError, match="data_dictionary_sha256 mismatch"):
        audit_governance_signoff(p, PROTOCOL, DICTIONARY)

    missing_gate = json.loads(SIGNOFF.read_text(encoding="utf-8"))
    missing_gate["gates"].pop()
    p.write_text(json.dumps(missing_gate), encoding="utf-8")
    with pytest.raises(ValidationError):
        audit_governance_signoff(p, PROTOCOL, DICTIONARY)

    approved_no_ref = json.loads(SIGNOFF.read_text(encoding="utf-8"))
    approved_no_ref["status"] = "in_review"
    approved_no_ref["gates"][0]["decision"] = "approved"
    p.write_text(json.dumps(approved_no_ref), encoding="utf-8")
    with pytest.raises(ValidationError, match="approval_reference"):
        audit_governance_signoff(p, PROTOCOL, DICTIONARY)

    false_site_approved = json.loads(SIGNOFF.read_text(encoding="utf-8"))
    false_site_approved["status"] = "site_approved"
    p.write_text(json.dumps(false_site_approved), encoding="utf-8")
    with pytest.raises(ValidationError, match="site_approved"):
        audit_governance_signoff(p, PROTOCOL, DICTIONARY)

    template_with_approval = json.loads(SIGNOFF.read_text(encoding="utf-8"))
    template_with_approval["gates"][0]["decision"] = "approved"
    template_with_approval["gates"][0]["approval_reference"] = "CHHHS-REF-1"
    template_with_approval["gates"][0]["signed_date"] = "2026-11-19"
    p.write_text(json.dumps(template_with_approval), encoding="utf-8")
    with pytest.raises(ValidationError, match="unapproved template"):
        audit_governance_signoff(p, PROTOCOL, DICTIONARY)


def test_complete_signoff_form_does_not_establish_local_authority(tmp_path: Path) -> None:
    claimed = json.loads(SIGNOFF.read_text(encoding="utf-8"))
    claimed["status"] = "site_approved"
    claimed["pending_protocol_decisions"] = {
        "current_care_funded_fte": 0.5,
        "liaison_service_funded_fte": 2.0,
        "hours_of_coverage_per_week": 80.0,
        "approved_noninferiority_margins": {"post_icu_death": 0.01},
        "minimum_data_completeness_approved": 0.9,
        "ethics_or_qi_pathway": "fictional-ethics-reference",
    }
    for idx, gate in enumerate(claimed["gates"]):
        gate["decision"] = "approved"
        gate["approval_reference"] = f"fictional-gate-{idx + 1}"
        gate["signed_date"] = "2026-11-19"
    signoff = tmp_path / "fictional-signoff.json"
    signoff.write_text(json.dumps(claimed), encoding="utf-8")
    audited = audit_governance_signoff(signoff, PROTOCOL, DICTIONARY)
    assert audited["status"] == "site_approval_declared_unverified"
    assert audited["declared_status"] == "site_approved"
    assert audited["approved_gate_count"] == 7
    assert audited["site_authority_verified"] is False
    assert audited["ready_for_local_claims"] is False
    assert "fictional-gate" not in json.dumps(audited)


@pytest.mark.parametrize(("field", "value"), [
    ("current_care_funded_fte", float("inf")),
    ("approved_noninferiority_margins", {"post_icu_death": float("nan")}),
])
def test_signoff_rejects_nonfinite_protocol_values(tmp_path: Path, field: str, value: object) -> None:
    pack = json.loads(SIGNOFF.read_text(encoding="utf-8"))
    pack["status"] = "in_review"
    pack["pending_protocol_decisions"][field] = value
    input_path = tmp_path / "signoff.json"
    input_path.write_text(json.dumps(pack), encoding="utf-8")

    with pytest.raises(ValidationError, match="finite number"):
        audit_governance_signoff(input_path, PROTOCOL, DICTIONARY)
