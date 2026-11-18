"""End-to-end executable P2 admission without a local clinical dataset."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / 'model-inputs/clinical-economic-protocol.json'
SCENARIO = ROOT / 'model-inputs/illustrative.json'
DICTIONARY = ROOT / 'model-inputs/clinical-data-dictionary.json'


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


def test_missing_input_does_not_produce_success_report(tmp_path):
    missing = tmp_path/'not-here.json'
    result = run(PROTOCOL, missing)
    assert result.returncode != 0
    assert not result.stdout.strip()
