"""Fail-closed qualification of the optional native Kairos ICU consumer.

Only real Rust tooling and exact pinned source/lock are allowed. A successful
local run is evidence of executed program behaviour, NOT an independent build
attestation or CHHHS clinical/operational acceptance.
"""
from __future__ import annotations

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
SCENARIO = ROOT / 'model-inputs/p6/kairos-synthetic-input.json'
SOURCE_LOCK = ROOT / 'model-inputs/p6/kairos-provider-lock.json'
REFERENCE = ROOT / 'tests/fixtures/p6_native/independent-reference.json'


def _call(argv: list[str], *, timeout: int = 240) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(argv, cwd=CONSUMER, capture_output=True, text=True,
                       timeout=timeout, check=False)
    if p.returncode:
        raise RuntimeError(f'{argv[0]} {argv[1]} failed (exit {p.returncode})')
    return p


def main() -> int:
    try:
        from icu_liaison.p6_native import (
            KairosScenario, KairosProducerOutput,
            compare_native_with_reference, invoke_native_binary,
        )
        cargo = shutil.which('cargo')
        rustc = shutil.which('rustc')
        if not cargo or not rustc:
            raise RuntimeError('missing installed Rust cargo/rustc')
        if not (CONSUMER / 'Cargo.lock').is_file():
            raise RuntimeError('Cargo.lock missing: generate, independently review, and commit first')
        lock = json.loads(SOURCE_LOCK.read_text())
        meta = json.loads(_call([cargo, 'metadata', '--locked', '--offline', '--format-version', '1']).stdout)
        pinned = lock['source_commit']
        providers = [p for p in meta['packages'] if p['name'] in ('kairo-ecs-types', 'kairo-ecs-des')]
        if len(providers) != 2 or not all(pinned in str(p.get('source', '')) for p in providers):
            raise RuntimeError('resolved native Kairos sources do not match locked revision')
        _call([cargo, 'fmt', '--all', '--check'])
        _call([cargo, 'clippy', '--locked', '--offline', '--all-targets', '--', '-D', 'warnings'])
        _call([cargo, 'test', '--locked', '--offline'], timeout=300)
        _call([cargo, 'build', '--locked', '--offline'], timeout=300)
        binary_name = 'icu-liaison-kairos-consumer.exe' if os.name == 'nt' else 'icu-liaison-kairos-consumer'
        binary = CONSUMER / 'target/debug' / binary_name
        if not binary.is_file():
            raise RuntimeError('built binary not present')
        digest = hashlib.sha256(binary.read_bytes()).hexdigest()
        observed = invoke_native_binary(binary, SCENARIO, expected_sha256=digest,
                                        provider_lock=lock)
        again = invoke_native_binary(binary, SCENARIO, expected_sha256=digest,
                                     provider_lock=lock)
        if observed['output_sha256'] != again['output_sha256']:
            raise RuntimeError('replay produced different raw output bytes')
        raw = _call([str(binary), str(SCENARIO)], timeout=40).stdout
        expected = json.loads(REFERENCE.read_text())
        parsed = KairosProducerOutput.model_validate_json(raw)
        judgement = compare_native_with_reference(parsed.model_dump(), expected,
                                                  KairosScenario.model_validate_json(SCENARIO.read_text()).model_dump())
        if not judgement['matches_reference']:
            raise RuntimeError('actual native output differs from independent reference fixture')
        result = {
            'status': 'LOCAL_NATIVE_CONSUMER_EXECUTED_NOT_INDEPENDENTLY_ATTESTED',
            'producer': 'icu-liaison-kairos-consumer',
            'source_commit': pinned,
            'executable_sha256': digest,
            'cargo_lock_sha256': hashlib.sha256((CONSUMER / 'Cargo.lock').read_bytes()).hexdigest(),
            'source_lock_sha256': hashlib.sha256(SOURCE_LOCK.read_bytes()).hexdigest(),
            'exact_replay_matched': True,
            'independent_one_bed_fixture_matched': True,
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
