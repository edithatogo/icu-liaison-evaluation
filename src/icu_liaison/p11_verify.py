"""Verify the current P11 pointers, immutable objects and paired summary."""
from __future__ import annotations
from typing import Any

import argparse
import csv
import json
from pathlib import Path
import sys

from .p11_figure import verify_figure
from .p11_model import verify_case
from .p11_p9 import verify_p9
from .p9_supplement_data import SUPPLEMENT_IDS
from .p11_records import digest_file, read_json, valid_digest
from .p11_summary import validate_suite, verify_summary


def _figure_lineage(output: Path, model: Path, f01_folder: Path, f01: dict[str, Any],
                    p9_folder: Path, p9: dict[str, Any]) -> dict[str, Any]:
    """Describe the inputs, marks and reviews of already-verified artifacts."""
    bundle = p9_folder / 'bundle'
    manifest = read_json(bundle / 'manifest.json')
    catalogue = read_json(p9_folder / 'inputs/catalogue.json')
    metrics = read_json(p9_folder / 'inputs/metrics.json')
    by_id = {entry['id']: entry for entry in catalogue['figures']}
    denominators = {entry['id']: entry['denominator_id'] for entry in metrics['metrics']}
    run = read_json(model / 'run.json')

    def file_ref(path: Path, sha256: str) -> dict[str, Any]:
        return {'path': path.relative_to(output).as_posix(), 'sha256': sha256}

    f01_source = 'p5-report/model-summary.json'
    f01_svg = 'scenario-comparison.svg'
    f01_metrics = by_id['F01']['metric_ids']
    figures = [{
        'id': 'F01',
        'figure_revision': f01['figure_revision'],
        'metric_ids': f01_metrics,
        'denominator_ids': sorted({denominators[key] for key in f01_metrics}),
        'source_table_id': by_id['F01']['source_table'],
        'inputs_sha256': {
            'effective_scenario': run['files_sha256']['inputs/effective-scenario.json'],
            'figure_style': f01['identity']['style_sha256'],
            **f01['identity']['renderer_sha256'],
        },
        'table': file_ref(model / f01_source, run['files_sha256'][f01_source]),
        'figure': file_ref(f01_folder / f01_svg, f01['files_sha256'][f01_svg]),
        'review': {
            'scope': 'svg_marks_rechecked_against_model_summary',
            'verifier_sha256': digest_file(Path(__file__).with_name('f01_review.py')),
        },
    }]
    for record in manifest['figures']:
        csv_name, svg_name = record['csv'], record['svg']
        figures.append({
            'id': record['id'],
            'figure_revision': p9['figure_revision'],
            'metric_ids': record['metric_ids'],
            'denominator_ids': record['denominator_ids'],
            'source_table_id': by_id[record['id']]['source_table'],
            'inputs_sha256': {key: manifest['inputs_sha256'][key] for key in record['sources']},
            'table': file_ref(bundle / csv_name, manifest['files_sha256'][csv_name]),
            'figure': file_ref(bundle / svg_name, manifest['files_sha256'][svg_name]),
            'review': {
                'scope': 'recorded_synthetic_source_and_marks',
                **file_ref(p9_folder / 'review.json', p9['files_sha256']['review.json']),
            },
        })
    return {
        'case_id': run['case_id'],
        'model_run_id': run['model_run_id'],
        'model_record': file_ref(model / 'run.json', p9['identity']['run_record_sha256']),
        'catalogue_sha256': p9['identity']['inputs_sha256']['catalogue.json'],
        'metrics_sha256': p9['identity']['inputs_sha256']['metrics.json'],
        'figures': figures,
    }


