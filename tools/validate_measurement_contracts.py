"""Validate the P10 contracts and assess claims on verified fictional artifacts."""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from typing import Any
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "reporting"
DATA_REQUEST = ROOT / "model-inputs" / "chhhs-data-request.json"
SYNTHETIC_CLAIM = "synthetic_illustration"
CLAIM_IDS = {
    SYNTHETIC_CLAIM, "local_descriptive", "clinical_effectiveness", "cash_savings",
    "nwau_activity", "provider_qualified", "investment_ready",
}
CLAIM_POLICY_STATUS = {
    "2026-11-19-P10-source-claims-v1": "template_only",
    "2026-11-25-P10-source-claims-v2": "verified_run_assessment",
}

def _read(name: str) -> dict[str, Any]:
    value = json.loads((CONTRACTS / name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("contract must be a JSON object")
    return value

def _validate_schema(value: dict[str, Any], name: str) -> None:
    schema = _read(name)
    Draft202012Validator.check_schema(schema)
    issues = sorted(Draft202012Validator(schema).iter_errors(value),
                    key=lambda e: (str(list(e.path)), e.message))
    if issues:
        i = issues[0]
        raise ValueError(f"{name} schema violation at {list(i.path)}: {i.message}")

def _claim_rules(policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    _validate_schema(policy, "claim-policy.schema.json")
    rules = {rule["id"]: rule for rule in policy["claim_classes"]}
    if set(rules) != CLAIM_IDS or len(rules) != len(policy["claim_classes"]):
        raise ValueError("claim policy incomplete or contains duplicate classes")
    synthetic = rules[SYNTHETIC_CLAIM]
    if (synthetic["requires_trusted_external_verifier"] or not synthetic["public_source_can_validate"]
            or set(synthetic["required_evidence"]) != {"p5_input_digest", "p5_numeric_review", "manifest_verified"}
            or policy["synthetic_evidence_receipt_status"] != CLAIM_POLICY_STATUS[policy["policy_revision"]]):
        raise ValueError("synthetic claim requirements differ from the assessment contract")
    for claim, rule in rules.items():
        if claim != SYNTHETIC_CLAIM and (
                rule["public_source_can_validate"] or not rule["requires_trusted_external_verifier"]):
            raise ValueError("external claim cannot be granted by JSON")
    return rules

def validate_assurance(*, catalogue: dict[str, Any] | None = None,
                       registry: dict[str, Any] | None = None,
                       policy: dict[str, Any] | None = None,
                       visual: dict[str, Any] | None = None,
                       taxonomy: dict[str, Any] | None = None) -> dict[str, Any]:
    c = catalogue if catalogue is not None else _read("catalogue.json")
    m = registry if registry is not None else _read("metrics.json")
    p = policy if policy is not None else _read("claim-policy.json")
    v = visual if visual is not None else _read("visual-review.json")
    u = taxonomy if taxonomy is not None else _read("uncertainty-taxonomy.json")
    _validate_schema(m, "metrics.schema.json")
    _claim_rules(p)
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
    fixed = {"M02":"D02","M03":"D03","M05":"D04","M06":"D04","M08":"D05","M31":"D14",
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
    _validate_schema(_read("provenance-template.json"), "provenance-record.schema.json")
    return {"status":"source_definition_valid_not_site_qualified",
            "metrics":len(ids),"denominators":len(ds),
            "tables":len(c["tables"]),"figures":len(c["figures"]),
            "authorities_verified":0,"visual_checks_executed":0}

def _p5_report_reproduces(inputs: Path, model_record: dict[str, Any]) -> bool:
    """Replay the P5 bundle from its verified inputs without writing to the run."""
    from icu_liaison.p4_model import EconomicScenario
    from icu_liaison.p5_reporting import build_report
    from icu_liaison.p11_records import digest_file

    hashes = model_record["files_sha256"]
    with TemporaryDirectory(prefix="icu-liaison-p10-replay-") as temporary:
        frozen = Path(temporary)
        for name in ("effective-scenario.json", "protocol.json", "benchmarks.json", "source-register.json"):
            source = inputs / name
            if source.is_symlink() or not source.is_file():
                raise ValueError("recorded P5 replay input is missing or unsafe")
            payload = source.read_bytes()
            if sha256(payload).hexdigest() != hashes[f"inputs/{name}"]:
                raise ValueError("recorded P5 replay input changed after verification")
            (frozen / name).write_bytes(payload)
        scenario = EconomicScenario.model_validate_json((frozen / "effective-scenario.json").read_bytes())
        replay = frozen / "p5-report"
        build_report(scenario, replay, protocol=frozen / "protocol.json",
                     catalogue=frozen / "benchmarks.json", source_register=frozen / "source-register.json")
        expected_digest = hashes["p5-report/manifest.json"]
        return isinstance(expected_digest, str) and digest_file(replay / "manifest.json") == expected_digest


def _assess_synthetic_artifact(
    run: Path, case_id: str, artifact_id: str, disclosure: str, policy_sha256: str,
) -> dict[str, Any]:
    from icu_liaison.p11_model import _runtime, _source_hashes
    from icu_liaison.p11_p9 import fingerprint
    from icu_liaison.p11_records import digest_file, digest_json, read_json
    from tools.validate_reporting_contracts import CATALOGUE, verify_run_coverage

    raw_catalogue = CATALOGUE.read_bytes()
    catalogue = json.loads(raw_catalogue)
    spec = next((row for row in catalogue["tables"] + catalogue["figures"] if row["id"] == artifact_id), None)
    if spec is None:
        return {"permitted": False, "reason": "unknown_reporting_artifact"}
    if spec["status"] == "placeholder":
        return {"permitted": False, "reason": "reporting_artifact_requires_external_evidence"}
    coverage = verify_run_coverage(run, catalogue)
    case = next((row for row in coverage["scenarios"] if row["case_id"] == case_id), None)
    if case is None:
        return {"permitted": False, "reason": "unknown_scenario"}
    artifact = next((row for row in case["tables"] + case["figures"] if row["id"] == artifact_id), None)
    if artifact is None:
        return {"permitted": False, "reason": "artifact_not_produced_in_run"}

    model = run / "models" / case["model_run_id"]
    record = model / "run.json"
    if record.is_symlink() or not record.is_file():
        raise ValueError("model record is missing or unsafe after verification")
    record_bytes = record.read_bytes()
    model_record = json.loads(record_bytes)
    identity = model_record["identity"]
    if identity["model_source_sha256"] != _source_hashes() or identity["runtime"] != _runtime():
        return {"permitted": False, "reason": "model_replay_unavailable"}
    companion = next(row for row in case["figures"] if row["id"] != "F01")
    p9_record = run / "priority-figures" / companion["figure_revision"] / "figure-set.json"
    p9_identity = read_json(p9_record)["identity"]
    record_sha256 = sha256(record_bytes).hexdigest()
    if (digest_json(identity) != case["model_run_id"]
            or digest_json(p9_identity) != companion["figure_revision"]
            or p9_identity["run_record_sha256"] != record_sha256
            or digest_file(run / artifact["path"]) != artifact["sha256"]):
        raise ValueError("the model record or artifact changed after verification")
    if "figure_revision" in artifact and artifact_id != "F01":
        recorded = {key: p9_identity[key] for key in ("sources_sha256", "inputs_sha256", "runtime")}
        if recorded != fingerprint():
            return {"permitted": False, "reason": "figure_replay_unavailable"}

    raw_metrics = (CONTRACTS / "metrics.json").read_bytes()
    metrics_sha256 = sha256(raw_metrics).hexdigest()
    catalogue_sha256 = sha256(raw_catalogue).hexdigest()
    if (case["run_catalogue_sha256"] != catalogue_sha256
            or p9_identity["inputs_sha256"]["metrics.json"] != metrics_sha256):
        return {"permitted": False, "reason": "reporting_contract_differs_from_verified_run"}
    if not _p5_report_reproduces(model / "inputs", model_record):
        return {"permitted": False, "reason": "p5_report_replay_mismatch"}
    if digest_file(run / artifact["path"]) != artifact["sha256"]:
        raise ValueError("artifact changed during the P5 report replay")
    denominators = {metric["id"]: metric["denominator_id"] for metric in json.loads(raw_metrics)["metrics"]}
    return {
        "permitted": True, "reason": "verified_synthetic_artifact", "scope": "synthetic_illustration_only",
        "claim_id": SYNTHETIC_CLAIM, "disclosure": disclosure, "policy_sha256": policy_sha256,
        "summary_id": coverage["summary_id"], "case_id": case_id, "model_run_id": case["model_run_id"],
        "model_record_sha256": record_sha256, "artifact": artifact,
        "catalogue_sha256": catalogue_sha256, "metrics_sha256": metrics_sha256,
        "metric_ids": spec["metric_ids"], "denominator_ids": sorted({denominators[key] for key in spec["metric_ids"]}),
        "external_authority_verified": False, "clinical_safety_approved": False, "investment_ready": False,
    }


def assess_claim(
    claim_id: str, evidence: Any = None, *, run: Path | None = None,
    case_id: str | None = None, artifact_id: str | None = None,
) -> dict[str, Any]:
    """Assess an artifact from source files. Caller-supplied evidence carries no approval."""
    raw_policy = (CONTRACTS / "claim-policy.json").read_bytes()
    policy = json.loads(raw_policy)
    rule = _claim_rules(policy).get(claim_id)
    if rule is None:
        return {"permitted":False,"reason":"unknown_claim"}
    if rule["requires_trusted_external_verifier"]:
        return {"permitted":False,"reason":"trusted_external_verifier_not_connected"}
    if (run is None or case_id is None or artifact_id is None
            or policy["synthetic_evidence_receipt_status"] != "verified_run_assessment"):
        return {"permitted":False,"reason":"requires_verified_p5_bundle_not_untrusted_receipts"}
    try:
        return _assess_synthetic_artifact(run, case_id, artifact_id, rule["disclosure"],
                                          sha256(raw_policy).hexdigest())
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        return {"permitted": False, "reason": "run_verification_failed", "error_type": type(exc).__name__}

def validate_provenance(record: dict[str, Any]) -> dict[str, Any]:
    _validate_schema(record, "provenance-record.schema.json")
    return {"admitted":False,"reason":(
        "figure_unproduced" if record["status"] == "unproduced"
        else "independent_artifact_review_pending")}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim", help="Claim class from the P10 policy")
    parser.add_argument("--run", type=Path, help="Synthetic P11 output directory")
    parser.add_argument("--case", help="Scenario ID in the run")
    parser.add_argument("--artifact", help="Table or figure ID in the reporting catalogue")
    args = parser.parse_args()
    if args.claim is None:
        if any(value is not None for value in (args.run, args.case, args.artifact)):
            parser.error("--run, --case and --artifact require --claim")
        print(json.dumps(validate_assurance(), sort_keys=True))
        return 0
    result = assess_claim(args.claim, run=args.run, case_id=args.case, artifact_id=args.artifact)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["permitted"] else 2

if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
