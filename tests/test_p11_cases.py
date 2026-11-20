"""P11 synthetic run identity, paired outcomes and atomic publication."""
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import json
from pathlib import Path

import pytest

from icu_liaison.p11_model import build_case, verify_case
from icu_liaison.p11_cases import materialise

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'model-inputs/p4/illustrative.json'
CASES = ROOT / 'model-inputs/p11/cases'


@pytest.fixture
def case_file(tmp_path):
    source = json.loads((CASES / 'base.json').read_text())
    source['iterations'] = 32
    path = tmp_path / 'base.json'
    path.write_text(json.dumps(source))
    return path


def rows(folder):
    with (folder / 'paired-outcomes.csv').open(newline='') as stream:
        return list(csv.DictReader(stream))


def test_fixed_override_preserves_other_dependence_submatrix():
    base = json.loads(BASE.read_text())
    groups = base['dependence_groups']
    groups[1]['variables'].append('resource.hours_released_per_improved_case')
    groups[1]['gaussian_correlation'] = [[1, .2, .1], [.2, 1, .3], [.1, .3, 1]]
    case = json.loads((CASES / 'base.json').read_text())
    case['overrides'] = {'resource.addressable_delay_fraction': {
        'family': 'fixed', 'params': {'value': .3}, 'unit': 'proportion',
        'evidence_status': 'illustrative_assumption', 'source_ref': 'P4-ILLUSTRATIVE',
    }}
    _, result = materialise(json.dumps(case).encode(), json.dumps(base).encode())
    assert result.resource.addressable_delay_fraction.params['value'] == .3
    assert result.dependence_groups[0].model_dump() == groups[0]
    assert result.dependence_groups[1].model_dump() == {
        'variables': groups[1]['variables'][1:],
        'gaussian_correlation': [[1, .3], [.3, 1]],
    }


def test_base_run_preserves_paired_p5_comparisons(tmp_path, case_file):
    output = tmp_path / 'run-store'
    receipt = build_case(case_file, BASE, output, tmp_path / 'base-pointer.json')
    folder = output / 'models' / receipt['model_run_id']
    verified = verify_case(folder)
    assert receipt['model_run_id'] == verified['model_run_id']
    assert verified['data_class'] == 'synthetic'
    assert verified['investment_ready'] is False
    assert verified['seed'] == 20261118 and verified['draws'] == 32
    values = rows(folder)
    assert {row['strategy_id'] for row in values} == {'liaison_service', 'extended_cover'}
    assert {row['measure'] for row in values} >= {
        'icu_bed_days_released', 'usable_bed_days', 'readmissions_avoided',
        'net_resource_benefit_aud', 'net_budget_impact_aud',
    }
    with (folder / 'p5-report' / 'paired-comparisons.csv').open(newline='') as stream:
        p5_rows = list(csv.DictReader(stream))
    for row in values:
        if row['measure'] in {'net_resource_benefit_aud', 'net_budget_impact_aud'}:
            match = next(item for item in p5_rows
                         if item['strategy_id'] == row['strategy_id'] and item['measure'] == row['measure'])
            assert float(row['mean']) == pytest.approx(float(match['mean']))


@pytest.mark.parametrize('variant', [
    'no_effect', 'harmful_returns', 'zero_addressable_delay',
    'zero_usable_capacity', 'zero_cash_realisability',
])
def test_existing_stress_cases_preserve_invariants(tmp_path, variant):
    data = json.loads((CASES / f'{variant}.json').read_text())
    data['iterations'] = 32
    case = tmp_path / f'{variant}.json'
    case.write_text(json.dumps(data))
    output = tmp_path / 'store'
    receipt = build_case(case, BASE, output, tmp_path / 'pointer.json')
    folder = output / 'models' / receipt['model_run_id']
    values = rows(folder)
    liaison = {row['measure']: float(row['mean']) for row in values
               if row['strategy_id'] == 'liaison_service'}
    if variant == 'no_effect':
        assert liaison['icu_bed_days_released'] == 0
        assert liaison['readmissions_avoided'] == 0
        assert liaison['net_resource_benefit_aud'] < 0
    if variant == 'harmful_returns':
        assert liaison['readmissions_avoided'] < 0
    if variant == 'zero_addressable_delay':
        assert liaison['icu_bed_days_released'] == 0
    if variant == 'zero_usable_capacity':
        assert liaison['usable_bed_days'] == 0
    if variant == 'zero_cash_realisability':
        assert liaison['net_budget_impact_aud'] < 0
    assert verify_case(folder)['case_id'] == variant


def test_changed_input_produces_new_version_and_preserves_prior(tmp_path, case_file):
    output = tmp_path / 'store'
    pointer = tmp_path / 'pointer.json'
    first = build_case(case_file, BASE, output, pointer)
    unchanged = build_case(case_file, BASE, output, pointer)
    assert unchanged['model_run_id'] == first['model_run_id']
    old = output / 'models' / first['model_run_id']
    old_hash = hashlib.sha256((old / 'run.json').read_bytes()).hexdigest()
    data = json.loads(case_file.read_text())
    data['seed'] = 20261119
    case_file.write_text(json.dumps(data))
    second = build_case(case_file, BASE, output, pointer)
    assert second['model_run_id'] != first['model_run_id']
    assert hashlib.sha256((old / 'run.json').read_bytes()).hexdigest() == old_hash
    assert verify_case(old)['seed'] == 20261118
    assert verify_case(output / 'models' / second['model_run_id'])['seed'] == 20261119


def test_rehashed_claim_and_tampering_are_rejected(tmp_path, case_file):
    output = tmp_path / 'store'
    receipt = build_case(case_file, BASE, output, tmp_path / 'pointer.json')
    folder = output / 'models' / receipt['model_run_id']
    data = json.loads((folder / 'run.json').read_text())
    data['investment_ready'] = True
    (folder / 'run.json').write_text(json.dumps(data))
    with pytest.raises(ValueError, match='synthetic|readiness'):
        verify_case(folder)


def test_interrupted_publication_can_be_retried(tmp_path, case_file, monkeypatch):
    import icu_liaison.p11_model as model

    output = tmp_path / 'store'
    pointer = tmp_path / 'pointer.json'
    first = build_case(case_file, BASE, output, pointer)
    original = model.build_report
    data = json.loads(case_file.read_text())
    data['seed'] = 20261119
    case_file.write_text(json.dumps(data))

    def interrupted(*args, **kwargs):
        original(*args, **kwargs)
        raise KeyboardInterrupt()

    monkeypatch.setattr(model, 'build_report', interrupted)
    with pytest.raises(KeyboardInterrupt):
        build_case(case_file, BASE, output, pointer)
    assert json.loads(pointer.read_text())['model_run_id'] == first['model_run_id']
    assert verify_case(output / 'models' / first['model_run_id'])
    monkeypatch.setattr(model, 'build_report', original)
    second = build_case(case_file, BASE, output, pointer)
    assert second['model_run_id'] != first['model_run_id']
    assert verify_case(output / 'models' / second['model_run_id'])


def test_concurrent_same_identity_publishes_one_verified_object(tmp_path, case_file):
    output = tmp_path / 'store'
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(build_case, case_file, BASE, output, tmp_path / f'pointer-{i}.json')
                   for i in range(2)]
        results = [future.result() for future in futures]
    assert results[0]['model_run_id'] == results[1]['model_run_id']
    assert len(list((output / 'models').iterdir())) == 1
    assert verify_case(output / 'models' / results[0]['model_run_id'])
