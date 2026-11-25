"""Check fictional P8.4 valuations with the reviewed macOS Dapane wheel."""
from __future__ import annotations
from typing import Any

import argparse
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
from importlib.metadata import version
from importlib.util import find_spec
import json
from pathlib import Path
import platform

from icu_liaison.adapters.dapane import (
    CostLine,
    compare_valued_scenarios,
    evaluate_request,
    make_request,
)
from icu_liaison.provider_contracts import load_provider_lock

ROOT = Path(__file__).resolve().parents[1]
LOCK = 'providers.lock.json'
ACTIVITY_RECEIPT = 'verification/p8-mchs-paired-acute-2026-11-24.json'
FIXTURE = 'model-inputs/p8/synthetic-mchs-pair.json'


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _reviewed_runtime(wheel: Path) -> dict[str, Any]:
    provider = load_provider_lock(ROOT / LOCK)['providers']['dapane']
    review = provider['reviewed_wheel']
    python = platform.python_version()
    host = f'macOS {platform.mac_ver()[0]} {platform.machine()}'
    if python != review['python'] or host != review['platform']:
        raise ValueError('The reviewed Dapane wheel requires its recorded Python and macOS host')
    if wheel.name != review['filename'] or _digest(wheel) != review['sha256']:
        raise ValueError('Dapane wheel differs from the reviewed archive')
    spec = find_spec('dapane')
    if spec is None or spec.origin is None or version('dapane') != provider['version']:
        raise ValueError('The reviewed Dapane wheel must be installed')
    extension = Path(spec.origin).parent / Path(review['native_extension']).name
    if _digest(extension) != provider['binary_sha256']:
        raise ValueError('Installed Dapane extension differs from the reviewed binary')
    return {
        'provider': 'dapane',
        'version': provider['version'],
        'python': python,
        'platform': host,
        'source_commit': provider['source_commit'],
        'wheel_sha256': review['sha256'],
        'native_extension_sha256': provider['binary_sha256'],
    }


def _paired_requests(case: dict[str, Any], basis: str, rate: str) -> dict[str, dict[str, Any]]:
    def care_line(hours: str) -> CostLine:
        return CostLine('episode-icu', 'icu_care', 'hour', hours, rate, ['icu_care'])

    policy = {'basis': basis, 'price_year': case['pricing_year']}
    current = make_request(f'fictional-p8-{basis}-current',
                           [care_line(case['icu_hours_current'])], **policy)
    proposed = make_request(f'fictional-p8-{basis}-liaison', [
        care_line(case['icu_hours_intervention']),
        CostLine('liaison-wage', 'liaison_staffing', 'hour', '2', '50', ['base_salary']),
        CostLine('liaison-oncost', 'liaison_staffing', 'hour', '2', '25', ['employment_oncost']),
    ], **policy)
    wage, oncost = proposed['usage'][1:]
    oncost.update(use_id=wage['use_id'], source=wage['source'])
    return {'current_care': current, 'liaison_service': proposed}


def run_check(wheel: Path) -> dict[str, Any]:
    runtime = _reviewed_runtime(wheel)
    DapaneError = __import__("dapane").DapaneError

    activity = json.loads((ROOT / ACTIVITY_RECEIPT).read_text())
    case = json.loads((ROOT / FIXTURE).read_text())
    if (activity['fixture'] != FIXTURE or case['data_class'] != 'synthetic'
            or activity['clinical_case_mix_accepted']):
        raise ValueError('The P8 valuation check requires fictional inputs')
    activity_pair = next(row for row in activity['cases']
                         if row['pricing_year'] == case['pricing_year'])
    economic = _paired_requests(case, 'economic_cost', '100')
    financial = _paired_requests(case, 'financial_cost', '10')
    resource = compare_valued_scenarios(economic)
    cash_cost = compare_valued_scenarios(financial)
    for result, expected in ((resource, ('5825.00', '5575.00', '250.00')),
                             (cash_cost, ('582.50', '692.50', '-110.00'))):
        reported = tuple(result[key] for key in (
            'avoidable_current_care_slice_aud', 'additional_liaison_slice_aud',
            'incremental_resource_benefit_aud',
        ))
        if reported != expected or result['provider_evidence'] != 'native_provider_executed':
            raise ValueError(f'Unexpected native {result["basis"]} amounts {reported}')

    priced = evaluate_request(financial['liaison_service'])
    staffing = [(line['use_id'], line['components'], line['rounded'])
                for line in priced['lines'] if line['target'] == 'liaison_staffing']
    if sorted(staffing) != [
        ('use-liaison-wage', ['base_salary'], '100.00'),
        ('use-liaison-wage', ['employment_oncost'], '50.00'),
    ]:
        raise ValueError('The paid shift must contribute its two cost components once')

    duplicate = deepcopy(financial['liaison_service'])
    duplicate['quotes'][2]['components'] = ['base_salary']
    try:
        evaluate_request(duplicate)
    except DapaneError as exc:
        if exc.code != 'component_overlap':
            raise
    else:
        raise ValueError('Dapane accepted a duplicate salary component')

    current_weight = Decimal(activity_pair['oracle_current_nwau'])
    proposed_weight = Decimal(activity_pair['oracle_intervention_nwau'])
    change = proposed_weight - current_weight
    funding_rate = Decimal('1000')
    if change != Decimal(activity_pair['oracle_change_nwau']):
        raise ValueError('The recorded fictional NWAU pair does not reconcile')
    return {
        'schema_version': 1,
        'scope': 'fictional_p8_native_costs_and_hypothetical_episode_funding',
        'runtime': runtime,
        'source_sha256': {name: _digest(ROOT / name) for name in (
            LOCK, ACTIVITY_RECEIPT, FIXTURE, 'src/icu_liaison/adapters/dapane.py',
            'src/icu_liaison/provider_contracts.py',
            'tools/qualify_p8_synthetic_valuation.py',
        )},
        'assumptions': {
            'icu_hours_current': case['icu_hours_current'],
            'icu_hours_liaison': case['icu_hours_intervention'],
            'economic_icu_rate_aud_per_hour': '100',
            'cash_icu_rate_aud_per_hour': '10',
            'paid_liaison_hours': '2',
            'liaison_salary_aud_per_hour': '50',
            'liaison_oncost_aud_per_hour': '25',
        },
        'economic_cost': {
            'current_aud': resource['avoidable_current_care_slice_aud'],
            'liaison_aud': resource['additional_liaison_slice_aud'],
            'resource_benefit_aud': resource['incremental_resource_benefit_aud'],
        },
        'financial_cost': {
            'current_aud': cash_cost['avoidable_current_care_slice_aud'],
            'liaison_aud': cash_cost['additional_liaison_slice_aud'],
            'change_aud': format(-Decimal(cash_cost['incremental_resource_benefit_aud']), '.2f'),
            'included_staffing_aud': format(sum(Decimal(line[2]) for line in staffing), '.2f'),
            'duplicate_staffing_rejected': 'component_overlap',
        },
        'hypothetical_episode_funding': {
            'pricing_year': case['pricing_year'],
            'change_nwau': format(change, 'f'),
            'assumed_aud_per_nwau': str(funding_rate),
            'change_aud': format(change * funding_rate, '.2f'),
            'actual_revenue_change_aud': None,
        },
        'annual_calculator_parity_accepted': False,
        'site_investment_approved': False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_check(args.wheel), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
