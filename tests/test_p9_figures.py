"""Fictional figure regression and source-to-mark rejection checks."""
from typing import Any
import csv
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from icu_liaison.p4_model import EconomicScenario, evaluate_scenarios
from icu_liaison.p5_reporting import build_report
from icu_liaison.p9_figure_data import (
    Fixtures, break_even_grid, coverage_rows, journey_rows, paired_capacity,
    resource_waterfall, sensitivity_grid,
)
from icu_liaison.p9_figures import build_figures, review_figures
from icu_liaison.p11_cases import materialise
from tools.p10_falsification import _variant

ROOT = Path(__file__).resolve().parents[1]
SCENARIO_FILE = ROOT / 'model-inputs/p4/illustrative.json'
FIXTURES_FILE = ROOT / 'model-inputs/p9/illustrative.json'
P3_MANIFEST = ROOT / 'model-inputs/placeholders/p3-synthetic/manifest.json'


@pytest.fixture
def scenario() -> EconomicScenario:
    source = json.loads(SCENARIO_FILE.read_text())
    source['iterations'] = 32
    return EconomicScenario.model_validate(source)


@pytest.fixture
def fixture_inputs() -> dict[str, Any]:
    value = json.loads(FIXTURES_FILE.read_text())
    assert isinstance(value, dict)
    return value


def test_waterfall_reconciles_three_unique_resource_components(scenario: EconomicScenario) -> None:
    rows = resource_waterfall(scenario)
    assert [row['value_aud'] for row in rows] == pytest.approx(
        [13770, 67500, -250000, -168730]
    )
    assert rows[-1]['end_aud'] == pytest.approx(sum(row['value_aud'] for row in rows[:-1]))


def test_break_even_limited_to_stated_priors(scenario: EconomicScenario) -> None:
    rows = break_even_grid(scenario)
    assert {min(r['delay_success'] for r in rows), max(r['delay_success'] for r in rows)} == {0.2, 0.8}
    assert {min(r['annual_cost_aud'] for r in rows), max(r['annual_cost_aud'] for r in rows)} == {200000, 380000}
    assert max(r['net_resource_aud'] for r in rows) == pytest.approx(-110468)
    assert not any(r['net_resource_aud'] >= 0 for r in rows)

    variant = scenario.model_dump()
    variant['strategies'][1]['annual_incremental_cost_aud']['params'] = {
        'low': 76000.0, 'mode': 82000.0, 'high': 88000.0
    }
    results = break_even_grid(EconomicScenario.model_validate(variant))
    assert min(r['net_resource_aud'] for r in results) < 0 < max(r['net_resource_aud'] for r in results)


def test_fixed_no_effect_prior_produces_a_one_dimensional_break_even(tmp_path: Path, scenario: EconomicScenario) -> None:
    no_effect = _variant(scenario.model_dump(mode='json'), 'no_effect')
    rows = break_even_grid(no_effect)
    assert len(rows) == 17
    assert {row['delay_success'] for row in rows} == {0.0}
    assert len({row['annual_cost_aud'] for row in rows}) == 17
    assert all(row['net_resource_aud'] < 0 for row in rows)
    scenario_file = tmp_path / 'scenario.json'
    scenario_file.write_text(no_effect.model_dump_json())
    p5, out = tmp_path / 'p5', tmp_path / 'figures'
    build_report(no_effect, p5)
    result = build_figures(scenario_file, p5, out)
    assert result['figures_checked'] == ['F02', 'F10', 'F11', 'F15', 'F20', 'F24']
    assert 'Delay resolution fixed at 0%' in (out / 'f10.svg').read_text()
    assert review_figures(scenario_file, p5, out)['investment_ready'] is False