def verify_output(output: Path, *, include_provenance: bool = False) -> dict[str, Any]:
    output = Path(output)
    summary_pointer = read_json(output / 'state/summary.json')
    summary_id = summary_pointer.get('summary_id')
    if (summary_pointer.get('data_class') != 'synthetic'
            or summary_pointer.get('investment_ready') is not False or not valid_digest(summary_id)):
        raise ValueError('invalid summary pointer')
    folder = output / 'summaries' / summary_id
    record = verify_summary(folder)
    identity = record['identity']
    if (summary_pointer.get('summary_record_sha256') != digest_file(folder / 'summary.json')
            or identity['suite_sha256'] != digest_file(folder / 'suite.json')
            or identity['audit_sha256'] != digest_file(folder / 'falsification.json')
            or record.get('comparison_scope') != 'paired_within_each_model_run'
            or record.get('cross_scenario_pairing') != 'not_asserted'
            or record.get('clinical_safety_approved') is not False):
        raise ValueError('summary linkage or interpretation mismatch')
    names = validate_suite(folder / 'suite.json')['cases']
    links = identity['runs']
    if ([item['case_id'] for item in links] != names
            or summary_pointer.get('scenario_count') != len(names)):
        raise ValueError('summary scenario list mismatch')
    expected_rows = []
    f01_records = {}
    for case_id, link in zip(names, links, strict=True):
        model_pointer = read_json(output / 'state/models' / f'{case_id}.json')
        run_id = link['model_run_id']
        if not valid_digest(run_id):
            raise ValueError('invalid model run identifier')
        model = output / 'models' / run_id
        run = verify_case(model)
        if (run['case_id'] != case_id or model_pointer.get('case_id') != case_id
                or model_pointer.get('data_class') != 'synthetic'
                or model_pointer.get('investment_ready') is not False
                or model_pointer.get('model_run_id') != run_id
                or model_pointer.get('run_record_sha256') != link['run_record_sha256']
                or link['run_record_sha256'] != digest_file(model / 'run.json')):
            raise ValueError('model run linkage mismatch')
        with (model / 'paired-outcomes.csv').open(newline='', encoding='utf-8') as stream:
            for row in csv.DictReader(stream):
                expected_rows.append({
                    'case_id': case_id, 'variant': run['variant'], 'model_run_id': run_id,
                    'seed': str(run['seed']), 'draws': str(run['draws']),
                    'description': run['description'], **row,
                })
        figure_pointer = read_json(output / 'state/figures' / f'{case_id}.json')
        figure_id = figure_pointer.get('figure_revision')
        if (not valid_digest(figure_id) or figure_pointer.get('case_id') != case_id
                or figure_pointer.get('model_run_id') != run_id
                or figure_pointer.get('data_class') != 'synthetic'
                or figure_pointer.get('investment_ready') is not False):
            raise ValueError('invalid figure pointer')
        figure_folder = output / 'figures' / figure_id
        figure = verify_figure(figure_folder)
        if (figure_pointer.get('figure_record_sha256') != digest_file(figure_folder / 'figure.json')
                or figure.get('case_id') != case_id or figure.get('model_run_id') != run_id
                or figure['identity'].get('model_run_id') != run_id
                or figure['identity'].get('run_record_sha256') != link['run_record_sha256']):
            raise ValueError('figure linkage mismatch')
        if include_provenance:
            f01_records[case_id] = (figure_folder, figure)
    with (folder / 'scenario-comparison.csv').open(newline='', encoding='utf-8') as stream:
        actual_rows = list(csv.DictReader(stream))
    if actual_rows != expected_rows:
        raise ValueError('summary rows differ from verified paired model outcomes')
    supplementary = 0
    lineage = []
    for link in links:
        case_id = link['case_id']
        priority = read_json(output / 'state/priority-figures' / f'{case_id}.json')
        figure_id = priority.get('figure_revision')
        if (not valid_digest(figure_id) or priority.get('case_id') != case_id
                or priority.get('data_class') != 'synthetic'
                or priority.get('investment_ready') is not False
                or priority.get('model_run_id') != link['model_run_id']):
            raise ValueError('invalid P9 scenario figure pointer')
        figure_folder = output / 'priority-figures' / figure_id
        model = output / 'models' / link['model_run_id']
        p9 = verify_p9(figure_folder, model)
        if p9['schema_version'] == 2:
            supplementary += len(SUPPLEMENT_IDS)
        if priority.get('figure_record_sha256') != digest_file(figure_folder / 'figure-set.json'):
            raise ValueError('P9 figure pointer differs from its revision record')
        if include_provenance:
            f01_folder, f01 = f01_records[case_id]
            lineage.append(_figure_lineage(output, model, f01_folder, f01, figure_folder, p9))
    result = {'status': 'verified_synthetic_outputs', 'summary_id': summary_id,
              'scenarios': len(names), 'paired_rows': len(actual_rows),
              'priority_figures': 6 * len(names), 'supplementary_figures': supplementary,
              'investment_ready': False, 'clinical_safety_approved': False}
    if include_provenance:
        result['provenance'] = {
            'schema_version': 1, 'scope': 'synthetic_computational_lineage',
            'edges': [['inputs', 'metrics'], ['metrics', 'table'],
                      ['table', 'figure'], ['figure', 'review']],
            'scenarios': lineage,
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--provenance', action='store_true',
                        help='Include lineage for each verified figure')
    args = parser.parse_args()
    try:
        result = verify_output(args.output, include_provenance=args.provenance)
    except (OSError, RuntimeError, TypeError, ValueError, KeyError) as exc:
        print(f'P11 INVALID_OR_UNVERIFIED: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
