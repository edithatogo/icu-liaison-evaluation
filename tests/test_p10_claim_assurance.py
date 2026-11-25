"""Claim decisions tied to actual fictional workflow artifacts."""
from icu_liaison.p4_model import P4Run
from pytest import CaptureFixture, MonkeyPatch, TempPathFactory

from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any
import subprocess
import sys

import pytest

from icu_liaison.p11_figure import build_figure
from icu_liaison.p11_model import build_case
from icu_liaison.p11_p9 import build_p9
from icu_liaison.p11_summary import build_summary
from tools.p10_falsification import run_suite
from tools.validate_measurement_contracts import CONTRACTS, ROOT, assess_claim


def _build_synthetic_run(directory: Path) -> Path:
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


@pytest.fixture(scope="module")
def synthetic_run(tmp_path_factory: TempPathFactory) -> Path:
    return _build_synthetic_run(tmp_path_factory.mktemp("p10-run"))


@pytest.mark.parametrize(("artifact", "metric", "denominator"), [
    ("T04", "M25", "D09"),
    ("F01", "M25", "D09"),
    ("F20", "M16", "D11"),
])
def test_claim_binds_a_verified_artifact_to_measures(synthetic_run: Path, artifact: str, metric: str, denominator: str) -> None:
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
def test_external_claims_remain_denied_before_any_artifact_read(tmp_path: Path, claim: str) -> None:
    assert assess_claim(claim, {"approved": True}, run=tmp_path / "missing",
                        case_id="base", artifact_id="F01") == {
        "permitted": False, "reason": "trusted_external_verifier_not_connected",
    }


def test_claim_cannot_substitute_a_placeholder_or_unknown_scenario(synthetic_run: Path) -> None:
    blocked = assess_claim("synthetic_illustration", run=synthetic_run, case_id="base", artifact_id="F16")
    assert blocked["permitted"] is False and blocked["reason"] == "reporting_artifact_requires_external_evidence"
    missing = assess_claim("synthetic_illustration", run=synthetic_run, case_id="different", artifact_id="F01")
    assert missing["permitted"] is False and missing["reason"] == "unknown_scenario"


def test_archived_figure_without_current_mark_replay_cannot_receive_claim(synthetic_run: Path, monkeypatch: MonkeyPatch) -> None:
    import icu_liaison.p11_p9 as figures

    monkeypatch.setattr(figures, "fingerprint", lambda: {"historical": True})
    result = assess_claim("synthetic_illustration", run=synthetic_run, case_id="base", artifact_id="F20")
    assert result == {"permitted": False, "reason": "figure_replay_unavailable"}


def test_archived_model_without_current_numeric_replay_cannot_receive_claim(synthetic_run: Path, monkeypatch: MonkeyPatch) -> None:
    import icu_liaison.p11_model as model

    monkeypatch.setattr(model, "_runtime", lambda: {"historical": True})
    result = assess_claim("synthetic_illustration", run=synthetic_run, case_id="base", artifact_id="T04")
    assert result == {"permitted": False, "reason": "model_replay_unavailable"}


def test_claim_does_not_use_a_different_reporting_catalogue(synthetic_run: Path, tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    from tools import validate_reporting_contracts as reporting

    catalogue = json.loads(reporting.CATALOGUE.read_bytes())
    next(row for row in catalogue["tables"] if row["id"] == "T04")["title"] += " (revised)"
    replacement = tmp_path / "catalogue.json"
    replacement.write_text(json.dumps(catalogue), encoding="utf-8")
    monkeypatch.setattr(reporting, "CATALOGUE", replacement)
    result = assess_claim("synthetic_illustration", run=synthetic_run, case_id="base", artifact_id="T04")
    assert result == {"permitted": False, "reason": "reporting_contract_differs_from_verified_run"}


@pytest.mark.parametrize("artifact_id", ["T01", "T03"])
def test_claim_requires_report_values_to_match_seeded_replay(tmp_path: Path, monkeypatch: MonkeyPatch, artifact_id: str) -> None:
    from icu_liaison import p5_reporting

    build_rows = p5_reporting._rows

    def inconsistent_report(run: P4Run) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        consequences, pairs, sensitivity = build_rows(run)
        if artifact_id == "T01":
            cost = next(row for row in consequences if row["measure"] == "incremental_service_cost_aud")
            cost["p95"] += 1000
        else:
            row = next(row for row in sensitivity if row["strategy_id"] != "liaison_service")
            row["low_net_resource_aud"] += 100
            row["high_net_resource_aud"] += 100
        return consequences, pairs, sensitivity

    with monkeypatch.context() as patch:
        patch.setattr(p5_reporting, "_rows", inconsistent_report)
        run = _build_synthetic_run(tmp_path)
    decision = assess_claim("synthetic_illustration", run=run, case_id="base", artifact_id=artifact_id)
    assert decision == {"permitted": False, "reason": "p5_report_replay_mismatch"}


@pytest.mark.parametrize("exception", [ValueError, AttributeError])
def test_claim_cli_omits_untrusted_failure_details(tmp_path: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str], exception: type[Exception]) -> None:
    from tools import validate_measurement_contracts as measurement
    from tools import validate_reporting_contracts as reporting

    def invalid_run(*_args: object) -> None:
        raise exception("example input value that must stay out of the decision")

    monkeypatch.setattr(reporting, "verify_run_coverage", invalid_run)
    monkeypatch.setattr(sys, "argv", [
        "validate_measurement_contracts", "--claim", "synthetic_illustration",
        "--run", str(tmp_path), "--case", "base", "--artifact", "T04",
    ])
    assert measurement.main() == 2
    captured = capsys.readouterr()
    assert not captured.err
    assert json.loads(captured.out) == {
        "permitted": False,
        "reason": "run_verification_failed",
        "error_type": exception.__name__,
    }


def test_claim_cli_rejects_a_changed_svg(synthetic_run: Path) -> None:
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
