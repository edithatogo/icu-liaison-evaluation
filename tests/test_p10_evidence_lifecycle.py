"""P10 evidence lifecycle: deterministic expiry and revocation checks."""
from copy import deepcopy
from datetime import date

import pytest
from tools.evidence_lifecycle import assess_registry, validate_registry


def test_unverified_registry_never_claims_site_admission() -> None:
    outcome = assess_registry(date(2026, 11, 19), price_year=2026)
    assert outcome["status"] == "all_sources_unverified"
    assert outcome["site_ready"] is False
    assert len(outcome["source_assessments"]) == 4
    assert all(not x["evidence_admitted"] for x in outcome["source_assessments"])


def test_expiry_is_exclusive_and_revocation_overrides_dates() -> None:
    r = deepcopy(validate_registry())
    s = r["records"][0]
    s.update(valid_from="2026-01-01", valid_until_exclusive="2027-01-01",
             pricing_year=2026)
    assert assess_registry(date(2026, 12, 31), price_year=2026,
                           registry=r)["source_assessments"][0]["temporal_state"] == (
                               "within_declared_dates_unverified")
    assert assess_registry(date(2027, 1, 1), price_year=2026,
                           registry=r)["source_assessments"][0]["temporal_state"] == "expired"
    s["revoked_at"] = "2026-06-01"
    assert assess_registry(date(2026, 12, 1), price_year=2026,
                           registry=r)["source_assessments"][0]["temporal_state"] == "revoked"


def test_mchs_wrong_year_cannot_be_considered_current() -> None:
    r = deepcopy(validate_registry())
    r["records"][0].update(valid_from="2026-01-01",
                            valid_until_exclusive="2027-01-01", pricing_year=2027)
    state = assess_registry(date(2026, 6, 1), price_year=2026,
                            registry=r)["source_assessments"][0]
    assert state["temporal_state"] == "pricing_year_unknown_or_mismatched"
    assert state["evidence_admitted"] is False


def test_future_effective_source_is_not_current() -> None:
    r = deepcopy(validate_registry())
    r["records"][0]["valid_from"] = "2027-07-01"
    out = assess_registry(date(2026, 11, 19), registry=r)
    assert out["source_assessments"][0]["temporal_state"] == "not_yet_effective"


@pytest.mark.parametrize("start,end", [
    ("2027-01-01", "2026-01-01"), ("2026-02-01", "2026-02-01")
])
def test_invalid_temporal_intervals_are_rejected(start: str, end: str) -> None:
    r = deepcopy(validate_registry())
    r["records"][0].update(valid_from=start, valid_until_exclusive=end)
    with pytest.raises(ValueError, match="invalid source validity"):
        validate_registry(r)


def test_fake_verification_flag_is_rejected() -> None:
    r = deepcopy(validate_registry())
    r["records"][0]["verification"] = "trusted_approved"
    with pytest.raises(ValueError, match="schema"):
        validate_registry(r)


def test_unknown_metric_and_source_ids_are_rejected() -> None:
    r = deepcopy(validate_registry())
    r["records"][0]["dependent_metric_ids"] = ["M99"]
    with pytest.raises(ValueError, match="unknown dependent metric"):
        validate_registry(r)


def test_duplicate_source_id_is_rejected() -> None:
    r = deepcopy(validate_registry())
    r["records"][0]["source_id"] = r["records"][1]["source_id"]
    with pytest.raises(ValueError, match="duplicate source identity"):
        validate_registry(r)
