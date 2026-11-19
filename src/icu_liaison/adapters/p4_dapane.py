"""P4 multi-strategy *consumer* of Dapane's exact 0.1 valuation contract.

Only construct separately nonnegative incremental resource-use ledgers here.
Dapane owns quotation arithmetic and half-even rounding. There is no fallback
provider, and an injected unit-test fake never establishes native qualification.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Callable

from .dapane import CostLine, _admit_valuation_report, evaluate_request, make_request
from ..p4_model import EconomicScenario


def _nominal(p) -> Decimal:
    """Retain user-written decimal modes/medians and exact beta mean ratios."""
    v = p.params
    if p.family == 'fixed':
        return Decimal(str(v['value']))
    if p.family == 'triangular':
        return Decimal(str(v['mode']))
    if p.family == 'lognormal':
        return Decimal(str(v['median']))
    return Decimal(str(v['alpha'])) / (Decimal(str(v['alpha'])) + Decimal(str(v['beta'])))


def _number(value: Decimal) -> str:
    return format(value, 'f')


def make_p4_nominal_requests(scenario: EconomicScenario, strategy_id: str) -> dict[str, dict | None]:
    """Build incremental current-care and proposed-care ledgers for one arm.

    A wholly empty source-use side returns None. We do not fabricate a zero-use
    line solely to satisfy Dapane's deliberately nonempty request contract.
    Results are modal/median counterfactuals, not complete hospital costs.
    """
    s = EconomicScenario.model_validate(scenario.model_dump(mode='json'))
    eligible = [x for x in s.strategies if x.id == strategy_id and x.role == 'proposed']
    if not eligible:
        raise ValueError('requested strategy must be a declared intervention')
    arm = eligible[0]
    p = lambda obj, key: _nominal(getattr(obj, key))
    n = Decimal(s.annual_eligible_discharges)
    coverage = p(arm, 'coverage_fraction')
    delay_days = (
        n * p(s.baseline, 'exit_block_rate')
        * p(s.resource, 'addressable_delay_fraction')
        * coverage * p(arm, 'delay_success_fraction')
        * p(s.resource, 'hours_released_per_improved_case') / Decimal(24)
    )
    baseline_risk = p(s.baseline, 'unplanned_72h_return_rate')
    return_risk = ((Decimal(1)-coverage) * baseline_risk
                   + coverage * max(Decimal(0), min(Decimal(1), baseline_risk * (1-p(arm,'relative_return_effect')))))
    returns_avoided = n * (baseline_risk-return_risk)
    day_price = _number(p(s.resource, 'net_index_delay_cost_aud_per_day'))
    return_price = _number(p(s.resource, 'incremental_return_cost_aud_per_return'))
    annual_service = p(arm, 'annual_incremental_cost_aud')
    current: list[CostLine] = []
    proposed: list[CostLine] = []
    if delay_days > 0:
        current.append(CostLine(
            f'{strategy_id}-avoidable-index-delay', 'index_ready_to_departure',
            'icu_day', _number(delay_days), day_price, ['index_ready_to_depart'],
        ))
    if returns_avoided > 0:
        current.append(CostLine(
            f'{strategy_id}-avoided-returns', 'post_icu_unplanned_return',
            'return', _number(returns_avoided), return_price, ['post_icu_readmission'],
        ))
    if annual_service > 0:
        proposed.append(CostLine(
            f'{strategy_id}-added-liaison-service', 'liaison_workforce_and_operations',
            'service_year', '1', _number(annual_service), ['incremental_service'],
        ))
    if returns_avoided < 0:
        proposed.append(CostLine(
            f'{strategy_id}-additional-returns', 'post_icu_unplanned_return',
            'return', _number(-returns_avoided), return_price, ['post_icu_readmission'],
        ))
    opts = {'price_year':s.price_year, 'perspective':'provider', 'basis':'economic_cost'}
    return {
        'current_care': make_request(f'{s.scenario_id}-{strategy_id}-counterfactual-current', current, **opts)
        if current else None,
        'liaison_service': make_request(f'{s.scenario_id}-{strategy_id}-counterfactual-proposed', proposed, **opts)
        if proposed else None,
    }


def evaluate_p4_nominal_valuation(requests: dict[str, dict | None], *, provider: Callable | None = None) -> dict:
    """Use actual Dapane, or an explicitly identified boundary-test stub.

    Optional empty sides mean zero declared incremental resource use, not a
    synthetic Dapane report. A missing installed provider is a blocking error
    whenever a nonempty ledger requires valuation.
    """
    if set(requests) != {'current_care', 'liaison_service'}:
        raise ValueError('expected two distinct incremental resource ledgers')
    policies = [r['policy'] for r in requests.values() if r is not None]
    if any(p != policies[0] for p in policies[1:]):
        raise ValueError('Dapane policy mismatch between counterfactuals')
    outputs = {}
    for name in ('current_care', 'liaison_service'):
        req = requests[name]
        if req is None:
            outputs[name] = Decimal('0.00')
        else:
            report = evaluate_request(req, provider=provider)
            outputs[name] = _admit_valuation_report(report, req)
    diff = outputs['current_care'] - outputs['liaison_service']
    return {
        'avoidable_current_care_slice_aud':format(outputs['current_care'], '.2f'),
        'added_proposed_care_slice_aud':format(outputs['liaison_service'], '.2f'),
        'incremental_resource_benefit_aud':format(diff, '.2f'),
        'provider_evidence':'injected_contract_test_only' if provider is not None else (
            'native_provider_executed' if any(req is not None for req in requests.values()) else
            'no_provider_call_no_resource_use'),
        'interpretation':'modal_incremental_resource_cost_only_not_full_hospital_budget',
        'clinical_approval':False,
    }
