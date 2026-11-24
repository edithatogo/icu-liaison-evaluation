"""Claim decisions tied to actual fictional workflow artifacts."""

from hashlib import sha256
import json
import os
import subprocess
import sys

import pytest

from icu_liaison.p11_figure import build_figure
from icu_liaison.p11_model import build_case
from icu_liaison.p11_p9 import build_p9
from icu_liaison.p11_summary import build_summary
from tools.p10_falsification import run_suite
from tools.validate_measurement_contracts import CONTRACTS, ROOT, assess_claim


@pytest.fixture(scope="module")
def synthetic_run(tmp_path_factory):
    directory = tmp_path_factory.mktemp("p10-run")
    output = directory / "outputs"
    inputs = ROOT / "model-inputs"
    case = json.loads((inputs / "p11/cases/base.json").read_bytes())
    case["iterations"] = 32
    case_file = directory / "case.json"
    case_file.write_text(json.dumps(case), encoding="utf-8")
    model_pointer = output / "state/models/base.json"
    build_case(case_file, inputs / "p4/illustrative.json", output, model_pointer)
    build_figure(model_pointer, inputs / "p11/f01-style.json", output, output / "state/figures/base.json")
    build_p9(model_pointer, output, output / "state/priority-figures/base.json")
    suite = directory / "suite.json"
    suite.write_text(json.dumps({"schema_version": 1, "data_class": "synthetic", "cases": ["base"]}),
                     encoding="utf-8")
    audit = directory / "falsification.json"
    audit.write_text(json.dumps(run_suite(32)), encoding="utf-8")
    build_summary(suite, output, [model_pointer], audit, output / "state/summary.json")
    return output


@pytest.mark.parametrize(("artifact", "metric", "denominator"), [
    ("T04", "M25", "D09"),
    ("F01", "M25", "D09"),
    ("F20", "M16", "D11"),
])
def test_claim_binds_a_verified_artifact_to_measures(synthetic_run, artifact, metric, denominator):
    result = assess_claim("synthetic_illustration", run=synthetic_run, case_id="base", artifact_id=artifact)
    assert result["permitted"] is True and result["scope"] == "synthetic_illustration_only"
    assert metric in result["metric_ids"] and denominator in result["denominator_ids"]
    assert result["artifact"]["id"] == artifact
    assert result["artifact"]["sha256"] == sha256((synthetic_run / result["artifact"]["path"]).read_bytes()).hexdigest()
    assert result["policy_sha256"] == sha256((CONTRACTS / "claim-policy.json").read_bytes()).hexdigest()
    assert result["investment_ready"] is False and result["external_authority_verified"] is False
    record = json.loads((synthetic_run / "state/models/base.json").read_bytes())
    assert result["model_run_id"] == record["model_run_id"]
    assert result["model_record_sha256"] == record["run_record_sha256"]


@pytest.mark.parametrize("claim", [
    "local_descriptive", "clinical_effectiveness", "cash_savings",
    "nwau_activity", "provider_qualified", "investment_ready",
])
def test_external_claims_remain_denied_before_any_artifact_read(tmp_path, claim):
    assert assess_claim(claim, {"approved": True}, run=tmp_path / "missing",
                        case_id="base", artifact_id="F01") == {
        "permitted": False, "reason": "trusted_external_verifier_not_connected",
    }


def test_claim_cannot_substitute_a_placeholder_or_unknown_scenario(synthetic_run):
    blocked = assess_claim("synthetic_illustration", run=synthetic_run, case_id="base", artifact_id="F16")
    assert blocked["permitted"] is False and blocked["reason"] == "reporting_artifact_requires_external_evidence"
    missing = assess_claim("synthetic_illustration", run=synthetic_run, case_id="different", artifact_id="F01")
    assert missing["permitted"] is False and missing["reason"] == "unknown_scenario"


def test_archived_figure_without_current_mark_replay_cannot_receive_claim(synthetic_run, monkeypatch):
    import icu_liaison.p11_p9 as figures

    monkeypatch.setattr(figures, "fingerprint", lambda: {"historical": True})
    result = assess_claim("synthetic_illustration", run=synthetic_run, case_id="base", artifact_id="F20")
    assert result == {"permitted": False, "reason": "figure_replay_unavailable"}


def test_archived_model_without_current_numeric_replay_cannot_receive_claim(synthetic_run, monkeypatch):
    import icu_liaison.p11_model as model

    monkeypatch.setattr(model, "_runtime", lambda: {"historical": True})
    result = assess_claim("synthetic_illustration", run=synthetic_run, case_id="base", artifact_id="T04")
    assert result == {"permitted": False, "reason": "model_replay_unavailable"}


def test_claim_does_not_use_a_different_reporting_catalogue(synthetic_run, tmp_path, monkeypatch):
    from tools import validate_reporting_contracts as reporting

    catalogue = json.loads(reporting.CATALOGUE.read_bytes())
    next(row for row in catalogue["tables"] if row["id"] == "T04")["title"] += " (revised)"
    replacement = tmp_path / "catalogue.json"
    replacement.write_text(json.dumps(catalogue), encoding="utf-8")
    monkeypatch.setattr(reporting, "CATALOGUE", replacement)
    result = assess_claim("synthetic_illustration", run=synthetic_run, case_id="base", artifact_id="T04")
    assert result == {"permitted": False, "reason": "reporting_contract_differs_from_verified_run"}


def test_claim_cli_rejects_a_changed_svg(synthetic_run):
    pointer = json.loads((synthetic_run / "state/figures/base.json").read_bytes())
    svg = synthetic_run / "figures" / pointer["figure_revision"] / "scenario-comparison.svg"
    command = [sys.executable, "-m", "tools.validate_measurement_contracts",
               "--claim", "synthetic_illustration", "--run", str(synthetic_run),
               "--case", "base", "--artifact", "F01"]
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
    original = svg.read_bytes()
    try:
        svg.write_bytes(original + b" ")
        rejected = subprocess.run(command, cwd=ROOT, env=environment,
                                  capture_output=True, text=True, timeout=45)
        assert rejected.returncode == 2
        assert json.loads(rejected.stdout)["reason"] == "run_verification_failed"
    finally:
        svg.write_bytes(original)
    admitted = subprocess.run(command, cwd=ROOT, env=environment,
                              capture_output=True, text=True, timeout=45)
    assert admitted.returncode == 0, admitted.stderr
    assert json.loads(admitted.stdout)["permitted"] is True
