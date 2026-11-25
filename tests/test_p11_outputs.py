"""Versioned P11 summaries and figure revisions."""
from pytest import MonkeyPatch
from typing import Any
import hashlib
import json
from pathlib import Path

import pytest

from icu_liaison.p11_figure import build_figure, verify_figure
from icu_liaison.p11_model import build_case, verify_case
from icu_liaison.p11_p9 import build_p9
from icu_liaison.p11_summary import build_summary, verify_summary
from icu_liaison.p11_verify import verify_output
from tools.p10_falsification import run_suite

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'model-inputs/p4/illustrative.json'
CASES = ROOT / 'model-inputs/p11/cases'
STYLE = ROOT / 'model-inputs/p11/f01-style.json'


def build_short_case(tmp_path: Path, output: Path, name: str) -> tuple[dict[str, Any], Path]:
    data = json.loads((CASES / f'{name}.json').read_text())
    data['iterations'] = 32
    case = tmp_path / f'{name}.json'
    case.write_text(json.dumps(data))
    pointer = tmp_path / f'{name}-pointer.json'
    return build_case(case, BASE, output, pointer), pointer


def test_summary_links_verified_paired_runs(tmp_path: Path) -> None:
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


def test_style_revision_reuses_same_model(tmp_path: Path) -> None:
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


def test_rehashed_paired_outcome_fails_numerical_replay(tmp_path: Path) -> None:
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


