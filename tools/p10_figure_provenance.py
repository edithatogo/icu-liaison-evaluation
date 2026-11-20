"""Source-bound provenance for the existing synthetic P5 F01 SVG only.

A receipt demonstrates reproducible file lineage and independent P5 computational
consistency. It never qualifies visual appearance, clinical safety, local hospital
outcomes, finance or the native-provider release. Output is kept OUTSIDE the
immutable P5 report directory.
"""
from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from icu_liaison.f01_review import review_f01
from icu_liaison.p4_model import EconomicScenario
from icu_liaison.p5_reporting import review_report
from tools.validate_reporting_contracts import CATALOGUE, ROOT, validate_report

SCHEMA = ROOT / "contracts/reporting/provenance-record.schema.json"
F_ID = "F01"
ARTIFACT = "scenario-comparison.svg"
EXPECTED_REVIEW = "self_consistency_verified_not_empirically_accepted"


def _digest(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError("provenance input is absent or symlinked")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def _validate_provenance(payload: dict) -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(payload)


def compile_receipt(report: Path, scenario_file: Path) -> dict:
    """Independently recompute hashes; do not trust an existing receipt or flag."""
    folder = Path(report)
    source = Path(scenario_file)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("synthetic report directory missing or symlinked")
    input_file_digest = _digest(source)
    scenario = EconomicScenario.model_validate_json(source.read_text(encoding="utf-8"))
    catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    figure = next(f for f in catalogue["figures"] if f["id"] == F_ID)
    if figure["evidence_tier"] != "synthetic_implemented" or figure["artifact"] != ARTIFACT:
        raise ValueError("F01 is not registered as the source-backed synthetic figure")
    p9 = validate_report(folder, catalogue)
    if F_ID not in p9["checked"]:
        raise ValueError("P5 report is missing its contracted F01 SVG")
    numeric = review_report(folder)
    if numeric["status"] != EXPECTED_REVIEW or numeric["provider_qualification"] is not False:
        raise ValueError("P5 independent numeric or provider status not admissible")
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    model = json.loads((folder / "model-summary.json").read_text(encoding="utf-8"))
    model_fingerprint = hashlib.sha256(_canonical(
        scenario.model_dump(mode="json"))).hexdigest()
    if (manifest.get("source_model_input_digest_sha256") != model_fingerprint or
            model.get("input_digest_sha256") != model_fingerprint):
        raise ValueError("scenario input digest does not match P5 output")
    if (manifest.get("scenario_id") != scenario.scenario_id or
            model.get("scenario_id") != scenario.scenario_id or
            model.get("draws") != scenario.iterations or
            model.get("price_year") != scenario.price_year):
        raise ValueError("scenario ID, draws or price year differ from report")
    if (manifest.get("data_class") != "synthetic" or
            manifest.get("publication_status") != "illustrative_only" or
            manifest.get("installed_provider_qualification") is not False or
            model.get("investment_ready") is not False):
        raise ValueError("unqualified P5 result asserted higher evidence")
    svg = folder / ARTIFACT
    artifact_digest = _digest(svg)
    if manifest["files_sha256"].get(ARTIFACT) != artifact_digest:
        raise ValueError("F01 SVG differs from report manifest")
    marks = review_f01(svg, model)
    matplotlib_version = metadata.version("matplotlib")
    provenance = {
        "schema_version": 1,
        "figure_id": F_ID,
        "status": "rendered_unqualified",
        "source_class": "synthetic_only",
        "source_input_sha256": model_fingerprint,
        "model_seed": scenario.seed,
        "renderer_version": f"matplotlib-{matplotlib_version}",
        "artifact_sha256": artifact_digest,
        "numeric_receipt_sha256": hashlib.sha256(_canonical(numeric)).hexdigest(),
        "visual_receipt_sha256": None,
        "approval_authority": None,
    }
    _validate_provenance(provenance)
    sources = {
        "raw_scenario_sha256": input_file_digest,
        "canonical_scenario_sha256": model_fingerprint,
        "p4_model_source_sha256": _digest(ROOT / "src/icu_liaison/p4_model.py"),
        "p5_renderer_source_sha256": _digest(ROOT / "src/icu_liaison/p5_reporting.py"),
        "p9_catalogue_sha256": _digest(CATALOGUE),
        "report_manifest_sha256": _digest(folder / "manifest.json"),
        "figure_svg_sha256": artifact_digest,
        "mark_reader_sha256": _digest(ROOT / "src/icu_liaison/f01_review.py"),
    }
    return {
        "schema_version": 1,
        "figure_id": F_ID,
        "status": "rendered_unqualified",
        "publication_scope": "synthetic_computational_consistency_only",
        "provenance": provenance,
        "sources": sources,
        "numerical_review": numeric,
        "svg_mark_review": marks,
        "p9_review_status": p9["status"],
        "directed_edges": [
            ["scenario_input", "P4_paired_draws"],
            ["P4_paired_draws", "T01_cost_consequences"],
            ["T01_cost_consequences", F_ID],
            ["P5_numeric_review", F_ID],
            ["P9_structural_review", F_ID],
            ["model_summary_mean_and_percentiles", "F01_SVG_marks"],
        ],
        "unverified": [
            "visual_human_or_multiviewport_acceptance",
            "clinical_effectiveness",
            "finance_cash_realisability",
            "CHHHS_site_approval",
            "native_provider_release",
        ],
    }


def verify_receipt(report: Path, scenario: Path, receipt: dict) -> dict:
    """A forged receipt cannot override source, figure or model hashes."""
    expected = compile_receipt(report, scenario)
    if receipt != expected:
        raise ValueError("provenance receipt does not match independently recomputed source")
    return {
        "status": "rendered_unqualified",
        "figure_id": F_ID,
        "checks": ["source_sha256", "canonical_input_digest", "P5_numeric_review",
                   "P9_figure_contract", "SVG_and_manifest_sha256", "F01_mean_and_percentile_marks"],
        "visual_checks_executed": 0,
        "external_claims_approved": False,
    }


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--report", required=True, type=Path)
    cli.add_argument("--scenario", required=True, type=Path)
    cli.add_argument("--output", type=Path)
    cli.add_argument("--verify", type=Path)
    a = cli.parse_args()
    if bool(a.output) == bool(a.verify):
        cli.error("choose exactly one of --output and --verify")
    if a.verify:
        result = verify_receipt(a.report, a.scenario,
                                json.loads(a.verify.read_text(encoding="utf-8")))
    else:
        result = compile_receipt(a.report, a.scenario)
        target = a.output
        assert target is not None
        if target.exists() or target.is_symlink():
            raise FileExistsError("cannot overwrite provenance receipt")
        report = a.report.resolve()
        if target.resolve().is_relative_to(report):
            raise ValueError("receipt must be outside immutable P5 report")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")
    print(json.dumps({
        "figure_id": F_ID, "status": "rendered_unqualified",
        "verified": bool(a.verify),
        "investment_ready": False, "visual_checks_executed": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
