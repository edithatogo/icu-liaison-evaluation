"""Adapter to Dapane's *current* exact quotation/usage contract 0.1.

No monetary total is computed here; only explicit nonnegative use and
quotation records are assembled. Compare independently evaluated baseline and
intervention totals outside Dapane. Do not invent negative resource quantities.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Callable, Any

from ..schemas import Parameter, Scenario

type ValuationProvider = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class CostLine:
    id: str
    target: str
    unit: str
    quantity: str
    unit_price_aud: str
    components: list[str]


def _nonnegative_decimal(s: str) -> str:
    try:
        number = Decimal(s)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError('Dapane requires explicit decimal quantities') from exc
    if not number.is_finite() or number < 0:
        raise ValueError('Dapane input must be a finite nonnegative quantity')
    return format(number, 'f')


def make_request(
    run_id: str, lines: list[CostLine], *, price_year: int = 2026,
    perspective: str = 'provider', basis: str = 'economic_cost',
) -> dict[str, Any]:
    if not run_id.strip() or not 2000 <= price_year <= 2100:
        raise ValueError('run id or price year invalid')
    if basis not in {'economic_cost','financial_cost','funding','charge'}:
        raise ValueError('invalid Dapane valuation basis')
    if not lines:
        raise ValueError('Dapane requires actual declared resource lines')
    if len({x.id for x in lines}) != len(lines):
        raise ValueError('same underlying use must not be counted twice')
    quotes, usage = [], []
    date = f'{price_year}-07-01'
    def source(identifier: str) -> dict[str, Any]:
        return {'id':identifier, 'version':'1.0.0', 'evidence':'synthetic',
                'access':'public', 'validation':'unvalidated'}
    for item in lines:
        if not item.id.strip() or not item.target.strip() or not item.unit.strip():
            raise ValueError('line identifiers, target and unit required')
        if not item.components or len(set(item.components)) != len(item.components):
            raise ValueError('cost components must be declared without duplicates')
        quantity = _nonnegative_decimal(item.quantity)
        price = _nonnegative_decimal(item.unit_price_aud)
        quote = f'quote-{item.id}'
        quotes.append({
            'id':quote, 'kind':'resource_use', 'target':item.target, 'unit':item.unit,
            'amount':price, 'per_quantity':'1', 'currency':'AUD',
            'price_year':price_year, 'basis':basis, 'components':item.components,
            'valid_from':f'{price_year}-01-01', 'valid_to':f'{price_year+1}-01-01',
            'known_from':f'{price_year}-01-01', 'source':source(f'quote-{item.id}'),
        })
        usage.append({
            'id':f'usage-{item.id}', 'use_id':f'use-{item.id}',
            'kind':'resource_use', 'target':item.target, 'unit':item.unit,
            'quantity':quantity, 'service_date':date, 'quote_id':quote,
            'source':source(f'usage-{item.id}'),
        })
    return {'schema_version':'0.1', 'run_id':run_id,
            'knowledge_cutoff':f'{price_year}-12-31',
            'policy':{'id':'icu-liaison-cost-profile','version':'1.0.0',
                      'currency':'AUD','price_year':price_year,
                      'perspective':perspective, 'basis':basis,
                      'rounding':{'scale':2,'mode':'half_even'}},
            'quotes':quotes,'usage':usage}


def evaluate_request(request: dict[str, Any], *, provider: ValuationProvider | None = None) -> dict[str, Any]:
    if provider is None:
        try:
            evaluate = __import__("dapane").evaluate
        except ImportError as exc:
            raise RuntimeError('Dapane native 0.1 provider not installed; cannot claim exact valuation') from exc
        provider = evaluate
    if provider is None:
        raise RuntimeError("Dapane evaluator unavailable")
    return provider(request)


def make_nominal_cost_bridge(
    scenario: 'Scenario', *, price_year: int = 2026,
    perspective: str = 'provider', basis: str = 'economic_cost',
) -> dict[str, dict[str, Any]]:
    """Express only *incremental* pathway costs as two nonnegative Dapane ledgers.

    This bridge is NOT a reconstruction of total hospitalisation costs. The
    current-care ledger contains the index ICU delay days and post-discharge
    returns that the *proposed* service would avoid. The liaison ledger contains
    incremental staffing and any additional returns associated with surveillance.
    Both use the same hypothetical unit quotations. No saving is represented as
    a negative Dapane ``Usage`` quantity, and the index/return periods must not
    overlap. Use the existing PSA engine to derive modal resource quantities;
    only Dapane values them.
    """
    # Even caller-mutated or model_construct data must be validated afresh.
    checked = Scenario.model_validate(scenario.model_dump())
    i = checked.inputs
    # Dapane consumes exact decimal quantities. Compute the already-specified
    # *nominal* cohort identities in Decimal rather than transporting rounded
    # NumPy binary floats into the exact provider contract. The stochastic PSA
    # remains separately owned by SciPy/NumPy.
    def d(parameter: Parameter) -> Decimal:
        return Decimal(str(parameter.value))
    n = Decimal(checked.annual_eligible_discharges)
    index_days = (
        n * d(i.delayed_discharge_ge12h_rate)
        * d(i.delayed_cases_addressable_fraction)
        * d(i.addressable_cases_improved_fraction)
        * d(i.hours_released_per_improved_case) / Decimal(24)
    )
    baseline_risk = d(i.unplanned_72h_readmission_risk)
    proposed_risk = max(Decimal(0), min(Decimal(1), baseline_risk * (1 - d(i.relative_readmission_reduction))))
    avoided_returns = n * (baseline_risk - proposed_risk)
    index_price = str(i.net_avoidable_cost_per_icu_day_aud.value)
    return_price = str(i.additional_cost_per_readmission_aud.value)
    service_price = str(i.annual_incremental_service_cost_aud.value)

    current_lines = [
        CostLine(
            'index-delay-counterfactual', 'index_delay', 'icu_day',
            format(index_days.normalize(), 'f'), index_price, ['index_ready_to_depart'],
        ),
    ]
    if avoided_returns > 0:
        current_lines.append(CostLine(
            'avoided-return-counterfactual', 'avoidable_return', 'readmission',
            format(avoided_returns.normalize(), 'f'), return_price, ['post_icu_readmission'],
        ))
    liaison_lines = [CostLine(
        'additional-liaison-service', 'liaison_staffing', 'service_year',
        '1', service_price, ['incremental_service'],
    )]
    if avoided_returns < 0:
        liaison_lines.append(CostLine(
            'additional-early-return', 'additional_return', 'readmission',
            format((-avoided_returns).normalize(), 'f'), return_price, ['post_icu_readmission'],
        ))
    return {
        'current_care': make_request(f'{checked.scenario_id}-current', current_lines, price_year=price_year, perspective=perspective, basis=basis),
        'liaison_service': make_request(f'{checked.scenario_id}-liaison', liaison_lines, price_year=price_year, perspective=perspective, basis=basis),
    }


def _admit_valuation_report(report: dict[str, Any], request: dict[str, Any]) -> Decimal:
    """Check the exact Dapane 0.1 output envelope before using its rounded total.

    These checks are a narrow consumer gate, not a replacement for the provider's
    JSON Schema, conservation or independently qualified numerical kernel.
    """
    if not isinstance(report, dict):
        raise ValueError('Dapane report must be an object')
    for key, expected in (
        ('schema_version', '0.1'),
        ('status', 'complete'),
        ('method_version', 'dapane-exact-v0.1.0'),
        ('run_id', request['run_id']),
    ):
        if report.get(key) != expected:
            raise ValueError(f'Dapane report {key} does not match the requested contract')
    policy = report.get('policy')
    if not isinstance(policy, dict) or any(
        policy.get(key) != request['policy'][key]
        for key in ('currency', 'price_year', 'basis', 'perspective')
    ):
        raise ValueError('Dapane report policy is incompatible with its request')
    if not isinstance(report.get('totals'), dict):
        raise ValueError('Dapane report is missing totals')
    rounded = report['totals'].get('rounded')
    if not isinstance(rounded, str):
        raise ValueError('Dapane rounded amount must be an exact decimal string')
    try:
        value = Decimal(rounded)
    except InvalidOperation as exc:
        raise ValueError('Dapane total is not a decimal') from exc
    if not value.is_finite() or value < 0 or value != value.quantize(Decimal('0.01')):
        raise ValueError('Dapane total is not a valid nonnegative AUD cents amount')
    return value


def compare_valued_scenarios(
    requests: dict[str, dict[str, Any]], *, provider: ValuationProvider | None = None,
) -> dict[str, Any]:
    """Value the same two strategies independently with Dapane; subtract only.

    All value *generation* is delegated to Dapane. Injected providers exist for
    boundary tests and are explicitly marked as non-native observations.
    """
    if set(requests) != {'current_care', 'liaison_service'}:
        raise ValueError('Both named counterfactual ledgers are required')
    current, liaison = requests['current_care'], requests['liaison_service']
    if current['policy'] != liaison['policy']:
        raise ValueError('Costing basis, currency, date and perspective must match')
    from copy import deepcopy
    expected_current, expected_liaison = deepcopy(current), deepcopy(liaison)
    current_report = evaluate_request(current, provider=provider)
    liaison_report = evaluate_request(liaison, provider=provider)
    cost_current = _admit_valuation_report(current_report, expected_current)
    cost_liaison = _admit_valuation_report(liaison_report, expected_liaison)
    return {
        'avoidable_current_care_slice_aud': format(cost_current, '.2f'),
        'additional_liaison_slice_aud': format(cost_liaison, '.2f'),
        'incremental_resource_benefit_aud': format(cost_current - cost_liaison, '.2f'),
        'basis': current['policy']['basis'],
        'perspective': current['policy']['perspective'],
        'price_year': current['policy']['price_year'],
        'currency': current['policy']['currency'],
        'method_version': 'dapane-exact-v0.1.0',
        'provider_evidence': 'native_provider_executed' if provider is None else 'injected_contract_test_only',
        'interpretation': 'incremental_resource_bridge_not_full_hospital_cost',
    }
