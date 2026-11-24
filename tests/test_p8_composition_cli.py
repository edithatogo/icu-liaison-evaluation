"""End-to-end P8.4 CLI tests: source-only output and controlled failure."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/'model-inputs'/'p4'/'illustrative.json'
P8=ROOT/'model-inputs'/'p8'


def cli(*args):
    env={**os.environ,'PYTHONPATH':str(ROOT/'src')}
    return subprocess.run([sys.executable,'-m','icu_liaison.p8_composition_cli',*map(str,args)],
                          capture_output=True,text=True,env=env,timeout=30)


def test_cli_source_only_emits_funding_and_workforce_nulls():
    proc=cli(INPUT,'--strategy','liaison_service')
    assert proc.returncode==0,proc.stdout+proc.stderr
    result=json.loads(proc.stdout)
    assert result['admission']=='planning_only'
    assert result['mchs']['case_change_nwau'] is None
    assert result['actual_hospital_revenue_change_aud'] is None
    assert result['workforce']['annual_labour_cost_aud'] is None
    assert result['extra_workforce_cost_applied_to_p4'] is False
    assert not list(Draft202012Validator(json.loads((P8/'p8-composition.schema.json').read_text())).iter_errors(result))


def test_cli_rejects_investment_ready_without_leaking_data():
    proc=cli(INPUT,'--strategy','liaison_service','--require-qualified')
    assert proc.returncode==2
    assert not proc.stdout
    assert 'UNVERIFIED' in proc.stderr


def test_cli_rejects_wrong_strategy_and_duplicate_json_keys(tmp_path):
    proc=cli(INPUT,'--strategy','current_care')
    assert proc.returncode==2
    p=tmp_path/'duplicate.json';p.write_text('{"schema_version":1,"schema_version":2}')
    proc=cli(p,'--strategy','liaison_service')
    assert proc.returncode==2
    assert not proc.stdout


def test_schema_generator_and_fixture_are_synchronised():
    from icu_liaison.p8_composition import P8Composition
    schema=json.loads((P8/'p8-composition.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    assert schema == P8Composition.model_json_schema()
    fixture=json.loads((P8/'synthetic-p8-composed-shadow.json').read_text())
    assert not list(Draft202012Validator(schema).iter_errors(fixture))


def test_cli_combines_two_synthetic_provider_shadows_without_monetisation():
    proc=cli(INPUT,'--strategy','liaison_service',
             '--mchs-result',P8/'synthetic-mchs-provider-output.json',
             '--workforce-result',P8/'synthetic-workforce-provider-output.json',
             '--roster-scenario-id','synthetic-nurse-roster')
    assert proc.returncode==0,proc.stdout+proc.stderr
    out=json.loads(proc.stdout)
    assert out['mchs']['case_change_nwau']=='-0.1000'
    assert out['mchs']['actual_revenue_aud'] is None
    assert out['workforce']['request_line_count']==1
    assert out['workforce']['annual_labour_cost_aud'] is None
    assert out['extra_workforce_cost_applied_to_p4'] is False


def test_cli_labels_assumed_case_funding_and_preserves_default_shape():
    args = (INPUT, '--strategy', 'liaison_service', '--mchs-result', P8/'synthetic-mchs-provider-output.json')
    baseline = cli(*args)
    assert baseline.returncode == 0, baseline.stderr
    priced = cli(*args, '--funding-pricing-year', '2025', '--assumed-aud-per-nwau', '1000')
    assert priced.returncode == 0, priced.stderr
    payload = json.loads(priced.stdout)
    assert payload.pop('episode_funding_sensitivity') == {
        'actual_revenue_aud': None, 'assumed_aud_per_nwau': '1000', 'case_change_aud': '-100.0000',
        'pricing_year': 2025, 'scope': 'one_synthetic_episode_at_assumed_price',
    }
    assert payload == json.loads(baseline.stdout)
    invalid = cli(*args, '--assumed-aud-per-nwau', '1000')
    assert invalid.returncode == 2 and not invalid.stdout
