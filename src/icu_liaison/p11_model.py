"""Build immutable, source-bound P4/P5 runs for fictional P11 scenarios."""
from __future__ import annotations
from typing import Any

import argparse
import csv
from datetime import datetime, timezone
import errno
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

import numpy as np

from .p11_cases import materialise
from .p11_records import (
    atomic_json, attempt, canonical, digest_bytes, digest_file, digest_json,
    inventory, read_json, valid_digest,
)
from .p4_model import EconomicScenario, P4Run, evaluate_scenarios, financial_decision_surface
from .p5_reporting import MEASURES, _stats, build_report, review_report
from .qualification_independent import audit_p4_draws

ROOT = Path(__file__).resolve().parents[2]
MODEL_SOURCES = (
    'src/icu_liaison/__init__.py',
    'src/icu_liaison/model.py',
    'src/icu_liaison/schemas.py',
    'src/icu_liaison/protocol.py',
    'src/icu_liaison/public_evidence.py',
    'src/icu_liaison/provider_contracts.py',
    'src/icu_liaison/p4_model.py',
    'src/icu_liaison/p4_admission.py',
    'src/icu_liaison/p5_reporting.py',
    'src/icu_liaison/qualification_independent.py',
    'src/icu_liaison/adapters/__init__.py',
    'src/icu_liaison/adapters/dapane.py',
    'src/icu_liaison/adapters/p4_dapane.py',
    'src/icu_liaison/adapters/voiage.py',
    'src/icu_liaison/p11_cases.py',
    'src/icu_liaison/p11_model.py',
    'src/icu_liaison/p11_records.py',
    'tools/p10_falsification.py',
    'tools/evaluate_safety_decision.py',
)
INPUTS = {
    'protocol.json': ROOT / 'model-inputs/clinical-economic-protocol.json',
    'benchmarks.json': ROOT / 'model-inputs/anzics-benchmarks.json',
    'source-register.json': ROOT / 'conductor/evidence/source-register.json',
    'falsification-matrix.json': ROOT / 'contracts/reporting/falsification-matrix.json',
    'providers.lock.json': ROOT / 'providers.lock.json',
}


def _runtime() -> dict[str, Any]:
    return {
        'python': platform.python_version(),
        'implementation': platform.python_implementation(),
        'machine': platform.machine(),
        'system': platform.system(),
        'versions': {name: metadata.version(name) for name in
                     ('numpy', 'scipy', 'pydantic', 'pydantic-core', 'jsonschema')},
    }


def _source_hashes() -> dict[str, str]:
    return {name: digest_file(ROOT / name) for name in MODEL_SOURCES}


