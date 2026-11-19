"""P5 Dapane: RED tests for actual opt-in valuation and fail-closed publication."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN
import json
from pathlib import Path
import subprocess
import sys

import pytest

from icu_liaison.p4_model import EconomicScenario
from icu_liaison.p5_reporting import build_report, verify_manifest

ROOT = Path(__file__).resolve().parents[1]


def scenario() -> EconomicScenario:
    return EconomicScenario.model_validate_json(
        (ROOT / 'model-inputs/p4/illustrative.json').read_text(encoding='utf-8')
    )


def exact_reference_provider(request: dict) -> dict:
    quotes = {
        q['id']: Decimal(q['amount']) / Decimal(q['per_quantity'])
        for q in request['quotes']
    }
    total = sum(
        (Decimal(u['quantity']) * quotes[u['quote_id']] for u in request['usage']),
        Decimal(0),
    ).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
    return {
        'schema_version': '0.1',
        'run_id': request['run_id'],
        'status': 'complete',
        'method_version': 'dapane-exact-v0.1.0',
        'policy': request['policy'],
        'totals': {'rounded': format(total, '.2f')},
    }


def test_provider_mode_emits_qualified_narrow_nominal_reconciliation(tmp_path):
    target = tmp_path / 'p5'
    build_report(scenario(), target, dapane_mode='provider', dapane_provider=exact_reference_provider)
    assert verify_manifest(target)
    result = json.loads((target / 'dapane-nominal-valuation.json').read_text())
    assert result['liaison_service']['incremental_resource_benefit_aud'] == '-168730.00'
    assert result['liaison_service']['provider_evidence'] == 'injected_contract_test_only'
    model = json.loads((target / 'model-summary.json').read_text())
    assert model['dapane_valuation']['status'] == 'injected_contract_test_only'
    assert model['dapane_valuation']['all_strategies_reconciled'] is True
    assert model['investment_ready'] is False


def test_p5_refuses_incorrect_provider_arithmetic_before_publication(tmp_path):
    target = tmp_path / 'should-not-exist'
    def faulty(request: dict) -> dict:
        report = exact_reference_provider(request)
        report['totals']['rounded'] = '0.00'
        return report
    with pytest.raises(ValueError, match='reconcil'):
        build_report(scenario(), target, dapane_mode='provider', dapane_provider=faulty)
    assert not target.exists()


def test_p5_no_implicit_provider_and_bad_mode_rejected(tmp_path):
    build_report(scenario(), tmp_path / 'default')
    model = json.loads((tmp_path / 'default/model-summary.json').read_text())
    assert model['dapane_valuation']['status'] == 'not_executed'
    assert not (tmp_path / 'default/dapane-nominal-valuation.json').exists()
    with pytest.raises(ValueError, match='requires'):
        build_report(scenario(), tmp_path / 'bad', dapane_provider=exact_reference_provider)
    assert not (tmp_path / 'bad').exists()


def test_p5_real_provider_missing_fails_closed_without_directory(tmp_path):
    target = tmp_path / 'missing'
    with pytest.raises(RuntimeError, match='Dapane'):
        build_report(scenario(), target, dapane_mode='provider')
    assert not target.exists()


def test_p5_cli_dapane_required_is_fail_closed(tmp_path):
    target = tmp_path / 'missing'
    result = subprocess.run(
        [sys.executable, '-m', 'icu_liaison.p5_cli',
         str(ROOT / 'model-inputs/p4/illustrative.json'),
         '--output-dir', str(target), '--dapane'],
        cwd=ROOT, env={'PYTHONPATH': str(ROOT / 'src')},
        capture_output=True, text=True,
    )
    assert result.returncode == 2
    assert not target.exists()
    assert 'UNVERIFIED' in result.stderr
