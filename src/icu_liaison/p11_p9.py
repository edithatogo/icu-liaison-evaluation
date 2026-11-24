"""Publish and verify the P9 figures for each synthetic P11 model run."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import errno
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import sys
import tempfile

from .p11_model import MODEL_SOURCES, verify_case
from .p11_records import atomic_json, digest_file, digest_json, inventory, read_json, valid_digest
from .p9_figures import build_figures, figure_contract_records, review_figures

ROOT = Path(__file__).resolve().parents[2]
LEGACY_SOURCE_PATHS = tuple(dict.fromkeys((*MODEL_SOURCES,
    'src/icu_liaison/p11_p9.py', 'src/icu_liaison/p11_records.py',
    'src/icu_liaison/p9_figures.py', 'src/icu_liaison/p9_figure_data.py',
    'src/icu_liaison/p9_figure_render.py', 'src/icu_liaison/p9_figure_review.py',
    'src/icu_liaison/local_data.py', 'src/icu_liaison/endpoints.py',
    'src/icu_liaison/p4_model.py', 'src/icu_liaison/qualification_independent.py',
)))
SOURCE_PATHS = (*LEGACY_SOURCE_PATHS, 'src/icu_liaison/p9_supplement_data.py',
                'src/icu_liaison/p9_supplement_render.py', 'src/icu_liaison/p9_supplement_review.py',
                'src/icu_liaison/p6_capacity.py')
LEGACY_INPUTS = {'p9_fixture.json', 'p3_manifest.json', 'p3_episodes.csv', 'catalogue.json', 'metrics.json'}


def source_hashes() -> dict[str, str]:
    return {path: digest_file(ROOT / path) for path in SOURCE_PATHS}


def input_files() -> dict[str, Path]:
    p3 = ROOT / 'model-inputs/placeholders/p3-synthetic/manifest.json'
    feeds = {}
    for key, spec in read_json(p3)['files'].items():
        relative = Path(spec['path'])
        path = p3.parent / relative
        if relative.is_absolute() or not path.resolve().is_relative_to(p3.parent.resolve()) or path.is_symlink():
            raise ValueError('P9 synthetic feed escapes its fixture')
        feeds[f'p3_{key}.csv'] = path
    return {
        'p9_fixture.json': ROOT / 'model-inputs/p9/illustrative.json',
        'p3_manifest.json': p3,
        **feeds,
        'p3_dictionary.json': ROOT / 'model-inputs/clinical-data-dictionary.json',
        'p6_trace.json': ROOT / 'model-inputs/p6/synthetic-trace.json',
        'event_study.json': ROOT / 'model-inputs/p9/event-study.json',
        'catalogue.json': ROOT / 'contracts/reporting/catalogue.json',
        'metrics.json': ROOT / 'contracts/reporting/metrics.json',
    }


def runtime() -> dict:
    return {'python': platform.python_version(), 'system': platform.system(),
            'machine': platform.machine(), 'versions': {
                name: metadata.version(name)
                for name in ('matplotlib', 'numpy', 'scipy', 'pydantic', 'pydantic-core')
            }}


def fingerprint() -> dict:
    return {'sources_sha256': source_hashes(),
            'inputs_sha256': {name: digest_file(path) for name, path in input_files().items()},
            'runtime': runtime()}


def _bundle_inputs(identity: dict, run: dict) -> dict:
    """Reconstruct the inner manifest's source hashes from the frozen outer records."""
    names = {'catalogue': 'p9_catalogue', 'metrics': 'p10_metrics'}
    expected = {names.get(Path(name).stem, Path(name).stem): digest
                for name, digest in identity['inputs_sha256'].items()}
    model_files = {'scenario': 'inputs/effective-scenario.json', 'p5_manifest': 'p5-report/manifest.json',
                   'p5_model_summary': 'p5-report/model-summary.json', 'p5_draws': 'p5-report/decision-surface.csv'}
    modules = {'p4_model_code': 'p4_model', 'p9_bundle_code': 'p9_figures', 'p9_data_code': 'p9_figure_data',
               'p9_renderer_code': 'p9_figure_render', 'p9_mark_review_code': 'p9_figure_review'}
    if identity['schema_version'] == 2:
        model_files.update(p5_consequences='p5-report/cost-consequence.csv',
                           p5_comparisons='p5-report/paired-comparisons.csv',
                           p5_sensitivity='p5-report/one-way-sensitivity.csv')
        for name in ('p9_supplement_data', 'p9_supplement_render', 'p9_supplement_review',
                     'p6_capacity', 'local_data', 'endpoints', 'protocol'):
            modules[name] = name
    expected.update({key: run['files_sha256'][name] for key, name in model_files.items()})
    expected.update({key: identity['sources_sha256'][f'src/icu_liaison/{module}.py']
                     for key, module in modules.items()})
    return expected


