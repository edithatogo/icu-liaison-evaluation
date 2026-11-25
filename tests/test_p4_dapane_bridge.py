"""P4 Dapane consumer tests: exact nonnegative resource requests and no fake native results."""
from typing import Any
import copy
from decimal import Decimal
import json
from pathlib import Path
import pytest

from icu_liaison.p4_model import EconomicScenario
from icu_liaison.adapters.p4_dapane import (make_p4_nominal_requests,
                                             evaluate_p4_nominal_valuation)

FIXTURE=Path(__file__).resolve().parents[1]/'model-inputs/p4/illustrative.json'

def sample() -> dict[str, Any]:
    value = json.loads(FIXTURE.read_text())
    assert isinstance(value, dict)
    return value

def fixed(value: float,unit: str) -> dict[str, Any]:return {'family':'fixed','params':{'value':value},'unit':unit,'evidence_status':'illustrative_assumption','source_ref':'TEST'}

def ledger_total(request: dict[str, Any] | None) -> Decimal:
    if request is None: return Decimal(0)
    quotes={q['id']:Decimal(q['amount'])/Decimal(q['per_quantity']) for q in request['quotes']}
    return sum((Decimal(x['quantity'])*quotes[x['quote_id']] for x in request['usage']),Decimal(0))


def test_nonnegative_distinct_cost_components_and_price_year() -> None:
    bridge=make_p4_nominal_requests(EconomicScenario.model_validate(sample()),'liaison_service')
    current,liaison=bridge['current_care'],bridge['liaison_service']
    assert current is not None and liaison is not None
    assert current['policy']['currency']=='AUD'
    assert current['policy']['price_year']==2026
    assert current['policy']['basis']=='economic_cost'
    assert liaison['policy']==current['policy']
    assert all(Decimal(u['quantity'])>=0 for req in (current,liaison) for u in req['usage'])
    assert {x['components'][0] for x in current['quotes']} == {'index_ready_to_depart','post_icu_readmission'}
    assert {x['components'][0] for x in liaison['quotes']} == {'incremental_service'}
    assert ledger_total(current)-ledger_total(liaison)==Decimal('-168730.000')


def test_more_returns_generate_positive_intervention_resource_use_not_negative_current_use() -> None:
    z=sample();z['strategies'][1]['relative_return_effect']=fixed(-.2,'signed_proportion')
    b=make_p4_nominal_requests(EconomicScenario.model_validate(z),'liaison_service')
    assert b['current_care'] is not None and b['liaison_service'] is not None
    assert 'post_icu_readmission' not in [y for q in b['current_care']['quotes'] for y in q['components']]
    assert 'post_icu_readmission' in [y for q in b['liaison_service']['quotes'] for y in q['components']]
    assert all(Decimal(u['quantity'])>=0 for u in b['liaison_service']['usage'])


def test_null_counterfactual_resource_lines_are_not_invented() -> None:
    z=sample();s=z['strategies'][1]
    s['delay_success_fraction']=fixed(0,'proportion')
    s['relative_return_effect']=fixed(0,'signed_proportion')
    z['dependence_groups']=[]
    b=make_p4_nominal_requests(EconomicScenario.model_validate(z),'liaison_service')
    assert b['current_care'] is None
    assert b['liaison_service'] is not None


def test_injection_is_contract_only_and_never_claims_native_dapane() -> None:
    b=make_p4_nominal_requests(EconomicScenario.model_validate(sample()),'liaison_service')
    def provider(req: dict[str, Any]) -> dict[str, Any]:
        total=ledger_total(req).quantize(Decimal('0.01'))
        return {'schema_version':'0.1','run_id':req['run_id'],'status':'complete',
                'method_version':'dapane-exact-v0.1.0','policy':req['policy'],
                'totals':{'rounded':str(total)}}
    out=evaluate_p4_nominal_valuation(b,provider=provider)
    assert out['incremental_resource_benefit_aud']=='-168730.00'
    assert out['provider_evidence']=='injected_contract_test_only'


def test_dapane_invalid_return_is_rejected() -> None:
    b=make_p4_nominal_requests(EconomicScenario.model_validate(sample()),'liaison_service')
    with pytest.raises(ValueError):
        evaluate_p4_nominal_valuation(b,provider=lambda req:{'status':'complete','totals':{'rounded':'0.00'}})


def test_unknown_or_comparator_strategy_cannot_be_costed_as_intervention() -> None:
    s=EconomicScenario.model_validate(sample())
    for arm in ('current_care','not_a_strategy'):
        with pytest.raises(ValueError):make_p4_nominal_requests(s,arm)


def test_service_with_no_additional_cost_does_not_create_ghost_usage() -> None:
    z=sample();z['strategies'][1]['annual_incremental_cost_aud']=fixed(0,'AUD_per_year')
    b=make_p4_nominal_requests(EconomicScenario.model_validate(z),'liaison_service')
    assert b['liaison_service'] is None
