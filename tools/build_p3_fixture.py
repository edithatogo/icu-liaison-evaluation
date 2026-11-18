"""Development-only generator for entirely fictional P3 test fixtures.

Run once to refresh source-hashed fixtures; it never opens live hospital files.
"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = json.loads((ROOT/'conductor/evidence/source-register.json').read_text())
OBS=[]
for name in ('ANZICS-CCR-2024-25','ANZICS-CORE-2024'):
    s=next(item for item in REG['sources'] if item['id']==name)
    for x in s['outcomes']:
        OBS.append({
            'source_id':name,'name':x['name'],'value':x['value'],'unit':x['unit'],
            'denominator':x['denominator'],'page':x['page'],
            'contributors':x.get('contributors'),
            'population':('binational_all_age_mixed' if name.startswith('ANZICS-CCR') else 'australia_adult'),
            'local_use':('illustrative_exit_block_proxy' if x['name']=='live_ward_home_discharge_delay_ge12h' else 'external_context_only'),
        })
contract={
    'schema_version':1,
    'data_class':'public_aggregated_only',
    'source_transcription':'previously_curated_public_report_values',
    'document_verification':{
        'status':'publisher_pdf_sha256_unavailable',
        'publisher_file_sha256':None,
        'claim':'Transcription reconciled against the existing source register; exact 2024/25 PDF bytes not authenticated by this P3 offline build.'
    },
    'observations':OBS,
    'forbidden_uses':['local_CHHHS_rate','unplanned_72h_return','incremental_cost_per_readmission_aud','net_avoidable_cost_per_icu_day_aud'],
}
folder=ROOT/'model-inputs/p3';folder.mkdir(exist_ok=True, parents=True)
(folder/'anzics-public-contract.json').write_text(json.dumps(contract,indent=2)+'\n')

D='2026-07-01T';Z='+10:00'
headers={
    'episodes':['hospitalisation_pseudonym','index_icu_episode_id','icu_admission_at','icu_medically_ready_at','icu_actual_departure_at','destination_category','adult_age_at_icu_admission_years','followup_observation_end_at','censor_reason','hospitalisation_final_departure_at','hospital_death_at'],
    'returns':['hospitalisation_pseudonym','index_icu_episode_id','return_episode_id','icu_readmission_at','readmission_planned_status','return_appropriateness_review'],
    'contacts':['hospitalisation_pseudonym','index_icu_episode_id','contact_id','liaison_contact_at','liaison_intervention_type'],
    'safety_events':['hospitalisation_pseudonym','index_icu_episode_id','event_id','event_type','ward_cardiac_arrest_at','deterioration_recognised_at','escalation_responded_at'],
    'cost_lines':['hospitalisation_pseudonym','index_icu_episode_id','cost_ledger_entry_id','cost_resource_segment','cost_resource_quantity','cost_unit_quotation','cost_currency','cost_price_year'],
}
A='synthetic_case_A';B='synthetic_case_B';C='synthetic_case_C';D_='synthetic_case_D';E='synthetic_case_E'
rows={
    'episodes':[
        [A,'synthetic_A_i1','2026-06-28T00:00:00+10:00',D+'06:00:00'+Z,D+'18:00:00'+Z,'ward_same_hospital','64','2026-07-04T18:00:00+10:00','completed_72h','2026-07-06T11:00:00+10:00',''],
        [A,'synthetic_A_i2','2026-07-02T20:00:00+10:00','2026-07-03T06:00:00+10:00','2026-07-03T10:00:00+10:00','ward_same_hospital','64','2026-07-06T10:00:00+10:00','completed_72h','2026-07-06T11:00:00+10:00',''],
        [B,'synthetic_B_i1','2026-06-30T11:00:00+10:00',D+'07:00:00'+Z,D+'09:00:00'+Z,'ward_same_hospital','74','2026-07-04T09:00:00+10:00','completed_72h','2026-07-06T18:00:00+10:00',''],
        [C,'synthetic_C_i1','2026-06-28T21:00:00+10:00','',D+'03:00:00'+Z,'ward_same_hospital','21',D+'23:00:00'+Z,'interhospital_transfer','2026-07-02T01:00:00+10:00',''],
        [D_,'synthetic_D_i1','2026-06-28T11:00:00+10:00','2026-06-30T22:00:00+10:00',D+'11:00:00'+Z,'ward_same_hospital','68','2026-07-02T07:00:00+10:00','death','2026-07-02T07:00:00+10:00','2026-07-02T07:00:00+10:00'],
        [E,'synthetic_E_i1','2026-06-30T12:00:00+10:00',D+'01:00:00'+Z,D+'05:00:00'+Z,'ward_same_hospital','47','2026-07-04T05:00:00+10:00','completed_72h','2026-07-05T18:00:00+10:00',''],
    ],
    'returns':[
        [A,'synthetic_A_i1','synthetic_A_return1','2026-07-02T18:00:00+10:00','unplanned','appropriate_rescue'],
        [E,'synthetic_E_i1','synthetic_E_return1','2026-07-01T11:00:00+10:00','planned','planned_followup'],
    ],
    'contacts':[
        [A,'synthetic_A_i1','synthetic_contact_A1','2026-07-01T21:00:00+10:00','ward_review'],
        [B,'synthetic_B_i1','synthetic_contact_B1','2026-07-01T08:30:00+10:00','handover_support'],
    ],
    'safety_events':[
        [A,'synthetic_A_i1','synthetic_event_A1','ward_cardiac_arrest','2026-07-02T12:00:00+10:00','2026-07-02T11:45:00+10:00','2026-07-02T11:55:00+10:00'],
    ],
    'cost_lines':[
        [A,'synthetic_A_i1','synthetic_cost_A_index','index_ready_to_departure','0.5','1800.00','AUD','2026'],
        [A,'synthetic_A_i1','synthetic_cost_A_return','return_episode','1','15000.00','AUD','2026'],
        ['','','synthetic_cost_incremental_service','incremental_service','1','250000.00','AUD','2026'],
    ],
}
folder=ROOT/'tests/fixtures/p3_synthetic'
folder.mkdir(exist_ok=True,parents=True)
for table,records in rows.items():
    with (folder/f'{table}.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f,lineterminator='\n')
        writer.writerow(headers[table]);writer.writerows(records)
manifest={
    'schema_version':1,'data_class':'synthetic_example',
    'site':'fictional_test_facility','source_system':'synthetic_conformance_fixture',
    'governance_reference':None,'approval_reference':None,'extract_owner_role':None,
    'clock_timezone':'Australia/Brisbane',
    'capture_status':{
        'ANZICS_APD':'synthetic_partial',
        'CHHHS_hospital_movements':'synthetic_partial',
        'CHHHS_liaison_activity':'synthetic_partial',
        'CHHHS_incident_MET':'synthetic_partial',
        'CHHHS_costing':'synthetic_partial',
    },
    'tables':{name:{'file':f'{name}.csv','sha256':hashlib.sha256((folder/f'{name}.csv').read_bytes()).hexdigest(),'column_map':{}} for name in headers},
}
(folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Generated frozen public pack and entirely fictional test extract')
