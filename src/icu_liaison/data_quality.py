"""Restricted-local CSV *diagnostic* boundary for P3 ICU liaison evaluation.

Only aggregated diagnostics are returned. No identifiers, raw rows, cost totals,
confidential source names or patient timestamps are ever emitted. This code
cannot certify governance, hospital-source completeness or causal validity.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .endpoints import ReturnEvent, TransitionObservation, classify_transition
from .protocol import load_data_dictionary

MAX_FILE_SIZE = 30 * 1024 * 1024
MAX_ROWS = 150_000
SUPPORTED_TABLES: dict[str, tuple[str, ...]] = {
    'episodes': ('hospitalisation_pseudonym', 'index_icu_episode_id', 'icu_admission_at',
                 'icu_medically_ready_at', 'icu_actual_departure_at', 'destination_category',
                 'adult_age_at_icu_admission_years', 'followup_observation_end_at',
                 'censor_reason', 'hospitalisation_final_departure_at', 'hospital_death_at'),
    'returns': ('hospitalisation_pseudonym', 'index_icu_episode_id', 'return_episode_id',
                'icu_readmission_at', 'readmission_planned_status', 'return_appropriateness_review'),
    'contacts': ('hospitalisation_pseudonym', 'index_icu_episode_id', 'contact_id',
                 'liaison_contact_at', 'liaison_intervention_type'),
    'safety_events': ('hospitalisation_pseudonym', 'index_icu_episode_id', 'event_id',
                      'event_type', 'ward_cardiac_arrest_at',
                      'deterioration_recognised_at', 'escalation_responded_at'),
    'cost_lines': ('hospitalisation_pseudonym', 'index_icu_episode_id', 'cost_ledger_entry_id',
                   'cost_resource_segment', 'cost_resource_quantity', 'cost_unit_quotation',
                   'cost_currency', 'cost_price_year'),
}
ADDITIONAL_TRANSPORT_KEYS = {'return_episode_id', 'contact_id', 'event_id', 'event_type',
                             'cost_currency', 'cost_price_year'}
DESTINATIONS = {'ward_same_hospital', 'ward_same_hhs', 'icu_death', 'icu_to_icu_transfer',
                'direct_home', 'interhospital_transfer_without_followup'}
CENSORS = {'completed_72h', 'hospital_discharge', 'interhospital_transfer', 'death', 'unknown'}
COST_SEGMENTS = {'index_ready_to_departure', 'return_episode', 'incremental_service'}


class ContractError(ValueError):
    """Privacy-safe validation failure (never contains row contents or IDs)."""


def _reject(message: str) -> None:
    raise ContractError(message)


def _check(condition: bool, message: str) -> None:
    if not condition:
        _reject(message)


def _parse_dt(value: str, field: str, table: str, index: int, optional: bool=False) -> datetime | None:
    if not value and optional:
        return None
    try:
        result = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        _reject(f'{table} row {index}: invalid datetime in {field}')
    if result.tzinfo is None or result.utcoffset() is None:
        _reject(f'{table} row {index}: timezone offset required in {field}')
    return result


def _numeric(value: str, table: str, index: int, field: str, *, integral: bool=False) -> Decimal:
    try:
        n = Decimal(value)
    except (TypeError, InvalidOperation):
        _reject(f'{table} row {index}: invalid numeric in {field}')
    _check(n.is_finite() and n >= 0, f'{table} row {index}: negative/nonfinite {field}')
    if integral:
        _check(n == n.to_integral_value(), f'{table} row {index}: noninteger {field}')
    return n


def _safe_id(value: str, table: str, index: int, field: str) -> str:
    _check(isinstance(value, str) and bool(value.strip()) and len(value.encode()) <= 128,
           f'{table} row {index}: empty/oversized {field}')
    # This is a narrow accidental-direct-identifier guard, not de-identification.
    _check(not value.isdigit() and not re.match(r'(?i)^(mrn|urn|patient[_ -]?id)[=: _-]', value),
           f'{table} row {index}: direct identifier pattern in {field}')
    return value


def _read_manifest(manifest_file: Path, folder: Path, root: Path, allow_restricted: bool) -> dict:
    _check(manifest_file.is_file() and not manifest_file.is_symlink(), 'manifest unavailable or symlink')
    try:
        m = json.loads(manifest_file.read_text(encoding='utf-8'))
    except (ValueError, OSError, UnicodeError):
        _reject('invalid manifest JSON')
    _check(type(m) is dict and m.get('schema_version') == 1, 'manifest schema version mismatch')
    kind = m.get('data_class')
    _check(kind in {'synthetic_example', 'restricted_local_extract'}, 'unsupported data class')
    _check(m.get('clock_timezone') == 'Australia/Brisbane', 'unqualified timezone semantics')
    _check(isinstance(m.get('source_system'),str) and bool(m['source_system'].strip()),
           'missing source identity')
    if kind == 'restricted_local_extract':
        _check(allow_restricted, 'restricted extract requires explicit --allow-restricted-local')
        _check(not folder.resolve().is_relative_to(root.resolve()),
               'restricted data cannot be stored inside project source')
        _check(all(isinstance(m.get(k),str) and m[k].strip() for k in
                   ('governance_reference', 'approval_reference', 'extract_owner_role', 'site')),
               'restricted extract requires governance and approval metadata')
    else:
        _check(m.get('site') == 'fictional_test_facility',
               'synthetic extract must identify fictional facility')
    captures = m.get('capture_status')
    _check(isinstance(captures,dict) and all(v in {'synthetic_partial','not_verified','source_coverage_verified'}
                      for v in captures.values()), 'invalid capture status declaration')
    _check(set(m.get('tables', {})) == set(SUPPORTED_TABLES), 'missing/extra table declaration')
    for table, info in m['tables'].items():
        _check(isinstance(info,dict) and set(info) == {'file','sha256','column_map'},
               'invalid table manifest shape')
        _check(info['file'] == table+'.csv', 'noncanonical or unsafe input filename')
        _check(isinstance(info['sha256'],str) and re.fullmatch(r'[a-f0-9]{64}',info['sha256']) is not None,
               'invalid sha256 input digest')
        cmap = info['column_map']
        _check(isinstance(cmap,dict) and set(cmap) <= set(SUPPORTED_TABLES[table]) and
               all(isinstance(k,str) and isinstance(v,str) and v.strip() for k,v in cmap.items()) and
               len(set(cmap.values())) == len(cmap.values()),
               'invalid or non-injective column_map')
    return m


def _load_csv(folder: Path, table: str, info: dict) -> list[dict[str,str]]:
    path = folder / info['file']
    _check(path.is_file() and not path.is_symlink(), f'{table}: file unavailable or symlink')
    _check(path.stat().st_size <= MAX_FILE_SIZE, f'{table}: oversize file')
    raw = path.read_bytes()
    _check(hashlib.sha256(raw).hexdigest() == info['sha256'], f'{table}: sha256 mismatch')
    try:
        content = raw.decode('utf-8-sig')
        reader = csv.DictReader(content.splitlines(), strict=True)
        header = reader.fieldnames
        _check(isinstance(header,list) and len(header) == len(set(header)),
               f'{table}: duplicate/missing header')
        cmap = info['column_map']
        fields = SUPPORTED_TABLES[table]
        mapping = {k:cmap.get(k,k) for k in fields}
        _check(len(set(mapping.values()))==len(mapping), f'{table}: column_map collision')
        _check(set(header) == set(mapping.values()), f'{table}: unexpected column/schema drift')
        result=[]
        for index,row in enumerate(reader, start=2):
            _check(index-1 <= MAX_ROWS, f'{table}: excessive rows')
            _check(None not in row and all(value is not None for value in row.values()),
                   f'{table} row {index}: malformed column count')
            result.append({k:row[source_key] for k,source_key in mapping.items()})
        return result
    except (UnicodeError, csv.Error):
        _reject(f'{table}: malformed UTF-8 or CSV')


def inspect_extract(input_dir: str | Path, manifest: str | Path,
                    dictionary: str | Path, protocol: str | Path,
                    *, project_root: str | Path, allow_restricted_local: bool=False) -> dict[str,Any]:
    """Return identifier-free QC. Never certify local completeness or treatment effects."""
    folder=Path(input_dir)
    root=Path(project_root)
    _check(folder.is_dir() and not folder.is_symlink(), 'extract directory unavailable or symlink')
    m=_read_manifest(Path(manifest),folder,root,allow_restricted_local)
    d=load_data_dictionary(dictionary)
    try:
        p=json.loads(Path(protocol).read_text(encoding='utf-8'))
    except (ValueError,OSError):
        _reject('protocol unavailable or malformed')
    _check(p.get('schema_version')==1 and p.get('eligibility',{}).get('analysis_unit') ==
           'first_eligible_live_ward_discharge_per_hospitalisation',
           'protocol cohort definition mismatch')
    _check(p.get('economics',{}).get('price_year') == 2026 and
           p['economics'].get('currency') == 'AUD', 'unqualified cost currency or price year')
    known = {f['name'] for f in d['fields']}
    mapped={x for columns in SUPPORTED_TABLES.values() for x in columns}
    _check((mapped-ADDITIONAL_TRANSPORT_KEYS) <= known, 'projected field missing from P2 dictionary')
    tables={name:_load_csv(folder,name,info) for name,info in m['tables'].items()}
    episodes=tables['episodes']
    by_episode={}
    by_hospital=defaultdict(list)
    missing_ready=0
    for index,row in enumerate(episodes,2):
        hosp=_safe_id(row['hospitalisation_pseudonym'],'episodes',index,'hospitalisation_pseudonym')
        ep=_safe_id(row['index_icu_episode_id'],'episodes',index,'index_icu_episode_id')
        key=(hosp,ep)
        _check(key not in by_episode, 'episodes: duplicate hospitalisation/episode identity')
        admission=_parse_dt(row['icu_admission_at'],'icu_admission_at','episodes',index)
        depart=_parse_dt(row['icu_actual_departure_at'],'icu_actual_departure_at','episodes',index)
        ready=_parse_dt(row['icu_medically_ready_at'],'icu_medically_ready_at','episodes',index,optional=True)
        end=_parse_dt(row['followup_observation_end_at'],'followup_observation_end_at','episodes',index)
        final=_parse_dt(row['hospitalisation_final_departure_at'],'hospitalisation_final_departure_at','episodes',index,optional=True)
        death=_parse_dt(row['hospital_death_at'],'hospital_death_at','episodes',index,optional=True)
        _check(admission <= depart <= end, f'episodes row {index}: admission/departure/observation chronology')
        _check(ready is None or admission <= ready <= depart,
               f'episodes row {index}: discharge readiness chronology')
        _check(final is None or end <= final, f'episodes row {index}: follow-up exceeds hospital separation')
        _check(death is None or (depart <= death and (final is None or death <= final)),
               f'episodes row {index}: death chronology')
        _check(row['destination_category'] in DESTINATIONS, f'episodes row {index}: unsupported destination')
        _check(row['censor_reason'] in CENSORS, f'episodes row {index}: unsupported censor reason')
        if row['censor_reason'] == 'death':
            _check(death == end, f'episodes row {index}: death/censor timestamp mismatch')
        if row['censor_reason']=='completed_72h':
            _check((end-depart).total_seconds() >= 72*3600,
                   f'episodes row {index}: incomplete follow-up labelled completed')
        age=_numeric(row['adult_age_at_icu_admission_years'],'episodes',index,'age',integral=True)
        _check(age <= 120, f'episodes row {index}: invalid age')
        if ready is None:missing_ready+=1
        record={'key':key,'admission':admission,'departure':depart,'ready':ready,
                'observed_until':end,'censor_reason':row['censor_reason'],
                'destination':row['destination_category'],'age':int(age)}
        by_episode[key]=record
        by_hospital[hosp].append(record)

    def get_key(row,table,index,allow_service=False):
        if allow_service and not row.get('hospitalisation_pseudonym') and not row.get('index_icu_episode_id'):
            return None
        key=(_safe_id(row['hospitalisation_pseudonym'],table,index,'hospitalisation_pseudonym'),
             _safe_id(row['index_icu_episode_id'],table,index,'index_icu_episode_id'))
        _check(key in by_episode, f'{table} row {index}: orphan event/episode join')
        return key

    returns=defaultdict(list)
    seen_returns=set()
    for index,row in enumerate(tables['returns'],2):
        key=get_key(row,'returns',index)
        rid=_safe_id(row['return_episode_id'],'returns',index,'return_episode_id')
        _check(rid not in seen_returns, 'returns: duplicate return episode identity')
        seen_returns.add(rid)
        at=_parse_dt(row['icu_readmission_at'],'icu_readmission_at','returns',index)
        parent=by_episode[key]
        _check(parent['departure'] <= at <= parent['observed_until'],
               f'returns row {index}: chronology incompatible with episode follow-up')
        planned=row['readmission_planned_status']
        _check(planned in {'planned','unplanned','unknown'},f'returns row {index}: invalid planned status')
        returns[key].append(ReturnEvent(at=at,planned=planned))

    seen_contacts=set()
    for index,row in enumerate(tables['contacts'],2):
        key=get_key(row,'contacts',index)
        cid=_safe_id(row['contact_id'],'contacts',index,'contact_id')
        _check(cid not in seen_contacts, 'contacts: duplicate contact identity')
        seen_contacts.add(cid)
        at=_parse_dt(row['liaison_contact_at'],'liaison_contact_at','contacts',index)
        _check(by_episode[key]['admission'] <= at <= by_episode[key]['observed_until'],
               f'contacts row {index}: contact timestamp chronology')
        _check(bool(row['liaison_intervention_type']), f'contacts row {index}: missing intervention')

    seen_events=set()
    arrests=0
    for index,row in enumerate(tables['safety_events'],2):
        key=get_key(row,'safety_events',index)
        event=_safe_id(row['event_id'],'safety_events',index,'event_id')
        _check(event not in seen_events,'safety_events: duplicate event identity')
        seen_events.add(event)
        _check(row['event_type'] in {'ward_cardiac_arrest','deterioration'},
               f'safety_events row {index}: event category invalid')
        parent=by_episode[key]
        actual=_parse_dt(row['ward_cardiac_arrest_at'],'ward_cardiac_arrest_at','safety_events',index,optional=True)
        recognised=_parse_dt(row['deterioration_recognised_at'],'deterioration_recognised_at','safety_events',index,optional=True)
        responded=_parse_dt(row['escalation_responded_at'],'escalation_responded_at','safety_events',index,optional=True)
        _check((recognised is None and responded is None) or
               (recognised is not None and responded is not None and recognised <= responded),
               f'safety_events row {index}: escalation chronology')
        for timestamp in (actual,recognised,responded):
            _check(timestamp is None or parent['departure'] <= timestamp <= parent['observed_until'],
                   f'safety_events row {index}: ward episode chronology')
        if row['event_type']=='ward_cardiac_arrest':
            _check(actual is not None, f'safety_events row {index}: missing cardiac arrest time')
            arrests+=1
        else:
            _check(actual is None, f'safety_events row {index}: incompatible arrest event')

    costids=set()
    segments=Counter()
    for index,row in enumerate(tables['cost_lines'],2):
        ident=_safe_id(row['cost_ledger_entry_id'],'cost_lines',index,'cost_ledger_entry_id')
        _check(ident not in costids, 'cost_lines: duplicate cost ledger entry across segments')
        costids.add(ident)
        seg=row['cost_resource_segment']
        _check(seg in COST_SEGMENTS, f'cost_lines row {index}: unknown resource segment')
        key=get_key(row,'cost_lines',index,allow_service=True)
        _check((key is None)==(seg=='incremental_service'),
               f'cost_lines row {index}: service vs episode resource identity mismatch')
        _numeric(row['cost_resource_quantity'],'cost_lines',index,'cost_resource_quantity')
        _numeric(row['cost_unit_quotation'],'cost_lines',index,'cost_unit_quotation')
        _check(row['cost_currency']=='AUD' and row['cost_price_year']=='2026',
               f'cost_lines row {index}: cost perspective/currency or price-year mismatch')
        _check(seg!='return_episode' or bool(returns.get(key)),
               f'cost_lines row {index}: return cost without linked return episode')
        segments[seg]+=1

    eligible=[]
    for hospital, records in by_hospital.items():
        options=[r for r in records if r['age']>=16 and r['destination'] in {'ward_same_hospital','ward_same_hhs'}]
        if options: eligible.append(min(options,key=lambda r:(r['departure'],r['key'][1])))
    counts=Counter();missing_index=0;block=0;after_hours=0;observed_delay=0;deaths=0
    for row in eligible:
        try:
            result=classify_transition(TransitionObservation(
                clinically_ready_at=row['ready'],
                physical_departure_at=row['departure'],
                observed_until=row['observed_until'],
                returns=returns.get(row['key'],[]),
                censor_reason=row['censor_reason'],
            ))
        except ValueError:
            _reject('episode transition clock or censor invalid')
        if result.delay_hours is None:missing_index+=1
        else:
            observed_delay+=1
            block+=int(result.exit_block_ge12h)
        after_hours+=int(result.after_hours_departure)
        code='unknown' if result.unplanned_return_within_72h is None else (
            'unplanned_yes' if result.unplanned_return_within_72h else 'unplanned_no')
        counts[code]+=1
        deaths+=int(result.competing_death)
    n=len(eligible)
    _check(n>0, 'no eligible index discharges in extract')
    yes=counts['unplanned_yes'];no=counts['unplanned_no'];unknown=counts['unknown']
    _check(yes+no+unknown==n, 'readmission cohort accounting invalid')
    fields_used={c for schema in SUPPORTED_TABLES.values() for c in schema if c in known}
    return {
        'schema_version':1,
        'status':'SYNTHETIC_DIAGNOSTIC_ONLY' if m['data_class']=='synthetic_example' else 'LOCAL_EXTRACT_DIAGNOSTIC_ONLY',
        'ready_for_local_effect_estimation':False,
        'ready_for_investment_claims':False,
        'source_manifest_sha256':hashlib.sha256(Path(manifest).read_bytes()).hexdigest(),
        'data_class':m['data_class'],
        'data_quality':{
            'table_counts':{t:len(rows) for t,rows in tables.items()},
            'missingness':{'icu_medically_ready_at':missing_ready,
                           'followup_observation_end_at':sum(not r['followup_observation_end_at'] for r in episodes)},
            'implemented_p2_dictionary_fields':len(fields_used),
            'unmapped_p2_dictionary_fields':len(known-fields_used),
            'capture_coverage_qualified':False,
            'unit_specific_completeness_threshold_approved':False,
        },
        'cohort':{
            'eligible_index_discharges':n,
            'nonindex_eligible_episodes':sum(max(0,len([r for r in x if r['age']>=16 and
                    r['destination'] in {'ward_same_hospital','ward_same_hhs'}])-1) for x in by_hospital.values()),
            'all_icu_episode_rows':len(episodes),
            'index_denominator':'first_eligible_live_ward_discharge_per_hospitalisation',
        },
        'discharge_delay':{
            'known_ready_count':observed_delay,
            'missing_ready_count':missing_index,
            'exit_block_ge12h_count':block,
            'observed_rate_given_known_ready':block/observed_delay if observed_delay else None,
            'lower_bound_all_eligible':block/n,
            'upper_bound_all_eligible':(block+missing_index)/n,
            'after_hours_departure_count':after_hours,
        },
        'readmission_72h':{
            'unplanned_yes':yes, 'unplanned_no':no, 'unknown':unknown,
            'observed_rate':yes/(yes+no) if yes+no else None,
            'lower_bound_all_eligible':yes/n,
            'upper_bound_all_eligible':(yes+unknown)/n,
            'competing_deaths':deaths,
            'denominator':'first_eligible_live_ward_discharge_per_hospitalisation',
            'not_equivalent_to':'ANZICS_CCR_all_admission_episode_rate_or_APD_patient_readmission_rate',
        },
        'safety':{'ward_cardiac_arrests_observed':arrests,
                  'capture_completeness_verified':False},
        'costing':{'segments':{s:segments[s] for s in sorted(COST_SEGMENTS)},
                   'financial_costs_calculated':False,
                   'resource_valuation_provider':'Dapane_separate_gate'},
        'errors':[],
        'limitations':[
            'Source coverage claims in a manifest are not independent evidence of data completeness.',
            'No official local outcome or cash-saving inference is permitted from this diagnostic.',
            'Only a subset of the P2 32-field dictionary is mapped; clinical case mix and safety review remain open.',
            'No patient-level data or valuation totals are emitted.',
        ]
    }
