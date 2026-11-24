"""Native Kairos adapter tests: contract/independent oracle, not binary execution."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from icu_liaison.p6_native import (
    KairosScenario, KairosProducerOutput, inspect_native_output,
    compare_native_with_reference, check_native_binary_capability, invoke_native_binary,
)
from icu_liaison.p6_native_cli import main as native_cli

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'model-inputs/p6/kairos-synthetic-input.json'
REFERENCE = ROOT / 'tests/fixtures/p6_native/independent-reference.json'
LOCK = ROOT / 'model-inputs/p6/kairos-provider-lock.json'
QUEUE_INPUT = REFERENCE.with_name('queue-scenario.json')
QUEUE_REFERENCE = REFERENCE.with_name('queue-reference.json')


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


@pytest.mark.parametrize(('field', 'value'), [
    ('seed', '20261118'),
    ('horizon_minutes', 240.0),
    ('staffed_beds', True),
    ('schema_version', 1.0),
])
def test_native_input_rejects_noninteger_json_fields(field, value):
    source = scenario()
    source[field] = value
    with pytest.raises(ValueError, match=field):
        KairosScenario.model_validate_json(json.dumps(source))


def test_native_input_rejects_duration_outside_rust_unsigned_range():
    source = scenario()
    source['arrivals'][0]['occupied_duration_minutes'] = 2**64
    with pytest.raises(ValueError, match='occupied_duration_minutes'):
        KairosScenario.model_validate_json(json.dumps(source))


@pytest.fixture
def native_files(tmp_path):
    binary = tmp_path / 'fictional-consumer'
    binary.write_bytes(b'\x7fELFfictional consumer bytes')
    binary.chmod(0o700)
    source = tmp_path / 'scenario.json'
    source.write_bytes(INPUT.read_bytes())
    return binary, source


def test_native_run_uses_checked_file_bytes(native_files, monkeypatch):
    binary, source = native_files
    original_binary = binary.read_bytes()
    original_input = source.read_bytes()
    invoked_paths = []

    def observe_invocation(argv, **kwargs):
        binary.write_bytes(b'updated fictional consumer')
        source.write_bytes(b'{}')
        invoked_paths.extend(Path(arg) for arg in argv)
        assert [path.read_bytes() for path in invoked_paths] == [original_binary, original_input]
        return subprocess.CompletedProcess(argv, 0, stdout=REFERENCE.read_bytes())

    monkeypatch.setattr(subprocess, 'run', observe_invocation)
    digest = hashlib.sha256(original_binary).hexdigest()
    report = invoke_native_binary(binary, source, expected_sha256=digest,
                                  provider_lock=json.loads(LOCK.read_bytes()))
    assert report['input_sha256'] == hashlib.sha256(original_input).hexdigest()
    assert report['binary_sha256'] == digest
    assert all(not path.exists() for path in invoked_paths)


def test_native_run_rejects_noninteger_output_times(native_files, monkeypatch):
    binary, source = native_files
    output = expected()
    output['strategies'][0]['requests'][0]['admitted_minute'] = '120'

    def fictional_result(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(output).encode())

    monkeypatch.setattr(subprocess, 'run', fictional_result)
    with pytest.raises(ValueError, match='admitted_minute'):
        invoke_native_binary(binary, source, expected_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
                             provider_lock=json.loads(LOCK.read_bytes()))


def test_native_cli_rejects_malformed_lock_before_execution(native_files, monkeypatch, tmp_path, capsys):
    binary, source = native_files
    lock = tmp_path / 'invalid-lock.json'
    lock.write_text('[]', encoding='utf-8')

    def unexpected_run(*args, **kwargs):
        pytest.fail('a malformed provider lock must be rejected before process startup')

    monkeypatch.setattr(subprocess, 'run', unexpected_run)
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    assert native_cli([str(source), '--binary', str(binary), '--expected-binary-sha256', digest,
                       '--provider-lock', str(lock)]) == 2
    captured = capsys.readouterr()
    assert not captured.out
    assert 'UNVERIFIED' in captured.err


def test_native_cli_reports_a_timeout_without_traceback(native_files, monkeypatch, capsys):
    binary, source = native_files

    def timeout(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, timeout=45)

    monkeypatch.setattr(subprocess, 'run', timeout)
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    assert native_cli([str(source), '--binary', str(binary), '--expected-binary-sha256', digest]) == 2
    captured = capsys.readouterr()
    assert not captured.out
    assert 'UNVERIFIED' in captured.err
    assert 'Traceback' not in captured.err


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


def test_queue_reference_demonstrates_reuse_with_the_same_demand():
    review = inspect_native_output(
        KairosProducerOutput.model_validate_json(QUEUE_REFERENCE.read_bytes()),
        scenario=KairosScenario.model_validate_json(QUEUE_INPUT.read_bytes()),
        provider_lock=json.loads(LOCK.read_text()),
    )
    comparison = review['admission']['paired_comparisons']['liaison_service']
    assert comparison['admitted_requests_change'] == 1
    assert comparison['spare_staffed_bed_minutes_change'] == 0
    assert comparison['mean_wait_minutes_change'] is None
    assert comparison['mean_wait_minutes_change_among_shared_admissions'] == -30
    assert comparison['request_disposition_transitions']['censored'] == {
        'admitted': 1, 'declined': 0, 'censored': 1,
    }


def test_native_trace_rejects_reversed_order_for_simultaneous_arrivals():
    output = json.loads(QUEUE_REFERENCE.read_bytes())
    baseline = output['strategies'][0]
    baseline['occupancies'][1:] = [
        {'episode_id': 'syn-demand-a', 'start_minute': 120, 'end_minute': 180},
        {'episode_id': 'syn-demand-z', 'start_minute': 180, 'end_minute': 240},
    ]
    baseline['requests'][0]['admitted_minute'] = 180
    baseline['requests'][1].update(disposition='admitted', admitted_minute=120)
    with pytest.raises(ValueError, match='FIFO'):
        inspect_native_output(
            KairosProducerOutput.model_validate(output),
            scenario=KairosScenario.model_validate_json(QUEUE_INPUT.read_bytes()),
            provider_lock=json.loads(LOCK.read_text()),
        )


def test_native_trace_rejects_waiting_with_a_vacant_staffed_bed():
    output = expected()
    arm = output['strategies'][1]
    arm['occupancies'][1].update(start_minute=95, end_minute=155)
    arm['requests'][0]['admitted_minute'] = 95
    with pytest.raises(ValueError, match='vacant staffed bed'):
        inspect_native_output(KairosProducerOutput.model_validate(output),
                              scenario=KairosScenario.model_validate(scenario()),
                              provider_lock=json.loads(LOCK.read_text()))


@pytest.mark.parametrize(('disposition', 'message'), [
    ('declined', 'does not decline'),
    ('censored', 'vacant staffed bed'),
])
def test_native_trace_rejects_inconsistent_unadmitted_demand(disposition, message):
    output = expected()
    arm = output['strategies'][1]
    arm['occupancies'].pop()
    arm['requests'][0].update(disposition=disposition, admitted_minute=None)
    with pytest.raises(ValueError, match=message):
        inspect_native_output(KairosProducerOutput.model_validate(output),
                              scenario=KairosScenario.model_validate(scenario()),
                              provider_lock=json.loads(LOCK.read_text()))


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
