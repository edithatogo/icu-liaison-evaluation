"""Verify the current P11 pointers, immutable objects and paired summary."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

from .p11_figure import verify_figure
from .p11_model import verify_case
from .p11_records import digest_file, read_json, valid_digest
from .p11_summary import validate_suite, verify_summary


def verify_output(output: Path) -> dict:
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
    with (folder / 'scenario-comparison.csv').open(newline='', encoding='utf-8') as stream:
        actual_rows = list(csv.DictReader(stream))
    if actual_rows != expected_rows:
        raise ValueError('summary rows differ from verified paired model outcomes')
    return {'status': 'verified_synthetic_outputs', 'summary_id': summary_id,
            'scenarios': len(names), 'paired_rows': len(actual_rows),
            'investment_ready': False, 'clinical_safety_approved': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = verify_output(args.output)
    except (OSError, RuntimeError, TypeError, ValueError, KeyError) as exc:
        print(f'P11 INVALID_OR_UNVERIFIED: {type(exc).__name__}: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
