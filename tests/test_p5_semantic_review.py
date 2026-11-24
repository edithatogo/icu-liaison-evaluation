"""P5 RED: independent report consumer checks that survive manifest rehashing."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import pytest

from icu_liaison.p4_model import EconomicScenario
from icu_liaison.p5_reporting import build_report, review_report

ROOT = Path(__file__).resolve().parents[1]


def _scenario():
    return EconomicScenario.model_validate_json((ROOT/'model-inputs/p4/illustrative.json').read_text())


def _rehash(directory: Path, file: str) -> None:
    manifest = json.loads((directory/'manifest.json').read_text())
    manifest['files_sha256'][file] = hashlib.sha256((directory/file).read_bytes()).hexdigest()
    (directory/'manifest.json').write_text(json.dumps(manifest))


def test_independent_report_reader_accepts_unmodified_generated_bundle(tmp_path):
    target = tmp_path/'report'
    build_report(_scenario(),target)
    reviewed = review_report(target)
    assert reviewed['status']=='self_consistency_verified_not_empirically_accepted'
    assert reviewed['independent_accounting_check']=='P4_draws_recomputed_from_published_decision_surface'
    assert reviewed['strategies_checked'] == 3
    assert reviewed['provider_qualification'] is False


def test_reader_rejects_rehashed_unregistered_attachment(tmp_path):
    target = tmp_path / 'report'
    build_report(_scenario(), target)
    attachment = target / 'unregistered.csv'
    attachment.write_text('scenario,draws\nfictional,10\n', encoding='utf-8')
    _rehash(target, attachment.name)
    with pytest.raises(ValueError, match='file-set mismatch'):
        review_report(target)


def test_reader_requires_manifest_to_be_a_regular_bundle_file(tmp_path):
    target = tmp_path / 'report'
    build_report(_scenario(), target)
    manifest = target / 'manifest.json'
    external_manifest = manifest.rename(tmp_path / 'manifest.json')
    manifest.symlink_to(external_manifest)
    with pytest.raises(ValueError, match='manifest'):
        review_report(target)


def test_reader_rejects_rehashed_contradictory_decision_brief(tmp_path):
    target = tmp_path / 'report'
    build_report(_scenario(), target)
    brief = target / 'report.md'
    original = brief.read_text(encoding='utf-8')
    brief.write_text(original.replace('Clinical safety: unmeasured.', 'Clinical safety: demonstrated.'),
                     encoding='utf-8')
    _rehash(target, brief.name)
    with pytest.raises(ValueError, match='decision brief'):
        review_report(target)


def test_reader_rejects_rehashed_inconsistent_sensitivity_swing(tmp_path):
    target = tmp_path / 'report'
    build_report(_scenario(), target)
    table = target / 'one-way-sensitivity.csv'
    with table.open(newline='', encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream))
    row = next(row for row in rows if float(row['absolute_net_resource_swing_aud']) > 0)
    row['absolute_net_resource_swing_aud'] = '0'
    with table.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    _rehash(target, table.name)
    with pytest.raises(ValueError, match='sensitivity'):
        review_report(target)


def test_rehashing_tampered_mean_does_not_evade_semantic_review(tmp_path):
    target=tmp_path/'report';build_report(_scenario(),target)
    f=target/'model-summary.json'
    model=json.loads(f.read_text())
    model['strategies']['liaison_service']['net_resource_benefit_aud']['mean'] += 10000
    f.write_text(json.dumps(model))
    _rehash(target,'model-summary.json')
    with pytest.raises(ValueError,match='summary'):
        review_report(target)


def test_rehashing_paired_probability_does_not_evade_semantic_review(tmp_path):
    target=tmp_path/'report';build_report(_scenario(),target)
    file=target/'paired-comparisons.csv'
    with file.open(newline='') as f:rows=list(csv.DictReader(f))
    rows[0]['probability_strictly_better']='0.99'
    with file.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    _rehash(target,'paired-comparisons.csv')
    with pytest.raises(ValueError,match='paired'):
        review_report(target)


@pytest.mark.parametrize(('filename', 'measure', 'field', 'value'), [
    ('cost-consequence.csv', 'net_budget_impact_aud', 'mean', '10000'),
    ('cost-consequence.csv', 'usable_bed_days', 'boundary', 'hypothetical_cash_realisability_only'),
    ('paired-comparisons.csv', 'net_budget_impact_aud', 'p50', '10000'),
    ('paired-comparisons.csv', 'net_budget_impact_aud', 'probability_strictly_better', '0.9'),
])
def test_reader_rejects_rehashed_cash_and_capacity_disagreements(tmp_path, filename, measure, field, value):
    target = tmp_path / 'report'
    build_report(_scenario(), target)
    file = target / filename
    with file.open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    row = next(row for row in rows if row['strategy_id'] == 'liaison_service' and row['measure'] == measure)
    row[field] = value
    with file.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    _rehash(target, filename)
    with pytest.raises(ValueError, match='cost|paired'):
        review_report(target)


def test_reader_rejects_an_admission_claim_changed_in_both_files(tmp_path):
    target = tmp_path / 'report'
    build_report(_scenario(), target)
    admission_file = target / 'evidence-admission.json'
    model_file = target / 'model-summary.json'
    admission = json.loads(admission_file.read_text())
    admission['document_verified'] = True
    model = json.loads(model_file.read_text())
    model['P4_source_admission'] = admission
    admission_file.write_text(json.dumps(admission))
    model_file.write_text(json.dumps(model))
    _rehash(target, admission_file.name)
    _rehash(target, model_file.name)
    with pytest.raises(ValueError, match='evidence|admission'):
        review_report(target)


def test_mislabelled_readiness_cannot_be_accepted_with_new_manifest(tmp_path):
    target=tmp_path/'report';build_report(_scenario(),target)
    file=target/'model-summary.json'
    model=json.loads(file.read_text());model['investment_ready']=True
    file.write_text(json.dumps(model));_rehash(target,'model-summary.json')
    with pytest.raises(ValueError,match='readiness'):
        review_report(target)
