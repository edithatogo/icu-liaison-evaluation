"""Execute installed-provider oracles; fail closed when artifacts are unavailable.

Version, schema and numerical oracle checks are necessary but not sufficient
for final release: wheel/extension provenance, license/advisory and hosted
platform qualification remain separately required. Injection tests cannot pass
this script. Use a separate CPython 3.15.2+ environment for Voiage 3.1.0.
"""
from __future__ import annotations

import argparse
import hashlib
from importlib.metadata import PackageNotFoundError, distribution, version
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
from icu_liaison.provider_contracts import load_provider_lock
from icu_liaison.schemas import Scenario

ROOT = Path(__file__).resolve().parents[1]


def _installed_version(provider: str, expected: str) -> dict:
    try:
        actual = version(provider)
    except PackageNotFoundError as exc:
        raise RuntimeError(f'{provider}: installed distribution unavailable') from exc
    if actual != expected:
        raise RuntimeError(f'{provider}: expected exact distribution {expected}, observed {actual}')
    dist = distribution(provider)
    extension_hashes = {}
    # RECORD-installed native-extension digests are observed facts, not a hash
    # of the complete wheel, an upstream provenance signature or a source SHA.
    for item in dist.files or []:
        text = str(item)
        if text.endswith(('.so', '.pyd', '.dylib')):
            path = Path(dist.locate_file(item))
            if path.is_file():
                extension_hashes[text] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not extension_hashes:
        raise RuntimeError(
            f'{provider}: installed distribution has no visible compiled native extension; '
            'cannot qualify the expected Rust-backed provider'
        )
    return {
        'distribution': provider,
        'version': actual,
        'native_extension_digests': extension_hashes,
        'origin_claim': 'installed_distribution_only_no_wheel_source_attestation',
    }


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
    args = parser.parse_args(argv)
    selected = ['dapane', 'voiage'] if args.provider == 'all' else [args.provider]
    environment = {
        'python': platform.python_version(),
        'platform': platform.platform(),
        'python_implementation': platform.python_implementation(),
    }
    try:
        lock = load_provider_lock(args.lock)
        metadata = []
        for name in selected:
            if name == 'voiage' and not ((3, 15, 2) <= sys.version_info[:3] < (3, 16, 0)):
                raise RuntimeError('Voiage 3.1.0 requires Python 3.15.2 through 3.15.x')
            metadata.append(_installed_version(name, lock['providers'][name]['version']))
        observations = []
        if 'dapane' in selected:
            observations.append(dapane_oracle())
        if 'voiage' in selected:
            observations.append(voiage_oracle())
    except (OSError, RuntimeError, ImportError, AssertionError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({
            'status': 'UNVERIFIED', 'providers_requested': selected,
            'environment': environment, 'reason': str(exc),
        }, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps({
        'status': 'NATIVE_ORACLES_PASSED_ARTIFACT_PROVENANCE_PENDING',
        'source_lock_sha256': hashlib.sha256(args.lock.read_bytes()).hexdigest(),
        'providers_requested': selected,
        'environment': environment,
        'installed_distributions': metadata,
        'observations': observations,
        'note': 'Compare installed wheel/native-extension digests with reviewed artifacts before integration acceptance.',
    }, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
