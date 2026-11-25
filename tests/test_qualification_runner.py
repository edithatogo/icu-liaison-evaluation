"""The full portability runner cannot claim provider, CHHHS or clinical acceptance."""
from pytest import MonkeyPatch
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path

import pytest

from tools.qualify_current_portable import qualify

ROOT = Path(__file__).resolve().parents[1]


def test_synthetic_qualification_runner_is_fail_closed() -> None:
    before = datetime.now(UTC).date().isoformat()
    result = qualify()
    assert result['status']=='SOURCE_ORACLES_PASSED_SYNTHETIC_ONLY'
    assert result['p4_independent_accounting']['draws_checked']==18
    assert result['p3_synthetic_quality']['return_72h']['unknown']==1
    assert result['native_kairos_executed'] is False
    assert result['dapane_native_executed'] is False
    assert result['voiage_native_executed'] is False
    assert result['clinical_or_causal_validation'] is False
    assert result['investment_ready'] is False
    assert result['date'] in {before, datetime.now(UTC).date().isoformat()}
    scenario = (ROOT / 'model-inputs/p4/illustrative.json').read_bytes()
    assert result['scenario_sha256'] == hashlib.sha256(scenario).hexdigest()
    assert result['p4_seed'] == json.loads(scenario)['seed']
    fixture = (ROOT / 'tests/fixtures/p3_episodes/manifest.json').read_bytes()
    assert result['p3_input_provenance']['manifest_sha256'] == hashlib.sha256(fixture).hexdigest()
    request = result['chhhs_data_request']
    assert request['status'] == 'request_only_no_local_data_obtained'
    assert (request['dataset_count'], request['field_count']) == (11, 115)
    assert request['source_sha256'] == hashlib.sha256(
        (ROOT / 'model-inputs/chhhs-data-request.json').read_bytes()
    ).hexdigest()
    publisher = result['publisher_check']
    assert publisher['status'] == 'PUBLISHER_RECEIPT_RECONCILED'
    assert publisher['checked_outcome_count'] == 6
    assert publisher['document_sha256_matched'] is False
    assert publisher['independent_source_admission'] == 'pending'


def test_qualification_rejects_a_nonmatching_saved_publisher_document(tmp_path: Path) -> None:
    candidate = tmp_path / 'fictional-report.pdf'
    candidate.write_bytes(b'Fictional document bytes')
    with pytest.raises(ValueError, match='document size mismatch'):
        qualify(publisher_document=candidate)


def test_qualification_can_audit_the_shortest_supported_scenario(monkeypatch: MonkeyPatch) -> None:
    path = ROOT / 'model-inputs/p4/illustrative.json'
    scenario = json.loads(path.read_bytes())
    scenario['iterations'] = 2
    original_read = Path.read_bytes

    def read_scenario(candidate: Path) -> bytes:
        if candidate == path:
            return json.dumps(scenario).encode('utf-8')
        return original_read(candidate)

    monkeypatch.setattr(Path, 'read_bytes', read_scenario)
    result = qualify()['p4_independent_accounting']
    assert result['selected_draw_indices'] == [0, 1]
    assert result['draws_checked'] == 2 * len(scenario['strategies'])
