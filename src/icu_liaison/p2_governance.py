"""P2.5 governance sign-off pack and 32-to-115 CHHHS field crosswalk validators."""
from __future__ import annotations

from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .data_request import DataRequestCatalogue
from .protocol import EvaluationProtocol, load_data_dictionary

REQUIRED_GOVERNANCE_GATES = frozenset(
    {
        "icu_medical_clinical_director",
        "icu_nursing_liaison_lead",
        "ward_nursing_operations",
        "finance_and_clinical_costing",
        "clinical_governance_patient_safety",
        "hrec_and_data_stewardship",
        "first_nations_and_consumer_governance",
    }
)


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class FieldCrosswalkEntry(_StrictModel):
    """Mapping from one P2 clinical-data-dictionary field to CHHHS request dataset field(s)."""

    p2_field: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    target_fields: list[str] = Field(min_length=1)
    mapping_kind: Literal[
        "exact",
        "renamed",
        "derived",
        "filtered_event",
        "aggregate_governed",
    ]
    reconciliation_note: str | None = None

    @model_validator(mode="after")
    def validate_mapping_rules(self) -> "FieldCrosswalkEntry":
        if any(not f.strip() for f in self.target_fields):
            raise ValueError(f"{self.p2_field}: target_fields cannot contain blank names")
        if len(set(self.target_fields)) != len(self.target_fields):
            raise ValueError(f"{self.p2_field}: duplicate target_fields")
        if self.mapping_kind == "exact" and self.target_fields != [self.p2_field]:
            raise ValueError(
                f"{self.p2_field}: exact mapping must target [{self.p2_field!r}], got {self.target_fields}"
            )
        if self.mapping_kind != "exact" and (
            not self.reconciliation_note or not self.reconciliation_note.strip()
        ):
            raise ValueError(
                f"{self.p2_field}: non-exact mapping ({self.mapping_kind}) requires reconciliation_note"
            )
        return self


class FieldCrosswalk(_StrictModel):
    """Complete mapping between P2 dictionary fields and the CHHHS data request pack."""

    schema_version: Literal[1]
    status: Literal["planning_crosswalk_no_local_data"]
    p2_dictionary_path: str = Field(min_length=1)
    chhhs_request_path: str = Field(min_length=1)
    mappings: list[FieldCrosswalkEntry] = Field(min_length=1)

    @model_validator(mode="after")
    def reject_duplicate_p2_fields(self) -> "FieldCrosswalk":
        seen = [entry.p2_field for entry in self.mappings]
        if len(seen) != len(set(seen)):
            raise ValueError("duplicate p2_field in crosswalk")
        return self


class PendingProtocolDecisions(_StrictModel):
    """Site parameters in protocol.json that remain null until governance approval."""

    model_config = ConfigDict(allow_inf_nan=False)

    current_care_funded_fte: float | int | None = Field(default=None, ge=0)
    liaison_service_funded_fte: float | int | None = Field(default=None, ge=0)
    hours_of_coverage_per_week: float | int | None = Field(default=None, ge=0, le=168)
    approved_noninferiority_margins: dict[str, float | int] = Field(default_factory=dict)
    minimum_data_completeness_approved: float | int | None = Field(default=None, gt=0, le=1)
    ethics_or_qi_pathway: str | None = None


class GovernanceGate(_StrictModel):
    """Individual stakeholder governance sign-off record."""

    id: str = Field(min_length=1)
    owner_role: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    decision: Literal["pending", "approved", "rejected", "deferred"]
    approval_reference: str | None = None
    signed_date: str | None = None
    conditions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_approval_evidence(self) -> "GovernanceGate":
        if self.decision == "approved":
            if not self.approval_reference or not self.approval_reference.strip():
                raise ValueError(f"{self.id}: approved gate requires non-empty approval_reference")
            if not self.signed_date or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", self.signed_date):
                raise ValueError(f"{self.id}: approved gate requires YYYY-MM-DD signed_date")
            date.fromisoformat(self.signed_date)
        return self


class GovernanceSignoffPack(_StrictModel):
    """Reviewer declarations for the P2.5 stakeholder sign-off form."""

    schema_version: Literal[1]
    status: Literal["template_unapproved_no_site_signoff", "in_review", "site_approved"]
    protocol_id: str = Field(min_length=1)
    protocol_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    data_dictionary_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    pending_protocol_decisions: PendingProtocolDecisions
    gates: list[GovernanceGate] = Field(min_length=len(REQUIRED_GOVERNANCE_GATES))

    @model_validator(mode="after")
    def validate_gate_completeness_and_status(self) -> "GovernanceSignoffPack":
        gate_ids = [gate.id for gate in self.gates]
        if len(gate_ids) != len(set(gate_ids)):
            raise ValueError("duplicate governance gate id")
        if set(gate_ids) != REQUIRED_GOVERNANCE_GATES:
            raise ValueError("gates must match REQUIRED_GOVERNANCE_GATES exactly")

        if self.status == "template_unapproved_no_site_signoff":
            if any(gate.decision != "pending" for gate in self.gates):
                raise ValueError("unapproved template cannot mark any gate as non-pending")
        elif self.status == "site_approved":
            if any(gate.decision != "approved" for gate in self.gates):
                raise ValueError("site_approved requires all governance gates to be approved")
            decisions = self.pending_protocol_decisions
            required_values = (
                decisions.current_care_funded_fte,
                decisions.liaison_service_funded_fte,
                decisions.hours_of_coverage_per_week,
                decisions.minimum_data_completeness_approved,
                decisions.ethics_or_qi_pathway,
            )
            if any(val is None for val in required_values) or (
                isinstance(decisions.ethics_or_qi_pathway, str)
                and not decisions.ethics_or_qi_pathway.strip()
            ):
                raise ValueError("site_approved requires all pending_protocol_decisions to be populated")
            if not decisions.approved_noninferiority_margins:
                raise ValueError("site_approved requires non-empty approved_noninferiority_margins")
        return self


