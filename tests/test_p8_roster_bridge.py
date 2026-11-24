"""Roster input and provider transport: no salary/award formulas in this project."""
from __future__ import annotations

import copy
from datetime import date
from decimal import Decimal
import json
import pytest

from icu_liaison.adapters.p8_workforce import RosterScenario, prepare_workforce_dapane_request


def use_record(**changes):
    return {'id': 'synthetic-1-base', 'quote_id': 'nursing-base-hour', 'unit': 'hour',
            'service_date': '2026-09-12', 'quantity': '8', 'source': {'evidence': 'synthetic'},
            **changes}



def shift(**changes):
    a = {'quantity_id':'synthetic-1-base', 'shift_id':'shift1',
        'quote_id':'nursing-base-hour', 'unit':'hour', 'quantity':'8',
        'kind':'analyst_assumption','component':'base_salary',
        'segment_start':'2026-09-12T07:00:00+10:00',
        'segment_end':'2026-09-12T15:00:00+10:00',
        'valued_on':'2026-09-12'}
    a.update(changes)
    return a


def example(lines=None, **changes):
    raw = {'schema_version':1, 'data_class':'synthetic',
        'scenario_id':'synthetic-nurse-roster',
        'jurisdiction':'Queensland',
        'classification':'candidate-clinical-nurse-grade-6',
        'classification_status':'candidate_unverified',
        'expected_artifact_sha256':'b'*64,
        'source_artifact_json': json.dumps({'release_snapshot': {
            'classification': 'candidate-clinical-nurse-grade-6', 'jurisdiction': 'QLD',
        }}),
        'financial_price_year':2026,
        'knowledge_cutoff':'2026-11-18',
        'exposures': lines if lines is not None else [shift()],
        'contains_superannuation': False,
        'contains_leave_relief': False,
        'contains_penalties': False,
        'completeness_status':'partial',
    }
    raw.update(changes)
    return RosterScenario.model_validate(raw)


def test_uses_provider_existing_quantities_and_dapane_builder_without_price_math():
    args=[]
    class FakeQuantity:
        def __init__(self, **kw): self.kw=kw
    def builder(artifact_json,quantities,*,expected_sha256,run_id,knowledge_cutoff):
        args.append((artifact_json, quantities,expected_sha256,run_id,knowledge_cutoff))
        return {'schema_version':'0.1','policy':{'basis':'financial_cost','currency':'AUD','price_year':2026}, 'quotes':[{'id':'nursing-base-hour','unit':'hour','basis':'financial_cost','components':['base_salary']}],'usage':[use_record()], 'run_id':run_id}
    res=prepare_workforce_dapane_request(example(),builder=builder,quantity_type=FakeQuantity)
    assert res['provider_evidence']=='injected_contract_test_only'
    assert res['financial_cost_status']=='not_valued'
    assert res['request']['policy']['basis']=='financial_cost'
    assert res['request']['policy']['price_year']==2026
    assert args[0][2]=='b'*64
    assert args[0][1][0].kw['quantity']==Decimal('8')
    assert args[0][1][0].kw['valued_on']==date(2026,9,12)
    assert args[0][1][0].kw['quantity_kind']=='analyst_assumption'
    assert res['annual_workforce_cost_aud'] is None


@pytest.mark.parametrize('changes',[
  {'quantity': '-1'}, {'quantity': 'NaN'}, {'quantity': 8.0},
  {'unit':''}, {'component':''}, {'kind':'observed_use'},
  {'segment_end':'2026-09-12T06:00:00+10:00'},
  {'segment_end':'2026-09-12T15:00:00'},
  {'valued_on':'2026-09-13'},
])
def test_reject_bad_shift_quantities_dates_and_units(changes):
    with pytest.raises((ValueError, TypeError)):
        example([shift(**changes)])


def test_reject_duplicate_cost_component_for_same_time_and_shift():
    with pytest.raises(ValueError,match='overlap'):
        example([shift(),shift(quantity_id='synthetic-2-base',quote_id='duplicate-base')])


def test_allows_penalty_layer_with_distinct_component_but_does_not_infer_entitlement():
    v=example([shift(),shift(quantity_id='synthetic-2-night',component='night_penalty',quote_id='nursing-night-hour',quantity='3')])
    assert len(v.exposures)==2
    assert v.classification_status=='candidate_unverified'


