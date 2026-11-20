"""Synthetic source values, conserved counts and rehashed visual tampering."""
import csv
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from icu_liaison.p4_model import EconomicScenario, evaluate_scenarios
from icu_liaison.p5_reporting import build_report
from icu_liaison.p9_figures import build_figures, review_figures

ROOT = Path(__file__).resolve().parents[1]
IDS = {'F05', 'F06', 'F07', 'F08', 'F09', 'F13', 'F18'}


def test_supplement_source_and_mark_reconciliation(tmp_path):
    raw = json.loads((ROOT / 'model-inputs/p4/illustrative.json').read_text())
    raw['iterations'] = 32
    scenario = EconomicScenario.model_validate(raw)
    case, p5, out = tmp_path / 'case.json', tmp_path / 'p5', tmp_path / 'figures'
    case.write_text(scenario.model_dump_json())
    build_report(scenario, p5)
    receipt = build_figures(case, p5, out, include_supplement=True)
    assert IDS <= set(receipt['figures_checked'])

    def rows(key):
        with (out / f'{key}.csv').open(newline='') as stream:
            return list(csv.DictReader(stream))

    with (p5 / 'decision-surface.csv').open(newline='') as stream:
        draws = [float(r['liaison_service']) - float(r['current_care']) for r in csv.DictReader(stream)]
    signs = {r['sign']: int(r['count']) for r in rows('f06') if r['strategy'] == 'liaison_service'}
    assert signs == {'positive': sum(x > 0 for x in draws), 'zero': draws.count(0),
                     'negative': sum(x < 0 for x in draws)}
    histogram = rows('f08')
    assert sum(int(r['count']) for r in histogram) == len(draws)
    assert float(histogram[0]['lower_aud']) <= min(draws) <= max(draws) <= float(histogram[-1]['upper_aud'])
    trace = rows('f09')
    bed_minutes = {arm: sum((int(r['end_minute']) - int(r['start_minute'])) * int(r['occupied_beds'])
                            for r in trace if r['strategy'] == arm) for arm in ('current_care','liaison_service')}
    assert bed_minutes == {'current_care': 180, 'liaison_service': 150}
    assert {r['outcome']: int(r['count']) for r in rows('f13')} == {
        'Unplanned return': 1, 'Observed without return': 1, 'Competing death': 1, 'Unknown': 0}
    weeks = rows('f18')
    assert [(int(r['week']), float(r['gap_change_hours'])) for r in weeks] == [
        (-3, 0), (-2, 0), (-1, 0), (0, -.5), (1, -1.5), (2, -1.5)]

    for key in sorted(IDS):
        svg = out / f'{key.lower()}.svg'
        original = svg.read_bytes()
        tree = ET.fromstring(original)
        group = next(n for n in tree.iter() if n.get('id') == 'data-0')
        group.clear()
        svg.write_bytes(ET.tostring(tree))
        manifest_path = out / 'manifest.json'
        original_manifest = manifest_path.read_bytes()
        manifest = json.loads(original_manifest)
        manifest['files_sha256'][svg.name] = hashlib.sha256(svg.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
        with pytest.raises(ValueError, match='mark|render'):
            review_figures(case, p5, out, include_supplement=True)
        svg.write_bytes(original)
        manifest_path.write_bytes(original_manifest)


@pytest.mark.parametrize('edit', ['duplicate', 'gap', 'no_baseline', 'observed'])
def test_event_design_requires_fictional_consecutive_periods(tmp_path, edit):
    from icu_liaison.p9_supplement_data import DESIGN, event_rows

    spec = json.loads(DESIGN.read_bytes())
    if edit == 'duplicate':
        spec['periods'].insert(0, spec['periods'][0])
    elif edit == 'gap':
        del spec['periods'][1]
    elif edit == 'no_baseline':
        spec['periods'] = [p for p in spec['periods'] if p['week'] >= 0]
    else:
        spec['data_class'] = 'observed'
    path = tmp_path / 'design.json'
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError):
        event_rows(path)


def test_constant_zero_differences_preserve_ties_and_histogram_total(tmp_path):
    from icu_liaison.p9_figure_data import paired_capacity
    from icu_liaison.p9_supplement_data import economic_rows

    raw = json.loads((ROOT / 'model-inputs/p4/illustrative.json').read_bytes())
    raw['iterations'] = 32
    raw['dependence_groups'] = []
    for arm in raw['strategies']:
        for key in ('coverage_fraction', 'annual_incremental_cost_aud'):
            arm[key].update(family='fixed', params={'value': 0})
    scenario = EconomicScenario.model_validate(raw)
    folder = tmp_path / 'p5'
    build_report(scenario, folder)
    run = evaluate_scenarios(scenario)
    rows = economic_rows(run, folder, paired_capacity(run, folder / 'decision-surface.csv'))
    assert all(row['count'] == (32 if row['sign'] == 'zero' else 0) for row in rows['F06'])
    occupied, = (row for row in rows['F08'] if row['count'])
    assert occupied['lower_aud'] <= 0 <= occupied['upper_aud'] and occupied['count'] == 32


def test_restricted_manifest_is_rejected_before_opening_episode_feeds(tmp_path):
    from icu_liaison.p9_figures import DEFAULT_P3
    from icu_liaison.p9_supplement_data import flow_rows

    manifest = json.loads(DEFAULT_P3.read_bytes())
    manifest['data_class'] = 'restricted'
    manifest['governance'] = {'status': 'approved_local_processing', 'approval_reference': 'test-fixture',
                              'custodian_role': 'fictional fixture custodian'}
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='requires a synthetic P3 cohort'):
        flow_rows(path)
