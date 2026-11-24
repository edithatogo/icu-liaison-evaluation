"""Reconcile offline source evidence and execute the synthetic P7 oracles.

This is not a native-provider or CHHHS clinical qualification runner. It cannot
promote status beyond SOURCE_ORACLES_PASSED_SYNTHETIC_ONLY.
"""
from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import platform

import numpy
import scipy
import pydantic

from icu_liaison.data_request import DataRequestCatalogue, render_request_csv, render_request_markdown
from icu_liaison.local_data import load_and_audit
from icu_liaison.p4_model import EconomicScenario, evaluate_scenarios
from icu_liaison.public_evidence import Catalogue, audit_publisher_receipt, reconcile_catalogue
from icu_liaison.qualification_independent import audit_local_aggregate, audit_p4_draws

ROOT = Path(__file__).resolve().parents[1]


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def qualify(*, publisher_document: Path | None = None) -> dict:
    scenario_bytes = (ROOT / 'model-inputs/p4/illustrative.json').read_bytes()
    scenario = EconomicScenario.model_validate_json(scenario_bytes)
    if scenario.data_class != 'synthetic':
        raise ValueError('this source-level report may use synthetic P4 scenarios only')
    catalogue_bytes = (ROOT / 'model-inputs/anzics-benchmarks.json').read_bytes()
    register_bytes = (ROOT / 'conductor/evidence/source-register.json').read_bytes()
    register = json.loads(register_bytes)
    sources = reconcile_catalogue(Catalogue.model_validate_json(catalogue_bytes), register)
    publisher_check = audit_publisher_receipt(
        ROOT / 'verification/p7-anzics-2024-25-publisher-2026-11-24.json',
        register, document_path=publisher_document,
    )
    request_bytes = (ROOT / 'model-inputs/chhhs-data-request.json').read_bytes()
    request = DataRequestCatalogue.model_validate_json(request_bytes)
    data = load_and_audit(ROOT / 'tests/fixtures/p3_episodes/manifest.json')
    if data['data_class'] != 'synthetic':
        raise ValueError('this source-level QA may only consume the committed synthetic fixture')
    local = audit_local_aggregate(data)
    run = evaluate_scenarios(scenario)
    iterations = scenario.iterations
    candidates = (0, 1, 7, 53, iterations // 2, iterations - 1)
    sampled_indices = sorted({index for index in candidates if index < iterations})
    numerical = audit_p4_draws(run, sampled_indices=sampled_indices)
    return {
        'status': 'SOURCE_ORACLES_PASSED_SYNTHETIC_ONLY',
        'date': datetime.now(UTC).date().isoformat(),
        'python': platform.python_version(),
        'numerical_libraries': {
            'numpy': numpy.__version__, 'scipy': scipy.__version__, 'pydantic': pydantic.__version__,
        },
        'scenario_sha256': _sha256(scenario_bytes),
        'p4_input_digest_sha256': run.input_digest_sha256,
        'p4_seed': scenario.seed,
        'source_register_sha256': _sha256(register_bytes),
        'benchmark_catalogue_sha256': _sha256(catalogue_bytes),
        'p4_independent_accounting': numerical,
        'p3_synthetic_quality': local,
        'p3_input_provenance': data['input_provenance'],
        'anzics_external_sources': {
            metric['id']: {'status': metric['verification_status'], 'value': metric['value']}
            for metric in sources['metrics']
        },
        'publisher_check': publisher_check,
        'chhhs_data_request': {
            'status': request.status,
            'source_sha256': _sha256(request_bytes),
            'dataset_count': len(request.datasets),
            'field_count': sum(len(dataset.fields) for dataset in request.datasets),
            'rendered_markdown_sha256': _sha256(render_request_markdown(request).encode('utf-8')),
            'rendered_csv_sha256': _sha256(render_request_csv(request).encode('utf-8')),
        },
        'native_kairos_executed': False,
        'dapane_native_executed': False,
        'voiage_native_executed': False,
        'CHHHS_approved_local_records_used': False,
        'clinical_or_causal_validation': False,
        'finance_approval': False,
        'investment_ready': False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publisher-document', type=Path, help='Retained ANZICS 2024/25 PDF to check offline')
    args = parser.parse_args()
    try:
        report = qualify(publisher_document=args.publisher_document)
    except (OSError, ValueError) as error:
        parser.exit(2, f'P7 qualification failed. {error}\n')
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