def test_changed_model_code_identity_invalidates_run(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
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


def test_current_outputs_detect_changed_summary_even_after_rehash(tmp_path: Path) -> None:
    import os
    import subprocess
    import sys

    from tools.validate_reporting_contracts import CATALOGUE, verify_run_coverage

    output = tmp_path / 'store'
    data = json.loads((CASES / 'base.json').read_text())
    data['iterations'] = 32
    case = tmp_path / 'case.json'
    case.write_text(json.dumps(data))
    model_pointer = output / 'state/models/base.json'
    model = build_case(case, BASE, output, model_pointer)
    build_figure(model_pointer, STYLE, output, output / 'state/figures/base.json')
    p9 = build_p9(model_pointer, output, output / 'state/priority-figures/base.json')
    suite = tmp_path / 'suite.json'
    suite.write_text(json.dumps({'schema_version': 1, 'data_class': 'synthetic', 'cases': ['base']}))
    audit = tmp_path / 'audit.json'
    audit.write_text(json.dumps(run_suite(32)))
    pointer = output / 'state/summary.json'
    result = build_summary(suite, output, [model_pointer], audit, pointer)
    verified = verify_output(output)
    assert verified['scenarios'] == 1 and verified['priority_figures'] == 6
    assert verified['supplementary_figures'] == 7
    catalogue = json.loads(CATALOGUE.read_bytes())
    command = [sys.executable, 'tools/validate_reporting_contracts.py', '--run', str(output)]
    completed = subprocess.run(command, cwd=ROOT, env={**os.environ, 'PYTHONPATH': str(ROOT / 'src')},
                               capture_output=True, text=True, timeout=60)
    assert completed.returncode == 0, completed.stderr
    coverage = json.loads(completed.stdout)
    assert coverage['summary_id'] == result['summary_id']
    assert coverage['investment_ready'] is False
    assert {entry['id'] for entry in coverage['blocked']} == {
        'T05', 'T06', 'T07', 'F03', 'F04', 'F12', 'F14', 'F16', 'F17', 'F19', 'F21', 'F22', 'F23'}
    assert all(entry['evidence_needed'] for entry in coverage['blocked'])
    case, = coverage['scenarios']
    assert case['case_id'] == 'base' and case['model_run_id'] == model['model_run_id']
    assert case['run_catalogue_sha256'] == hashlib.sha256(CATALOGUE.read_bytes()).hexdigest()
    assert [entry['id'] for entry in case['tables']] == ['T01', 'T02', 'T03', 'T04']
    assert len(case['figures']) == 14
    assert case['not_in_run'] == []
    for entry in case['tables'] + case['figures'] + [figure['source'] for figure in case['figures']]:
        assert hashlib.sha256((output / entry['path']).read_bytes()).hexdigest() == entry['sha256']

    for name in ('f20.svg', 'f18.svg'):
        svg = output / 'priority-figures' / p9['figure_revision'] / 'bundle' / name
        original = svg.read_bytes()
        svg.write_bytes(original + b' ')
        with pytest.raises(ValueError, match='inventory or digest'):
            verify_run_coverage(output, catalogue)
        svg.write_bytes(original)

    f01_pointer_path = output / 'state/figures/base.json'
    f01_pointer = json.loads(f01_pointer_path.read_bytes())
    f01_folder = output / 'figures' / f01_pointer['figure_revision']
    f01_svg = f01_folder / 'scenario-comparison.svg'
    f01_record = f01_folder / 'figure.json'
    original_files = {file: file.read_bytes() for file in (f01_pointer_path, f01_svg, f01_record)}
    f01_svg.write_text('<svg', encoding='utf-8')
    figure = json.loads(original_files[f01_record])
    figure['files_sha256'][f01_svg.name] = hashlib.sha256(f01_svg.read_bytes()).hexdigest()
    f01_record.write_text(json.dumps(figure), encoding='utf-8')
    f01_pointer['figure_record_sha256'] = hashlib.sha256(f01_record.read_bytes()).hexdigest()
    f01_pointer_path.write_text(json.dumps(f01_pointer), encoding='utf-8')
    rejected = subprocess.run(command, cwd=ROOT, env={**os.environ, 'PYTHONPATH': str(ROOT / 'src')},
                              capture_output=True, text=True, timeout=60)
    assert rejected.returncode == 2
    assert rejected.stdout == '' and 'P9 INVALID_OR_UNVERIFIED' in rejected.stderr
    assert 'Traceback' not in rejected.stderr
    for file, content in original_files.items():
        file.write_bytes(content)

    figure = json.loads(original_files[f01_record])
    figure['clinical_safety_approved'] = True
    f01_record.write_text(json.dumps(figure), encoding='utf-8')
    f01_pointer['figure_record_sha256'] = hashlib.sha256(f01_record.read_bytes()).hexdigest()
    f01_pointer_path.write_text(json.dumps(f01_pointer), encoding='utf-8')
    with pytest.raises(ValueError, match='F01 clinical safety'):
        verify_run_coverage(output, catalogue)
    for file, content in original_files.items():
        file.write_bytes(content)

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


def test_rehashed_f01_interval_is_checked_against_model(tmp_path: Path) -> None:
    import re

    output = tmp_path / 'store'
    _, pointer = build_short_case(tmp_path, output, 'base')
    receipt = build_figure(pointer, STYLE, output, tmp_path / 'f01.json')
    folder = output / 'figures' / receipt['figure_revision']
    svg = folder / 'scenario-comparison.svg'
    text = svg.read_text()
    # Change only a plotted percentile, retaining the title, description and mean bars.
    changed, count = re.subn(r'(<path d="M [\d.]+ )[\d.]+( \nL [\d.]+ [\d.]+ \n" clip-path=[^>]+stroke-width: 1.8)',
                             r'\g<1>999.5\2', text, count=1)
    assert count == 1
    svg.write_text(changed)
    record_file = folder / 'figure.json'
    record = json.loads(record_file.read_text())
    record['files_sha256'][svg.name] = hashlib.sha256(svg.read_bytes()).hexdigest()
    record_file.write_text(json.dumps(record))
    with pytest.raises(ValueError, match='mark'):
        verify_figure(folder)


@pytest.mark.parametrize(('alter', 'error'), [
    ('bundle_file', 'manifest'),
    ('source_hash', 'manifest'),
    ('scenario_seed', 'source run'),
    ('denominator_ids', 'catalogue'),
    ('sources', 'catalogue'),
    ('accessible_description', 'accessibility'),
])
def test_archived_p9_checks_frozen_figure_evidence(tmp_path: Path, monkeypatch: MonkeyPatch, alter: str, error: str) -> None:
    import icu_liaison.p11_p9 as figures
    from icu_liaison.p11_records import digest_file, inventory

    output = tmp_path / 'store'
    model, pointer = build_short_case(tmp_path, output, 'base')
    result = build_p9(pointer, output, tmp_path / 'figures.json')
    folder = output / 'priority-figures' / result['figure_revision']
    monkeypatch.setattr(figures, 'fingerprint', lambda: {'archived': True})
    assert figures.verify_p9(folder, output / 'models' / model['model_run_id'])
    if alter == 'bundle_file':
        svg = folder / 'bundle/f18.svg'
        svg.write_bytes(svg.read_bytes() + b' ')
    else:
        manifest_file = folder / 'bundle/manifest.json'
        manifest = json.loads(manifest_file.read_bytes())
        if alter == 'source_hash':
            manifest['inputs_sha256']['p3_episodes'] = '1' * 64
        elif alter == 'scenario_seed':
            manifest['scenario_seed'] += 1
        elif alter == 'denominator_ids':
            manifest['figures'][0]['denominator_ids'] = ['D01']
        elif alter == 'sources':
            manifest['figures'][0]['sources'].remove('p5_model_summary')
        elif alter == 'accessible_description':
            svg = folder / 'bundle/f02.svg'
            markup = svg.read_text(encoding='utf-8')
            catalogue = json.loads((folder / 'inputs/catalogue.json').read_bytes())
            text = next(figure['alt_text'] for figure in catalogue['figures'] if figure['id'] == 'F02')
            assert text in markup
            svg.write_text(markup.replace(text, 'Description from a different figure'), encoding='utf-8')
            manifest['files_sha256'][svg.name] = digest_file(svg)
        manifest_file.write_text(json.dumps(manifest))
        review_file = folder / 'review.json'
        review = json.loads(review_file.read_bytes())
        review['manifest_sha256'] = digest_file(manifest_file)
        review_file.write_text(json.dumps(review))
    record_file = folder / 'figure-set.json'
    record = json.loads(record_file.read_bytes())
    record['files_sha256'] = inventory(folder, exclude='figure-set.json')
    record_file.write_text(json.dumps(record))
    with pytest.raises(ValueError, match=error):
        figures.verify_p9(folder, output / 'models' / model['model_run_id'])
