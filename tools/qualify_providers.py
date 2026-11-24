"""Execute installed-provider oracles; fail closed when artifacts are unavailable.

Version, schema and numerical oracle checks are necessary but not sufficient
for final release: wheel/extension provenance, license/advisory and hosted
platform qualification remain separately required. Injection tests cannot pass
this script. Use a separate CPython 3.15.2+ environment for Voiage 3.1.0.
"""
from __future__ import annotations

import argparse
import hashlib
from importlib.machinery import ExtensionFileLoader, ModuleSpec, PathFinder
from importlib.metadata import PackageNotFoundError, distribution
from importlib.util import find_spec
import json
from pathlib import Path
import platform
import sys

import numpy as np

from icu_liaison.adapters.dapane import (
    CostLine,
    compare_valued_scenarios,
    evaluate_request,
    make_nominal_cost_bridge,
    make_request,
)
from icu_liaison.adapters.voiage import evaluate_financial_information
from icu_liaison.model import simulate
from icu_liaison.provider_contracts import parse_provider_lock, require_provider_python
from icu_liaison.schemas import Scenario

ROOT = Path(__file__).resolve().parents[1]
EXTENSION_MODULES = {'dapane': 'dapane._native', 'voiage': 'voiage._core'}


def _extension_origin(spec: ModuleSpec | None) -> Path | None:
    if spec and spec.origin and isinstance(spec.loader, ExtensionFileLoader):
        return Path(spec.origin)
    return None


def _inspect_installation(provider: str, expected: str) -> tuple[dict, Path]:
    try:
        dist = distribution(provider)
    except PackageNotFoundError as exc:
        raise RuntimeError(f'{provider}: installed distribution unavailable') from exc
    actual = dist.version
    if actual != expected:
        raise RuntimeError(f'{provider}: expected exact distribution {expected}, observed {actual}')
    files = {item.as_posix(): item for item in dist.files or ()}
    package_file = files.get(f'{provider}/__init__.py')
    package = find_spec(provider)
    if (
        package_file is None or package is None or not package.origin
        or package.submodule_search_locations is None
        or Path(package.origin).resolve() != Path(dist.locate_file(package_file)).resolve()
    ):
        raise RuntimeError(f'{provider}: import does not resolve to the installed distribution package')

    # PathFinder can resolve the extension within the package without running
    # its initializer. A different binary anywhere in RECORD is insufficient.
    module = EXTENSION_MODULES[provider]
    path = _extension_origin(PathFinder.find_spec(module, package.submodule_search_locations))
    if path is None:
        raise RuntimeError(f'{provider}: expected native extension {module} is unavailable')
    extension = f'{provider}/{path.name}'
    record = files.get(extension)
    if record is None or path.resolve() != Path(dist.locate_file(record)).resolve():
        raise RuntimeError(f'{provider}: native extension {module} does not match the installed distribution')
    return {
        'distribution': provider,
        'version': actual,
        'native_module': module,
        'native_extension_digests': {extension: hashlib.sha256(path.read_bytes()).hexdigest()},
        'origin_claim': 'installed_distribution_only_no_wheel_source_attestation',
    }, path.resolve()


def _require_reviewed_extension(entry: dict, installed: dict) -> None:
    machine = platform.machine().lower()
    if sys.platform == 'darwin' and machine == 'arm64':
        reviewed = entry.get('reviewed_wheel', {})
        digest = entry.get('binary_sha256')
    else:
        key = {
            ('linux', 'x86_64'): 'linux-x86_64',
            ('win32', 'amd64'): 'windows-x86_64',
            ('win32', 'x86_64'): 'windows-x86_64',
        }.get((sys.platform, machine))
        reviewed = entry.get('reviewed_platforms', {}).get(key, {}) if key else {}
        digest = reviewed.get('binary_sha256')
    provider = installed['distribution']
    if reviewed.get('python') != platform.python_version() or not digest:
        raise RuntimeError(f'{provider}: no reviewed extension for this platform and Python version')
    if installed['native_extension_digests'] != {reviewed.get('native_extension'): digest}:
        raise RuntimeError(f'{provider}: installed native extension does not match the reviewed digest')
    installed['reviewed_extension_matched'] = True


def _verify_loaded_extension(installed: dict, expected: Path) -> None:
    module = sys.modules.get(installed['native_module'])
    path = _extension_origin(getattr(module, '__spec__', None))
    if path is None or path.resolve() != expected:
        raise RuntimeError(f'{installed["distribution"]}: oracle did not load the recorded native extension')
    digest = hashlib.sha256(expected.read_bytes()).hexdigest()
    if digest not in installed['native_extension_digests'].values():
        raise RuntimeError(f'{installed["distribution"]}: native extension changed during qualification')


