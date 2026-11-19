"""P10 draft causal preregistration and implementation fidelity admission."""
from __future__ import annotations

import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "contracts/clinical/preregistration.json"
SCHEMA = ROOT / "contracts/clinical/preregistration.schema.json"
PROTOCOL = ROOT / "model-inputs/clinical-economic-protocol.json"
METRICS = ROOT / "contracts/reporting/metrics.json"


def validate_preregistration(value: dict | None = None) -> dict:
    data = value if value is not None else json.loads(REGISTRY.read_text())
    schema = json.loads(SCHEMA.read_text())
    Draft202012Validator.check_schema(schema)
    problems = list(Draft202012Validator(schema).iter_errors(data))
    if problems:
        raise ValueError("preregistration schema: " + problems[0].message)
    p = json.loads(PROTOCOL.read_text())
    if p["status"] != "draft_unapproved" or data["protocol_id"] != p["protocol_id"]:
        raise ValueError("unexpected clinical protocol/approval state")
    if data["target_population"]["denominator_id"] != "D03":
        raise ValueError("index eligibility cohort drift")
    if data["target_population"]["minimum_age_years_draft"] != p["eligibility"]["minimum_age_years"]:
        raise ValueError("draft age eligibility drift")
    if set(data["outcomes"]["mandatory_safety_endpoints"]) != set(
            p["safety"]["required_endpoints"]):
        raise ValueError("missing mandatory clinical safety balancing endpoints")
    metrics = {m["id"]:m for m in json.loads(METRICS.read_text())["metrics"]}
    if metrics["M05"]["denominator_id"] != "D04":
        raise ValueError("descriptive ready-time denominator is unrecognised")
    if data["outcomes"]["primary_index_ready_delay_metric_id"] is not None:
        raise ValueError("unqualified index-specific delay metric claimed")
    if data["outcomes"]["descriptive_all_live_ready_delay_metric_id"] != "M05":
        raise ValueError("descriptive and index estimand confused")
    if metrics["M08"]["denominator_id"] != "D05" or data["outcomes"]["return_followup_hours"] != 72:
        raise ValueError("72-hour index return denominator drift")
    if data["causal_design"]["rollout_date"] is not None:
        raise ValueError("draft source cannot supply unverified intervention rollout")
    if not data["causal_design"]["post_treatment_contact_not_baseline_confounder"]:
        raise ValueError("post-treatment contact cannot be a baseline adjustment")
    return {
        "status":"draft_not_registered",
        "clinical_effects_estimated":False,
        "fidelity_observed":False,
        "analysis_frozen":False,
        "site_approved":False,
        "index_delay_metric_gap":data["outcomes"]["index_ready_delay_gap"],
        "denominators":{"clinical_index":"D03","ANZICS_ready_valid":"D04",
                        "index_return_72h":"D05"},
    }


def main() -> int:
    print(json.dumps(validate_preregistration(),sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
