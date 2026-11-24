"""End-to-end executable P2 admission without a local clinical dataset."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / 'model-inputs/clinical-economic-protocol.json'
SCENARIO = ROOT / 'model-inputs/illustrative.json'
DICTIONARY = ROOT / 'model-inputs/clinical-data-dictionary.json'
CROSSWALK = ROOT / 'model-inputs/p2-chhhs-field-crosswalk.json'
REQUEST = ROOT / 'model-inputs/chhhs-data-request.json'
SIGNOFF = ROOT / 'model-inputs/p2-governance-signoff-TEMPLATE.json'


def run(*args):
    env = {**os.environ, 'PYTHONPATH': str(ROOT / 'src')}
    return subprocess.run([sys.executable, '-m', 'icu_liaison.protocol_cli', *map(str, args)],
                          cwd=ROOT, env=env, capture_output=True, text=True, check=False)


def test_cli_produces_reproducible_source_trace_and_reports_blocks():
    result = run(PROTOCOL, SCENARIO, '--data-dictionary', DICTIONARY)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload['status'] == 'ADMITTED_ILLUSTRATIVE_ONLY'
    assert payload['data_dictionary']['field_count'] >= 30
    assert len(payload['data_dictionary']['sha256']) == 64
    assert payload['ready_for_local_claims'] is False
    assert result.stdout == run(PROTOCOL, SCENARIO, '--data-dictionary', DICTIONARY).stdout


def test_cli_can_fail_closed_when_local_investment_ready_is_required():
    result = run(PROTOCOL, SCENARIO, '--data-dictionary', DICTIONARY, '--require-local-ready')
    assert result.returncode == 2
    assert json.loads(result.stdout)['ready_for_local_claims'] is False
    assert 'UNVERIFIED' in result.stderr


def test_cli_audits_the_review_pack_with_the_same_sources():
    args = (PROTOCOL, SCENARIO, '--data-dictionary', DICTIONARY, '--field-crosswalk', CROSSWALK,
            '--chhhs-request', REQUEST, '--governance-signoff', SIGNOFF)
    result = run(*args)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['field_crosswalk']['p2_field_count'] == 32
    assert report['field_crosswalk']['dictionary_sha256'] == report['data_dictionary']['sha256']
    assert report['governance_signoff']['protocol_sha256'] == hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
    assert report['governance_signoff']['dictionary_sha256'] == report['data_dictionary']['sha256']
    assert report['governance_signoff']['pending_gate_count'] == 7
    assert report['governance_signoff']['site_authority_verified'] is False
    blocked = run(*args, '--require-local-ready')
    assert blocked.returncode == 2 and 'UNVERIFIED' in blocked.stderr
    assert blocked.stdout == result.stdout


def test_missing_input_does_not_produce_success_report(tmp_path):
    missing = tmp_path/'not-here.json'
    result = run(PROTOCOL, missing)
    assert result.returncode != 0
    assert not result.stdout.strip()
