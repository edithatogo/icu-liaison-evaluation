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


def test_mislabelled_readiness_cannot_be_accepted_with_new_manifest(tmp_path):
    target=tmp_path/'report';build_report(_scenario(),target)
    file=target/'model-summary.json'
    model=json.loads(file.read_text());model['investment_ready']=True
    file.write_text(json.dumps(model));_rehash(target,'model-summary.json')
    with pytest.raises(ValueError,match='readiness'):
        review_report(target)
