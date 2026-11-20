"""Versioned P11 summaries and figure revisions."""
import hashlib
import json
from pathlib import Path

import pytest

from icu_liaison.p11_figure import build_figure, verify_figure
from icu_liaison.p11_model import build_case, verify_case
from icu_liaison.p11_summary import build_summary, verify_summary
from icu_liaison.p11_verify import verify_output
from tools.p10_falsification import run_suite

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'model-inputs/p4/illustrative.json'
CASES = ROOT / 'model-inputs/p11/cases'
STYLE = ROOT / 'model-inputs/p11/f01-style.json'


def build_short_case(tmp_path, output, name):
    data = json.loads((CASES / f'{name}.json').read_text())
    data['iterations'] = 32
    case = tmp_path / f'{name}.json'
    case.write_text(json.dumps(data))
    pointer = tmp_path / f'{name}-pointer.json'
    return build_case(case, BASE, output, pointer), pointer


def test_summary_links_verified_paired_runs(tmp_path):
    output = tmp_path / 'store'
    base, base_pointer = build_short_case(tmp_path, output, 'base')
    harm, harm_pointer = build_short_case(tmp_path, output, 'harmful_returns')
    suite = tmp_path / 'suite.json'
    suite.write_text(json.dumps({'schema_version': 1, 'data_class': 'synthetic',
                                 'cases': ['base', 'harmful_returns']}))
    audit = tmp_path / 'audit.json'
    audit.write_text(json.dumps(run_suite(32)))
    result = build_summary(suite, output, [base_pointer, harm_pointer], audit,
                           tmp_path / 'summary-pointer.json')
    folder = output / 'summaries' / result['summary_id']
    record = verify_summary(folder)
    assert record['cross_scenario_pairing'] == 'not_asserted'
    assert [item['model_run_id'] for item in record['identity']['runs']] == [
        base['model_run_id'], harm['model_run_id']
    ]
    assert 'harmful_returns' in (folder / 'scenario-comparison.csv').read_text()
    assert record['investment_ready'] is False


def test_style_revision_reuses_same_model(tmp_path):
    output = tmp_path / 'store'
    model, model_pointer = build_short_case(tmp_path, output, 'base')
    run_json = output / 'models' / model['model_run_id'] / 'run.json'
    model_hash = hashlib.sha256(run_json.read_bytes()).hexdigest()
    style = tmp_path / 'style.json'
    settings = json.loads(STYLE.read_text())
    style.write_text(json.dumps(settings))
    first = build_figure(model_pointer, style, output, tmp_path / 'figure-pointer.json')
    settings['bar_color'] = '#9c4128'
    style.write_text(json.dumps(settings))
    second = build_figure(model_pointer, style, output, tmp_path / 'figure-pointer.json')
    assert first['figure_revision'] != second['figure_revision']
    assert first['model_run_id'] == second['model_run_id'] == model['model_run_id']
    assert hashlib.sha256(run_json.read_bytes()).hexdigest() == model_hash
    first_folder = output / 'figures' / first['figure_revision']
    second_folder = output / 'figures' / second['figure_revision']
    assert verify_figure(first_folder) and verify_figure(second_folder)
    assert (first_folder / 'scenario-comparison.svg').read_bytes() != (
        second_folder / 'scenario-comparison.svg').read_bytes()


def test_rehashed_paired_outcome_fails_numerical_replay(tmp_path):
    output = tmp_path / 'store'
    model, _ = build_short_case(tmp_path, output, 'base')
    folder = output / 'models' / model['model_run_id']
    path = folder / 'paired-outcomes.csv'
    data = path.read_text()
    path.write_text(data.replace('within_run_paired_parameter_draws', 'falsely_paired', 1))
    record_file = folder / 'run.json'
    record = json.loads(record_file.read_text())
    record['files_sha256']['paired-outcomes.csv'] = hashlib.sha256(path.read_bytes()).hexdigest()
    record_file.write_text(json.dumps(record))
    with pytest.raises(ValueError, match='paired outcomes'):
        verify_case(folder)


def test_changed_model_code_identity_invalidates_run(tmp_path, monkeypatch):
    import icu_liaison.p11_model as model

    output = tmp_path / 'store'
    first, pointer = build_short_case(tmp_path, output, 'base')
    old_hashes = model._source_hashes()
    changed = dict(old_hashes)
    changed['src/icu_liaison/p4_model.py'] = 'a' * 64
    monkeypatch.setattr(model, '_source_hashes', lambda: changed)
    case = tmp_path / 'base.json'
    second = build_case(case, BASE, output, pointer)
    assert first['model_run_id'] != second['model_run_id']
    assert (output / 'models' / first['model_run_id']).is_dir()
    assert (output / 'models' / second['model_run_id']).is_dir()


def test_current_outputs_detect_changed_summary_even_after_rehash(tmp_path):
    output = tmp_path / 'store'
    data = json.loads((CASES / 'base.json').read_text())
    data['iterations'] = 32
    case = tmp_path / 'case.json'
    case.write_text(json.dumps(data))
    model_pointer = output / 'state/models/base.json'
    model = build_case(case, BASE, output, model_pointer)
    build_figure(model_pointer, STYLE, output, output / 'state/figures/base.json')
    suite = tmp_path / 'suite.json'
    suite.write_text(json.dumps({'schema_version': 1, 'data_class': 'synthetic', 'cases': ['base']}))
    audit = tmp_path / 'audit.json'
    audit.write_text(json.dumps(run_suite(32)))
    pointer = output / 'state/summary.json'
    result = build_summary(suite, output, [model_pointer], audit, pointer)
    assert verify_output(output)['scenarios'] == 1
    folder = output / 'summaries' / result['summary_id']
    comparison = folder / 'scenario-comparison.csv'
    comparison.write_text(comparison.read_text().replace('within_run_paired_parameter_draws', 'false', 1))
    record_path = folder / 'summary.json'
    record = json.loads(record_path.read_text())
    record['files_sha256']['scenario-comparison.csv'] = hashlib.sha256(comparison.read_bytes()).hexdigest()
    record_path.write_text(json.dumps(record))
    summary_pointer = json.loads(pointer.read_text())
    summary_pointer['summary_record_sha256'] = hashlib.sha256(record_path.read_bytes()).hexdigest()
    pointer.write_text(json.dumps(summary_pointer))
    with pytest.raises(ValueError, match='summary rows'):
        verify_output(output)
    assert (output / 'models' / model['model_run_id']).is_dir()
