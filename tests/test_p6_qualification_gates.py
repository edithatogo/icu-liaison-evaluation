"""P6 provider source pin and qualification gates."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from tools.qualify_p6_native import _verify_resolved_provider

ROOT = Path(__file__).resolve().parents[1]


def test_native_qualification_fails_without_rust_or_reviewed_lock() -> None:
    p=subprocess.run([sys.executable,'tools/qualify_p6_native.py'],cwd=ROOT,
                     env={'PYTHONPATH':str(ROOT/'src')},text=True,capture_output=True)
    assert p.returncode==2
    result=json.loads(p.stderr)
    assert result['status']=='UNVERIFIED'
    assert not result['investment_ready']


def test_pin_contract_names_upstream_blob_shas_not_just_a_mutable_branch() -> None:
    lock=json.loads((ROOT/'model-inputs/p6/kairos-provider-lock.json').read_text())
    assert len(lock['source_commit'])==40
    assert lock['source_verification']=='exact_upstream_file_at_pinned_sha_read_via_authenticated_GitHub_connector'
    assert all(len(v)==40 for v in lock['inspected_upstream_blob_shas'].values())
    assert lock['binary_sha256'] is None


def test_build_checks_transitive_pin_and_inspected_provider_bytes(tmp_path: Path) -> None:
    lock = json.loads((ROOT / 'model-inputs/p6/kairos-provider-lock.json').read_text())
    for name in lock['inspected_upstream_blob_shas']:
        source_file = tmp_path / name
        source_file.parent.mkdir(parents=True, exist_ok=True)
        content = f'Fictional source witness for {source_file.name}\n'.encode()
        source_file.write_bytes(content)
        blob = f'blob {len(content)}\0'.encode() + content
        lock['inspected_upstream_blob_shas'][name] = hashlib.sha1(blob, usedforsecurity=False).hexdigest()
    commit = lock['source_commit']
    source = f"git+{lock['repository']}?rev={commit}#{commit}"
    packages = [
        {'name': name, 'source': source, 'manifest_path': str(tmp_path / 'crates' / name / 'Cargo.toml')}
        for name in ('kairo-ecs-des', 'kairo-ecs-types', 'kairo-ecs-core')
    ]
    metadata = {'packages': packages}
    _verify_resolved_provider(metadata, lock)
    packages[-1]['source'] = source.replace(f'#{commit}', '#' + '0' * 40)
    with pytest.raises(RuntimeError, match='exact locked revision'):
        _verify_resolved_provider(metadata, lock)
    packages[-1]['source'] = source
    (tmp_path / 'crates/kairo-ecs-des/src/staged_runtime.rs').write_bytes(b'Changed fictional source')
    with pytest.raises(RuntimeError, match='locked Git blob'):
        _verify_resolved_provider(metadata, lock)
