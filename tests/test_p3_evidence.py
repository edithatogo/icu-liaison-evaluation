"""P3 ANZICS public source acceptance and denominator compatibility oracles."""
from typing import Any
from pathlib import Path
import json
import pytest

from icu_liaison.evidence import verify_public_benchmarks

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / 'conductor/evidence/source-register.json'
CONTRACT = ROOT / 'model-inputs/p3/anzics-public-contract.json'
PROTOCOL = ROOT / 'model-inputs/clinical-economic-protocol.json'


def read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding='utf-8'))
    assert isinstance(value, dict)
    return value


def test_public_anzics_pack_reconciles_reports_and_protocol_without_claiming_cairns_data() -> None:
    result = verify_public_benchmarks(read(REGISTER), read(CONTRACT), read(PROTOCOL))
    assert result['status'] == 'PUBLIC_TRANSCRIPTION_RECONCILED_NOT_DOCUMENT_AUTHENTICATED'
    assert result['checked_observations'] == 10
    assert result['local_72h_readmission_available'] is False
    assert result['local_cost_per_icu_day_available'] is False
    assert result['cairns_rates_verified'] is False


def test_72_hour_readmission_cannot_be_filled_from_ccr_episode_rate() -> None:
    contract = read(CONTRACT)
    entry = next(x for x in contract['observations'] if x['name'] == 'return_icu_hdu_admission_episodes')
    entry['local_use'] = 'unplanned_72h_return'
    with pytest.raises(ValueError, match='local_use|denominator'):
        verify_public_benchmarks(read(REGISTER), contract, read(PROTOCOL))


def test_public_rate_mismatch_and_missing_source_are_rejected() -> None:
    register = read(REGISTER)
    entry = register['sources'][0]['outcomes'][0]
    entry['value'] = 0.205
    with pytest.raises(ValueError, match='source|value'):
        verify_public_benchmarks(register, read(CONTRACT), read(PROTOCOL))
    register = read(REGISTER)
    register['sources'] = [x for x in register['sources'] if x['id'] != 'ANZICS-CORE-2024']
    with pytest.raises(ValueError, match='source'):
        verify_public_benchmarks(register, read(CONTRACT), read(PROTOCOL))


def test_protocol_benchmark_drift_is_blocked() -> None:
    proto = read(PROTOCOL)
    proto['reference_benchmark']['value'] = 0.28
    with pytest.raises(ValueError, match='protocol'):
        verify_public_benchmarks(read(REGISTER), read(CONTRACT), proto)


def test_duplicate_public_source_id_and_fake_sha_blocked() -> None:
    reg=read(REGISTER)
    reg['sources'].append(reg['sources'][0])
    with pytest.raises(ValueError, match='duplicate'):
        verify_public_benchmarks(reg,read(CONTRACT),read(PROTOCOL))
    c=read(CONTRACT)
    c['document_verification']['status']='publisher_pdf_hash_verified'
    with pytest.raises(ValueError, match='document_verification'):
        verify_public_benchmarks(read(REGISTER),c,read(PROTOCOL))