def verify_p9(folder: Path, model: Path) -> dict:
    folder, model = Path(folder), Path(model)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('P9 figure revision is missing or unsafe')
    record = read_json(folder / 'figure-set.json')
    identity = record['identity']
    revision = record.get('figure_revision')
    edition = record.get('schema_version')
    if (edition not in (1, 2) or identity.get('schema_version') != edition or record.get('data_class') != 'synthetic'
            or record.get('investment_ready') is not False
            or record.get('clinical_safety_approved') is not False
            or not valid_digest(revision) or folder.name != revision
            or digest_json(identity) != revision):
        raise ValueError('P9 figure revision identity or readiness mismatch')
    if record.get('files_sha256') != inventory(folder, exclude='figure-set.json'):
        raise ValueError('P9 figure revision file inventory or digest mismatch')
    run = verify_case(model)
    if (identity['case_id'] != run['case_id']
            or identity['model_run_id'] != run['model_run_id']
            or identity['run_record_sha256'] != digest_file(model / 'run.json')):
        raise ValueError('P9 figure revision does not match its scenario model')
    if (set(identity['inputs_sha256']) != (LEGACY_INPUTS if edition == 1 else set(input_files()))
            or set(identity['sources_sha256']) != set(LEGACY_SOURCE_PATHS if edition == 1 else SOURCE_PATHS)):
        raise ValueError('P9 source or input snapshot inventory mismatch')
    for name, expected in identity['inputs_sha256'].items():
        if digest_file(folder / 'inputs' / name) != expected:
            raise ValueError('P9 input snapshot digest mismatch')
    bundle = folder / 'bundle'
    manifest = read_json(bundle / 'manifest.json')
    review = read_json(folder / 'review.json')
    model_summary = read_json(model / 'p5-report/model-summary.json')
    recorded_runtime = identity['runtime']
    expected_metadata = {
        'schema_version': 1, 'data_class': 'synthetic',
        'scenario_id': model_summary['scenario_id'], 'scenario_seed': run['seed'],
        'draws': run['draws'], 'price_year': model_summary['price_year'],
        'model_input_sha256': model_summary['input_digest_sha256'],
        'python': recorded_runtime['python'],
        'versions': {name: recorded_runtime['versions'][name] for name in ('matplotlib', 'numpy', 'scipy')},
    }
    if (manifest.get('investment_ready') is not False
            or any(manifest.get(key) != value for key, value in expected_metadata.items())):
        raise ValueError('P9 figure manifest disagrees with its source run or recorded runtime')
    inputs = folder / 'inputs'
    feeds = tuple(read_json(inputs / 'p3_manifest.json')['files']) if edition == 2 else None
    descriptions, expected_figures = figure_contract_records(
        read_json(inputs / 'catalogue.json'), read_json(inputs / 'metrics.json'),
        price_year=model_summary['price_year'], supplementary_feeds=feeds,
    )
    if manifest.get('figures') != expected_figures:
        raise ValueError('P9 figure manifest differs from its frozen catalogue, denominators or source links')
    expected_files = {'index.html'} | {
        item[kind] for item in expected_figures for kind in ('svg', 'csv')
    }
    inner_files = inventory(bundle, exclude='manifest.json')
    if (set(inner_files) != expected_files or manifest.get('files_sha256') != inner_files
            or manifest.get('inputs_sha256') != _bundle_inputs(identity, run)):
        raise ValueError('P9 inner manifest disagrees with its frozen inputs or figure files')
    if (review.get('status') != 'synthetic_source_and_marks_verified'
            or review.get('investment_ready') is not False
            or review.get('figures_checked') != list(descriptions)
            or review.get('manifest_sha256') != digest_file(bundle / 'manifest.json')):
        raise ValueError('P9 figure bundle review mismatch')
    recorded = {key: identity[key] for key in ('sources_sha256', 'inputs_sha256', 'runtime')}
    if recorded == fingerprint():
        replay = review_figures(model / 'inputs/effective-scenario.json', model / 'p5-report', bundle,
                                include_supplement=edition == 2)
        if replay != review:
            raise ValueError('P9 numerical and visual-mark review differs from replay')
    else:
        from .p9_figure_review import read_accessible_svg

        for figure in expected_figures:
            read_accessible_svg(bundle / figure['svg'], descriptions[figure['id']])
    return record


