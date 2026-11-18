"""P6 provider source pin and qualification gates."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_native_qualification_fails_without_rust_or_reviewed_lock():
    p=subprocess.run([sys.executable,'tools/qualify_p6_native.py'],cwd=ROOT,
                     env={'PYTHONPATH':str(ROOT/'src')},text=True,capture_output=True)
    assert p.returncode==2
    result=json.loads(p.stderr)
    assert result['status']=='UNVERIFIED'
    assert not result['investment_ready']


def test_pin_contract_names_upstream_blob_shas_not_just_a_mutable_branch():
    lock=json.loads((ROOT/'model-inputs/p6/kairos-provider-lock.json').read_text())
    assert len(lock['source_commit'])==40
    assert lock['source_verification']=='exact_upstream_file_at_pinned_sha_read_via_authenticated_GitHub_connector'
    assert all(len(v)==40 for v in lock['inspected_upstream_blob_shas'].values())
    assert lock['binary_sha256'] is None
