"""Source-only prerollout registration and intervention fidelity boundaries."""
from typing import Any
from copy import deepcopy

import pytest

from tools.validate_preregistration import REGISTRY, validate_preregistration
import json


def load() -> dict[str, Any]:
    value = json.loads(REGISTRY.read_text())
    assert isinstance(value, dict)
    return value


def test_draft_preregistration_preserves_clinical_index_and_all_live_denominator() -> None:
    result = validate_preregistration()
    assert result["status"] == "draft_not_registered"
    assert result["denominators"]["clinical_index"] == "D03"
    assert result["denominators"]["ANZICS_ready_valid"] == "D04"
    assert result["denominators"]["index_return_72h"] == "D05"
    assert result["index_delay_metric_gap"] is None
    assert result["index_delay_metric_id"] == "M31"
    assert result["denominators"]["index_ready_valid"] == "D14"
    assert result["site_approved"] is False


def test_preregistration_cannot_fake_clinical_registration_or_approval() -> None:
    a=deepcopy(load())
    a["frozen_plan_sha256"]="a"*64
    with pytest.raises(ValueError,match="schema"):
        validate_preregistration(a)
    a=deepcopy(load())
    a["clinical_governance_review"]={"approved": True}
    with pytest.raises(ValueError,match="schema"):
        validate_preregistration(a)


def test_missing_mandatory_safety_outcome_or_followup_window_rejected() -> None:
    a=deepcopy(load())
    a["outcomes"]["mandatory_safety_endpoints"].pop()
    with pytest.raises(ValueError,match="schema|mandatory"):
        validate_preregistration(a)
    a=deepcopy(load())
    a["outcomes"]["return_followup_hours"]=24
    with pytest.raises(ValueError,match="schema|72-hour"):
        validate_preregistration(a)


def test_contact_based_analysis_cannot_be_mislabeled_intention_to_cover() -> None:
    a=deepcopy(load())
    a["exposure_definition"]["primary"]="contact_receipt_only"
    with pytest.raises(ValueError,match="schema"):
        validate_preregistration(a)


def test_uncounted_roster_exposure_not_assumed_zero() -> None:
    a=load()
    assert a["exposure_definition"]["existing_rostered_hours"] is None
    assert a["exposure_definition"]["incremental_rostered_hours"] is None
    assert a["exposure_definition"]["actual_contact_events"] is None
    a["exposure_definition"]["actual_contact_events"]=[]
    with pytest.raises(ValueError,match="schema"):
        validate_preregistration(a)


def test_future_index_delay_metric_cannot_be_falsely_replaced_by_all_live() -> None:
    a=deepcopy(load())
    a["outcomes"]["primary_index_ready_delay_metric_id"]="M05"
    with pytest.raises(ValueError,match="schema|index"):
        validate_preregistration(a)
