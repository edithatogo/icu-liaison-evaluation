"""P3 red tests: public source integrity and denominator separation."""
import json
from pathlib import Path

import pytest

from icu_liaison.public_evidence import load_benchmark_catalogue, select_external_benchmark

ROOT = Path(__file__).resolve().parents[1]


def test_public_rates_preserve_source_populations_and_denominators() -> None:
    data = load_benchmark_catalogue(ROOT / 'model-inputs/anzics-benchmarks.json',
                                     ROOT / 'conductor/evidence/source-register.json')
    exit_rate = select_external_benchmark(data, 'CCR_2024_25_EXIT_BLOCK')
    assert exit_rate['value'] == 0.204
    assert exit_rate['denominator_key'] == 'all_live_ward_home_discharges'
    assert exit_rate['cohort'] == 'all_age_binational_reporting_units'
    assert exit_rate['verification_status'] == 'previous_transcription_not_independently_reverified'
    readm = select_external_benchmark(data, 'CCR_2024_25_RETURN_EPISODES')
    assert readm['denominator_key'] == 'all_icu_hdu_admissions'
    assert readm['outcome_definition'] != 'unplanned_72h_return'
    assert select_external_benchmark(data, 'CCR_2023_24_EXIT_BLOCK')['value'] == 0.198


def test_unverified_source_cannot_be_promoted_to_verified() -> None:
    data = load_benchmark_catalogue(ROOT / 'model-inputs/anzics-benchmarks.json',
                                     ROOT / 'conductor/evidence/source-register.json')
    with pytest.raises(ValueError, match='unverified'):
        select_external_benchmark(data, 'CCR_2024_25_EXIT_BLOCK', require_document_verified=True)
    data['metrics'][0].update(
        verification_status='document_hash_attested_and_substantively_reviewed',
        document_sha256='1' * 64,
    )
    with pytest.raises(ValueError, match='independent admission'):
        select_external_benchmark(data, 'CCR_2024_25_EXIT_BLOCK', require_document_verified=True)


def test_wrong_source_or_denominator_is_rejected(tmp_path: Path) -> None:
    orig = json.loads((ROOT / 'model-inputs/anzics-benchmarks.json').read_text())
    orig['metrics'][0]['denominator_key'] = 'eligible_index_discharges'
    p = tmp_path / 'wrong.json'
    p.write_text(json.dumps(orig))
    with pytest.raises(ValueError, match='denominator'):
        load_benchmark_catalogue(p, ROOT / 'conductor/evidence/source-register.json')
    orig = json.loads((ROOT / 'model-inputs/anzics-benchmarks.json').read_text())
    orig['metrics'][0]['source_id'] = 'NONEXISTENT'
    p.write_text(json.dumps(orig))
    with pytest.raises(ValueError, match='source'):
        load_benchmark_catalogue(p, ROOT / 'conductor/evidence/source-register.json')


@pytest.mark.parametrize('change', ['different_edition', 'wrong_period', 'duplicate_source'])
def test_benchmark_is_bound_to_one_report_and_reporting_period(tmp_path: Path, change: str) -> None:
    catalogue = json.loads((ROOT / 'model-inputs/anzics-benchmarks.json').read_text())
    registry = json.loads((ROOT / 'conductor/evidence/source-register.json').read_text())
    if change == 'different_edition':
        previous = next(m for m in catalogue['metrics'] if m['id'] == 'CCR_2023_24_EXIT_BLOCK')
        catalogue['metrics'][0] = dict(previous, id='CCR_2024_25_EXIT_BLOCK')
    elif change == 'wrong_period':
        catalogue['metrics'][0]['period'] = '2023-07-01/2024-06-30'
    else:
        registry['sources'].append(registry['sources'][0].copy())
    catalogue_file = tmp_path / 'catalogue.json'
    catalogue_file.write_text(json.dumps(catalogue))
    register_file = tmp_path / 'register.json'
    register_file.write_text(json.dumps(registry))

    with pytest.raises(ValueError, match='edition|period|duplicate source'):
        load_benchmark_catalogue(catalogue_file, register_file)


def test_clinical_72h_risk_cannot_be_inferred_from_ccr_or_apd() -> None:
    data = load_benchmark_catalogue(ROOT / 'model-inputs/anzics-benchmarks.json',
                                     ROOT / 'conductor/evidence/source-register.json')
    with pytest.raises(ValueError, match='unavailable'):
        select_external_benchmark(data, 'UNPLANNED_72H_RETURN')


def test_source_register_cannot_silently_change_rate_or_verification(tmp_path: Path) -> None:
    source = json.loads((ROOT / 'conductor/evidence/source-register.json').read_text())
    source['sources'][0]['outcomes'][0]['value'] = 0.275
    altered = tmp_path/'source.json'
    altered.write_text(json.dumps(source))
    with pytest.raises(ValueError, match='value|conflict'):
        load_benchmark_catalogue(ROOT/'model-inputs/anzics-benchmarks.json',altered)
    source = json.loads((ROOT / 'conductor/evidence/source-register.json').read_text())
    source['sources'][0]['verification_status'] = 'document_hash_attested_and_substantively_reviewed'
    altered.write_text(json.dumps(source))
    with pytest.raises(ValueError, match='verification'):
        load_benchmark_catalogue(ROOT/'model-inputs/anzics-benchmarks.json',altered)
