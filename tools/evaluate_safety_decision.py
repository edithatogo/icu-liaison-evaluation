"""P10 clinical safety gate for illustrative ICU liaison economics."""
from __future__ import annotations
from typing import Any

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "contracts/clinical/safety-decision.json"
SCHEMA = ROOT / "contracts/clinical/safety-decision.schema.json"
PROTOCOL = ROOT / "model-inputs/clinical-economic-protocol.json"
METRICS = ROOT / "contracts/reporting/metrics.json"


def validate_policy(value: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = value if value is not None else json.loads(POLICY.read_text())
    schema = json.loads(SCHEMA.read_text())
    Draft202012Validator.check_schema(schema)
    failures = list(Draft202012Validator(schema).iter_errors(policy))
    if failures:
        raise ValueError("clinical safety schema violation: " + failures[0].message)
    proto = json.loads(PROTOCOL.read_text())
    if policy["protocol_id"] != proto["protocol_id"] or proto["status"] != "draft_unapproved":
        raise ValueError("unexpected clinical protocol or approval state")
    safety = proto["safety"]
    if safety["measurements_status"] != "unmeasured" or safety["approved_noninferiority_margins"]:
        raise ValueError("unknown safety evidence falsely promoted")
    actual = [e["id"] for e in policy["required_endpoints"]]
    expected = safety["required_endpoints"]
    if len(actual) != len(set(actual)) or set(actual) != set(expected):
        raise ValueError("incomplete or duplicated safety outcomes")
    registered = {m["id"] for m in json.loads(METRICS.read_text())["metrics"]}
    for e in policy["required_endpoints"]:
        if e["metric_id"] is not None and e["metric_id"] not in registered:
            raise ValueError("unknown safety metric")
        fixed = {"post_icu_death": "M15", "ward_cardiac_arrest": "M14"}
        if e["id"] in fixed and e["metric_id"] != fixed[e["id"]]:
            raise ValueError("safety metric identity drift")
    return policy


def evaluate_decision(synthetic_net_resource_benefit_aud: object | None = None,
                      policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Compute the sign only; refuse ALL clinical and investment acceptance."""
    defined = validate_policy(policy)
    if synthetic_net_resource_benefit_aud is None:
        sign = "unknown"
    else:
        try:
            value = Decimal(str(synthetic_net_resource_benefit_aud))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("invalid synthetic decimal amount") from exc
        if not value.is_finite():
            raise ValueError("nonfinite economic input")
        sign = "positive" if value > 0 else "negative" if value < 0 else "zero"
    return {
        "decision": "not_authorised",
        "economic_sign": sign,
        "data_class": "synthetic_only",
        "safety_status": "unmeasured",
        "noninferiority_margins_approved": False,
        "site_authority_verified": False,
        "investment_ready": False,
        "missing_safety_endpoints": [x["id"] for x in defined["required_endpoints"]],
        "safety_overrides_favourable_economics": True,
        "caution": "An appropriate early ICU return can reflect better rescue, not necessarily worse care.",
    }


def main() -> int:
    cli = argparse.ArgumentParser()
    cli.add_argument("--synthetic-net-resource-benefit", default="1000000")
    args = cli.parse_args()
    print(json.dumps(evaluate_decision(args.synthetic_net_resource_benefit),
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
