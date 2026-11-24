"""P1 behavioural requirements written before the provider integration changes.

Injected providers are boundary fakes, NOT evidence of installed Dapane/Voiage.
"""
from __future__ import annotations

from dataclasses import replace
from decimal import Decimal, ROUND_HALF_EVEN
from importlib.machinery import EXTENSION_SUFFIXES
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

from icu_liaison.adapters.dapane import (
    compare_valued_scenarios,
    make_nominal_cost_bridge,
)
from icu_liaison.adapters.voiage import evaluate_financial_information
from icu_liaison.provider_contracts import load_provider_lock, qualify_runtime_versions
from icu_liaison.model import simulate
from icu_liaison.schemas import Scenario

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def native_qualifier() -> ModuleType:
    spec = spec_from_file_location('icu_p1_qualifier', ROOT / 'tools/qualify_providers.py')
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture() -> Scenario:
    return Scenario.model_validate_json((ROOT / "model-inputs/illustrative.json").read_text())


def fixed_scenario() -> Scenario:
    scenario = fixture()
    for p in scenario.inputs.__dict__.values():
        p.low = p.value
        p.high = p.value
    scenario.iterations = 1
    return scenario


def independent_ledger_provider(request: dict) -> dict:
    """An elementary two-line independent test oracle, never a production fallback."""
    prices = {quote["id"]: Decimal(quote["amount"]) for quote in request["quotes"]}
    total = sum(
        (Decimal(use["quantity"]) * prices[use["quote_id"]] for use in request["usage"]),
        Decimal(0),
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
    return {
        "schema_version": "0.1", "status": "complete",
        "method_version": "dapane-exact-v0.1.0", "run_id": request["run_id"],
        "policy": dict(request["policy"]), "totals": {"rounded": format(total, ".2f")},
    }


def test_nominal_bridge_has_two_nonnegative_counterfactual_ledgers() -> None:
    bridge = make_nominal_cost_bridge(fixed_scenario(), price_year=2026)
    assert set(bridge) == {"current_care", "liaison_service"}
    assert {"index_delay", "avoidable_return"} == {
        line["target"] for line in bridge["current_care"]["usage"]
    }
    assert bridge["liaison_service"]["usage"][0]["target"] == "liaison_staffing"
    assert all(
        Decimal(u["quantity"]) >= 0
        for request in bridge.values()
        for u in request["usage"]
    )
    assert bridge["current_care"]["usage"][0]["quantity"] == "7.65"
    assert bridge["current_care"]["usage"][1]["quantity"] == "4.5"
    assert bridge["liaison_service"]["quotes"][0]["amount"] == "250000.0"
    assert all(request["policy"]["basis"] == "economic_cost" for request in bridge.values())


def test_nominal_bridge_handles_more_appropriate_returns_as_cost_not_negative_use() -> None:
    scenario = fixed_scenario()
    scenario.inputs.relative_readmission_reduction.low = -0.25
    scenario.inputs.relative_readmission_reduction.value = -0.25
    scenario.inputs.relative_readmission_reduction.high = -0.25
    bridge = make_nominal_cost_bridge(scenario)
    assert all(u["target"] != "avoidable_return" for u in bridge["current_care"]["usage"])
    additional = [u for u in bridge["liaison_service"]["usage"] if u["target"] == "additional_return"]
    assert len(additional) == 1
    assert Decimal(additional[0]["quantity"]) == Decimal("7.5")
    assert all(Decimal(u["quantity"]) >= 0 for req in bridge.values() for u in req["usage"])


def test_dapane_comparison_matches_independent_nominal_cost_identity() -> None:
    bridge = make_nominal_cost_bridge(fixed_scenario())
    result = compare_valued_scenarios(bridge, provider=independent_ledger_provider)
    # 7.65*1800 + 4.5*15000 - 250000 = -168730
    assert result["avoidable_current_care_slice_aud"] == "81270.00"
    assert result["additional_liaison_slice_aud"] == "250000.00"
    assert result["incremental_resource_benefit_aud"] == "-168730.00"
    assert result["basis"] == "economic_cost"
    assert result["interpretation"] == "incremental_resource_bridge_not_full_hospital_cost"


@pytest.mark.parametrize("mutation", [
    lambda report: report.update(status="partial"),
    lambda report: report.update(run_id="unrelated-run"),
    lambda report: report["policy"].update(currency="USD"),
    lambda report: report["totals"].update(rounded="NaN"),
    lambda report: report.update(method_version="unknown"),
    lambda report: report["totals"].update(rounded="-10.00"),
])
def test_unqualified_dapane_report_fails_closed(mutation) -> None:
    bridge = make_nominal_cost_bridge(fixed_scenario())

    def broken_provider(request):
        report = independent_ledger_provider(request)
        mutation(report)
        return report

    with pytest.raises((ValueError, RuntimeError)):
        compare_valued_scenarios(bridge, provider=broken_provider)


def test_nominal_bridge_rejects_non_synthetic_and_non_economic_benefit_claim() -> None:
    scenario = fixed_scenario()
    bridge = make_nominal_cost_bridge(scenario, basis="financial_cost")
    assert all(r["policy"]["basis"] == "financial_cost" for r in bridge.values())
    invalid = fixed_scenario()
    invalid.data_class = "patient_records"
    with pytest.raises(ValueError):
        make_nominal_cost_bridge(invalid)


def test_voiage_information_adapter_calls_provider_without_homegrown_evpi() -> None:
    draws = simulate(fixed_scenario())
    seen = {}

    def value_array_factory(data, labels):
        seen["array"] = data
        seen["labels"] = labels
        return (data, labels)

    class FakeAnalysis:
        def __init__(self, value_array):
            seen["array_arg"] = value_array

        def evpi(self):
            return 12.5

    result = evaluate_financial_information(
        draws, value_array_factory=value_array_factory, analysis_factory=FakeAnalysis,
    )
    assert result["evpi_per_decision_aud"] == 12.5
    assert result["decision_strategies"] == ["current_care", "liaison_service"]
    assert result["value_type"] == "financial_resource_only_not_qaly"
    assert seen["array"].shape == (1, 2)
    assert np.array_equal(seen["array"][:, 0], [0.0])


def test_voiage_adapter_rejects_invalid_provider_evpi() -> None:
    draws = simulate(fixed_scenario())
    class Bad:
        def __init__(self, value_array): pass
        def evpi(self): return float("nan")
    with pytest.raises(ValueError):
        evaluate_financial_information(draws, value_array_factory=lambda *args: "placeholder", analysis_factory=Bad)


def test_voiage_rejects_empty_draws_before_calling_provider() -> None:
    draws = replace(simulate(fixed_scenario()), net_resource_benefit_aud=np.array([]))

    def must_not_call_provider(*args):
        pytest.fail("Voiage should not receive an empty decision surface")

    with pytest.raises(ValueError, match="nonempty"):
        evaluate_financial_information(
            draws, value_array_factory=must_not_call_provider, analysis_factory=must_not_call_provider,
        )


def test_lock_contains_exact_known_provider_sources() -> None:
    lock = load_provider_lock(ROOT / "providers.lock.json")
    assert lock["providers"]["dapane"]["source_commit"] == "0658d94ad772023a0185a000b5254f9c2f4a63a9"
    assert lock["providers"]["voiage"]["tag_commit"] == "d40af0276019a7d63657349b53dad96845e2b4c1"
    assert lock["providers"]["voiage"]["version"] == "3.1.0"


def test_provider_version_gates_are_strict() -> None:
    lock = load_provider_lock(ROOT / "providers.lock.json")
    lookup = {"dapane": "0.1.0", "voiage": "3.1.0"}
    assert qualify_runtime_versions(lock, lookup.get, (3, 15, 2))["status"] == "candidate_environment_compatible"
    with pytest.raises(RuntimeError, match="Python 3.15.2"):
        qualify_runtime_versions(lock, lookup.get, (3, 13, 5))
    with pytest.raises(RuntimeError, match="voiage"):
        qualify_runtime_versions(lock, {"dapane": "0.1.0", "voiage": "3.0.0"}.get, (3, 15, 2))
    with pytest.raises(RuntimeError, match="dapane"):
        qualify_runtime_versions(lock, {"dapane": None, "voiage": "3.1.0"}.get, (3, 15, 2))


@pytest.mark.parametrize(("case", "reason"), [
    ("version_only", "expected native extension dapane._native is unavailable"),
    ("other_extension", "expected native extension dapane._native is unavailable"),
    ("shadowed_package", "import does not resolve to the installed distribution package"),
])
def test_native_qualifier_checks_import_identity_before_executing_provider(
    tmp_path: Path, case: str, reason: str,
) -> None:
    install = tmp_path / "installed"
    package = install / "dapane"
    package.mkdir(parents=True)
    dist_info = install / "dapane-0.1.0.dist-info"
    dist_info.mkdir()
    (dist_info / "METADATA").write_text("Name: dapane\nVersion: 0.1.0\n")
    (package / "__init__.py").write_text("raise AssertionError('installed package was executed')\n")
    record = ["dapane/__init__.py,,"]
    if case != "version_only":
        stem = "_native" if case == "shadowed_package" else "_other"
        extension = stem + EXTENSION_SUFFIXES[0]
        (package / extension).write_bytes(b"synthetic extension fixture")
        record.append(f"dapane/{extension},,")
    (dist_info / "RECORD").write_text("\n".join(record) + "\n")

    shadow = tmp_path / "shadow"
    shadow.mkdir()
    if case == "shadowed_package":
        (shadow / "dapane.py").write_text("raise AssertionError('shadowed package was executed')\n")
    process = subprocess.run(
        [sys.executable, str(ROOT / 'tools/qualify_providers.py'), '--provider', 'dapane'],
        cwd=ROOT, capture_output=True, text=True,
        env={**os.environ, 'PYTHONPATH': os.pathsep.join(map(str, (shadow, install, ROOT / 'src')))},
        check=False,
    )
    assert process.returncode == 2
    result = json.loads(process.stderr)
    assert result['status'] == 'UNVERIFIED'
    assert reason in result['reason']


def test_native_qualifier_requires_the_oracle_to_load_the_expected_extension(
    native_qualifier: ModuleType, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture, tmp_path: Path,
) -> None:
    installed = {'distribution': 'dapane', 'native_module': 'dapane._native'}
    monkeypatch.delitem(sys.modules, 'dapane._native', raising=False)
    monkeypatch.setattr(native_qualifier, '_inspect_installation', lambda *_: (installed, tmp_path / '_native.so'))
    monkeypatch.setattr(native_qualifier, 'dapane_oracle', lambda: {'oracle': 'synthetic match'})

    assert native_qualifier.main(['--provider', 'dapane']) == 2
    captured = capsys.readouterr()
    assert not captured.out
    assert json.loads(captured.err)['reason'] == 'dapane: oracle did not load the recorded native extension'


@pytest.mark.parametrize(("system", "machine", "key"), [
    ("linux", "x86_64", "linux-x86_64"),
    ("win32", "AMD64", "windows-x86_64"),
])
def test_reviewed_extension_uses_the_selected_platform_pin(
    native_qualifier: ModuleType, monkeypatch: pytest.MonkeyPatch,
    system: str, machine: str, key: str,
) -> None:
    entry = load_provider_lock(ROOT / 'providers.lock.json')['providers']['dapane']
    reviewed = entry['reviewed_platforms'][key]
    monkeypatch.setattr(native_qualifier, 'sys', SimpleNamespace(platform=system))
    monkeypatch.setattr(
        native_qualifier, 'platform',
        SimpleNamespace(machine=lambda: machine, python_version=lambda: '3.15.2'),
    )
    installed = {
        'distribution': 'dapane',
        'native_extension_digests': {reviewed['native_extension']: reviewed['binary_sha256']},
    }
    native_qualifier._require_reviewed_extension(entry, installed)
    assert installed['reviewed_extension_matched']

    installed['native_extension_digests'] = {reviewed['native_extension']: entry['binary_sha256']}
    with pytest.raises(RuntimeError, match='does not match the reviewed digest'):
        native_qualifier._require_reviewed_extension(entry, installed)


def test_missing_provider_lock_returns_machine_readable_unverified(tmp_path) -> None:
    """No uncaught traceback or false PASS for a missing contract lock."""
    process = subprocess.run(
        [sys.executable, str(ROOT / 'tools/qualify_providers.py'), '--provider', 'dapane',
         '--lock', str(tmp_path / 'no-provider-lock.json')],
        cwd=ROOT, capture_output=True, text=True,
        env={**os.environ, 'PYTHONPATH': str(ROOT / 'src')}, check=False,
    )
    assert process.returncode == 2
    assert json.loads(process.stderr)['status'] == 'UNVERIFIED'
