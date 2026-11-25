"""Render a versioned F01 companion from an existing synthetic P5 report."""
from __future__ import annotations
from typing import Any

import argparse
from datetime import datetime, timezone
import errno
from importlib import metadata
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from xml.etree import ElementTree

from .f01_review import review_f01
from .p11_model import verify_case
from .p11_records import atomic_json, digest_bytes, digest_file, digest_json, inventory, read_json, valid_digest
from .p5_reporting import _plot

DESCRIPTION = (
    'Synthetic net resource benefit by strategy with fifth to ninety-fifth percentile ranges, '
    'not CHHHS outcomes'
)


def verify_figure(folder: Path, *, model: Path | None = None) -> dict[str, Any]:
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('synthetic figure directory is missing or unsafe')
    record = read_json(folder / 'figure.json')
    if (record.get('schema_version') != 1 or record.get('data_class') != 'synthetic'
            or record.get('investment_ready') is not False
            or not valid_digest(record.get('figure_revision'))
            or folder.name != record['figure_revision']
            or digest_json(record['identity']) != record['figure_revision']):
        raise ValueError('synthetic figure identity or readiness mismatch')
    if record.get('clinical_safety_approved') is not False:
        raise ValueError('F01 clinical safety cannot be approved by a synthetic figure record')
    if record.get('files_sha256') != inventory(folder, exclude='figure.json'):
        raise ValueError('synthetic figure file inventory or digest mismatch')
    try:
        svg = ElementTree.parse(folder / 'scenario-comparison.svg').getroot()
    except ElementTree.ParseError as exc:
        raise ValueError('malformed F01 SVG') from exc
    desc = svg.find('.//{http://purl.org/dc/elements/1.1/}description')
    if desc is None or desc.text != DESCRIPTION:
        raise ValueError('synthetic figure description differs from P5 contract')
    if digest_file(folder / 'style.json') != record['identity']['style_sha256']:
        raise ValueError('synthetic figure style snapshot changed')
    model_id = record['identity'].get('model_run_id')
    if not valid_digest(model_id) or model_id != record.get('model_run_id'):
        raise ValueError('invalid F01 model identity')
    model = model or folder.parent.parent / 'models' / model_id
    summary = model / 'p5-report/model-summary.json'
    if (model.name != model_id or digest_file(model / 'run.json') != record['identity']['run_record_sha256']
            or digest_file(summary) != read_json(model / 'run.json')['files_sha256']['p5-report/model-summary.json']):
        raise ValueError('F01 model source linkage mismatch')
    review_f01(folder / 'scenario-comparison.svg', read_json(summary))
    return record


def build_figure(model_pointer: Path, style_file: Path, output: Path, pointer: Path) -> dict[str, Any]:
    import matplotlib
    from cycler import cycler

    model_pointer, style_file, output, pointer = map(Path, (model_pointer, style_file, output, pointer))
    model_link = read_json(model_pointer)
    model_id = model_link.get('model_run_id')
    if (not valid_digest(model_id) or model_link.get('data_class') != 'synthetic'
            or model_link.get('investment_ready') is not False):
        raise ValueError('invalid synthetic model pointer')
    model = output / 'models' / model_id
    run = verify_case(model)
    if (model_link.get('run_record_sha256') != digest_file(model / 'run.json')
            or model_link.get('case_id') != run['case_id']):
        raise ValueError('figure model pointer differs from its source run')
    style_bytes = style_file.read_bytes() if not style_file.is_symlink() else None
    if style_bytes is None:
        raise ValueError('unsafe synthetic figure style')
    style = json.loads(style_bytes)
    if (set(style) != {'schema_version', 'font_size', 'bar_color'}
            or style['schema_version'] != 1 or type(style['font_size']) not in (int, float)
            or not 6 <= style['font_size'] <= 20 or not isinstance(style['bar_color'], str)
            or not re.fullmatch(r'#[0-9a-fA-F]{6}', style['bar_color'])):
        raise ValueError('invalid synthetic F01 presentation')
    identity = {
        'schema_version': 1, 'model_run_id': model_id,
        'run_record_sha256': model_link['run_record_sha256'],
        'style_sha256': digest_bytes(style_bytes),
        'renderer_sha256': {
            Path(__file__).name: digest_file(Path(__file__)),
            'p5_reporting.py': digest_file(Path(__file__).with_name('p5_reporting.py')),
            'p11_records.py': digest_file(Path(__file__).with_name('p11_records.py')),
            'f01_review.py': digest_file(Path(__file__).with_name('f01_review.py')),
        },
        'matplotlib': metadata.version('matplotlib'),
    }
    revision = digest_json(identity)
    parent = output / 'figures'
    parent.mkdir(parents=True, exist_ok=True)
    target = parent / revision
    if not target.exists():
        with tempfile.TemporaryDirectory(prefix='.p11-stage-', dir=parent) as temp:
            staging = Path(temp) / revision
            staging.mkdir()
            (staging / 'style.json').write_bytes(style_bytes)
            model_summary = read_json(model / 'p5-report/model-summary.json')
            with matplotlib.rc_context({'font.size': style['font_size'],
                                        'axes.prop_cycle': cycler(color=[style['bar_color']])}):
                _plot(staging / 'scenario-comparison.svg', model_summary)
            record = {
                'schema_version': 1, 'data_class': 'synthetic',
                'figure_revision': revision, 'identity': identity, 'case_id': run['case_id'],
                'model_run_id': model_id, 'created_at_utc': datetime.now(timezone.utc).isoformat(),
                'source_check': 'P5_report_reconciled_and_P4_replayed_when_source_matches',
                'clinical_safety_approved': False, 'investment_ready': False,
                'files_sha256': inventory(staging, exclude='figure.json'),
            }
            (staging / 'figure.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
            verify_figure(staging, model=model)
            try:
                os.rename(staging, target)
            except OSError as exc:
                if exc.errno not in (errno.EEXIST, errno.ENOTEMPTY) or not target.is_dir():
                    raise
    verify_figure(target)
    result = {
        'schema_version': 1, 'data_class': 'synthetic', 'case_id': run['case_id'],
        'model_run_id': model_id, 'figure_revision': revision,
        'figure_record_sha256': digest_file(target / 'figure.json'),
        'investment_ready': False,
    }
    atomic_json(pointer, result)
    return result


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--model-pointer', type=Path, required=True)
    cli.add_argument('--style', type=Path, required=True)
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--pointer', type=Path, required=True)
    args = cli.parse_args()
    try:
        result = build_figure(args.model_pointer, args.style, args.output, args.pointer)
    except (OSError, RuntimeError, TypeError, ValueError, KeyError, ElementTree.ParseError) as exc:
        print(f'P11 INVALID_OR_UNVERIFIED: {type(exc).__name__}', file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