@pytest.mark.parametrize('fixed_effect', [False, True])
def test_fixed_cost_and_fixed_both_axes_use_only_stated_values(tmp_path: Path, fixed_effect: bool) -> None:
    case = json.loads((ROOT / 'model-inputs/p11/cases/base.json').read_text())
    case['iterations'] = 32
    case['overrides']['strategy.liaison_service.annual_incremental_cost_aud'] = {
        'family': 'fixed', 'params': {'value': 82000}, 'unit': 'AUD_per_year',
        'evidence_status': 'illustrative_assumption', 'source_ref': 'P4-ILLUSTRATIVE',
    }
    if fixed_effect:
        case['overrides']['strategy.liaison_service.delay_success_fraction'] = {
            'family': 'fixed', 'params': {'value': .5}, 'unit': 'proportion',
            'evidence_status': 'illustrative_assumption', 'source_ref': 'P4-ILLUSTRATIVE',
        }
    _, scenario = materialise(json.dumps(case).encode(), SCENARIO_FILE.read_bytes())
    rows = break_even_grid(scenario)
    assert {row['annual_cost_aud'] for row in rows} == {82000.0}
    assert len(rows) == (1 if fixed_effect else 17)
    if not fixed_effect:
        assert min(row['net_resource_aud'] for row in rows) < 0 < max(row['net_resource_aud'] for row in rows)
    scenario_file = tmp_path / 'scenario.json'
    scenario_file.write_text(scenario.model_dump_json())
    p5, out = tmp_path / 'p5', tmp_path / 'figures'
    build_report(scenario, p5)
    assert build_figures(scenario_file, p5, out)['investment_ready'] is False
    assert review_figures(scenario_file, p5, out)['figures_checked'][1] == 'F10'
    text = (out / 'f10.svg').read_text()
    assert ('Both assumptions fixed' if fixed_effect else 'Annual service cost fixed') in text
    if not fixed_effect:
        assert 'breakeven-zero' in text


def test_draw_order_must_match_the_seeded_model(tmp_path: Path, scenario: EconomicScenario) -> None:
    p5 = tmp_path / 'p5'
    build_report(scenario, p5)
    surface = p5 / 'decision-surface.csv'
    run = evaluate_scenarios(scenario)
    assert [row['draw_id'] for row in paired_capacity(run, surface)] == list(range(1, 33))
    lines = surface.read_text().splitlines()
    surface.write_text('\n'.join([lines[0], *reversed(lines[1:])]) + '\n')
    with pytest.raises(ValueError, match='draw order'):
        paired_capacity(run, surface)


def test_journey_conserves_elapsed_time_and_distinguishes_unknown(fixture_inputs: dict[str, Any]) -> None:
    rows = journey_rows(Fixtures.model_validate(fixture_inputs).journeys, P3_MANIFEST)
    assert [r['duration_minutes'] for r in rows if r['episode'] == 'A'] == [75, 585, 120]
    unresolved = [r for r in rows if r['stage'] == 'unresolved_stage']
    assert unresolved[0]['duration_minutes'] == 195
    missing = [r for r in rows if r['stage'] == 'readiness_unknown']
    assert missing[0]['start_minute'] is None
    assert missing[0]['duration_minutes'] is None
    fixture_inputs['journeys'][0]['ward_bed_minute'] = 60
    with pytest.raises(ValueError, match='journey order'):
        journey_rows(Fixtures.model_validate(fixture_inputs).journeys, P3_MANIFEST)


def test_coverage_conserves_hours_and_rejects_overlap_and_rates(fixture_inputs: dict[str, Any]) -> None:
    rows = coverage_rows(Fixtures.model_validate(fixture_inputs).week)
    assert len(rows) == 168
    assert sum(r['paid_staff_hours'] for r in rows) == 44
    assert sum(r['productive_staff_hours'] for r in rows) == 32
    assert sum(r['eligible_readiness_cases'] for r in rows) > 0
    shift = fixture_inputs['week']['shifts'][0]
    fixture_inputs['week']['shifts'].append(shift.copy())
    with pytest.raises(ValueError, match='overlap'):
        coverage_rows(Fixtures.model_validate(fixture_inputs).week)
    fixture_inputs['week']['shifts'].pop()
    shift['productive_end'] = 17
    with pytest.raises(ValueError, match='productive'):
        coverage_rows(Fixtures.model_validate(fixture_inputs).week)
    shift['award_cost_aud'] = 50
    with pytest.raises(ValueError, match='award_cost_aud'):
        Fixtures.model_validate(fixture_inputs)


def test_clinical_stress_grid_retains_null_and_harm(scenario: EconomicScenario) -> None:
    rows = sensitivity_grid(evaluate_scenarios(scenario))
    joint_null, = (row for row in rows if row['effect_class'] == 'joint_null')
    assert joint_null['mean_returns_avoided'] == 0
    assert joint_null['mean_bed_days'] == 0
    assert joint_null['mean_net_resource_aud'] < 0
    adverse = [row for row in rows if row['effect_class'] == 'more_returns']
    assert adverse and all(row['mean_returns_avoided'] < 0 for row in adverse)
    assert all(row['draws'] == scenario.iterations for row in rows)
    for row in rows:
        assert row['joint_null_aud'] == joint_null['mean_net_resource_aud']
        assert (row['joint_null_aud'] + row['delay_contrast_aud'] + row['return_contrast_aud']
                + row['interaction_aud']) == pytest.approx(row['mean_net_resource_aud'], abs=1e-7)
        # The current P4 resource kernel adds the two pathways independently.
        assert row['interaction_aud'] == pytest.approx(0, abs=1e-7)
        if row['delay_success'] == 0:
            assert row['delay_contrast_aud'] == 0
        if row['relative_return_reduction'] == 0:
            assert row['return_contrast_aud'] == 0