def dapane_oracle() -> dict:
    """Exercise the real installed Rust-backed Python provider, not a fake."""
    request = make_request('p1-independent-reference', [
        CostLine('one', 'staff_time', 'minute', '2', '50.00', ['salary']),
    ])
    result = evaluate_request(request)
    if (
        result.get('schema_version') != '0.1'
        or result.get('method_version') != 'dapane-exact-v0.1.0'
        or result.get('totals', {}).get('rounded') != '100.00'
    ):
        raise AssertionError('Dapane exact 2*50 oracle did not produce 100.00')

    fixture = Scenario.model_validate_json((ROOT / 'model-inputs/illustrative.json').read_text())
    bridge = make_nominal_cost_bridge(fixture)
    comparison = compare_valued_scenarios(bridge)
    if comparison['incremental_resource_benefit_aud'] != '-168730.00':
        raise AssertionError('Dapane paired incremental cost oracle mismatch')
    if comparison['provider_evidence'] != 'native_provider_executed':
        raise AssertionError('Dapane provider execution was not established')
    return {
        'provider': 'dapane', 'contract': '0.1',
        'one_line_rounded_aud': '100.00',
        'nominal_resource_bridge_aud': comparison['incremental_resource_benefit_aud'],
        'status': 'native_numerical_oracles_executed',
    }


def voiage_oracle() -> dict:
    """Exercise released Voiage 3.1.0 EVPI on an independent two-state oracle."""
    from voiage.analysis import DecisionAnalysis
    from voiage.schema import ValueArray

    vals = np.asarray([[0.0, 10.0], [0.0, -10.0]], dtype=np.float64)
    analysis = DecisionAnalysis(ValueArray.from_numpy(vals, ['current_care', 'liaison_service']))
    actual = float(analysis.evpi())
    if not np.isfinite(actual) or abs(actual - 5.0) > 1e-10:
        raise AssertionError(f'Voiage independent two-state EVPI expected 5, got {actual}')

    fixture = Scenario.model_validate_json((ROOT / 'model-inputs/illustrative.json').read_text())
    result = evaluate_financial_information(simulate(fixture))
    if result['provider_evidence'] != 'native_provider_executed':
        raise AssertionError('Voiage provider execution was not established')
    if not np.isfinite(result['evpi_per_decision_aud']):
        raise AssertionError('Voiage scenario EVPI must be finite')
    return {
        'provider': 'voiage', 'two_state_evpi_aud': actual,
        'illustrative_annual_programme_evpi_aud': result['evpi_per_decision_aud'],
        'status': 'native_numerical_oracles_executed',
        'interpretation': 'resource_only_no_QALYs_or_patient_level_EVPI',
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=('dapane', 'voiage', 'all'), required=True)
    parser.add_argument('--lock', type=Path, default=ROOT / 'providers.lock.json')
    parser.add_argument(
        '--require-reviewed-extension', action='store_true',
        help='Require the native extension filename and digest reviewed for this platform and Python patch.',
    )
    args = parser.parse_args(argv)
    selected = ['dapane', 'voiage'] if args.provider == 'all' else [args.provider]
    environment = {
        'python': platform.python_version(),
        'platform': platform.platform(),
        'python_implementation': platform.python_implementation(),
    }
    try:
        if environment['python_implementation'] != 'CPython':
            raise RuntimeError('Provider qualification requires CPython')
        require_provider_python(sys.version_info[:3])
        lock_bytes = args.lock.read_bytes()
        lock = parse_provider_lock(lock_bytes)
        installations = []
        for name in selected:
            entry = lock['providers'][name]
            installed, native_path = _inspect_installation(name, entry['version'])
            if args.require_reviewed_extension:
                _require_reviewed_extension(entry, installed)
            installations.append((installed, native_path))
        observations = []
        oracles = {'dapane': dapane_oracle, 'voiage': voiage_oracle}
        for installed, native_path in installations:
            name = installed['distribution']
            observations.append(oracles[name]())
            _verify_loaded_extension(installed, native_path)
    except Exception as exc:
        print(json.dumps({
            'status': 'UNVERIFIED', 'providers_requested': selected,
            'environment': environment, 'reason': str(exc),
        }, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps({
        'status': 'NATIVE_ORACLES_PASSED_ARTIFACT_PROVENANCE_PENDING',
        'source_lock_sha256': hashlib.sha256(lock_bytes).hexdigest(),
        'providers_requested': selected,
        'environment': environment,
        'installed_distributions': [installed for installed, _ in installations],
        'observations': observations,
        'note': 'Verify the original wheel and its provenance separately before integration acceptance.',
    }, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
