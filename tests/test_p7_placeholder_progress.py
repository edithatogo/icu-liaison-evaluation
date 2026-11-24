"""Executable acceptance for placeholder-backed progress, without false site admission."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'model-inputs/placeholders/registry.json'


def registry():
    from icu_liaison.placeholders import load_registry
    return load_registry(REGISTRY)


def test_registry_covers_replacement_gates_and_is_explicitly_unresolved():
    from icu_liaison.placeholders import REQUIRED_IDS, audit_placeholders

    record = registry()
    report = audit_placeholders(record, root=ROOT)
    assert {row.id for row in record.entries} == REQUIRED_IDS
    assert report['status'] == 'development_placeholders_only'
    assert report['unresolved_count'] == len(REQUIRED_IDS)
    assert report['placeholder_count_by_track']['P6'] >= 3
    assert report['investment_ready'] is False
    assert report['observed_CHHHS_data_used'] is False
    assert not report['native_providers_qualified']
    assert report['source_bindings_verified'] == len(REQUIRED_IDS)
    assert report['external_gates_pending']


def test_scoped_voiage_artifact_does_not_accept_broader_qualification(tmp_path):
    from shutil import copyfile, copytree

    from icu_liaison.placeholders import audit_placeholders

    record = registry()
    entry = next(row for row in record.entries if row.id == 'native_voiage_receipt')
    assert 'native_voiage_receipt' in audit_placeholders(record, root=ROOT)['unresolved_ids']
    assert entry.binding.pointer == '/providers/voiage/provider_qualification_receipt_sha256'

    copytree(ROOT / 'model-inputs', tmp_path / 'model-inputs')
    for artifact in {row.binding.artifact for row in record.entries}:
        target = tmp_path / artifact
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            copyfile(ROOT / artifact, target)
    lock_path = tmp_path / entry.binding.artifact
    lock = json.loads(lock_path.read_text())
    voiage = lock['providers']['voiage']
    assert voiage['binary_sha256'] and voiage['provider_qualification_receipt_sha256'] is None
    voiage['provider_qualification_receipt_sha256'] = 'f' * 64
    lock_path.write_text(json.dumps(lock))
    with pytest.raises(ValueError, match='native_voiage_receipt.*qualified independently'):
        audit_placeholders(record, root=tmp_path)


def test_known_repository_url_does_not_satisfy_hosted_ci_evidence(tmp_path):
    import shutil
    from icu_liaison.placeholders import audit_placeholders

    record = registry()
    entry = next(row for row in record.entries if row.id == 'dedicated_repo_ci')
    unresolved = json.loads((ROOT/'model-inputs/placeholders/unresolved.json').read_text())
    assert unresolved['dedicated_repository_url'] == 'https://github.com/edithatogo/icu-liaison-evaluation'
    assert entry.binding.pointer == '/dedicated_repository_ci_receipt'
    assert unresolved['dedicated_repository_ci_receipt'] is None
    report = audit_placeholders(record, root=ROOT)
    assert 'dedicated_repo_ci' in report['unresolved_ids']
    assert 'repository_integration' in report['external_gates_pending']
    assert report['investment_ready'] is False

    project = tmp_path/'project'
    shutil.copytree(ROOT/'model-inputs', project/'model-inputs')
    shutil.copy(ROOT/'providers.lock.json', project/'providers.lock.json')
    unresolved['dedicated_repository_ci_receipt'] = {'status': 'self_declared_pass'}
    (project/'model-inputs/placeholders/unresolved.json').write_text(json.dumps(unresolved))
    with pytest.raises(ValueError, match='dedicated_repo_ci.*without review'):
        audit_placeholders(record, root=project)


def test_registry_rejects_any_false_resolution_or_unsupported_status():
    from icu_liaison.placeholders import PlaceholderRegistry

    raw = registry().model_dump(mode='json')
    raw['entries'][0]['status'] = 'verified'
    with pytest.raises(ValidationError):
        PlaceholderRegistry.model_validate(raw)
    raw['entries'][0]['status'] = 'placeholder'
    raw['policy'] = 'clinically_approved'
    with pytest.raises(ValidationError):
        PlaceholderRegistry.model_validate(raw)


def test_registry_rejects_missing_binding_and_silent_observed_p4_promotion(tmp_path):
    from icu_liaison.placeholders import audit_placeholders

    record = registry()
    with pytest.raises(ValueError, match='source artifact|binding'):
        audit_placeholders(record, root=tmp_path)
    tmp = tmp_path/'isolated'
    import shutil
    shutil.copytree(ROOT/'model-inputs', tmp/'model-inputs')
    (tmp/'conductor/evidence').mkdir(parents=True)
    shutil.copy(ROOT/'conductor/evidence/source-register.json', tmp/'conductor/evidence/source-register.json')
    (tmp/'providers.lock.json').write_bytes((ROOT/'providers.lock.json').read_bytes())
    scenario = tmp/'model-inputs/p4/illustrative.json'
    data = json.loads(scenario.read_text())
    data['resource']['addressable_delay_fraction']['evidence_status'] = 'local_aggregate_unvalidated'
    scenario.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='placeholder prior'):
        audit_placeholders(record, root=tmp)


def test_source_binding_rejects_absolute_parent_symlink_or_bad_pointer(tmp_path):
    from icu_liaison.placeholders import PlaceholderRegistry, audit_placeholders

    raw=registry().model_dump(mode='json')
    raw['entries'][0]['binding']['artifact'] = '../external.json'
    with pytest.raises(ValidationError):
        PlaceholderRegistry.model_validate(raw)
    raw=registry().model_dump(mode='json')
    raw['entries'][0]['binding']['pointer']='/nonexistent'
    with pytest.raises(ValueError,match='binding'):
        audit_placeholders(PlaceholderRegistry.model_validate(raw),root=ROOT)


@pytest.mark.parametrize('location', ['private_binding', 'binding_alias', 'private_feed'])
def test_public_audit_rejects_sources_in_private_storage(tmp_path, location):
    from icu_liaison.placeholders import PlaceholderRegistry, audit_placeholders

    shutil.copytree(ROOT / 'model-inputs', tmp_path / 'model-inputs')
    shutil.copyfile(ROOT / 'providers.lock.json', tmp_path / 'providers.lock.json')
    record = registry().model_dump(mode='json')
    if location == 'private_feed':
        manifest = tmp_path / 'model-inputs/placeholders/p3-synthetic/manifest.json'
        feeds = json.loads(manifest.read_bytes())
        episode = feeds['files']['episodes']
        private_dir = manifest.parent / '.local'
        private_dir.mkdir()
        (manifest.parent / episode['path']).rename(private_dir / episode['path'])
        episode['path'] = '.local/' + episode['path']
        manifest.write_text(json.dumps(feeds), encoding='utf-8')
    else:
        private_dir = tmp_path / 'private'
        private_dir.mkdir()
        (private_dir / 'fictional.json').write_text('{"clinical_safety_approval": null}', encoding='utf-8')
        artifact = 'private/fictional.json'
        if location == 'binding_alias':
            (tmp_path / 'source-alias').symlink_to(private_dir, target_is_directory=True)
            artifact = 'source-alias/fictional.json'
        entry = next(item for item in record['entries'] if item['id'] == 'clinical_safety_approval')
        entry['binding']['artifact'] = artifact

    with pytest.raises(ValueError, match='private storage'):
        audit_placeholders(PlaceholderRegistry.model_validate(record), root=tmp_path)


def test_private_replacement_candidate_hash_is_checked_but_not_approved(tmp_path):
    from icu_liaison.placeholders import inspect_replacement_candidates

    record=registry()
    private=tmp_path/'private'
    private.mkdir()
    artifact=private/'data.fixture'
    artifact.write_text('NON-CLINICAL-CONTRACT-EXAMPLE', encoding='utf-8')
    sha=hashlib.sha256(artifact.read_bytes()).hexdigest()
    entry=next(e for e in record.entries if e.id=='local_icu_episodes')
    submission={
        'schema_version':1,
        'status':'candidates_for_independent_review',
        'entries':[{ 'id':entry.id,'evidence_type':entry.replacement.evidence_type,
            'artifact_path':str(artifact),'sha256':sha,
            'source_custodian_role':'Data custodian','approval_reference':'EXAMPLE-NOT-REAL'}],
    }
    reviewed=inspect_replacement_candidates(submission, record, project_root=ROOT)
    assert reviewed['candidate_hashes_matched']==1
    assert reviewed['independently_approved']==False
    assert reviewed['investment_ready']==False
    assert reviewed['unresolved_count']==len(record.entries)
    submission['entries'][0]['sha256']='0'*64
    with pytest.raises(ValueError,match='digest'):
        inspect_replacement_candidates(submission,record,project_root=ROOT)
    submission['entries'][0]['sha256']=sha
    submission['entries'][0]['artifact_path']=str(ROOT/'model-inputs/p4/illustrative.json')
    with pytest.raises(ValueError,match='private'):
        inspect_replacement_candidates(submission,record,project_root=ROOT)


def test_replacement_cannot_be_satisfied_with_a_synthetic_test_fixture(tmp_path):
    from icu_liaison.placeholders import inspect_replacement_candidates

    record=registry()
    f=ROOT/'tests/fixtures/p3_episodes/manifest.json'
    assert f.is_file()
    entry=next(e for e in record.entries if e.id=='local_icu_episodes')
    body={'schema_version':1,'status':'candidates_for_independent_review', 'entries':[{
        'id':entry.id,'evidence_type':entry.replacement.evidence_type,
        'artifact_path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),
        'source_custodian_role':'Clinical Informatics','approval_reference':'SYNTHETIC-NO-AUTHORITY'}]}
    with pytest.raises(ValueError,match='private'):
        inspect_replacement_candidates(body,record,project_root=ROOT)


def test_cli_requires_a_private_candidate_submission(tmp_path, monkeypatch, capsys):
    from icu_liaison import placeholders_cli

    checkout = tmp_path / 'checkout'
    checkout.mkdir()
    private = checkout / 'private'
    private.mkdir()
    artifact = private / 'candidate.txt'
    artifact.write_text('FICTIONAL CANDIDATE', encoding='utf-8')
    body = {
        'schema_version': 1,
        'status': 'candidates_for_independent_review',
        'entries': [{
            'id': 'local_icu_episodes',
            'evidence_type': 'approved_site_extract',
            'artifact_path': str(artifact),
            'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
            'source_custodian_role': 'Example custodian',
            'approval_reference': 'FICTIONAL-REFERENCE',
        }],
    }
    public_submission = checkout / 'submission.json'
    public_submission.write_text(json.dumps(body), encoding='utf-8')
    monkeypatch.setattr(placeholders_cli, 'ROOT', checkout)
    command = ['review-candidates', '--registry', str(REGISTRY), '--submission']

    assert placeholders_cli.main([*command, str(public_submission)]) == 2
    rejected = capsys.readouterr()
    assert not rejected.out
    assert 'UNVERIFIED_PLACEHOLDER' in rejected.err
    assert str(public_submission) not in rejected.err

    private_submission = public_submission.rename(private / public_submission.name)
    assert placeholders_cli.main([*command, str(private_submission)]) == 0
    accepted = capsys.readouterr()
    report = json.loads(accepted.out)
    assert report['candidate_hashes_matched'] == 1
    assert report['independently_approved'] is False
    assert report['unresolved_count'] == 33
    assert 'FICTIONAL-REFERENCE' not in accepted.out
    assert str(artifact) not in accepted.out


@pytest.mark.parametrize('checked_file', ['submission', 'artifact'])
@pytest.mark.parametrize('tracked', [False, True])
def test_candidate_files_in_other_checkout_require_ignored_storage(tmp_path, checked_file, tracked):
    from icu_liaison.placeholders import review_candidate_submission

    checkout = tmp_path / 'other-checkout'
    subprocess.run([
        'git', 'init', '--quiet', '--separate-git-dir', str(tmp_path / 'git-directory'), str(checkout),
    ], check=True)
    (checkout / '.gitignore').write_text('private/\n', encoding='utf-8')
    safe_dir = tmp_path / 'evidence-storage'
    safe_dir.mkdir()
    candidate_dir = checkout / 'private' if tracked else checkout
    candidate_dir.mkdir(exist_ok=True)
    submission = (candidate_dir if checked_file == 'submission' else safe_dir) / 'submission.json'
    artifact = (candidate_dir if checked_file == 'artifact' else safe_dir) / 'candidate.txt'
    artifact.write_text('FICTIONAL CANDIDATE', encoding='utf-8')
    submission.write_text(json.dumps({
        'schema_version': 1,
        'status': 'candidates_for_independent_review',
        'entries': [{
            'id': 'local_icu_episodes',
            'evidence_type': 'approved_site_extract',
            'artifact_path': str(artifact),
            'sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
            'source_custodian_role': 'Example custodian',
            'approval_reference': 'FICTIONAL-REFERENCE',
        }],
    }), encoding='utf-8')
    record = registry()
    if tracked:
        report = review_candidate_submission(submission, record, project_root=ROOT)
        assert report['candidate_hashes_matched'] == 1 and report['independently_approved'] is False
        to_add = submission if checked_file == 'submission' else artifact
        subprocess.run(['git', '-C', str(checkout), 'add', '-f', '--', str(to_add)], check=True)

    with pytest.raises(ValueError, match='private storage'):
        review_candidate_submission(submission, record, project_root=ROOT)


def test_synthetic_progress_builds_reproducible_existing_p3_p4_p5_p6_assets(tmp_path):
    from icu_liaison.placeholders import build_synthetic_progress_bundle
    from icu_liaison.p5_reporting import review_report,verify_manifest

    target=tmp_path/'placeholder-progress'
    outcome=build_synthetic_progress_bundle(root=ROOT, registry_path=REGISTRY, output_dir=target)
    assert outcome['status']=='synthetic_progress_complete_external_gates_open'
    assert outcome['investment_ready'] is False
    assert outcome['native_kairos_executed'] is False
    assert (target/'p5-report/manifest.json').exists()
    assert verify_manifest(target/'p5-report')
    assert review_report(target/'p5-report')['provider_qualification'] is False
    data=json.loads((target/'progress.json').read_text())
    assert data['p3']['data_class']=='synthetic'
    assert data['p4']['investment_ready'] is False
    assert data['p6']['trace']['status']=='synthetic_trace_admitted_not_a_DES_run'
    assert data['p6']['holdout']['local_CHHHS_data_used'] is False
    assert data['placeholders']['unresolved_count']==len(registry().entries)
    assert (target/'manifest.json').is_file()
    assert all(len(v)==64 for v in json.loads((target/'manifest.json').read_text())['files_sha256'].values())
    with pytest.raises(FileExistsError):
        build_synthetic_progress_bundle(root=ROOT, registry_path=REGISTRY, output_dir=target)


def test_dry_run_fails_closed_on_missing_synthetic_input_without_partial_output(tmp_path):
    from icu_liaison.placeholders import build_synthetic_progress_bundle
    import shutil
    project=tmp_path/'project'
    shutil.copytree(ROOT/'model-inputs', project/'model-inputs')
    shutil.copytree(ROOT/'tests/fixtures/p3_episodes', project/'tests/fixtures/p3_episodes')
    shutil.copytree(ROOT/'conductor/evidence', project/'conductor/evidence')
    shutil.copy(ROOT/'providers.lock.json',project/'providers.lock.json')
    (project/'model-inputs/p6/synthetic-trace.json').unlink()
    destination=tmp_path/'should-not-exist'
    with pytest.raises(ValueError):
        build_synthetic_progress_bundle(root=project,registry_path=project/'model-inputs/placeholders/registry.json',output_dir=destination)
    assert not destination.exists()


def test_cli_audit_and_site_readiness_gate(tmp_path):
    cmd=[sys.executable,'-m','icu_liaison.placeholders_cli','audit','--registry',str(REGISTRY)]
    p=subprocess.run(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    assert p.returncode==0,p.stderr
    r=json.loads(p.stdout)
    assert r['investment_ready'] is False
    p=subprocess.run(cmd+['--require-site-ready'],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    assert p.returncode==2
    assert json.loads(p.stdout)['investment_ready'] is False


def test_versioned_registry_and_candidate_json_schemas_reject_malicious_status():
    from jsonschema import Draft202012Validator
    record=registry().model_dump(mode='json')
    schema=json.loads((ROOT/'model-inputs/placeholders/registry.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(record)
    evil=copy.deepcopy(record)
    evil['entries'][0]['status']='reviewed'
    assert list(Draft202012Validator(schema).iter_errors(evil))
    cand=json.loads((ROOT/'model-inputs/placeholders/replacement-candidate-TEMPLATE.json').read_text())
    cand_schema=json.loads((ROOT/'model-inputs/placeholders/replacement-candidates.schema.json').read_text())
    Draft202012Validator.check_schema(cand_schema)
    Draft202012Validator(cand_schema).validate(cand)
    cand['status']='approved'
    assert list(Draft202012Validator(cand_schema).iter_errors(cand))


def test_registered_native_receipts_remain_unverified_and_p4_core_unmodified():
    record=registry()
    registered={x.id:x for x in record.entries}
    assert registered['native_kairos_receipt'].status=='placeholder'
    for name in ['native_kairos_receipt','native_dapane_receipt','native_voiage_receipt']:
        assert registered[name].binding.shape=='unverified_provider'
    assert registered['anzics_primary_pdf'].source_class=='unverified_public_metadata'
    assert registered['clinical_safety_approval'].binding.shape=='unknown'
    historical=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
    original=historical['file_sha256']['src/icu_liaison/p4_model.py']
    assert hashlib.sha256((ROOT/'src/icu_liaison/p4_model.py').read_bytes()).hexdigest()==original


def test_progress_manifest_rejects_modified_source_without_rehash(tmp_path):
    from icu_liaison.placeholders import build_synthetic_progress_bundle, verify_progress_manifest
    dest=tmp_path/'receipt'
    build_synthetic_progress_bundle(root=ROOT,registry_path=REGISTRY,output_dir=dest)
    assert verify_progress_manifest(dest)
    body=dest/'replacement-checklist.csv'
    body.write_bytes(body.read_bytes()+b'\\n')
    with pytest.raises(ValueError,match='hash'):
        verify_progress_manifest(dest)


def test_progress_manifest_requires_bundle_files(tmp_path):
    from icu_liaison.placeholders import verify_progress_manifest

    (tmp_path / 'manifest.json').write_text(json.dumps({
        'schema_version': 1,
        'data_class': 'synthetic',
        'status': 'portable_dry_run_only',
        'investment_ready': False,
        'files_sha256': {},
    }), encoding='utf-8')
    with pytest.raises(ValueError, match='file inventory'):
        verify_progress_manifest(tmp_path)


def test_progress_manifest_requires_complete_nested_p5_report(tmp_path):
    from icu_liaison.placeholders import build_synthetic_progress_bundle, verify_progress_manifest

    dest = tmp_path / 'receipt'
    build_synthetic_progress_bundle(root=ROOT, registry_path=REGISTRY, output_dir=dest)
    missing = 'p5-report/model-summary.json'
    (dest / missing).unlink()
    manifest_path = dest / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    del manifest['files_sha256'][missing]
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')

    with pytest.raises(ValueError, match='file-set mismatch'):
        verify_progress_manifest(dest)


@pytest.mark.parametrize('change', ['readiness_claim', 'closed_placeholder', 'empty_checklist'])
def test_progress_verifier_rejects_inconsistent_contents_even_with_matching_hashes(tmp_path, change):
    from icu_liaison.placeholders import build_synthetic_progress_bundle, verify_progress_manifest

    dest = tmp_path / 'receipt'
    build_synthetic_progress_bundle(root=ROOT, registry_path=REGISTRY, output_dir=dest)
    if change == 'empty_checklist':
        target = dest / 'replacement-checklist.csv'
        with target.open(encoding='utf-8') as file:
            header = file.readline()
        target.write_text(header, encoding='utf-8')
    else:
        target = dest / 'progress.json'
        progress = json.loads(target.read_bytes())
        if change == 'readiness_claim':
            progress['investment_ready'] = True
        else:
            progress['placeholders']['unresolved_ids'].remove('finance_approval')
            progress['placeholders']['unresolved_count'] -= 1
        target.write_text(json.dumps(progress), encoding='utf-8')
    manifest_path = dest / 'manifest.json'
    manifest = json.loads(manifest_path.read_bytes())
    manifest['files_sha256'][target.name] = hashlib.sha256(target.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')

    with pytest.raises(ValueError, match='synthetic progress receipt|unresolved placeholders'):
        verify_progress_manifest(dest)


def test_duplicate_candidate_fails_without_any_approval(tmp_path):
    from icu_liaison.placeholders import inspect_replacement_candidates
    private=tmp_path/'private';private.mkdir()
    f=private/'witness.bin';f.write_bytes(b'NON-PATIENT-CANDIDATE')
    sha=hashlib.sha256(f.read_bytes()).hexdigest()
    body={'schema_version':1,'status':'candidates_for_independent_review',
          'entries':[{'id':'native_kairos_receipt','evidence_type':'native_execution_receipt',
          'artifact_path':str(f),'sha256':sha,
          'source_custodian_role':'Software Assurance',
          'approval_reference':'NOT-A-REVIEW'}]*2}
    with pytest.raises(ValueError,match='duplicate'):
        inspect_replacement_candidates(body,registry(),project_root=ROOT)


def test_p7_track_metadata_retains_all_external_gates():
    x=json.loads((ROOT/'conductor/tracks/P7-placeholder-assisted-qualification/metadata.json').read_text())
    assert x['status']=='in_progress'
    assert x['accepted_phases']==['P7.1','P7.2','P7.3']
    assert any('CHHHS' in s for s in x['blocked_phases'])
    assert x['native_execution']=='not_executed'
    assert x['clinical_validation'] is False
    assert x['investment_ready'] is False
