"""P3 RED: synthetic admissions, linkage, ascertainment, and PHI prevention."""
import csv
import hashlib
import json
from pathlib import Path
import shutil
from datetime import datetime, timedelta, timezone

import pytest
from icu_liaison.local_data import load_and_audit, LocalDatasetError

FIX = Path(__file__).parent / 'fixtures/p3_episodes'


def fixture(tmp_path):
    target = tmp_path / 'synthetic'
    shutil.copytree(FIX, target)
    return target


def rewrite_csv(directory, filename, change):
    path = directory / filename
    with path.open(newline='', encoding='utf-8') as f:
        table = list(csv.DictReader(f))
        keys = list(table[0])
    change(table)
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(table)
    manifest_path = directory / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    file_key = next(k for k,v in manifest['files'].items() if v['path']==filename)
    manifest['files'][file_key]['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2))


def test_index_uses_first_eligible_live_ward_discharge_per_hospitalisation():
    result = load_and_audit(FIX / 'manifest.json')
    counts = result['cohort']
    assert counts['all_icu_episodes'] == 7
    assert counts['hospitalisations'] == 4
    assert counts['eligible_index_discharges'] == 3
    assert counts['index_with_readiness'] == 2
    assert counts['index_exit_block_ge12h'] == 1
    assert counts['index_after_hours_departure'] == 1
    assert counts['unplanned_return_within_72h'] == 1
    assert counts['early_return_unknown'] == 1
    assert counts['early_return_observed_no_event'] == 1
    assert counts['competing_death_before_return'] == 1
    assert counts['index_discharge_denominator_differs_from_CCR'] is True
    assert result['investment_ready'] is False
    assert result['quality']['field_completeness']['icu_medically_ready_at']['missing'] >= 1


def test_raw_person_fields_and_unsigned_source_files_fail_closed(tmp_path):
    x = fixture(tmp_path)
    rewrite_csv(x, 'episodes.csv', lambda rows: rows[0].update({'hospitalisation_pseudonym': '123456789'}))
    with pytest.raises(LocalDatasetError, match='pseudonym'):
        load_and_audit(x / 'manifest.json')
    x = fixture(tmp_path / 'other')
    with (x / 'episodes.csv').open('ab') as f:
        f.write(b'\n')
    with pytest.raises(LocalDatasetError, match='sha256'):
        load_and_audit(x / 'manifest.json')


def test_duplicate_episode_and_overlapping_episode_fail_closed(tmp_path):
    x = fixture(tmp_path)
    rewrite_csv(x, 'episodes.csv', lambda rows: rows[1].update({'index_icu_episode_id': rows[0]['index_icu_episode_id']}))
    with pytest.raises(LocalDatasetError, match='duplicate'):
        load_and_audit(x / 'manifest.json')
    x = fixture(tmp_path / 'overlap')
    rewrite_csv(x, 'episodes.csv', lambda rows: rows[1].update({'icu_admission_at': '2026-01-01T09:00:00+10:00'}))
    with pytest.raises(LocalDatasetError, match='overlap'):
        load_and_audit(x / 'manifest.json')


def test_local_readiness_unknown_is_not_zero_and_missing_censor_not_no_event(tmp_path):
    x = fixture(tmp_path)
    rewrite_csv(x, 'episodes.csv',lambda rows: rows[0].update({'icu_medically_ready_at': ''}))
    res = load_and_audit(x / 'manifest.json')
    assert res['cohort']['index_with_readiness'] == 1
    assert res['cohort']['index_exit_block_ge12h'] == 0
    assert res['cohort']['eligible_index_discharges'] == 3
    assert res['cohort']['early_return_unknown'] == 1


def test_unplanned_return_at_exactly_72h_not_a_positive(tmp_path):
    x = fixture(tmp_path)
    rewrite_csv(x, 'episodes.csv',lambda rows: rows[1].update({'icu_admission_at': '2026-01-04T10:00:00+10:00'}))
    res = load_and_audit(x / 'manifest.json')
    assert res['cohort']['unplanned_return_within_72h'] == 0


def test_restricted_requires_specific_attestation_and_private_output(tmp_path):
    x=fixture(tmp_path)
    m=json.loads((x/'manifest.json').read_text())
    m['data_class']='restricted'
    (x/'manifest.json').write_text(json.dumps(m))
    with pytest.raises(LocalDatasetError, match='governance'):
        load_and_audit(x / 'manifest.json', restricted_acknowledged=True)
    m['governance']={'status':'approved_local_processing','approval_reference':'CHHHS-PLACEHOLDER-LOCAL-APPROVAL', 'custodian_role':'ICU data custodian'}
    (x/'manifest.json').write_text(json.dumps(m))
    with pytest.raises(LocalDatasetError, match='explicit'):
        load_and_audit(x / 'manifest.json')
    # Attestation flag does not confer clinical approval or suppress unknowns.
    result=load_and_audit(x/'manifest.json',restricted_acknowledged=True)
    assert result['investment_ready'] is False
    assert result['data_class'] == 'restricted'


def test_unknown_columns_or_cost_component_duplicates_fail_closed(tmp_path):
    x=fixture(tmp_path)
    with (x/'episodes.csv').open('a',encoding='utf-8') as f:f.write('')
    rewrite_csv(x,'cost_lines.csv',lambda rows: rows[1].update({'cost_use_id':rows[0]['cost_use_id'],'cost_component_id':rows[0]['cost_component_id']}))
    with pytest.raises(LocalDatasetError,match='duplicate cost component'):
        load_and_audit(x/'manifest.json')


def test_missing_followup_for_eligible_hospitalisation_rejected(tmp_path):
    x=fixture(tmp_path)
    rewrite_csv(x,'followup.csv',lambda rows: rows.pop(0))
    with pytest.raises(LocalDatasetError,match='followup'):
        load_and_audit(x/'manifest.json')


def test_report_contains_no_pseudonyms_or_patient_rows():
    result=load_and_audit(FIX/'manifest.json')
    s=json.dumps(result)
    assert 'SYNHOSP' not in s and 'SYNICU' not in s
    assert '2026-01-01T10:00' not in s
    assert 'rows' not in result


def test_local_source_header_mapping_works_without_changing_source(tmp_path):
    x=fixture(tmp_path)
    path=x/'episodes.csv'
    with path.open(newline='',encoding='utf-8') as handle:
        rows=list(csv.DictReader(handle))
        names=list(rows[0])
    old='icu_medically_ready_at';vendor='APD_DIS_DEC_DT'
    with path.open('w',newline='',encoding='utf-8') as handle:
        writer=csv.DictWriter(handle,fieldnames=[vendor if v==old else v for v in names])
        writer.writeheader()
        writer.writerows([{(vendor if k==old else k):v for k,v in row.items()} for row in rows])
    mf=x/'manifest.json';m=json.loads(mf.read_text())
    m['files']['episodes']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    m['files']['episodes']['column_map']={vendor:old}
    mf.write_text(json.dumps(m))
    result=load_and_audit(mf)
    assert result['cohort']['index_exit_block_ge12h']==1


def test_unmapped_source_header_fails_without_echoing_sensitive_values(tmp_path):
    x=fixture(tmp_path)
    path=x/'episodes.csv'
    with path.open(newline='',encoding='utf-8') as handle:
        rows=list(csv.DictReader(handle));names=list(rows[0])
    with path.open('w',newline='',encoding='utf-8') as handle:
        names.append('person_full_name')
        writer=csv.DictWriter(handle,fieldnames=names);writer.writeheader()
        writer.writerows([{**row,'person_full_name':'Fictional Test'} for row in rows])
    mf=x/'manifest.json';m=json.loads(mf.read_text())
    m['files']['episodes']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    mf.write_text(json.dumps(m))
    with pytest.raises(LocalDatasetError) as err:
        load_and_audit(mf)
    assert 'Fictional' not in str(err.value)


def test_cost_basis_and_price_year_required_for_audit(tmp_path):
    x=fixture(tmp_path)
    rewrite_csv(x,'cost_lines.csv',lambda rows: rows[0].update({'cost_basis':''}))
    with pytest.raises(LocalDatasetError,match='validation'):
        load_and_audit(x/'manifest.json')


def test_timestamp_requires_offset_and_death_record_is_complete(tmp_path):
    x=fixture(tmp_path)
    rewrite_csv(x,'episodes.csv',lambda rows: rows[0].update({'icu_actual_departure_at':'2026-01-01T10:00:00'}))
    with pytest.raises(LocalDatasetError,match='validation'):
        load_and_audit(x/'manifest.json')
    x=fixture(tmp_path/'death')
    rewrite_csv(x,'followup.csv',lambda rows: rows[1].update({'hospital_death_at':''}))
    with pytest.raises(LocalDatasetError,match='validation'):
        load_and_audit(x/'manifest.json')


def test_observation_cannot_extend_past_final_hospital_separation(tmp_path):
    x=fixture(tmp_path)
    rewrite_csv(x,'followup.csv',lambda rows: rows[0].update({
        'hospitalisation_final_departure_at':'2026-01-02T09:00:00+10:00',
        'censor_reason':'completed_72h',
    }))
    with pytest.raises(LocalDatasetError,match='validation'):
        load_and_audit(x/'manifest.json')


def test_death_cannot_be_reported_without_death_censor(tmp_path):
    x=fixture(tmp_path)
    rewrite_csv(x,'followup.csv',lambda rows: rows[1].update({'censor_reason':'hospital_discharge'}))
    with pytest.raises(LocalDatasetError,match='validation'):
        load_and_audit(x/'manifest.json')


def test_all_zero_endpoint_counts_are_explicit(tmp_path):
    x=fixture(tmp_path)
    rewrite_csv(x,'episodes.csv',lambda rows: [
       row.update({'icu_medically_ready_at':''}) for row in rows
    ])
    result=load_and_audit(x/'manifest.json')
    assert result['cohort']['index_with_readiness']==0
    assert result['cohort']['index_exit_block_ge12h']==0


def test_extract_provenance_and_age_are_explicit_not_freshness_approval():
    report=load_and_audit(FIX/'manifest.json')
    freshness=report['quality']['source_freshness']
    assert freshness['source_extracted_at'].startswith('2026-11-18')
    assert freshness['days_since_last_episode_at_extraction'] >= 1
    assert freshness['freshness_admission']=='threshold_not_approved'


def test_extraction_cannot_predate_observed_episode_departure(tmp_path):
    x=fixture(tmp_path)
    mf=x/'manifest.json';m=json.loads(mf.read_text())
    m['extracted_at']='2026-01-01T00:00:00+10:00'
    mf.write_text(json.dumps(m))
    with pytest.raises(LocalDatasetError,match='extraction'):
        load_and_audit(mf)


@pytest.mark.parametrize('future_field', ['followup_observation_end_at', 'hospitalisation_final_departure_at'])
def test_extraction_cannot_predate_observed_followup_or_separation(tmp_path, future_field):
    directory = fixture(tmp_path)
    future = '2026-11-19T08:00:00+10:00'

    def edit(rows):
        rows[0][future_field] = future
        if future_field == 'followup_observation_end_at':
            rows[0]['hospitalisation_final_departure_at'] = ''

    rewrite_csv(directory, 'followup.csv', edit)
    with pytest.raises(LocalDatasetError, match='extraction'):
        load_and_audit(directory / 'manifest.json')


def test_identifier_completeness_uses_the_dictionary_grain():
    report = load_and_audit(FIX / 'manifest.json')
    fields = report['quality']['field_completeness']
    assert fields['hospitalisation_pseudonym']['source_feed'] == 'followup'
    assert fields['hospitalisation_pseudonym']['present'] == report['cohort']['hospitalisations']
    assert fields['index_icu_episode_id']['source_feed'] == 'episodes'
    assert fields['index_icu_episode_id']['present'] == report['cohort']['all_icu_episodes']


def test_index_delay_mean_excludes_repeats_home_and_unknown_readiness(tmp_path):
    directory = fixture(tmp_path)
    metric = load_and_audit(directory / 'manifest.json')['index_ready_delay']
    assert metric == {'metric_id': 'M31', 'population_id': 'D03', 'denominator_id': 'D14',
                      'eligible': 3, 'valid': 2, 'missing': 1, 'mean_hours': 8.5}
    rewrite_csv(directory, 'episodes.csv', lambda rows: [
        row.update(icu_medically_ready_at='') for row in rows])
    empty = load_and_audit(directory / 'manifest.json')['index_ready_delay']
    assert (empty['valid'], empty['missing'], empty['mean_hours']) == (0, 3, None)
