"""P3 CLI red tests: source provenance and private results boundaries."""
from pytest import CaptureFixture, MonkeyPatch
from subprocess import CompletedProcess
import hashlib
import json
import subprocess
import os
import sys
from pathlib import Path
from collections.abc import Callable
from typing import Concatenate
import shutil

import pytest

from icu_liaison import local_data
from icu_liaison.p3_cli import _restricted_output_allowed, main

ROOT = Path(__file__).resolve().parents[1]
PKG_ENV = {**os.environ, 'PYTHONPATH':str(ROOT/'src')}
PUBLISHER_RECEIPT = ROOT / 'verification/p7-anzics-2024-25-publisher-2026-11-24.json'
SOURCE_ARGS = (
    'sources', '--catalogue', ROOT / 'model-inputs/anzics-benchmarks.json',
    '--source-register', ROOT / 'conductor/evidence/source-register.json',
)


def cli(*arguments: object) -> CompletedProcess[str]:
    return subprocess.run([sys.executable,'-m','icu_liaison.p3_cli',*map(str,arguments)],
        cwd=ROOT,env=PKG_ENV,capture_output=True,text=True)


def test_public_sources_check_does_not_certify_binary() -> None:
    result=cli('sources','--catalogue',ROOT/'model-inputs/anzics-benchmarks.json',
               '--source-register',ROOT/'conductor/evidence/source-register.json')
    assert result.returncode==0,result.stderr
    out=json.loads(result.stdout)
    assert out['metrics']==6
    assert out['unverified_document_count']==6
    assert out['eligible_local_72h_readmission_rate_available'] is False


def test_sources_reconciles_the_publisher_receipt_without_granting_admission() -> None:
    result = cli(*SOURCE_ARGS, '--publisher-receipt', PUBLISHER_RECEIPT)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    publisher = report['publisher_check']
    assert publisher['source_id'] == 'ANZICS-CCR-2024-25'
    assert publisher['checked_outcome_count'] == 6
    assert publisher['receipt_sha256'] == hashlib.sha256(PUBLISHER_RECEIPT.read_bytes()).hexdigest()
    assert publisher['document_sha256_matched'] is False
    assert publisher['independent_source_admission'] == 'pending'
    assert report['unverified_document_count'] == 6
    assert report['eligible_local_72h_readmission_rate_available'] is False


@pytest.mark.parametrize('change', ['locator', 'coverage', 'claimed_admission', 'different_document', 'receipt_edition'])
def test_sources_rejects_inconsistent_publisher_evidence(tmp_path: Path, change: str) -> None:
    receipt = json.loads(PUBLISHER_RECEIPT.read_text(encoding='utf-8'))
    receipt_path = tmp_path / 'receipt.json'
    args = [*SOURCE_ARGS, '--publisher-receipt', receipt_path]
    if change == 'locator':
        receipt['checked_locators'][0]['page'] += 1
    elif change == 'coverage':
        receipt['checked_locators'].pop()
    elif change == 'claimed_admission':
        receipt['independent_source_admission'] = 'approved'
    elif change == 'receipt_edition':
        receipt['checked_on'] = '2026-11-25'
    else:
        document = tmp_path / 'different.pdf'
        with document.open('wb') as stream:
            stream.truncate(receipt['document']['size_bytes'])
        args.extend(['--publisher-document', document])
    if change == 'different_document':
        shutil.copyfile(PUBLISHER_RECEIPT, receipt_path)
    else:
        receipt_path.write_text(json.dumps(receipt), encoding='utf-8')
    result = cli(*args)
    assert result.returncode == 2
    assert 'INVALID_SOURCE' in result.stderr
    assert not result.stdout


def test_synthetic_source_quality_cli_no_rows() -> None:
    result=cli('audit','--manifest',ROOT/'tests/fixtures/p3_episodes/manifest.json',
               '--dictionary',ROOT/'model-inputs/clinical-data-dictionary.json')
    assert result.returncode==0,result.stderr
    report=json.loads(result.stdout)
    assert report['cohort']['eligible_index_discharges']==3
    assert 'SYNHOSP' not in result.stdout
    assert report['investment_ready'] is False