def _git_source_state() -> dict[str, Any]:
    revision = subprocess.run(
        ['git', '-C', str(ROOT), 'rev-parse', '--verify', 'HEAD'],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    status = subprocess.run(
        ['git', '-C', str(ROOT), 'status', '--porcelain=v1', '--untracked-files=all',
         '--', *MODEL_SOURCES],
        check=True, capture_output=True, text=True,
    ).stdout
    return {'git_revision': revision, 'executed_source_dirty': bool(status)}


def _paired_rows(scenario: EconomicScenario) -> tuple[P4Run, dict[str, Any], list[dict[str, Any]]]:
    run = evaluate_scenarios(scenario)
    audit = audit_p4_draws(run)
    baseline = run.strategies['current_care']
    rows = []
    for strategy in run.scenario.strategies[1:]:
        result = run.strategies[strategy.id]
        for name, unit, boundary in MEASURES:
            delta = getattr(result, name) - getattr(baseline, name)
            rows.append({
                'strategy_id': strategy.id,
                'reference_strategy': 'current_care',
                'measure': name,
                'unit': f'AUD_{scenario.price_year}' if unit == 'AUD' else unit,
                'boundary': boundary,
                **_stats(delta),
                'probability_positive_difference': float(np.mean(delta > 0)),
                'definition': 'within_run_paired_parameter_draws',
                'uncertainty': 'PSA_quantiles_not_confidence_intervals',
            })
    return run, audit, rows


def _check_surface(folder: Path, run: P4Run) -> None:
    expected, labels = financial_decision_surface(run)
    with (folder / 'decision-surface.csv').open(newline='', encoding='utf-8') as stream:
        reader = csv.reader(stream)
        if next(reader, None) != labels:
            raise ValueError('P5 strategy order differs from P4 replay')
        data = np.asarray(list(reader), dtype=np.float64)
    if data.shape != expected.shape or not np.allclose(data, expected, rtol=1e-12, atol=1e-7):
        raise ValueError('P5 paired draws differ from the seeded P4 replay')


def _check_variant(variant: str, run: P4Run) -> None:
    for arm in run.scenario.strategies[1:]:
        result = run.strategies[arm.id]
        if variant == 'no_effect':
            if not (np.allclose(result.icu_bed_days_released, 0)
                    and np.allclose(result.readmissions_avoided, 0)):
                raise ValueError('no-effect case violates its P10 invariant')
        elif variant == 'harmful_returns' and not np.all(result.readmissions_avoided < 0):
            raise ValueError('harmful-return case violates its P10 invariant')
        elif variant == 'zero_addressable_delay' and not np.allclose(result.icu_bed_days_released, 0):
            raise ValueError('zero-addressable case violates its P10 invariant')
        elif variant == 'zero_usable_capacity' and not np.allclose(result.usable_bed_days, 0):
            raise ValueError('zero-usable case violates its P10 invariant')
        elif variant == 'zero_cash_realisability':
            cost = run.sampled_inputs[f'strategy.{arm.id}.annual_incremental_cost_aud']
            if not np.allclose(result.net_budget_impact_aud, -cost):
                raise ValueError('zero-cash case violates its P10 invariant')


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def _validate_rows(path: Path, expected: list[dict[str, Any]]) -> None:
    with path.open(encoding='utf-8', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(expected[0]):
            raise ValueError('paired outcome columns changed')
        actual = list(reader)
    serialised = [{key: str(value) for key, value in row.items()} for row in expected]
    if actual != serialised:
        raise ValueError('paired outcomes differ from P4 replay')


def verify_case(folder: Path) -> dict[str, Any]:
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError('synthetic model output directory is missing or unsafe')
    record = read_json(folder / 'run.json')
    run_id = record.get('model_run_id')
    if set(record) != {
        'schema_version', 'data_class', 'model_run_id', 'identity', 'case_id', 'variant',
        'description', 'seed', 'draws', 'source', 'created_at_utc', 'assumption_changes',
        'provider_versions_locked', 'provider_execution', 'clinical_safety_approved',
        'investment_ready', 'files_sha256',
    }:
        raise ValueError('unexpected or missing synthetic run field')
    if (type(record['schema_version']) is not int or record['schema_version'] != 1 or record.get('data_class') != 'synthetic'
            or record.get('investment_ready') is not False
            or record.get('clinical_safety_approved') is not False):
        raise ValueError('synthetic run has unsupported readiness')
    identity = record['identity']
    if (not isinstance(identity, dict) or set(identity) != {
            'schema_version', 'data_class', 'case_id', 'inputs_sha256', 'effective_scenario_sha256',
            'model_source_sha256', 'runtime', 'provider_execution',
        } or type(identity['schema_version']) is not int or identity['schema_version'] != 1
        or identity['data_class'] != 'synthetic' or identity['case_id'] != record['case_id']):
        raise ValueError('invalid synthetic model identity')
    if not valid_digest(run_id) or folder.name != run_id or digest_json(record['identity']) != run_id:
        raise ValueError('model run identity mismatch')
    if (record.get('provider_execution') != {'dapane': 'not_executed', 'voiage': 'not_executed'}
            or record['identity'].get('provider_execution') != record['provider_execution']):
        raise ValueError('unsupported provider qualification claim')
    if record.get('files_sha256') != inventory(folder, exclude='run.json'):
        raise ValueError('synthetic model output file inventory or digest mismatch')
    expected_inputs = {'case.json', 'base-scenario.json', *INPUTS}
    if set(identity['inputs_sha256']) != expected_inputs:
        raise ValueError('synthetic input snapshot inventory mismatch')
    for name, expected in identity['inputs_sha256'].items():
        if digest_file(folder / 'inputs' / name) != expected:
            raise ValueError('synthetic input snapshot digest mismatch')
    case, scenario = materialise(
        (folder / 'inputs/case.json').read_bytes(),
        (folder / 'inputs/base-scenario.json').read_bytes(),
    )
    saved = read_json(folder / 'inputs/effective-scenario.json')
    if saved != scenario.model_dump(mode='json') or digest_json(saved) != identity['effective_scenario_sha256']:
        raise ValueError('effective scenario identity mismatch')
    if (record['case_id'] != case.case_id or record['seed'] != scenario.seed
            or record['draws'] != scenario.iterations):
        raise ValueError('scenario run metadata mismatch')
    review = review_report(folder / 'p5-report')
    if review['provider_qualification'] is not False or review['clinical_safety_approved'] is not False:
        raise ValueError('P5 review incorrectly asserts provider or clinical readiness')
    # Replaying is meaningful only when this verifier is using the recorded
    # model code and runtime. Historical objects remain inspectable by hashes.
    if identity['model_source_sha256'] == _source_hashes() and identity['runtime'] == _runtime():
        run, independent_audit, rows = _paired_rows(scenario)
        _check_surface(folder / 'p5-report', run)
        _check_variant(case.variant, run)
        _validate_rows(folder / 'paired-outcomes.csv', rows)
        expected_review = {'p5': review, 'independent_sampled_accounting': independent_audit}
        if read_json(folder / 'review.json') != expected_review:
            raise ValueError('synthetic numerical review differs from independent replay')
    return record


def build_case(case_file: Path, base_file: Path, output: Path, pointer: Path, *,
               expected_case: str | None = None) -> dict[str, Any]:
    case_file, base_file, output, pointer = map(Path, (case_file, base_file, output, pointer))
    case_bytes = case_file.read_bytes() if not case_file.is_symlink() else None
    base_bytes = base_file.read_bytes() if not base_file.is_symlink() else None
    if case_bytes is None or base_bytes is None:
        raise ValueError('symlinked scenario input rejected')
    case, scenario = materialise(case_bytes, base_bytes)
    if expected_case is not None and case.case_id != expected_case:
        raise ValueError('scenario case identifier differs from the workflow target')
    attempt_file, attempt_record = attempt(output, case.case_id)
    try:
        snapshots = {'case.json': case_bytes, 'base-scenario.json': base_bytes}
        snapshots.update({name: path.read_bytes() for name, path in INPUTS.items()})
        identity = {
            'schema_version': 1,
            'data_class': 'synthetic',
            'case_id': case.case_id,
            'inputs_sha256': {name: digest_bytes(value) for name, value in snapshots.items()},
            'effective_scenario_sha256': digest_json(scenario.model_dump(mode='json')),
            'model_source_sha256': _source_hashes(),
            'runtime': _runtime(),
            'provider_execution': {'dapane': 'not_executed', 'voiage': 'not_executed'},
        }
        run_id = digest_json(identity)
        models = output / 'models'
        models.mkdir(parents=True, exist_ok=True)
        target = models / run_id
        if not target.exists():
            with tempfile.TemporaryDirectory(prefix='.p11-stage-', dir=models) as temp:
                staging = Path(temp) / run_id
                inputs = staging / 'inputs'
                inputs.mkdir(parents=True)
                for name, value in snapshots.items():
                    (inputs / name).write_bytes(value)
                (inputs / 'effective-scenario.json').write_bytes(canonical(scenario.model_dump(mode='json')))
                build_report(
                    scenario, staging / 'p5-report', protocol=inputs / 'protocol.json',
                    catalogue=inputs / 'benchmarks.json', source_register=inputs / 'source-register.json',
                    voiage_mode='skip', dapane_mode='skip', plots=False,
                )
                report_review = review_report(staging / 'p5-report')
                run, independent_audit, rows = _paired_rows(scenario)
                _check_surface(staging / 'p5-report', run)
                _check_variant(case.variant, run)
                _write_rows(staging / 'paired-outcomes.csv', rows)
                (staging / 'review.json').write_text(json.dumps({
                    'p5': report_review, 'independent_sampled_accounting': independent_audit,
                }, indent=2, sort_keys=True) + '\n', encoding='utf-8')
                if _source_hashes() != identity['model_source_sha256']:
                    raise ValueError('executed model source changed during the run')
                provider_lock = json.loads(snapshots['providers.lock.json'])
                locked_versions = {
                    name: provider_lock['providers'][name]['version'] for name in ('dapane', 'voiage')
                }
                matrix = json.loads(snapshots['falsification-matrix.json'])
                change = next((item['change'] for item in matrix['cases']
                               if item['id'] == case.variant), 'baseline assumptions')
                record = {
                    'schema_version': 1, 'data_class': 'synthetic', 'model_run_id': run_id,
                    'identity': identity, 'case_id': case.case_id, 'variant': case.variant,
                    'description': case.description, 'seed': scenario.seed, 'draws': scenario.iterations,
                    'source': _git_source_state(), 'created_at_utc': datetime.now(timezone.utc).isoformat(),
                    'assumption_changes': {'variant': change, 'overrides': case.overrides,
                                           'seed_override': case.seed,
                                           'iterations_override': case.iterations},
                    'provider_versions_locked': locked_versions,
                    'provider_execution': identity['provider_execution'],
                    'clinical_safety_approved': False, 'investment_ready': False,
                    'files_sha256': inventory(staging, exclude='run.json'),
                }
                (staging / 'run.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
                verify_case(staging)
                try:
                    os.rename(staging, target)
                except OSError as exc:
                    if exc.errno not in (errno.EEXIST, errno.ENOTEMPTY) or not target.is_dir():
                        raise
        record = verify_case(target)
        receipt = {
            'schema_version': 1, 'data_class': 'synthetic', 'case_id': case.case_id,
            'model_run_id': run_id, 'run_record_sha256': digest_file(target / 'run.json'),
            'investment_ready': False,
        }
        atomic_json(pointer, receipt)
        attempt_record.update(status='completed', model_run_id=run_id,
                              finished_at_utc=datetime.now(timezone.utc).isoformat())
        atomic_json(attempt_file, attempt_record)
        return receipt
    except BaseException as exc:
        attempt_record.update(status='failed', error_type=type(exc).__name__,
                              finished_at_utc=datetime.now(timezone.utc).isoformat())
        atomic_json(attempt_file, attempt_record)
        raise


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--case', type=Path, required=True)
    cli.add_argument('--base', type=Path, required=True)
    cli.add_argument('--expected-case')
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--pointer', type=Path, required=True)
    args = cli.parse_args()
    try:
        result = build_case(args.case, args.base, args.output, args.pointer,
                            expected_case=args.expected_case)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        print(f'P11 INVALID_OR_UNVERIFIED: {type(exc).__name__}', file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