def build_p9(model_pointer: Path, output: Path, pointer: Path) -> dict:
    output = Path(output)
    link = read_json(model_pointer)
    model_id = link.get('model_run_id')
    if (link.get('data_class') != 'synthetic'
            or link.get('investment_ready') is not False or not valid_digest(model_id)):
        raise ValueError('invalid P9 scenario model pointer')
    model = output / 'models' / model_id
    run = verify_case(model)
    if (link.get('case_id') != run['case_id']
            or link.get('run_record_sha256') != digest_file(model / 'run.json')):
        raise ValueError('P9 model pointer differs from its scenario source')
    before = fingerprint()
    identity = {'schema_version': 2, 'case_id': run['case_id'], 'model_run_id': model_id,
                'run_record_sha256': link['run_record_sha256'], **before}
    revision = digest_json(identity)
    parent = output / 'priority-figures'
    parent.mkdir(parents=True, exist_ok=True)
    target = parent / revision
    if not target.exists():
        with tempfile.TemporaryDirectory(prefix='.p11-stage-', dir=parent) as temp:
            staging = Path(temp) / revision
            inputs = staging / 'inputs'
            inputs.mkdir(parents=True)
            for name, path in input_files().items():
                (inputs / name).write_bytes(path.read_bytes())
            review = build_figures(model / 'inputs/effective-scenario.json',
                                   model / 'p5-report', staging / 'bundle', include_supplement=True)
            if fingerprint() != before:
                raise ValueError('P9 source or input changed during figure production')
            (staging / 'review.json').write_text(json.dumps(review, indent=2, sort_keys=True) + '\n')
            record = {'schema_version': 2, 'data_class': 'synthetic', 'figure_revision': revision,
                      'identity': identity, 'created_at_utc': datetime.now(timezone.utc).isoformat(),
                      'clinical_safety_approved': False, 'investment_ready': False,
                      'files_sha256': inventory(staging, exclude='figure-set.json')}
            (staging / 'figure-set.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
            verify_p9(staging, model)
            try:
                os.rename(staging, target)
            except OSError as exc:
                if exc.errno not in (errno.EEXIST, errno.ENOTEMPTY) or not target.is_dir():
                    raise
    verify_p9(target, model)
    receipt = {'schema_version': 1, 'data_class': 'synthetic', 'case_id': run['case_id'],
               'model_run_id': model_id, 'figure_revision': revision,
               'figure_record_sha256': digest_file(target / 'figure-set.json'),
               'investment_ready': False}
    atomic_json(pointer, receipt)
    return receipt


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--model-pointer', type=Path, required=True)
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--pointer', type=Path, required=True)
    args = cli.parse_args()
    try:
        result = build_p9(args.model_pointer, args.output, args.pointer)
    except (OSError, RuntimeError, TypeError, ValueError, KeyError) as exc:
        print(f'P11 INVALID_OR_UNVERIFIED: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