def test_bundle_detects_rehashed_mark_and_table_tampering(tmp_path: Path, scenario: EconomicScenario) -> None:
    p5, out = tmp_path / 'p5', tmp_path / 'p9'
    scenario_file = tmp_path / 'scenario.json'
    scenario_file.write_text(scenario.model_dump_json())
    build_report(scenario, p5)
    build_figures(scenario_file, p5, out)
    receipt = review_figures(scenario_file, p5, out)
    assert receipt['figures_checked'] == ['F02', 'F10', 'F11', 'F15', 'F20', 'F24']
    assert receipt['investment_ready'] is False
    manifest_file = out / 'manifest.json'
    manifest = json.loads(manifest_file.read_text())
    plot = out / 'f11.svg'
    original = plot.read_bytes()
    svg = ET.fromstring(original)
    group = next(node for node in svg.iter() if node.attrib.get('id') == 'paired-scatter')
    dots = [node for node in group.iter() if node.tag.endswith('}use')]
    assert len(dots) == scenario.iterations
    dots[1].set('y', dots[0].attrib['y'])
    plot.write_bytes(ET.tostring(svg))
    manifest['files_sha256'][plot.name] = hashlib.sha256(plot.read_bytes()).hexdigest()
    manifest_file.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='mark'):
        review_figures(scenario_file, p5, out)
    plot.write_bytes(original)
    manifest['files_sha256'][plot.name] = hashlib.sha256(original).hexdigest()
    table = out / 'f02.csv'
    with table.open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    rows[1]['value_aud'] = rows[0]['value_aud']
    with table.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    manifest['files_sha256'][table.name] = hashlib.sha256(table.read_bytes()).hexdigest()
    manifest_file.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='source rows'):
        review_figures(scenario_file, p5, out)


@pytest.mark.parametrize('mutation', ['missing_coverage', 'displaced_coverage',
                                       'invisible_coverage', 'off_canvas_demand',
                                       'missing_demand_cell'])
def test_f20_rejects_rehashed_geometry_or_missing_marks(tmp_path: Path, scenario: EconomicScenario, mutation: str) -> None:
    p5, out = tmp_path / 'p5', tmp_path / 'p9'
    scenario_file = tmp_path / 'scenario.json'
    scenario_file.write_text(scenario.model_dump_json())
    build_report(scenario, p5)
    build_figures(scenario_file, p5, out)
    plot = out / 'f20.svg'
    svg = ET.fromstring(plot.read_bytes())
    nodes = {node.get('id'): node for node in svg.iter() if node.get('id')}
    if mutation == 'missing_coverage':
        group = nodes['coverage-0-9']
        group.remove(next(child for child in group if child.tag.endswith('}path')))
    elif mutation == 'displaced_coverage':
        path = next(child for child in nodes['coverage-0-9'] if child.tag.endswith('}path'))
        path.set('d', re.sub(r'(?<=M )[-+0-9.]+', '0', path.attrib['d'], count=1))
    elif mutation == 'invisible_coverage':
        path = next(child for child in nodes['coverage-0-9'] if child.tag.endswith('}path'))
        path.set('style', path.attrib['style'].replace('fill: #196872', 'fill: none'))
    elif mutation == 'off_canvas_demand':
        label = next(child for child in nodes['demand-0-7'] if child.tag.endswith('}text'))
        label.set('x', '-1000')
    else:
        group = nodes['demand-cell-0-7']
        group.remove(next(child for child in group if child.tag.endswith('}path')))
    plot.write_bytes(ET.tostring(svg))
    manifest_file = out / 'manifest.json'
    manifest = json.loads(manifest_file.read_text())
    manifest['files_sha256'][plot.name] = hashlib.sha256(plot.read_bytes()).hexdigest()
    manifest_file.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='coverage|demand|mark'):
        review_figures(scenario_file, p5, out)
