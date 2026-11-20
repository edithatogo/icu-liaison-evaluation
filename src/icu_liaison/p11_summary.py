"""Review and combine the versioned P11 scenario comparisons."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import errno
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from .p11_model import verify_case
from .p11_records import atomic_json, digest_file, digest_json, inventory, read_json, valid_digest
from tools.p10_falsification import run_suite


def validate_suite(path: Path) -> dict:
    suite = read_json(path)
    if set(suite) != {'schema_version', 'data_class', 'cases'}:
        raise ValueError('unexpected scenario suite fields')
    cases = suite['cases']
    if (suite['schema_version'] != 1 or suite['data_class'] != 'synthetic'
            or not isinstance(cases, list) or not cases
            or any(not isinstance(case, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,47}', case)
                   for case in cases) or len(cases) != len(set(cases))):
        raise ValueError('invalid synthetic scenario suite')
    return suite


def verify_summary(folder: Path) -> dict:
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('synthetic summary directory is missing or unsafe')
    record = read_json(folder / 'summary.json')
    if (record.get('schema_version') != 1 or record.get('data_class') != 'synthetic'
            or record.get('investment_ready') is not False
            or not valid_digest(record.get('summary_id'))
            or folder.name != record['summary_id']
            or digest_json(record['identity']) != record['summary_id']):
        raise ValueError('synthetic summary identity or readiness mismatch')
    if record.get('files_sha256') != inventory(folder, exclude='summary.json'):
        raise ValueError('synthetic summary file inventory or digest mismatch')
    return record


def build_summary(suite_file: Path, output: Path, pointers: list[Path], audit_file: Path,
                  pointer: Path) -> dict:
    suite_file, output, audit_file, pointer = map(Path, (suite_file, output, audit_file, pointer))
    suite = validate_suite(suite_file)
    audit = read_json(audit_file)
    if (audit.get('status') != 'synthetic_falsification_passed_not_empirically_validated'
            or audit.get('investment_ready') is not False
            or audit.get('clinical_safety_measured') is not False):
        raise ValueError('synthetic falsification audit is missing or unqualified')
    audit_cases = [item['case'] for item in audit['cases']]
    expected_cases = ['no_effect', 'harmful_returns', 'zero_addressable_delay',
                      'zero_usable_capacity', 'zero_cash_realisability']
    if audit_cases != expected_cases or not all(item['invariants_passed'] for item in audit['cases']):
        raise ValueError('synthetic falsification audit coverage mismatch')
    receipts = {}
    for path in pointers:
        item = read_json(path)
        case_id, run_id = item.get('case_id'), item.get('model_run_id')
        if (item.get('data_class') != 'synthetic' or item.get('investment_ready') is not False
                or case_id in receipts or not valid_digest(run_id)):
            raise ValueError('invalid or duplicated scenario run pointer')
        model = output / 'models' / run_id
        record = verify_case(model)
        if (record['case_id'] != case_id
                or item.get('run_record_sha256') != digest_file(model / 'run.json')):
            raise ValueError('scenario pointer differs from the model record')
        receipts[case_id] = (item, record, model)
    if set(receipts) != set(suite['cases']):
        raise ValueError('scenario suite and run pointers differ')
    identity = {
        'schema_version': 1,
        'suite_sha256': digest_file(suite_file),
        'audit_sha256': digest_file(audit_file),
        'summary_source_sha256': {
            Path(__file__).name: digest_file(Path(__file__)),
            'p11_records.py': digest_file(Path(__file__).with_name('p11_records.py')),
        },
        'runs': [{
            'case_id': case,
            'model_run_id': receipts[case][0]['model_run_id'],
            'run_record_sha256': receipts[case][0]['run_record_sha256'],
        } for case in suite['cases']],
    }
    summary_id = digest_json(identity)
    parent = output / 'summaries'
    parent.mkdir(parents=True, exist_ok=True)
    target = parent / summary_id
    if not target.exists():
        with tempfile.TemporaryDirectory(prefix='.p11-stage-', dir=parent) as temp:
            staging = Path(temp) / summary_id
            staging.mkdir()
            rows = []
            for case_id in suite['cases']:
                _, run, model = receipts[case_id]
                with (model / 'paired-outcomes.csv').open(encoding='utf-8', newline='') as stream:
                    for row in csv.DictReader(stream):
                        rows.append({
                            'case_id': case_id, 'variant': run['variant'],
                            'model_run_id': run['model_run_id'], 'seed': run['seed'],
                            'draws': run['draws'], 'description': run['description'], **row,
                        })
            with (staging / 'scenario-comparison.csv').open('w', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
                writer.writeheader()
                writer.writerows(rows)
            (staging / 'falsification.json').write_bytes(audit_file.read_bytes())
            (staging / 'suite.json').write_bytes(suite_file.read_bytes())
            record = {
                'schema_version': 1, 'data_class': 'synthetic', 'summary_id': summary_id,
                'identity': identity, 'created_at_utc': datetime.now(timezone.utc).isoformat(),
                'clinical_safety_approved': False, 'investment_ready': False,
                'comparison_scope': 'paired_within_each_model_run',
                'cross_scenario_pairing': 'not_asserted',
                'files_sha256': inventory(staging, exclude='summary.json'),
            }
            (staging / 'summary.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
            verify_summary(staging)
            try:
                os.rename(staging, target)
            except OSError as exc:
                if exc.errno not in (errno.EEXIST, errno.ENOTEMPTY) or not target.is_dir():
                    raise
    verify_summary(target)
    result = {
        'schema_version': 1, 'data_class': 'synthetic', 'summary_id': summary_id,
        'summary_record_sha256': digest_file(target / 'summary.json'),
        'scenario_count': len(suite['cases']), 'investment_ready': False,
    }
    atomic_json(pointer, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    audit = sub.add_parser('audit')
    audit.add_argument('--pointer', type=Path, required=True)
    summary = sub.add_parser('summary')
    summary.add_argument('--suite', type=Path, required=True)
    summary.add_argument('--output', type=Path, required=True)
    summary.add_argument('--audit', type=Path, required=True)
    summary.add_argument('--pointer', type=Path, required=True)
    summary.add_argument('--cases', nargs='+', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.action == 'audit':
            result = run_suite(iterations=128)
            atomic_json(args.pointer, result)
        else:
            result = build_summary(args.suite, args.output, args.cases, args.audit, args.pointer)
    except (OSError, RuntimeError, TypeError, ValueError, KeyError) as exc:
        print(f'P11 INVALID_OR_UNVERIFIED: {type(exc).__name__}', file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
