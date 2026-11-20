"""P10.10 source-to-F01 provenance: real synthetic reports and negative cases."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

import pytest

from icu_liaison.p4_model import EconomicScenario
from icu_liaison.p5_reporting import build_report
from tools.p10_figure_provenance import compile_receipt, verify_receipt
from tools.validate_reporting_contracts import ROOT


@pytest.fixture(scope="module")
def source_bundle(tmp_path_factory):
    base = tmp_path_factory.mktemp("p10-provenance")
    scenario_path = ROOT / "model-inputs/p4/illustrative.json"
    scenario = EconomicScenario.model_validate_json(scenario_path.read_text())
    report = base / "p5-report"
    build_report(scenario, report, plots=True)
    return report, scenario_path, base


def test_genuine_synthetic_figure_has_recomputed_lineage_not_approval(source_bundle):
    report, scenario, _ = source_bundle
    receipt = compile_receipt(report, scenario)
    assert receipt["figure_id"] == "F01"
    assert receipt["svg_mark_review"] == {"mean_bars": 3, "percentile_intervals": 3, "zero_reference": True}
    assert receipt["provenance"]["status"] == "rendered_unqualified"
    assert receipt["provenance"]["visual_receipt_sha256"] is None
    assert receipt["provenance"]["approval_authority"] is None
    assert receipt["provenance"]["model_seed"] == 20261118
    assert receipt["provenance"]["artifact_sha256"] == hashlib.sha256(
        (report / "scenario-comparison.svg").read_bytes()).hexdigest()
    result = verify_receipt(report, scenario, receipt)
    assert result["visual_checks_executed"] == 0
    assert result["external_claims_approved"] is False


def test_modified_scenario_with_matching_id_and_iterations_is_denied(source_bundle):
    report, scenario, tmp = source_bundle
    altered = json.loads(scenario.read_text())
    altered["seed"] += 1
    changed = tmp / "other-scenario.json"
    changed.write_text(json.dumps(altered), encoding="utf-8")
    with pytest.raises(ValueError, match="scenario input digest"):
        compile_receipt(report, changed)


def test_rehashed_svg_can_still_not_pass_old_receipt(source_bundle, tmp_path):
    report, scenario, _ = source_bundle
    receipt = compile_receipt(report, scenario)
    # Retain P9 accessibility text so a manifest rehash alone cannot fool P10.
    svg = report / "scenario-comparison.svg"
    original = svg.read_bytes()
    manifest_path = report / "manifest.json"
    original_manifest = manifest_path.read_bytes()
    try:
        svg.write_bytes(original.replace(b"black", b"navy") + b" ")
        manifest = json.loads(original_manifest)
        manifest["files_sha256"][svg.name] = hashlib.sha256(svg.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with pytest.raises(ValueError, match="does not match independently"):
            verify_receipt(report, scenario, receipt)
    finally:
        svg.write_bytes(original)
        manifest_path.write_bytes(original_manifest)


def test_no_svg_cannot_be_called_generated(source_bundle, tmp_path):
    report, scenario, _ = source_bundle
    svg = report / "scenario-comparison.svg"
    tmp = tmp_path / svg.name
    tmp.write_bytes(svg.read_bytes())
    svg.unlink()
    try:
        with pytest.raises((ValueError, FileNotFoundError)):
            compile_receipt(report, scenario)
    finally:
        svg.write_bytes(tmp.read_bytes())


def test_receipt_remains_output_outside_p5_manifest(source_bundle):
    report, scenario, _ = source_bundle
    before = set(p.name for p in report.iterdir())
    _ = compile_receipt(report, scenario)
    assert set(p.name for p in report.iterdir()) == before
    assert "p10-figure-provenance.json" not in before
