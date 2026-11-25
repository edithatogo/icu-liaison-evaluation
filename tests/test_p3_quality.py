"""P3 synthetic source QC: no patient identifiers or raw rows in output."""
from typing import Any
from collections.abc import Callable
import csv
import hashlib
import json
from pathlib import Path
from shutil import copytree

import pytest

from icu_liaison.data_quality import inspect_extract, ContractError

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/p3_synthetic'
DICT = ROOT / 'model-inputs/clinical-data-dictionary.json'
PROTOCOL = ROOT / 'model-inputs/clinical-economic-protocol.json'


def inspect(folder: Path=FIXTURE, manifest: Path | None=None) -> dict[str, Any]:
    return inspect_extract(folder, manifest or folder/'manifest.json', DICT, PROTOCOL, project_root=ROOT)


def modified(tmp_path: Path, table: str, fn: Callable[[list[dict[str, str]]], object]) -> Path:
    dst=tmp_path/'test-extract'
    copytree(FIXTURE,dst)
    file=dst/f'{table}.csv'
    with file.open(newline='', encoding='utf-8') as f:
        reader=csv.DictReader(f)
        rows=list(reader)
        fields=reader.fieldnames
    assert fields is not None
    fn(rows)
    with file.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n')
        writer.writeheader();writer.writerows(rows)
    manifest=json.loads((dst/'manifest.json').read_text(encoding='utf-8'))
    manifest['tables'][table]['sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
    (dst/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    return dst


def test_synthetic_valid_extract_preserves_denominators_and_missingness() -> None:
    result = inspect()
    assert result['status'] == 'SYNTHETIC_DIAGNOSTIC_ONLY'
    assert result['ready_for_local_effect_estimation'] is False
    assert result['cohort']['eligible_index_discharges'] == 5
    assert result['cohort']['nonindex_eligible_episodes'] == 1
    assert result['discharge_delay']['known_ready_count'] == 4
    assert result['discharge_delay']['exit_block_ge12h_count'] == 2
    assert result['readmission_72h']['unplanned_yes'] == 1
    assert result['readmission_72h']['unknown'] == 2
    assert result['readmission_72h']['unplanned_no'] == 2
    assert result['readmission_72h']['observed_rate'] == pytest.approx(1/3)
    assert result['readmission_72h']['lower_bound_all_eligible'] == pytest.approx(1/5)
    assert result['readmission_72h']['upper_bound_all_eligible'] == pytest.approx(3/5)
    assert result['readmission_72h']['competing_deaths'] == 1
    assert result['safety']['ward_cardiac_arrests_observed'] == 1
    assert result['costing']['segments']['return_episode'] == 1
    assert not result['errors']
    assert 'synthetic_case_A' not in json.dumps(result)
    assert 'patient_id' not in json.dumps(result)


def test_file_digest_tampering_is_rejected_without_printing_values(tmp_path: Path) -> None:
    dst=tmp_path/'source';copytree(FIXTURE,dst)
    with (dst/'episodes.csv').open('a') as f:f.write('unexpected-content\n')
    with pytest.raises(ContractError,match='sha256') as exc:
        inspect(dst)
    assert 'synthetic_case_A' not in str(exc.value)


def test_duplicate_episode_key_rejected(tmp_path: Path) -> None:
    dst=modified(tmp_path,'episodes',lambda rows:rows.append(dict(rows[0])))
    with pytest.raises(ContractError,match='duplicate'):
        inspect(dst)


def test_orphan_return_rejected(tmp_path: Path) -> None:
    dst=modified(tmp_path,'returns',lambda rows:rows.__setitem__(0,dict(rows[0],index_icu_episode_id='nonexistent-key')))
    with pytest.raises(ContractError,match='orphan'):
        inspect(dst)


def test_return_before_departure_is_rejected(tmp_path: Path) -> None:
    dst=modified(tmp_path,'returns',lambda rows:rows.__setitem__(0,dict(rows[0],icu_readmission_at='2026-07-01T02:00:00+10:00')))
    with pytest.raises(ContractError,match='chronology'):
        inspect(dst)


def test_naive_date_rejected(tmp_path: Path) -> None:
    dst=modified(tmp_path,'episodes',lambda rows:rows.__setitem__(0,dict(rows[0],icu_actual_departure_at='2026-07-01T18:00:00')))
    with pytest.raises(ContractError,match='timezone'):
        inspect(dst)


def test_unknown_readmission_status_does_not_become_no(tmp_path: Path) -> None:
    dst=modified(tmp_path,'returns',lambda rows:rows.__setitem__(0,dict(rows[0],readmission_planned_status='unknown')))
    report=inspect(dst)
    assert report['readmission_72h']['unplanned_yes']==0
    assert report['readmission_72h']['unknown']==3
    assert report['readmission_72h']['unplanned_no']==2


def test_cost_duplicate_across_segments_rejected(tmp_path: Path) -> None:
    def duplicate(rows: list[dict[str, Any]]) -> None:
        rows.append(dict(rows[0],cost_resource_segment='return_episode'))
    dst=modified(tmp_path,'cost_lines',duplicate)
    with pytest.raises(ContractError,match='duplicate'):
        inspect(dst)


def test_forbidden_extra_column_rejected(tmp_path: Path) -> None:
    dst=tmp_path/'copied';copytree(FIXTURE,dst)
    file=dst/'episodes.csv'
    content=file.read_text();file.write_text(content.replace('hospitalisation_pseudonym,','hospitalisation_pseudonym,patient_name,',1))
    man=json.loads((dst/'manifest.json').read_text());man['tables']['episodes']['sha256']=hashlib.sha256(file.read_bytes()).hexdigest()
    (dst/'manifest.json').write_text(json.dumps(man))
    with pytest.raises(ContractError,match='unexpected column'):
        inspect(dst)


def test_restricted_source_requires_private_path_and_approval(tmp_path: Path) -> None:
    dst=tmp_path/'private';copytree(FIXTURE,dst)
    m=json.loads((dst/'manifest.json').read_text());m['data_class']='restricted_local_extract'
    (dst/'manifest.json').write_text(json.dumps(m))
    with pytest.raises(ContractError,match='restricted'):
        inspect(dst)
    with pytest.raises(ContractError,match='governance|approval'):
        inspect_extract(dst,dst/'manifest.json',DICT,PROTOCOL,project_root=ROOT,allow_restricted_local=True)


def test_restricted_source_even_if_approved_is_diagnostic_not_locally_qualified(tmp_path: Path) -> None:
    dst=tmp_path/'restricted';copytree(FIXTURE,dst)
    m=json.loads((dst/'manifest.json').read_text());m.update(data_class='restricted_local_extract',
        governance_reference='synthetic-authorisation-placeholder-for-test',
        extract_owner_role='authorised_hhs_analyst',
        approval_reference='synthetic-test-approval', site='fictional_test_facility')
    (dst/'manifest.json').write_text(json.dumps(m))
    result=inspect_extract(dst,dst/'manifest.json',DICT,PROTOCOL,project_root=ROOT,allow_restricted_local=True)
    assert result['status']=='LOCAL_EXTRACT_DIAGNOSTIC_ONLY'
    assert result['ready_for_local_effect_estimation'] is False


def test_missing_time_and_truncated_followup_are_visible() -> None:
    report=inspect()
    assert report['discharge_delay']['missing_ready_count'] == 1
    assert report['readmission_72h']['unknown'] == 2
    assert report['data_quality']['missingness']['icu_medically_ready_at'] == 1
    assert report['data_quality']['missingness']['followup_observation_end_at'] == 0


def test_extract_rejects_unregistered_metadata_before_reading_tables(tmp_path: Path) -> None:
    manifest = json.loads((FIXTURE / 'manifest.json').read_bytes())
    manifest['unregistered_authority'] = 'fictional'
    path = tmp_path / 'attempt.json'
    path.write_text(json.dumps(manifest))
    with pytest.raises(ContractError, match='unexpected manifest field'):
        inspect(FIXTURE, path)
