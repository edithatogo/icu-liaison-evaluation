"""P10 source-date freshness checks, never external provenance admission."""
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "contracts/reporting/evidence-lifecycle.json"
SCHEMA = ROOT / "contracts/reporting/evidence-lifecycle.schema.json"
METRICS = ROOT / "contracts/reporting/metrics.json"
CATALOGUE = ROOT / "contracts/reporting/catalogue.json"


def _date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value is not None else None


def validate_registry(value: dict | None = None) -> dict:
    r = value if value is not None else json.loads(REGISTRY.read_text())
    schema = json.loads(SCHEMA.read_text())
    Draft202012Validator.check_schema(schema)
    issues = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(r))
    if issues:
        raise ValueError("evidence lifecycle schema: " + issues[0].message)
    metrics = {x["id"] for x in json.loads(METRICS.read_text())["metrics"]}
    figures = {x["id"] for x in json.loads(CATALOGUE.read_text())["figures"]}
    ids = [x["source_id"] for x in r["records"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate source identity")
    for source in r["records"]:
        if not set(source["dependent_metric_ids"]) <= metrics:
            raise ValueError("unknown dependent metric")
        if not set(source["dependent_figure_ids"]) <= figures:
            raise ValueError("unknown dependent figure")
        start, end = _date(source["valid_from"]), _date(source["valid_until_exclusive"])
        if start is not None and end is not None and start >= end:
            raise ValueError("invalid source validity interval")
    return r


def assess_source(source: dict, as_of: date, *, price_year: int | None = None) -> dict:
    """Report temporal metadata without treating it as approved or authenticated."""
    start = _date(source["valid_from"])
    end = _date(source["valid_until_exclusive"])
    revoked = _date(source["revoked_at"])
    if revoked is not None and as_of >= revoked:
        state = "revoked"
    elif end is not None and as_of >= end:
        state = "expired"
    elif start is not None and as_of < start:
        state = "not_yet_effective"
    elif price_year is not None and source["kind"] == "activity_weight" and (
            source["pricing_year"] is None or source["pricing_year"] != price_year):
        state = "pricing_year_unknown_or_mismatched"
    elif start is None or end is None:
        state = "validity_unknown"
    else:
        state = "within_declared_dates_unverified"
    return {
        "source_id": source["source_id"],
        "temporal_state": state,
        "evidence_admitted": False,
        "approval_verified": False,
        "reason": "trusted_independent_source_and_revocation_verifier_not_connected",
    }


def assess_registry(as_of: date, *, price_year: int | None = None,
                    registry: dict | None = None) -> dict:
    if price_year is not None and not 2000 <= price_year <= 2100:
        raise ValueError("invalid price year")
    record = validate_registry(registry)
    return {
        "status": "all_sources_unverified",
        "as_of": as_of.isoformat(),
        "price_year": price_year,
        "source_assessments": [assess_source(x, as_of, price_year=price_year)
                               for x in record["records"]],
        "site_ready": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", type=date.fromisoformat, required=True)
    parser.add_argument("--price-year", type=int, default=2026)
    args = parser.parse_args()
    print(json.dumps(assess_registry(args.as_of, price_year=args.price_year),
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