def _sha256(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def validate_p2_chhhs_crosswalk(
    crosswalk_path: Path,
    dictionary_path: Path,
    request_path: Path,
) -> dict:
    """Validate 1:1 coverage of all P2 dictionary fields against CHHHS request datasets."""
    crosswalk_bytes = Path(crosswalk_path).read_bytes()
    dictionary_bytes = Path(dictionary_path).read_bytes()
    request_bytes = Path(request_path).read_bytes()

    cw = FieldCrosswalk.model_validate_json(crosswalk_bytes)
    dictionary = load_data_dictionary(json.loads(dictionary_bytes))
    request = DataRequestCatalogue.model_validate_json(request_bytes)

    dict_fields = {field["name"] for field in dictionary["fields"]}
    mapped_fields = {entry.p2_field for entry in cw.mappings}
    if mapped_fields != dict_fields:
        missing = sorted(dict_fields - mapped_fields)
        extra = sorted(mapped_fields - dict_fields)
        raise ValueError(f"P2 dictionary coverage mismatch (missing={missing}, extra={extra})")

    dataset_fields = {
        ds.id: {field.name for field in ds.fields}
        for ds in request.datasets
    }
    for entry in cw.mappings:
        if entry.dataset_id not in dataset_fields:
            raise ValueError(f"{entry.p2_field}: unknown CHHHS dataset_id {entry.dataset_id!r}")
        unknown_targets = sorted(set(entry.target_fields) - dataset_fields[entry.dataset_id])
        if unknown_targets:
            raise ValueError(
                f"{entry.p2_field}: unknown target field(s) {unknown_targets} in dataset {entry.dataset_id!r}"
            )

    counts = dict(sorted(Counter(entry.mapping_kind for entry in cw.mappings).items()))
    exact_count = counts.get("exact", 0)
    return {
        "status": "CROSSWALK_VERIFIED_NO_LOCAL_DATA",
        "p2_field_count": len(cw.mappings),
        "exact_count": exact_count,
        "non_exact_count": len(cw.mappings) - exact_count,
        "counts_by_kind": counts,
        "datasets_referenced": sorted({entry.dataset_id for entry in cw.mappings}),
        "dictionary_sha256": _sha256(dictionary_bytes),
        "request_sha256": _sha256(request_bytes),
        "crosswalk_sha256": _sha256(crosswalk_bytes),
    }


def audit_governance_signoff(
    signoff_path: Path,
    protocol_path: Path,
    dictionary_path: Path,
) -> dict:
    """Check the sign-off document and its source bindings without authenticating decisions."""
    signoff_bytes = Path(signoff_path).read_bytes()
    protocol_bytes = Path(protocol_path).read_bytes()
    dictionary_bytes = Path(dictionary_path).read_bytes()

    pack = GovernanceSignoffPack.model_validate_json(signoff_bytes)
    actual_proto_sha = _sha256(protocol_bytes)
    if pack.protocol_sha256 != actual_proto_sha:
        raise ValueError(
            f"protocol_sha256 mismatch: signoff={pack.protocol_sha256}, actual={actual_proto_sha}"
        )
    actual_dict_sha = _sha256(dictionary_bytes)
    if pack.data_dictionary_sha256 != actual_dict_sha:
        raise ValueError(
            f"data_dictionary_sha256 mismatch: signoff={pack.data_dictionary_sha256}, actual={actual_dict_sha}"
        )
    protocol = EvaluationProtocol.model_validate_json(protocol_bytes)
    if pack.protocol_id != protocol.protocol_id:
        raise ValueError("protocol_id mismatch between the sign-off form and the draft protocol")
    load_data_dictionary(json.loads(dictionary_bytes))

    approved_count = sum(1 for gate in pack.gates if gate.decision == "approved")
    pending_count = sum(1 for gate in pack.gates if gate.decision == "pending")
    return {
        "status": "site_approval_declared_unverified" if pack.status == "site_approved" else pack.status,
        "declared_status": pack.status,
        "protocol_id": pack.protocol_id,
        "protocol_sha256": actual_proto_sha,
        "protocol_sha256_verified": True,
        "dictionary_sha256": actual_dict_sha,
        "data_dictionary_sha256_verified": True,
        "gate_count": len(pack.gates),
        "approved_gate_count": approved_count,
        "pending_gate_count": pending_count,
        "site_authority_verified": False,
        "ready_for_local_claims": False,
        "signoff_sha256": _sha256(signoff_bytes),
    }
