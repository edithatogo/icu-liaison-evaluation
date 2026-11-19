"""Provider boundaries are checked without claiming installed provider acceptance."""
from pathlib import Path
import json
import numpy as np
import pytest
from icu_liaison.schemas import Scenario
from icu_liaison.model import simulate
from icu_liaison.adapters.voiage import financial_decision_array, make_voiage_analysis
from icu_liaison.adapters.dapane import CostLine, make_request, evaluate_request

F = Path(__file__).resolve().parents[1] / 'model-inputs' / 'illustrative.json'


def test_voiage_decision_strategies_retain_aud_label():
    draws = simulate(Scenario.model_validate_json(F.read_text()))
    values, labels = financial_decision_array(draws)
    assert labels == ['current_care', 'liaison_service']
    assert values.shape == (5000, 2)
    assert np.all(values[:,0] == 0)
    assert np.array_equal(values[:,1], draws.net_resource_benefit_aud)


def test_voiage_adapter_passes_real_contract_to_injected_factories():
    class FakeValueArray:
        @staticmethod
        def from_numpy(values, labels):
            assert values.shape[1] == 2
            assert labels[1] == 'liaison_service'
            return 'value-array'
    def factory(value_array):
        assert value_array == 'value-array'
        return 'analysis-instance'
    assert make_voiage_analysis(simulate(Scenario.model_validate_json(F.read_text())), value_array_factory=FakeValueArray.from_numpy, analysis_factory=factory) == 'analysis-instance'


def test_dapane_builds_exact_nonnegative_cost_requests_without_evaluating():
    lines = [
        CostLine('icu-delay', 'index_icu_delay', 'icu_day', '12.25', '1800.00', ['staffing', 'consumables']),
        CostLine('liaison-workforce', 'liaison_service', 'service_year', '1', '250000.00', ['salary', 'oncost'])
    ]
    req = make_request('synthetic-baseline', lines)
    assert req['schema_version'] == '0.1'
    assert req['policy']['currency'] == 'AUD'
    assert req['policy']['basis'] == 'economic_cost'
    assert req['quotes'][0]['amount'] == '1800.00'
    assert req['usage'][0]['quantity'] == '12.25'
    assert req['usage'][1]['quantity'] == '1'
    assert req['quotes'][0]['components'] == ['staffing', 'consumables']


def test_dapane_negative_or_duplicate_use_is_rejected():
    x = CostLine('a', 'icu_delay', 'day', '-1', '100', ['salary'])
    with pytest.raises(ValueError): make_request('test', [x])
    x = CostLine('a', 'icu_delay', 'day', '1', '100', ['salary'])
    with pytest.raises(ValueError): make_request('test', [x, x])


def test_dapane_never_silently_uses_fallback_valuation():
    req = make_request('test', [CostLine('one', 'icu_delay', 'day', '1','100', ['staff'])])
    captured=[]
    def fake_provider(request):
        captured.append(request)
        return {'totals':{'rounded':'100.00'}}
    assert evaluate_request(req, provider=fake_provider)['totals']['rounded'] == '100.00'
    assert captured == [req]


def test_currency_price_year_and_economic_basis_can_be_overridden():
    lines=[CostLine('one','icu_delay','day','2','100',['staff'])]
    req=make_request('test', lines, price_year=2027, basis='financial_cost')
    assert req['policy']['price_year'] == 2027
    assert req['policy']['basis'] == 'financial_cost'
    assert req['quotes'][0]['basis'] == 'financial_cost'
