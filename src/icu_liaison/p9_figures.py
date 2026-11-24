"""Generate and review the P9 companion bundle without altering a P5 report."""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
from html import escape
from importlib import metadata
import json
from pathlib import Path
import platform
import sys
from tempfile import TemporaryDirectory

from .local_data import DatasetManifest
from .p4_model import EconomicScenario, evaluate_scenarios
from .p5_reporting import review_report
from .p9_figure_data import (
    FIGURE_IDS, Fixtures, break_even_grid, coverage_rows, journey_rows, paired_capacity,
    resource_waterfall, sensitivity_grid,
)
from .qualification_independent import audit_p4_draws
from .p9_supplement_data import (
    DESIGN, DICTIONARY, SUPPLEMENT_IDS, TRACE, capacity_rows, economic_rows, event_rows, flow_rows,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACTS = ROOT / 'contracts/reporting'
DEFAULT_FIXTURE = ROOT / 'model-inputs/p9/illustrative.json'
DEFAULT_P3 = ROOT / 'model-inputs/placeholders/p3-synthetic/manifest.json'


@dataclass(frozen=True)
class SourceFigures:
    scenario: EconomicScenario
    model_input_sha256: str
    rows: dict[str, list[dict]]
    descriptions: dict[str, dict]
    figure_records: list[dict]
    inputs_sha256: dict[str, str]
    numerical_review: dict


def _hash(file: Path):
    if file.is_symlink() or not file.is_file():
        raise ValueError('figure input or artifact is missing or symlinked')
    return hashlib.sha256(file.read_bytes()).hexdigest()


def _load(file: Path):
    return json.loads(file.read_text(encoding='utf-8'))


def figure_contract_records(
    catalogue: dict, metrics: dict, *, price_year: int, supplementary_feeds: tuple[str, ...] | None,
) -> tuple[dict[str, dict], list[dict]]:
    """Build the figure manifest records from versioned reporting inputs."""
    include_supplement = supplementary_feeds is not None
    bundles = {'p9', 'p9_supplement'} if include_supplement else {'p9'}
    selected = [figure for figure in catalogue['figures'] if figure.get('bundle') in bundles]
    expected_ids = sorted((*FIGURE_IDS, *SUPPLEMENT_IDS)) if include_supplement else list(FIGURE_IDS)
    if [figure['id'] for figure in selected] != expected_ids:
        raise ValueError('P9 catalogue differs from the selected figure set')
    descriptions = {figure['id']: figure for figure in selected}
    denominators = {metric['id']: metric['denominator_id'] for metric in metrics['metrics']}
    shared = ['scenario', 'p9_catalogue', 'p10_metrics', 'p9_data_code', 'p9_renderer_code']
    additional = {
        'F02': ['p4_model_code', 'p5_model_summary'],
        'F10': ['p4_model_code'],
        'F11': ['p4_model_code', 'p5_manifest', 'p5_draws'],
        'F15': ['p3_manifest', 'p3_episodes', 'p9_fixture'],
        'F20': ['p9_fixture'],
        'F24': ['p4_model_code', 'p5_draws'],
        'F05': ['p4_model_code', 'p5_consequences'],
        'F06': ['p4_model_code', 'p5_draws', 'p5_comparisons'],
        'F07': ['p4_model_code', 'p5_sensitivity'],
        'F08': ['p4_model_code', 'p5_draws'],
        'F09': ['p6_trace', 'p6_capacity'],
        'F13': ['p3_manifest', 'p3_dictionary', 'local_data', 'protocol', 'endpoints',
                *(f'p3_{name}' for name in supplementary_feeds or ())],
        'F18': ['event_study'],
    }
    records = []
    for key, figure in descriptions.items():
        if (figure['artifact'] != f'{key.lower()}.svg' or figure['privacy'] != 'synthetic_only'
                or figure['evidence_tier'] != 'synthetic_implemented'):
            raise ValueError('unqualified P9 figure catalogue entry')
        if figure['y_unit'].startswith('AUD_') and figure['y_unit'] != f'AUD_{price_year}':
            raise ValueError('scenario price year differs from the reporting contract')
        records.append({
            'id': key, 'svg': figure['artifact'], 'csv': f'{key.lower()}.csv',
            'metric_ids': figure['metric_ids'],
            'denominator_ids': sorted({denominators[metric] for metric in figure['metric_ids']}),
            'sources': shared + additional[key] + (
                ['p9_supplement_data', 'p9_supplement_render', 'p9_supplement_review']
                if key in SUPPLEMENT_IDS else []),
        })
    return descriptions, records


def _source_figures(scenario_file: Path, p5: Path, include_supplement: bool) -> SourceFigures:
    if p5.is_symlink() or not p5.is_dir():
        raise ValueError('P5 report directory is missing or symlinked')
    catalogue_file = DEFAULT_CONTRACTS / 'catalogue.json'
    metrics_file = DEFAULT_CONTRACTS / 'metrics.json'
    feeds = DatasetManifest.model_validate_json(DEFAULT_P3.read_bytes()).files
    feed = feeds['episodes']
    episodes = (DEFAULT_P3.parent / feed.path)
    if not episodes.resolve().is_relative_to(DEFAULT_P3.parent.resolve()):
        raise ValueError('P3 feed path escapes the synthetic fixture directory')
    input_files = {
        'scenario': scenario_file, 'p5_manifest': p5 / 'manifest.json',
        'p5_model_summary': p5 / 'model-summary.json', 'p5_draws': p5 / 'decision-surface.csv',
        'p9_fixture': DEFAULT_FIXTURE, 'p3_manifest': DEFAULT_P3,
        'p3_episodes': episodes, 'p9_catalogue': catalogue_file,
        'p10_metrics': metrics_file, 'p4_model_code': Path(__file__).with_name('p4_model.py'),
        'p9_bundle_code': Path(__file__),
        'p9_data_code': Path(__file__).with_name('p9_figure_data.py'),
        'p9_renderer_code': Path(__file__).with_name('p9_figure_render.py'),
        'p9_mark_review_code': Path(__file__).with_name('p9_figure_review.py'),
    }
    if include_supplement:
        for key, spec in feeds.items():
            path = DEFAULT_P3.parent / spec.path
            if not path.resolve().is_relative_to(DEFAULT_P3.parent.resolve()) or path.is_symlink():
                raise ValueError('P3 figure source escapes the fixture directory')
            input_files[f'p3_{key}'] = path
        input_files.update(p6_trace=TRACE, event_study=DESIGN, p3_dictionary=DICTIONARY,
                          p5_consequences=p5 / 'cost-consequence.csv',
                          p5_comparisons=p5 / 'paired-comparisons.csv',
                          p5_sensitivity=p5 / 'one-way-sensitivity.csv')
        for module in ('p9_supplement_data', 'p9_supplement_render', 'p9_supplement_review',
                       'p6_capacity', 'local_data', 'endpoints', 'protocol'):
            input_files[module] = Path(__file__).with_name(f'{module}.py')
    inputs = {key: _hash(file) for key, file in input_files.items()}
    numeric = review_report(p5)
    manifest = _load(p5 / 'manifest.json')
    if (numeric['provider_qualification'] is not False
            or manifest.get('installed_provider_qualification') is not False):
        raise ValueError('P9 requires an illustrative P5 report')
    scenario = EconomicScenario.model_validate_json(scenario_file.read_bytes())
    run = evaluate_scenarios(scenario)
    if (manifest['source_model_input_digest_sha256'] != run.input_digest_sha256
            or manifest['scenario_id'] != scenario.scenario_id):
        raise ValueError('P5 report and scenario do not match')
    audit = audit_p4_draws(run)
    fixture = Fixtures.model_validate_json(DEFAULT_FIXTURE.read_bytes())
    descriptions, records = figure_contract_records(
        _load(catalogue_file), _load(metrics_file), price_year=scenario.price_year,
        supplementary_feeds=tuple(feeds) if include_supplement else None,
    )
    rows = {
        'F02': resource_waterfall(scenario),
        'F10': break_even_grid(scenario),
        'F11': paired_capacity(run, p5 / 'decision-surface.csv'),
        'F15': journey_rows(fixture.journeys, DEFAULT_P3),
        'F20': coverage_rows(fixture.week),
        'F24': sensitivity_grid(run),
    }
    if include_supplement:
        rows.update(economic_rows(run, p5, rows['F11']))
        rows.update(F09=capacity_rows(TRACE), F13=flow_rows(DEFAULT_P3), F18=event_rows(DESIGN))
    if any(_hash(input_files[key]) != digest for key, digest in inputs.items()):
        raise ValueError('figure input changed during source reconciliation')
    return SourceFigures(scenario, run.input_digest_sha256, rows, descriptions, records, inputs, {
        'p5_draws_reconciled': numeric['draws_checked'],
        'independent_p4_sample_checks': audit['draws_checked'],
    })


def _table(file: Path, rows: list[dict]) -> None:
    with file.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def _check_table(file: Path, rows: list[dict]) -> None:
    with file.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(rows[0]):
            raise ValueError('figure source rows have a different header')
        expected = [{key: str(value) if value is not None else '' for key, value in row.items()} for row in rows]
        if list(reader) != expected:
            raise ValueError('figure source rows differ from independently regenerated values')


def _index(sources: SourceFigures) -> str:
    items = []
    links = []
    for record in sources.figure_records:
        key = record['id']
        meta = sources.descriptions[key]
        title = escape(meta['title'])
        links.append(f'<li><a href="#{key}">{title}</a></li>')
        items.append(f"""<section aria-labelledby="{key}">
<h2 id="{key}">{title}</h2>
<p>{escape(meta['decision_question'])}</p>
<figure><a href="{record['svg']}">
<img src="{record['svg']}" alt="{escape(meta['alt_text'], quote=True)}">
<span>Open full-size figure (SVG)</span></a></figure>
<p class="links"><a href="{record['csv']}">Source values (CSV)</a></p>
</section>""")
    return f"""<!doctype html>
<html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ICU liaison synthetic figures</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: #eef3f5; color: #172b3b; font: 1rem/1.55 system-ui, sans-serif; }}
  main {{ width: min(100% - 2rem, 49rem); margin: auto; }}
  h1 {{ line-height: 1.15; margin: 1.8rem 0 1rem; font-size: clamp(1.7rem, 4vw, 2.5rem); }}
  h2 {{ line-height: 1.2; margin: 0 0 .5rem; font-size: 1.35rem; }}
  a {{ color: #125162; text-underline-offset: .14em; }}
  a:focus-visible {{ outline: .15rem solid #9c4128; }}
  nav ol {{ padding-left: 1.4rem; }}
  section {{ background: white; padding: clamp(.65rem, 2.5vw, 1.25rem); margin: 1.1rem 0; }}
  figure {{ margin: .5rem auto; max-width: 35rem; }}
  figure a {{ display: block; }}
  img {{ display: block; width: 100%; height: auto; }}
  .links {{ display: flex; flex-wrap: wrap; gap: .2rem 1.3rem; margin-bottom: 0; }}
  @page {{ size: A4; margin: 14mm; }}
  @media print {{
    body {{ background: white; }}
    main {{ width: 100%; }}
    section {{ break-before: page; break-inside: avoid; }}
    figure img {{ max-height: 205mm; object-fit: contain; filter: grayscale(1); }}
    figure a span {{ display: none; }}
  }}
</style>
<main>
<h1>ICU liaison synthetic figures</h1>
<p>Fictional economic scenarios, discharge journeys and nursing coverage.
Clinical safety and suitability for local investment remain unverified.</p>
<p>Economic scenario seed {sources.scenario.seed} · {sources.scenario.iterations:,} paired draws
· AUD {sources.scenario.price_year} · <a href="manifest.json">Source and artifact hashes</a></p>
<nav aria-label="Figures"><ol>{''.join(links)}</ol></nav>
{''.join(items)}
</main></html>
"""


def _manifest(sources: SourceFigures, files: dict[str, str]) -> dict:
    return {
        'schema_version': 1, 'data_class': 'synthetic', 'investment_ready': False,
        'scenario_id': sources.scenario.scenario_id, 'scenario_seed': sources.scenario.seed,
        'model_input_sha256': sources.model_input_sha256,
        'draws': sources.scenario.iterations, 'price_year': sources.scenario.price_year,
        'python': platform.python_version(),
        'versions': {name: metadata.version(name) for name in ('matplotlib', 'numpy', 'scipy')},
        'inputs_sha256': sources.inputs_sha256,
        'figures': sources.figure_records,
        'files_sha256': files,
    }


def _review(folder: Path, sources: SourceFigures) -> dict:
    from .p9_figure_review import review_svg

    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('figure bundle directory is missing or symlinked')
    manifest_file = folder / 'manifest.json'
    _hash(manifest_file)
    manifest = _load(manifest_file)
    expected = {'index.html'} | {record[key] for record in sources.figure_records for key in ('csv', 'svg')}
    if {file.name for file in folder.iterdir()} != expected | {'manifest.json'}:
        raise ValueError('figure bundle file inventory differs from the catalogue')
    hashes = {name: _hash(folder / name) for name in sorted(expected)}
    if manifest != _manifest(sources, hashes):
        raise ValueError('figure bundle provenance differs from the current source, runtime or artifacts')
    if (folder / 'index.html').read_text(encoding='utf-8') != _index(sources):
        raise ValueError('figure index differs from the source catalogue')
    for record in sources.figure_records:
        key = record['id']
        _check_table(folder / record['csv'], sources.rows[key])
        review_svg(folder / record['svg'], sources.descriptions[key], sources.rows[key])
    return {
        'status': 'synthetic_source_and_marks_verified',
        'figures_checked': list(sources.descriptions), 'investment_ready': False,
        'manifest_sha256': _hash(manifest_file),
        'source_rows_checked': {key: len(sources.rows[key]) for key in sources.descriptions},
        **sources.numerical_review,
    }


def build_figures(scenario: Path, p5: Path, destination: Path, *, include_supplement=False) -> dict:
    from .p9_figure_render import render_svg

    if destination.exists() or destination.is_symlink():
        raise FileExistsError('refuse to overwrite a synthetic figure bundle')
    if destination.resolve().is_relative_to(p5.resolve()):
        raise ValueError('figure bundle must be outside the immutable P5 report')
    sources = _source_figures(scenario, p5, include_supplement)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='.p9-figures-', dir=destination.parent) as tmp:
        staging = Path(tmp) / 'figures'
        staging.mkdir()
        for record in sources.figure_records:
            key = record['id']
            _table(staging / record['csv'], sources.rows[key])
            render_svg(staging / record['svg'], sources.descriptions[key], sources.rows[key],
                       sources.scenario.price_year, sources.scenario.annual_eligible_discharges)
        (staging / 'index.html').write_text(_index(sources), encoding='utf-8')
        files = {file.name: _hash(file) for file in sorted(staging.iterdir())}
        (staging / 'manifest.json').write_text(
            json.dumps(_manifest(sources, files), indent=2, sort_keys=True, allow_nan=False) + '\n',
            encoding='utf-8',
        )
        receipt = _review(staging, sources)
        if destination.exists() or destination.is_symlink():
            raise FileExistsError('figure bundle appeared during generation')
        staging.rename(destination)
    return receipt


