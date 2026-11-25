"""Fail-closed qualification of the optional native Kairos ICU consumer.

Only real Rust tooling and exact pinned source/lock are allowed. A successful
local run is evidence of executed program behaviour, NOT an independent build
attestation or CHHHS clinical/operational acceptance.
"""
from __future__ import annotations
from typing import Any

from collections.abc import Mapping
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / 'native/kairos-icu-liaison'
TARGET = Path(os.environ.get('CARGO_TARGET_DIR', CONSUMER / 'build')).resolve()
SOURCE_LOCK = ROOT / 'model-inputs/p6/kairos-provider-lock.json'
FIXTURES = ROOT / 'tests/fixtures/p6_native'
REPLAYS = (
    (ROOT / 'model-inputs/p6/kairos-synthetic-input.json', FIXTURES / 'independent-reference.json'),
    (FIXTURES / 'queue-scenario.json', FIXTURES / 'queue-reference.json'),
)
INSPECTED_PATHS = {
    'crates/kairo-ecs-des/src/staged_runtime.rs',
    'crates/kairo-ecs-types/src/lib.rs',
    'crates/kairo-ecs-des/Cargo.toml',
}


def _call(argv: list[str], *, timeout: int = 240) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(argv, cwd=CONSUMER, capture_output=True, text=True,
                       env={**os.environ, 'CARGO_TARGET_DIR': str(TARGET)},
                       timeout=timeout, check=False)
    if p.returncode:
        raise RuntimeError(f'{argv[0]} {argv[1]} failed (exit {p.returncode})')
    return p


def _verify_resolved_provider(metadata: Mapping[str, Any], lock: Mapping[str, Any]) -> None:
    pinned = lock['source_commit']
    source = f"git+{lock['repository']}?rev={pinned}#{pinned}"
    packages = [package for package in metadata['packages'] if (package.get('source') or '').startswith('git+')]
    if ({'kairo-ecs-des', 'kairo-ecs-types'} - {package['name'] for package in packages}
            or any(package['source'] != source for package in packages)):
        raise RuntimeError('resolved native Kairos sources do not match the exact locked revision')
    des = next(package for package in packages if package['name'] == 'kairo-ecs-des')
    checkout = Path(des['manifest_path']).resolve().parents[2]
    blobs = lock['inspected_upstream_blob_shas']
    if set(blobs) != INSPECTED_PATHS:
        raise RuntimeError('incomplete inspected Kairos source files in provider lock')
    for name, expected in blobs.items():
        data = (checkout / name).read_bytes()
        header = f'blob {len(data)}\0'.encode('ascii')
        if hashlib.sha1(header + data, usedforsecurity=False).hexdigest() != expected:
            raise RuntimeError(f'inspected Kairos source differs from the locked Git blob: {name}')


def main() -> int:
    try:
        from icu_liaison.p6_native import KairosProducerOutput, invoke_native_binary
        cargo = shutil.which('cargo')
        rustc = shutil.which('rustc')
        if not cargo or not rustc:
            raise RuntimeError('missing installed Rust cargo/rustc')
        if not (CONSUMER / 'Cargo.lock').is_file():
            raise RuntimeError('Cargo.lock missing: generate, independently review, and commit first')
        lock = json.loads(SOURCE_LOCK.read_text())
        meta = json.loads(_call([cargo, 'metadata', '--locked', '--offline', '--format-version', '1']).stdout)
        _verify_resolved_provider(meta, lock)
        _call([cargo, 'fmt', '--all', '--check'])
        _call([cargo, 'clippy', '--locked', '--offline', '--all-targets', '--', '-D', 'warnings'])
        _call([cargo, 'test', '--locked', '--offline'], timeout=300)
        _call([cargo, 'build', '--locked', '--offline'], timeout=300)
        binary_name = 'icu-liaison-kairos-consumer.exe' if os.name == 'nt' else 'icu-liaison-kairos-consumer'
        binary = TARGET / 'debug' / binary_name
        if not binary.is_file():
            raise RuntimeError('built binary not present')
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        replays = []
        for scenario_path, reference_path in REPLAYS:
            reference_bytes = reference_path.read_bytes()
            reference = KairosProducerOutput.model_validate_json(reference_bytes, strict=True)
            observed = invoke_native_binary(binary, scenario_path, expected_sha256=digest,
                                            provider_lock=lock, reference=reference)
            repeated = invoke_native_binary(binary, scenario_path, expected_sha256=digest,
                                            provider_lock=lock, reference=reference)
            if any(observed[key] != repeated[key] for key in ('input_sha256', 'output_sha256')):
                raise RuntimeError('replay input or output bytes differ')
            replays.append({
                'scenario_id': reference.scenario_id,
                'input_sha256': observed['input_sha256'],
                'output_sha256': observed['output_sha256'],
                'reference_sha256': hashlib.sha256(reference_bytes).hexdigest(),
            })
        result = {
            'status': 'LOCAL_NATIVE_CONSUMER_EXECUTED_NOT_INDEPENDENTLY_ATTESTED',
            'producer': 'icu-liaison-kairos-consumer',
            'source_commit': lock['source_commit'],
            'executable_sha256': digest,
            'cargo_lock_sha256': hashlib.sha256((CONSUMER / 'Cargo.lock').read_bytes()).hexdigest(),
            'source_lock_sha256': hashlib.sha256(SOURCE_LOCK.read_bytes()).hexdigest(),
            'exact_replay_matched': True,
            'independent_one_bed_fixture_matched': True,
            'fixture_replays': replays,
            'clinical_or_finance_approval': False,
            'investment_ready': False,
            'platform': platform.platform(),
            'rustc': _call([rustc, '--version']).stdout.strip(),
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, subprocess.TimeoutExpired) as error:
        print(json.dumps({'status': 'UNVERIFIED', 'scope': 'native_qualification',
                          'reason': str(error), 'investment_ready': False}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
