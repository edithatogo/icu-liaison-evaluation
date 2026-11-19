"""P10 source-only metric, provenance, uncertainty, visual and claim contract checks.

No public JSON flag or unverified digest constitutes clinical, financial or
provider approval. Actual file/authority verification is a separate task.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "reporting"
DATA_REQUEST = ROOT / "model-inputs" / "chhhs-data-request.json"

def _read(name: str) -> dict:
    return json.loads((CONTRACTS / name).read_text(encoding="utf-8"))

def _validate_schema(value: dict, name: str) -> None:
    schema = _read(name)
    Draft202012Validator.check_schema(schema)
    issues = sorted(Draft202012Validator(schema).iter_errors(value),
                    key=lambda e: (str(list(e.path)), e.message))
    if issues:
        i = issues[0]
        raise ValueError(f"{name} schema violation at {list(i.path)}: {i.message}")

def validate_assurance(*, catalogue: dict | None = None,
                       registry: dict | None = None,
                       policy: dict | None = None,
                       visual: dict | None = None,
                       taxonomy: dict | None = None) -> dict[str, Any]:
    c = catalogue if catalogue is not None else _read("catalogue.json")
    m = registry if registry is not None else _read("metrics.json")
    p = policy if policy is not None else _read("claim-policy.json")
    v = visual if visual is not None else _read("visual-review.json")
    u = taxonomy if taxonomy is not None else _read("uncertainty-taxonomy.json")
    _validate_schema(m, "metrics.schema.json")
    _validate_schema(p, "claim-policy.schema.json")
    datasets = json.loads(DATA_REQUEST.read_text(encoding="utf-8"))["datasets"]
    valid_datasets = {item["id"] for item in datasets}
    if len(valid_datasets) != len(datasets):
        raise ValueError("duplicate source dataset")
    ds = {item["id"]: item for item in m["denominators"]}
    ids = {item["id"]: item for item in m["metrics"]}
    if len(ds) != len(m["denominators"]) or len(ids) != len(m["metrics"]):
        raise ValueError("duplicate denominator or metric identity")
    for item in m["metrics"]:
        if item["denominator_id"] not in ds or not set(item["source_datasets"]) <= valid_datasets:
            raise ValueError("unknown source or denominator reference")
        if item["followup_hours"] and item["time_anchor"] != "physical_icu_departure":
            raise ValueError("follow-up anchored before ICU departure")
    fixed = {"M02":"D02","M03":"D03","M06":"D04","M08":"D05",
             "M09":"D01","M11":"D06","M20":"D10","M25":"D09","M26":"D09"}
    for name, denominator in fixed.items():
        if name not in ids or ids[name]["denominator_id"] != denominator:
            raise ValueError(f"denominator drift for {name}")
    if ids["M08"]["followup_hours"] != 72:
        raise ValueError("72-hour return horizon drift")
    if "12 hours" not in ids["M06"]["numerator"]:
        raise ValueError("12-hour exit block threshold drift")
    if ids["M20"]["unit"] != "NWAU" or ids["M26"]["unit"] != "AUD_2026":
        raise ValueError("NWAU and cash units conflated")
    classes = {x["id"] for x in u["classes"]}
    if u["status"] != "taxonomy_only_not_fitted" or len(classes) != len(u["classes"]):
        raise ValueError("uncertainty taxonomy incomplete or falsely fitted")
    tmap = {x["id"]: x for x in c["tables"]}
    if len(tmap) != len(c["tables"]):
        raise ValueError("duplicate table identity")
    for entry in c["tables"] + c["figures"]:
        refs = entry.get("metric_ids")
        if not refs or len(refs) != len(set(refs)) or not set(refs) <= set(ids):
            raise ValueError(f"unknown or duplicate metric references: {entry['id']}")
        uncertainty = entry.get("uncertainty_classes")
        if not uncertainty or len(uncertainty) != len(set(uncertainty)) or not set(uncertainty) <= classes:
            raise ValueError(f"unknown uncertainty class: {entry['id']}")
    for figure in c["figures"]:
        if not set(figure["metric_ids"]) & set(tmap[figure["source_table"]]["metric_ids"]):
            raise ValueError(f"figure {figure['id']} has no source-table metric")
        if (figure["evidence_tier"] in ("empirical_blocked","provider_blocked")
                and figure["interval_semantics"] != "not_estimated"):
            raise ValueError("unqualified figure cannot show accepted interval")
    if (v["status"] != "contract_only_unexecuted"
            or {x["id"] for x in v["required_profiles"]}
               != {"mobile","tablet","desktop","print_a4"}
            or len(v["checks"]) < 8):
        raise ValueError("visual review incomplete or falsely passed")
    if p["source_mode"] != "fail_closed_without_trusted_external_verifier":
        raise ValueError("claim gate weakened")
    claim_ids = {x["id"] for x in p["claim_classes"]}
    if len(claim_ids) != len(p["claim_classes"]) or "synthetic_illustration" not in claim_ids:
        raise ValueError("claim policy incomplete")
    for rule in p["claim_classes"]:
        if rule["id"] != "synthetic_illustration" and (
                rule["public_source_can_validate"] or not rule["requires_trusted_external_verifier"]):
            raise ValueError("external claim cannot be granted by JSON")
    _validate_schema(_read("provenance-template.json"), "provenance-record.schema.json")
    return {"status":"source_definition_valid_not_site_qualified",
            "metrics":len(ids),"denominators":len(ds),
            "tables":len(c["tables"]),"figures":len(c["figures"]),
            "authorities_verified":0,"visual_checks_executed":0}

def assess_claim(claim_id: str, evidence: Any = None) -> dict:
    """Always deny untrusted public-source claims; genuine evidence requires an adapter."""
    rule = next((x for x in _read("claim-policy.json")["claim_classes"]
                 if x["id"] == claim_id), None)
    if rule is None:
        return {"permitted":False,"reason":"unknown_claim"}
    if rule["requires_trusted_external_verifier"]:
        return {"permitted":False,"reason":"trusted_external_verifier_not_connected"}
    return {"permitted":False,"reason":"requires_verified_p5_bundle_not_untrusted_receipts"}

def validate_provenance(record: dict) -> dict:
    _validate_schema(record, "provenance-record.schema.json")
    return {"admitted":False,"reason":(
        "figure_unproduced" if record["status"] == "unproduced"
        else "independent_artifact_review_pending")}

def main() -> int:
    print(json.dumps(validate_assurance(), sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