def test_reject_roster_that_claims_full_conditions_when_incomplete():
    with pytest.raises(ValueError,match='completeness'):
        example(completeness_status='full',contains_superannuation=False)


def test_requires_release_source_digest_and_does_not_accept_local_claims():
    for change in ({'expected_artifact_sha256':'fake'}, {'data_class':'patient_records'},
                   {'classification_status':'chhhs_hr_approved'},
                   {'source_artifact_json':''}, {'jurisdiction':'SA'}):
        with pytest.raises((ValueError, TypeError)):
            example(**change)


def test_missing_workforce_package_fails_closed(monkeypatch):
    import icu_liaison.adapters.p8_workforce as adapter
    monkeypatch.setattr(adapter,'import_module',lambda _: (_ for _ in ()).throw(ImportError()))
    with pytest.raises(RuntimeError,match='workforce.*not installed'):
        prepare_workforce_dapane_request(example())


def test_reject_dapane_financial_policy_mismatch():
    def wrong(*a,**kw):
        return {'schema_version':'0.1','run_id':'synthetic-nurse-roster','policy':{'basis':'economic_cost','currency':'AUD','price_year':2026},'quotes':[],'usage':[]}
    with pytest.raises(ValueError, match='financial_cost'):
        prepare_workforce_dapane_request(example(),builder=wrong,quantity_type=lambda **kw:kw)


def test_injected_builder_must_not_drop_use_or_change_component():
    ok = lambda quote: {
        'schema_version':'0.1','run_id':'synthetic-nurse-roster',
        'policy':{'basis':'financial_cost','currency':'AUD','price_year':2026},
        'quotes':[quote],
        'usage':[use_record()],
    }
    fake_quote={'id':'nursing-base-hour','basis':'financial_cost','components':['base_salary']}
    with pytest.raises(ValueError,match='component'):
        prepare_workforce_dapane_request(example(),builder=lambda *a,**k:ok({**fake_quote,'components':['loaded_salary']}),quantity_type=lambda **k:k)
    with pytest.raises(ValueError,match='omitted'):
        prepare_workforce_dapane_request(example(),builder=lambda *a,**k:ok({**fake_quote,'id':'other'}),quantity_type=lambda **k:k)
    with pytest.raises(ValueError,match='lost'):
        prepare_workforce_dapane_request(example(),builder=lambda *a,**k:{**ok(fake_quote),'usage':[]},quantity_type=lambda **k:k)
    with pytest.raises(ValueError,match='identity'):
        prepare_workforce_dapane_request(example(),builder=lambda *a,**k:{**ok(fake_quote),'run_id':'wrong'},quantity_type=lambda **k:k)


@pytest.mark.parametrize('changes, error', [
    ({'quantity': '7.99'}, 'quantity'),
    ({'quantity': 8.0}, 'exact decimal'),
    ({'source': {'evidence': 'observed'}}, 'synthetic exposure'),
])
def test_bridge_preserves_exact_quantity_and_synthetic_evidence(changes, error):
    def returned_request(*_args, **kwargs):
        return {
            'schema_version': '0.1', 'run_id': kwargs['run_id'],
            'policy': {'basis': 'financial_cost', 'currency': 'AUD', 'price_year': 2026},
            'quotes': [{'id': 'nursing-base-hour', 'basis': 'financial_cost', 'components': ['base_salary']}],
            'usage': [use_record(**changes)],
        }

    with pytest.raises(ValueError, match=error):
        prepare_workforce_dapane_request(example(), builder=returned_request, quantity_type=lambda **kw: kw)


def test_bridge_cannot_use_health_practitioner_quotes_for_a_nursing_roster():
    roster = example(source_artifact_json=json.dumps({'release_snapshot': {
        'classification': 'HP3', 'jurisdiction': 'QLD',
    }}))
    with pytest.raises(ValueError, match='classification'):
        prepare_workforce_dapane_request(roster, builder=lambda *a, **k: {}, quantity_type=lambda **kw: kw)


def test_requires_explicit_segmentation_at_fiscal_year_boundary():
    # Pricing-year here is a single annual quotation basis, not a payroll calendar.
    with pytest.raises(ValueError, match='price-year boundary'):
        example([shift(segment_start='2026-12-31T23:00:00+10:00',segment_end='2027-01-01T07:00:00+10:00',valued_on='2026-12-31')])
