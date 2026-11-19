"""P8 entrypoints must never imply installed-provider qualification."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator

from icu_liaison.adapters.p8_mchs import MchsPair
from icu_liaison.adapters.p8_workforce import RosterScenario

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'model-inputs'/'p8'


def execute(*args):
    env = {**os.environ, 'PYTHONPATH':str(ROOT/'src')}
    return subprocess.run([sys.executable, '-m','icu_liaison.p8_cli',*map(str,args)],
                          text=True, capture_output=True, env=env, timeout=20)


def test_mchs_fixture_schema_and_model_agree():
    payload=json.loads((DATA/'synthetic-mchs-pair.json').read_text())
    schema=json.loads((DATA/'mchs-paired-episode.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    assert list(Draft202012Validator(schema).iter_errors(payload))==[]
    assert MchsPair.model_validate(payload).pricing_year == 2025


def test_roster_fixture_schema_and_model_agree():
    payload=json.loads((DATA/'synthetic-nursing-roster.json').read_text())
    schema=json.loads((DATA/'nursing-roster.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    assert list(Draft202012Validator(schema).iter_errors(payload))==[]
    assert RosterScenario.model_validate(payload).completeness_status=='partial'


def test_inspection_commands_require_no_provider_installs():
    for kind,path in [('mchs','synthetic-mchs-pair.json'),('roster','synthetic-nursing-roster.json')]:
        run=execute('inspect-'+kind, DATA/path)
        assert run.returncode==0,run.stderr
        result=json.loads(run.stdout)
        assert result['status']=='VALIDATED_SYNTHETIC_INPUT'
        assert result['installed_provider_executed'] is False
        assert result['cash_or_revenue_verified'] is False
        assert 'source_artifact_json' not in run.stdout


def test_native_commands_fail_closed_without_installed_providers():
    for kind,path in [('mchs','synthetic-mchs-pair.json'),('roster','synthetic-nursing-roster.json')]:
        command='run-mchs' if kind=='mchs' else 'build-roster'
        args=[command, DATA/path]
        if kind=='mchs': args += ['--ref-dir','/fake/mchs/ref']
        run=execute(*args)
        assert run.returncode==2,run.stdout+run.stderr
        result=json.loads(run.stdout)
        assert result['status']=='UNVERIFIED'
        assert result['installed_provider_executed'] is False
        assert 'source_artifact_json' not in run.stdout


def test_invalid_or_duplicate_object_keys_fail_validation(tmp_path):
    p=tmp_path/'bad.json'
    p.write_text('{"pricing_year":2025,"pricing_year":2024}')
    run=execute('inspect-mchs',p)
    assert run.returncode==1
    result=json.loads(run.stdout)
    assert result['status']=='INVALID'


def test_conductor_p8_phase_receipts_do_not_claim_native_acceptance():
    meta=json.loads((ROOT/'conductor/tracks/P8-abf-workforce-interop/metadata.json').read_text())
    assert meta['native_integrations_qualified'] is False
    assert meta['finance_validation'] is False
    assert meta['clinical_validation'] is False
    assert meta['provider_owner_changes_committed'] is False
    assert (ROOT/'docs/P8-implemented-consumer-contracts.md').exists()


def test_committed_schema_matches_generated_contracts_and_rejects_binary_float():
    from icu_liaison.p8_contract_schema import schema_for
    for kind,name in [('mchs','mchs-paired-episode.schema.json'),('roster','nursing-roster.schema.json')]:
        schema=json.loads((DATA/name).read_text())
        assert schema == schema_for(kind)
        p=json.loads((DATA/('synthetic-mchs-pair.json' if kind=='mchs' else 'synthetic-nursing-roster.json')).read_text())
        if kind == 'mchs':
            p['icu_hours_current']=58.25
        else:
            p['exposures'][0]['quantity']=8.0
        assert list(Draft202012Validator(schema).iter_errors(p))