def test_restricted_local_requires_acknowledgment_and_private_destination(tmp_path: Path) -> None:
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


def test_private_report_can_not_be_written_to_public_repository(tmp_path: Path) -> None:
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


def test_audit_uses_one_manifest_for_privacy_and_provenance(tmp_path: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]) -> None:
    source = tmp_path / 'source'
    shutil.copytree(ROOT / 'tests/fixtures/p3_episodes', source)
    manifest = source / 'manifest.json'
    initial = manifest.read_bytes()
    replacement = json.loads(initial)
    replacement['data_class'] = 'restricted'
    replacement['governance'] = {
        'status': 'approved_local_processing', 'approval_reference': 'fictional-reference',
        'custodian_role': 'fictional_role',
    }
    reads = 0

    def replace_after_read[**P, R](method: Callable[Concatenate[Path, P], R]) -> Callable[Concatenate[Path, P], R]:
        def read(path: Path, /, *args: P.args, **kwargs: P.kwargs) -> R:
            nonlocal reads
            contents = method(path, *args, **kwargs)
            if path == manifest:
                reads += 1
                if reads == 1:
                    path.write_text(json.dumps(replacement), encoding='utf-8')
            return contents
        return read

    monkeypatch.setattr(Path, 'read_bytes', replace_after_read(Path.read_bytes))
    monkeypatch.setattr(Path, 'read_text', replace_after_read(Path.read_text))
    args = [
        'audit', '--manifest', str(manifest), '--dictionary',
        str(ROOT / 'model-inputs/clinical-data-dictionary.json'), '--acknowledge-approved-processing',
    ]
    assert main(args) == 0
    report = json.loads(capsys.readouterr().out)
    assert reads == 1
    assert report['data_class'] == 'synthetic'
    assert report['input_provenance']['manifest_sha256'] == hashlib.sha256(initial).hexdigest()

    assert main(args) == 2
    assert not capsys.readouterr().out


def test_output_check_finds_the_destination_checkout_for_an_installed_cli(tmp_path: Path) -> None:
    checkout = tmp_path / 'checkout'
    checkout.mkdir()
    subprocess.run(['git', 'init', '--quiet', str(checkout)], check=True)
    package_home = tmp_path / 'installed'
    assert not _restricted_output_allowed(checkout / 'report.json', package_home)
    assert not _restricted_output_allowed(checkout / 'private/report.json', package_home)

    (checkout / '.gitignore').write_text('private/\n', encoding='utf-8')
    assert _restricted_output_allowed(checkout / 'private/report.json', package_home)


def test_existing_private_output_is_rejected_before_opening_feeds(tmp_path: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]) -> None:
    source = tmp_path / 'source'
    shutil.copytree(ROOT / 'tests/fixtures/p3_episodes', source)
    manifest = source / 'manifest.json'
    content = json.loads(manifest.read_text())
    content['data_class'] = 'restricted'
    content['governance'] = {
        'status': 'approved_local_processing', 'approval_reference': 'fictional-reference',
        'custodian_role': 'fictional_role',
    }
    manifest.write_text(json.dumps(content))
    output = tmp_path / 'existing-report.json'
    output.write_text('existing fictional report')

    def unexpected_read(*args: object, **kwargs: object) -> None:
        pytest.fail('a feed was opened before rejecting the destination')

    monkeypatch.setattr(local_data, '_read_feed', unexpected_read)
    assert main([
        'audit', '--manifest', str(manifest), '--dictionary',
        str(ROOT / 'model-inputs/clinical-data-dictionary.json'),
        '--acknowledge-approved-processing', '--private-output', str(output),
    ]) == 2
    assert not capsys.readouterr().out
    assert output.read_text() == 'existing fictional report'


def test_machine_schema_is_public_and_dependency_generated() -> None:
    result=cli('schema')
    assert result.returncode==0,result.stderr
    schema=json.loads(result.stdout)
    assert schema['schema_version']==1
    assert {'manifest','episodes','followup','liaison_contacts','cost_lines'} <= set(schema['schemas'])
    assert schema['schemas']['manifest']['properties']['data_class']
    assert 'cost_price_year' in schema['schemas']['cost_lines']['properties']
