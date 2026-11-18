"""P3 CLI red tests: source provenance and private results boundaries."""
import json
import subprocess
import os
import sys
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
PKG_ENV = {**os.environ, 'PYTHONPATH':str(ROOT/'src')}


def cli(*arguments):
    return subprocess.run([sys.executable,'-m','icu_liaison.p3_cli',*map(str,arguments)],
        cwd=ROOT,env=PKG_ENV,capture_output=True,text=True)


def test_public_sources_check_does_not_certify_binary():
    result=cli('sources','--catalogue',ROOT/'model-inputs/anzics-benchmarks.json',
               '--source-register',ROOT/'conductor/evidence/source-register.json')
    assert result.returncode==0,result.stderr
    out=json.loads(result.stdout)
    assert out['metrics']==6
    assert out['unverified_document_count']==6
    assert out['eligible_local_72h_readmission_rate_available'] is False


def test_synthetic_source_quality_cli_no_rows():
    result=cli('audit','--manifest',ROOT/'tests/fixtures/p3_episodes/manifest.json',
               '--dictionary',ROOT/'model-inputs/clinical-data-dictionary.json')
    assert result.returncode==0,result.stderr
    report=json.loads(result.stdout)
    assert report['cohort']['eligible_index_discharges']==3
    assert 'SYNHOSP' not in result.stdout
    assert report['investment_ready'] is False


def test_restricted_local_requires_acknowledgment_and_private_destination(tmp_path):
    x=tmp_path/'source';shutil.copytree(ROOT/'tests/fixtures/p3_episodes',x)
    manifest=x/'manifest.json';raw=json.loads(manifest.read_text())
    raw['data_class']='restricted';raw['governance']={'status':'approved_local_processing',
         'approval_reference':'SYNTHETIC-DISPATCH-REFERENCE', 'custodian_role':'local_test_role'}
    manifest.write_text(json.dumps(raw))
    common=['audit','--manifest',manifest,'--dictionary',ROOT/'model-inputs/clinical-data-dictionary.json']
    assert cli(*common).returncode==2
    assert cli(*common,'--acknowledge-approved-processing').returncode==2
    out=tmp_path/'private_result.json'
    result=cli(*common,'--acknowledge-approved-processing','--private-output',out)
    assert result.returncode==0,result.stderr
    assert out.exists() and 'SYNHOSP' not in out.read_text()
    assert json.loads(out.read_text())['data_class']=='restricted'
    assert result.stdout.count('RESTRICTED_SOURCE_AUDITED')==1
    assert 'eligible_index_discharges' not in result.stdout


def test_private_report_can_not_be_written_to_public_repository(tmp_path):
    x=tmp_path/'source';shutil.copytree(ROOT/'tests/fixtures/p3_episodes',x)
    manifest=x/'manifest.json';raw=json.loads(manifest.read_text())
    raw['data_class']='restricted';raw['governance']={'status':'approved_local_processing',
         'approval_reference':'SYNTHETIC-DISPATCH-REFERENCE', 'custodian_role':'local_test_role'}
    manifest.write_text(json.dumps(raw))
    out=ROOT/'verification/should_not_write_private.json'
    r=cli('audit','--manifest',manifest,'--dictionary',ROOT/'model-inputs/clinical-data-dictionary.json',
          '--acknowledge-approved-processing','--private-output',out)
    assert r.returncode==2
    assert not out.exists()


def test_machine_schema_is_public_and_dependency_generated():
    result=cli('schema')
    assert result.returncode==0,result.stderr
    schema=json.loads(result.stdout)
    assert schema['schema_version']==1
    assert {'manifest','episodes','followup','liaison_contacts','cost_lines'} <= set(schema['schemas'])
    assert schema['schemas']['manifest']['properties']['data_class']
    assert 'cost_price_year' in schema['schemas']['cost_lines']['properties']
