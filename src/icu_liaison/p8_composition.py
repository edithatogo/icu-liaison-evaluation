"""P8.4: Compose *source-only* views without changing P4/P5 numerical results.

This is a typed audit sidecar, not an ABF calculator, nursing payroll engine,
resource valuator, or Voiage decision method. MCHS computes activity; workforce
and Dapane own source prices; P4 owns illustrative cohort accounting.
Every non-financially qualified producer remains a shadow, not an expense or
revenue used in a model draw. In particular, prospective staffing costs must
REPLACE the appropriate P4 prior component after reconciliation, not be added.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
import re
from typing import Any, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .p4_model import P4Run, summarise_p4


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class MchsShadow(_Strict):
    scope: Literal['one_synthetic_episode_not_programme_total']
    status: Literal['unavailable', 'unqualified_annual_calculation']
    episode_id: str | None = None
    pricing_year: int | None = None
    drg_edition: str | None = None
    source_bundle_sha256_declared: str | None = None
    case_change_nwau: str | None = None
    annual_calculator_parity: Literal['unverified'] = 'unverified'
    actual_revenue_aud: None = None


class WorkforceShadow(_Strict):
    financial_cost_status: Literal['unavailable', 'not_valued']
    roster_scenario_id: str | None = None
    financial_price_year: int | None = None
    source_evidence: str | None = None
    request_line_count: int | None = None
    annual_labour_cost_aud: None = None
    reconciliation_to_p4_cost_prior: Literal['not_reconciled'] = 'not_reconciled'


class P8Composition(_Strict):
    schema_version: Literal[1] = 1
    data_class: Literal['synthetic'] = 'synthetic'
    admission: Literal['planning_only'] = 'planning_only'
    scenario_id: str
    strategy_id: str
    p4_input_sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    p4_price_year: int
    modelled_financial_basis: Literal['illustrative_P4_uncalibrated'] = 'illustrative_P4_uncalibrated'
    p4_annual_incremental_service_cost_prior_aud_nominal: float
    p4_illustrative_net_resource_benefit_aud_mean: float
    p4_illustrative_net_budget_impact_aud_mean: float
    mchs: MchsShadow
    workforce: WorkforceShadow
    net_modelled_nwau_aud: None = None
    actual_hospital_revenue_change_aud: None = None
    extra_workforce_cost_applied_to_p4: Literal[False] = False
    clinical_investment_approval: Literal[False] = False
    finance_authorisation: Literal[False] = False


def _exact_decimal(text: Any, name: str, *, nonnegative: bool = False) -> Decimal:
    if type(text) is not str or not re.fullmatch(r'-?(0|[1-9][0-9]*)(\.[0-9]+)?', text):
        raise ValueError(f'{name} requires exact finite decimal text')
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f'{name} is not a decimal') from exc
    if not value.is_finite() or (nonnegative and value < 0) or len(value.as_tuple().digits) > 96:
        raise ValueError(f'{name} is unsupported')
    return value


def _admit_mchs(result: Mapping[str, Any] | None) -> MchsShadow:
    if result is None:
        return MchsShadow(scope='one_synthetic_episode_not_programme_total',status='unavailable')
    required = {
        'schema_version', 'episode_id', 'data_class', 'provider', 'pricing_year',
        'drg_edition', 'source_bundle_id', 'source_bundle_sha256_declared',
        'unit', 'current_nwau', 'proposed_nwau', 'change_nwau',
        'actual_revenue_aud', 'technical_modelled_aud', 'execution_evidence',
        'annual_calculator_parity', 'clinical_case_mix_qualification',
    }
    if set(result) != required:
        raise ValueError('MCHS result does not match the admitted exact source contract')
    if (result['schema_version'] != 1 or result['data_class'] != 'synthetic'
        or result['provider'] != 'mchs' or result['unit'] != 'NWAU'
        or result['pricing_year'] not in (2024,2025)
        or result['drg_edition'] != 'v11.0'
        or result['actual_revenue_aud'] is not None or result['technical_modelled_aud'] is not None
        or result['annual_calculator_parity'] != 'unverified'
        or result['clinical_case_mix_qualification'] != 'not_established'
        or result['execution_evidence'] not in ('injected_contract_test_only','installed_source_unqualified')):
        raise ValueError('MCHS unqualified output improperly promotes funding or evidence')
    if (not isinstance(result['episode_id'],str)
        or not re.fullmatch(r'synthetic-[a-zA-Z0-9_-]{1,117}',result['episode_id'])
        or not isinstance(result['source_bundle_id'],str)
        or not result['source_bundle_id'].strip()
        or not isinstance(result['source_bundle_sha256_declared'],str)
        or not re.fullmatch('[a-f0-9]{64}',result['source_bundle_sha256_declared'])):
        raise ValueError('MCHS source/episode identity invalid')
    current = _exact_decimal(result['current_nwau'],'current NWAU',nonnegative=True)
    proposed = _exact_decimal(result['proposed_nwau'],'proposed NWAU',nonnegative=True)
    change = _exact_decimal(result['change_nwau'],'change NWAU')
    if proposed - current != change:
        raise ValueError('MCHS NWAU change is inconsistent with annual outputs')
    return MchsShadow(
        scope='one_synthetic_episode_not_programme_total',
        status='unqualified_annual_calculation',
        episode_id=result['episode_id'],
        pricing_year=result['pricing_year'],
        drg_edition=result['drg_edition'],
        source_bundle_sha256_declared=result['source_bundle_sha256_declared'],
        case_change_nwau=result['change_nwau'],
    )


def _admit_workforce(
    result: Mapping[str, Any] | None,
    expected_scenario: str | None,
    p4_price_year: int,
) -> WorkforceShadow:
    if result is None:
        if expected_scenario is not None:
            raise ValueError('roster scenario selected without a returned provider request')
        return WorkforceShadow(financial_cost_status='unavailable')
    if not isinstance(expected_scenario,str) or not expected_scenario.strip():
        raise ValueError('workforce request requires an independent scenario identity')
    if set(result) != {
        'provider_evidence','scenario_id','financial_cost_status',
        'annual_workforce_cost_aud','classification_eligibility',
        'roster_completeness','request'
    }:
        raise ValueError('workforce output does not match bounded consumer contract')
    if (result['scenario_id'] != expected_scenario or result['financial_cost_status'] != 'not_valued'
        or result['annual_workforce_cost_aud'] is not None
        or result['classification_eligibility'] != 'unverified'
        or result['roster_completeness'] not in ('partial','full')
        or result['provider_evidence'] not in ('injected_contract_test_only','unqualified_installed_workforce_source')):
        raise ValueError('workforce output improperly claims validated expenditure or source')
    request=result['request']
    if not isinstance(request,dict) or request.get('schema_version') != '0.1' or request.get('run_id') != expected_scenario:
        raise ValueError('workforce Dapane source request mismatch')
    policy=request.get('policy')
    if (not isinstance(policy,dict) or policy.get('basis') != 'financial_cost'
        or policy.get('currency') != 'AUD' or policy.get('price_year') != p4_price_year):
        raise ValueError('workforce Dapane request has incompatible financial cost policy')
    quotes=request.get('quotes'); usage=request.get('usage')
    if not isinstance(quotes,list) or not isinstance(usage,list) or not quotes or not usage:
        raise ValueError('workforce Dapane request requires nonempty quote and usage lists')
    if any(not isinstance(q,dict) or not isinstance(q.get('id'),str) for q in quotes):
        raise ValueError('workforce quote identity missing')
    if any(not isinstance(u,dict) or not isinstance(u.get('id'),str) for u in usage):
        raise ValueError('workforce usage identity missing')
    quote_ids={q['id'] for q in quotes}
    use_ids={u['id'] for u in usage}
    if len(quote_ids)!=len(quotes) or len(use_ids)!=len(usage):
        raise ValueError('duplicate workforce quote or use identity')
    for quote in quotes:
        if (quote.get('basis')!='financial_cost' or quote.get('currency')!='AUD'
            or quote.get('price_year') != p4_price_year
            or not isinstance(quote.get('components'),list) or not quote['components']):
            raise ValueError('workforce quote has incompatible financial-cost basis')
    for use in usage:
        quote=next((q for q in quotes if q['id']==use.get('quote_id')), None)
        if quote is None or use.get('unit') != quote.get('unit'):
            raise ValueError('workforce use is missing source-bound same-unit quotation')
    return WorkforceShadow(
        financial_cost_status='not_valued',
        roster_scenario_id=expected_scenario,
        financial_price_year=p4_price_year,
        source_evidence=result['provider_evidence'],
        request_line_count=len(usage),
    )


def compose_p8_shadow(
    run: P4Run,
    *,
    strategy_id: str,
    mchs_result: Mapping[str, Any] | None = None,
    workforce_result: Mapping[str, Any] | None = None,
    expected_roster_scenario_id: str | None = None,
) -> dict[str, Any]:
    """Attach source-only context to one strategy without changing financial draws.

    Funding remains an isolated, single-episode NWAU shadow. Workforce transport
    does not establish expense; a fully valued and workforce-scope-qualified
    replacement must enter P4's cost prior only after separate reconciliation.
    """
    if strategy_id == 'current_care' or strategy_id not in run.strategies:
        raise ValueError('P8 composition requires an existing proposed strategy')
    if run.scenario.data_class != 'synthetic':
        raise ValueError('P8 composition supports synthetic-source data only')
    mchs=_admit_mchs(mchs_result)
    workforce=_admit_workforce(workforce_result,expected_roster_scenario_id,run.scenario.price_year)
    summary=summarise_p4(run)['strategies'][strategy_id]
    arm=next(a for a in run.scenario.strategies if a.id == strategy_id)
    out=P8Composition(
        scenario_id=run.scenario.scenario_id,
        strategy_id=strategy_id,
        p4_input_sha256=run.input_digest_sha256,
        p4_price_year=run.scenario.price_year,
        p4_annual_incremental_service_cost_prior_aud_nominal=arm.annual_incremental_cost_aud.nominal(),
        p4_illustrative_net_resource_benefit_aud_mean=summary['net_resource_benefit_aud']['mean'],
        p4_illustrative_net_budget_impact_aud_mean=summary['net_budget_impact_aud']['mean'],
        mchs=mchs,
        workforce=workforce,
    )
    return out.model_dump(mode='json')