def review_figures(scenario: Path, p5: Path, folder: Path, *, include_supplement=False) -> dict:
    sources = _source_figures(scenario, p5, include_supplement)
    receipt = _review(folder, sources)
    if include_supplement:
        # Independent coordinates cover the data. Replay also covers labels,
        # transforms, clipping and presentation changes on the recorded runtime.
        from .p9_figure_render import render_svg
        with TemporaryDirectory() as tmp:
            for key in SUPPLEMENT_IDS:
                filename = sources.descriptions[key]['artifact']
                replay = Path(tmp) / filename
                render_svg(replay, sources.descriptions[key], sources.rows[key], sources.scenario.price_year,
                           sources.scenario.annual_eligible_discharges)
                if _hash(replay) != _hash(folder / filename):
                    raise ValueError(f'{key} rendering differs from its source replay')
    return receipt


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('scenario', type=Path)
    cli.add_argument('--p5-report', type=Path, required=True)
    cli.add_argument('--include-supplement', action='store_true', help='Include all seven supplementary figures')
    mode = cli.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output-dir', type=Path)
    mode.add_argument('--review', type=Path)
    args = cli.parse_args()
    try:
        if args.output_dir:
            receipt = build_figures(args.scenario, args.p5_report, args.output_dir, include_supplement=args.include_supplement)
        else:
            receipt = review_figures(args.scenario, args.p5_report, args.review, include_supplement=args.include_supplement)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f'P9 INVALID_OR_UNVERIFIED: {type(exc).__name__}', file=sys.stderr)
        return 2
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
