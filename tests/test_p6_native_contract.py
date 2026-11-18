"""Native Kairos adapter tests: contract/independent oracle, not binary execution."""
import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from icu_liaison.p6_native import (
    KairosScenario, KairosProducerOutput, inspect_native_output,
    compare_native_with_reference, check_native_binary_capability,
)

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'model-inputs/p6/kairos-synthetic-input.json'
REFERENCE = ROOT / 'tests/fixtures/p6_native/independent-reference.json'
LOCK = ROOT / 'model-inputs/p6/kairos-provider-lock.json'


def scenario():
    return json.loads(INPUT.read_text())


def expected():
    return json.loads(REFERENCE.read_text())


def test_native_scenario_is_fully_externalised_and_synthetic():
    model = KairosScenario.model_validate(scenario())
    assert model.horizon_minutes == 240
    assert model.strategies[0].initial_departure_minute == 120
    assert model.strategies[1].initial_departure_minute == 90
    assert model.arrivals[0].request_minute == 60


def test_reference_bridge_audits_one_bed_conservation_without_native_claim():
    actual = KairosProducerOutput.model_validate(expected())
    review = inspect_native_output(actual, scenario=KairosScenario.model_validate(scenario()),
                                   provider_lock=json.loads(LOCK.read_text()))
    assert review['admission']['strategies']['current_care']['occupied_bed_minutes'] == 180
    assert review['admission']['strategies']['liaison_service']['occupied_bed_minutes'] == 150
    assert review['admission']['paired_comparisons']['liaison_service']['mean_wait_minutes_change'] == -30
    assert review['native_binary_executed'] is False
    assert review['native_provenance_qualified'] is False
    assert review['investment_ready'] is False


def test_independent_reference_is_explicitly_not_native_execution():
    same = compare_native_with_reference(expected(), expected(), scenario())
    assert same['matches_reference'] is True
    assert same['native_binary_executed'] is False


def test_rejects_tampered_or_mismatched_provider_revision():
    e = expected()
    e['provider']['source_commit'] = '0' * 40
    with pytest.raises(ValueError, match='revision'):
        inspect_native_output(KairosProducerOutput.model_validate(e),
                              scenario=KairosScenario.model_validate(scenario()),
                              provider_lock=json.loads(LOCK.read_text()))


def test_rejects_unpaired_request_time_even_if_each_arm_physically_valid():
    e = expected()
    e['strategies'][1]['requests'][0]['request_minute'] = 61
    with pytest.raises(ValueError, match='paired'):
        inspect_native_output(KairosProducerOutput.model_validate(e),
                              scenario=KairosScenario.model_validate(scenario()),
                              provider_lock=json.loads(LOCK.read_text()))


def test_rejects_fake_admission_and_ghost_occupancy():
    e = expected()
    e['strategies'][1]['requests'][0]['admitted_minute'] = 80
    with pytest.raises(ValueError, match='matching occupancy'):
        inspect_native_output(KairosProducerOutput.model_validate(e),
                              scenario=KairosScenario.model_validate(scenario()),
                              provider_lock=json.loads(LOCK.read_text()))


def test_rejects_real_id_even_with_synthetic_data_label():
    e = expected()
    e['strategies'][0]['occupancies'][0]['episode_id'] = 'MRN-123456'
    with pytest.raises(ValueError):
        KairosProducerOutput.model_validate(e)


def test_native_provider_gate_fails_closed_without_compiler_or_binary():
    capability = check_native_binary_capability(ROOT / 'native/kairos-icu-liaison')
    assert capability['native_execution_qualified'] is False
    if capability['rustc_present'] is False:
        assert capability['blocking_reason'] == 'rust_toolchain_unavailable'


def test_native_cli_refuses_unqualified_input_without_executable():
    p = subprocess.run([sys.executable, '-m', 'icu_liaison.p6_native_cli', str(INPUT)],
                       capture_output=True, text=True, cwd=ROOT,
                       env={'PYTHONPATH': str(ROOT / 'src')})
    assert p.returncode == 2
    assert 'UNVERIFIED' in p.stderr
    assert 'admitted_requests' not in p.stdout


def test_scenario_rejects_duplicate_and_non_synthetic_request():
    s = scenario(); s['arrivals'].append(copy.deepcopy(s['arrivals'][0]))
    with pytest.raises(ValueError, match='duplicate'):
        KairosScenario.model_validate(s)
    s = scenario(); s['arrivals'][0]['request_id'] = 'patient-004'
    with pytest.raises(ValueError):
        KairosScenario.model_validate(s)
