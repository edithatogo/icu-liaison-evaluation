"""Publish six reviewed P9 figures for each synthetic P11 model run."""
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
from .p9_figures import FIGURE_IDS, build_figures, review_figures

ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATHS = tuple(dict.fromkeys((*MODEL_SOURCES,
    'src/icu_liaison/p11_p9.py', 'src/icu_liaison/p11_records.py',
    'src/icu_liaison/p9_figures.py', 'src/icu_liaison/p9_figure_data.py',
    'src/icu_liaison/p9_figure_render.py', 'src/icu_liaison/p9_figure_review.py',
    'src/icu_liaison/local_data.py', 'src/icu_liaison/endpoints.py',
    'src/icu_liaison/p4_model.py', 'src/icu_liaison/qualification_independent.py',
)))


def source_hashes() -> dict[str, str]:
    return {path: digest_file(ROOT / path) for path in SOURCE_PATHS}


def input_files() -> dict[str, Path]:
    p3 = ROOT / 'model-inputs/placeholders/p3-synthetic/manifest.json'
    relative = read_json(p3)['files']['episodes']['path']
    episode_file = p3.parent / relative
    if (Path(relative).is_absolute() or not episode_file.resolve().is_relative_to(p3.parent.resolve())
            or episode_file.is_symlink()):
        raise ValueError('P9 synthetic episode feed escapes its fixture')
    return {
        'p9_fixture.json': ROOT / 'model-inputs/p9/illustrative.json',
        'p3_manifest.json': p3,
        'p3_episodes.csv': episode_file,
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


def verify_p9(folder: Path, model: Path) -> dict:
    folder, model = Path(folder), Path(model)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('P9 figure revision is missing or unsafe')
    record = read_json(folder / 'figure-set.json')
    identity = record['identity']
    revision = record.get('figure_revision')
    if (record.get('schema_version') != 1 or record.get('data_class') != 'synthetic'
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
    if (set(identity['inputs_sha256']) != set(input_files())
            or set(identity['sources_sha256']) != set(SOURCE_PATHS)):
        raise ValueError('P9 source or input snapshot inventory mismatch')
    for name, expected in identity['inputs_sha256'].items():
        if digest_file(folder / 'inputs' / name) != expected:
            raise ValueError('P9 input snapshot digest mismatch')
    bundle = folder / 'bundle'
    manifest = read_json(bundle / 'manifest.json')
    review = read_json(folder / 'review.json')
    if (review.get('status') != 'synthetic_source_and_marks_verified'
            or review.get('investment_ready') is not False
            or review.get('figures_checked') != list(FIGURE_IDS)
            or review.get('manifest_sha256') != digest_file(bundle / 'manifest.json')
            or manifest.get('data_class') != 'synthetic'
            or manifest.get('investment_ready') is not False
            or [item['id'] for item in manifest['figures']] != list(FIGURE_IDS)):
        raise ValueError('P9 figure bundle review or catalogue mismatch')
    recorded = {key: identity[key] for key in ('sources_sha256', 'inputs_sha256', 'runtime')}
    if recorded == fingerprint():
        replay = review_figures(model / 'inputs/effective-scenario.json', model / 'p5-report', bundle)
        if replay != review:
            raise ValueError('P9 numerical and visual-mark review differs from replay')
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
    identity = {'schema_version': 1, 'case_id': run['case_id'], 'model_run_id': model_id,
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
                                   model / 'p5-report', staging / 'bundle')
            if fingerprint() != before:
                raise ValueError('P9 source or input changed during figure production')
            (staging / 'review.json').write_text(json.dumps(review, indent=2, sort_keys=True) + '\n')
            record = {'schema_version': 1, 'data_class': 'synthetic', 'figure_revision': revision,
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
