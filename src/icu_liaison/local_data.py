"""P3 local-source intake: bounded CSV contracts, linkage and aggregate-only QA.

The caller is responsible for obtaining approval and pseudonymising data before
this utility sees it. This module cannot validate clinical coding or confer
privacy/governance authority. No raw patient/event rows leave its output.
"""
from __future__ import annotations
from typing import Any

import csv
from collections import Counter, defaultdict
from collections.abc import Callable, Sequence
from datetime import datetime
from decimal import Decimal
import hashlib
from pathlib import Path
import re
from typing import Literal

from .schemas import SchemaVersion
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, ValidationError, model_validator

from .endpoints import ReturnEvent, TransitionObservation, classify_transition

MAX_FILE_BYTES = 100 * 1024 * 1024
MAX_ROWS = 1_000_000
TOKEN = re.compile(r'^[A-Za-z][A-Za-z0-9_-]{7,127}$')
SHA = re.compile(r'^[a-f0-9]{64}$')


class LocalDatasetError(ValueError):
    """Refusal to accept a nonconforming local-data package (no row contents)."""


class _Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_assignment=True)


class Governance(_Strict):
    model_config = ConfigDict(strict=True)
    status: Literal['not_applicable_synthetic', 'approved_local_processing']
    approval_reference: str | None = None
    custodian_role: str | None = None


class FileSpec(_Strict):
    model_config = ConfigDict(strict=True)
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    column_map: dict[str, str] = Field(default_factory=dict)


class DatasetManifest(_Strict):
    model_config = ConfigDict(strict=True)
    schema_version: SchemaVersion
    data_class: Literal['synthetic', 'restricted']
    description: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    extracted_at: AwareDatetime
    governance: Governance
    files: dict[str, FileSpec]

    @model_validator(mode='after')
    def check_required_feeds(self) -> 'DatasetManifest':
        if not {'episodes', 'followup'} <= set(self.files):
            raise ValueError('episodes and followup feeds are required')
        if set(self.files) - {'episodes', 'followup', 'liaison_contacts', 'cost_lines'}:
            raise ValueError('unsupported feed type')
        if self.data_class == 'restricted':
            if (self.governance.status != 'approved_local_processing' or
                not self.governance.approval_reference or
                not self.governance.custodian_role):
                raise ValueError('restricted dataset needs specific governance attestation')
        elif self.governance.status != 'not_applicable_synthetic':
            raise ValueError('synthetic profile cannot claim local governance approval')
        return self


class Episode(_Strict):
    hospitalisation_pseudonym: str
    index_icu_episode_id: str
    icu_admission_at: AwareDatetime
    icu_medically_ready_at: AwareDatetime | None = None
    icu_actual_departure_at: AwareDatetime
    destination_category: Literal[
        'ward_same_hospital', 'ward_same_hhs', 'direct_home', 'icu_to_icu_transfer',
        'interhospital_transfer_without_followup', 'icu_death', 'other',
    ]
    adult_age_at_icu_admission_years: int = Field(ge=0, le=120)
    readmission_planned_status: Literal['not_applicable', 'planned', 'unplanned', 'unknown']

    @model_validator(mode='after')
    def check_times(self) -> 'Episode':
        if self.icu_admission_at > self.icu_actual_departure_at:
            raise ValueError('ICU departure before admission')
        if self.icu_medically_ready_at is not None and not (
            self.icu_admission_at <= self.icu_medically_ready_at <= self.icu_actual_departure_at
        ):
            raise ValueError('readiness outside ICU episode')
        return self


class Followup(_Strict):
    hospitalisation_pseudonym: str
    followup_observation_end_at: AwareDatetime
    censor_reason: Literal['completed_72h', 'hospital_discharge', 'interhospital_transfer', 'death', 'unknown']
    hospitalisation_final_departure_at: AwareDatetime | None = None
    hospital_death_at: AwareDatetime | None = None

    @model_validator(mode='after')
    def check_times(self) -> 'Followup':
        if self.censor_reason == 'death' and (
            self.hospital_death_at is None or self.hospital_death_at != self.followup_observation_end_at
        ):
            raise ValueError('death censor requires death at observed end')
        if self.censor_reason != 'death' and self.hospital_death_at is not None:
            raise ValueError('hospital death must be classified as death censor')
        if (self.hospitalisation_final_departure_at is not None and
            self.followup_observation_end_at > self.hospitalisation_final_departure_at):
            raise ValueError('observation cannot extend beyond final hospital departure')
        return self


class Contact(_Strict):
    hospitalisation_pseudonym: str
    index_icu_episode_id: str
    liaison_contact_at: AwareDatetime
    liaison_intervention_type: str = Field(min_length=1)


class CostLine(_Strict):
    hospitalisation_pseudonym: str
    index_icu_episode_id: str
    cost_ledger_entry_id: str
    cost_resource_segment: Literal['index_ready_to_departure', 'post_departure_return']
    cost_resource_quantity: Decimal = Field(ge=0)
    cost_unit_quotation: Decimal = Field(ge=0)
    cost_currency: Literal['AUD']
    cost_price_year: int = Field(ge=2000, le=2100)
    cost_basis: Literal['economic_cost', 'financial_cost']
    cost_use_id: str
    cost_component_id: str


FEED_MODELS: dict[str, type[_Strict]] = {
    'episodes': Episode,
    'followup': Followup,
    'liaison_contacts': Contact,
    'cost_lines': CostLine,
}


def _validate_token(value: str, role: str) -> None:
    # This catches obvious raw numeric identifiers; cryptographic
    # de-identification must be externally attested and cannot be inferred here.
    if not TOKEN.fullmatch(value):
        raise LocalDatasetError(f'{role}: invalid pseudonym or key syntax; reject raw numeric IDs')


def _read_feed[T: _Strict](root: Path, name: str, spec: FileSpec, model: type[T]) -> list[T]:
    if Path(spec.path).is_absolute() or '..' in Path(spec.path).parts:
        raise LocalDatasetError(f'{name}: unsafe relative source path')
    file = root / spec.path
    if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(root.resolve()):
        raise LocalDatasetError(f'{name}: missing, symlink or escaped source file')
    if file.stat().st_size > MAX_FILE_BYTES:
        raise LocalDatasetError(f'{name}: source exceeds bounded file limit')
    raw = file.read_bytes()
    if hashlib.sha256(raw).hexdigest() != spec.sha256:
        raise LocalDatasetError(f'{name}: sha256 mismatch; source may have drifted')
    if b'\x00' in raw:
        raise LocalDatasetError(f'{name}: binary content rejected')
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError as e:
        raise LocalDatasetError(f'{name}: invalid UTF-8') from e
    expected = set(model.model_fields)
    from io import StringIO
    reader = csv.DictReader(StringIO(text), restkey='__unexpected_values__', restval=None)
    if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise LocalDatasetError(f'{name}: missing or duplicate source headers')
    if any(k not in reader.fieldnames for k in spec.column_map):
        raise LocalDatasetError(f'{name}: mapping key absent from headers')
    remapped = [spec.column_map.get(k, k) for k in reader.fieldnames]
    if set(remapped) != expected or len(set(remapped)) != len(remapped):
        raise LocalDatasetError(f'{name}: unknown, missing or duplicated canonical columns')
    rows = []
    try:
        for i, row in enumerate(reader, start=1):
            if i > MAX_ROWS:
                raise LocalDatasetError(f'{name}: row limit exceeded')
            if '__unexpected_values__' in row or any(v is None for v in row.values()):
                raise LocalDatasetError(f'{name}: malformed CSV row width')
            clean = {spec.column_map.get(key, key): value if value != '' else None
                     for key, value in row.items()}
            rows.append(model.model_validate(clean))
    except (ValidationError, csv.Error) as e:
        # Do not echo Pydantic errors; they can include patient-level input values.
        raise LocalDatasetError(f'{name}: field or timestamp validation failed') from e
    return rows


def load_and_audit(
    manifest_path: Path, *, restricted_acknowledged: bool = False,
    data_dictionary_path: Path | None = None,
    before_restricted_read: Callable[[], None] | None = None,
) -> dict[str, Any]:
    """Derive aggregate clinical and source-quality counts from versioned feeds.

    Fails closed on invalid source lineage, unknown columns, episode overlaps,
    duplicate IDs and missing hospitalisation follow-up. Never emits row data.
    A flag only records operator acknowledgement; it does not grant approval.
    The CLI checks its output destination before any restricted feed is read.
    """
    path = Path(manifest_path)
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 128_000:
        raise LocalDatasetError('missing or invalid source manifest')
    try:
        manifest_bytes = path.read_bytes()
        if len(manifest_bytes) > 128_000:
            raise LocalDatasetError('source manifest exceeds the file limit')
        manifest = DatasetManifest.model_validate_json(manifest_bytes)
    except (ValidationError, UnicodeDecodeError) as e:
        raise LocalDatasetError('source manifest or governance invalid') from e
    if manifest.data_class == 'restricted':
        if not restricted_acknowledged:
            raise LocalDatasetError('restricted data requires explicit operator acknowledgement')
        if before_restricted_read is not None:
            before_restricted_read()
    root = path.resolve().parent
    ep = _read_feed(root, 'episodes', manifest.files['episodes'], Episode)
    fu = _read_feed(root, 'followup', manifest.files['followup'], Followup)
    contacts = (_read_feed(root, 'liaison_contacts', manifest.files['liaison_contacts'], Contact)
                if 'liaison_contacts' in manifest.files else [])
    costs = (_read_feed(root, 'cost_lines', manifest.files['cost_lines'], CostLine)
             if 'cost_lines' in manifest.files else [])
    feeds: dict[str, Sequence[_Strict]] = {'episodes': ep, 'followup': fu}
    if 'liaison_contacts' in manifest.files:
        feeds['liaison_contacts'] = contacts
    if 'cost_lines' in manifest.files:
        feeds['cost_lines'] = costs
    if not ep or not fu:
        raise LocalDatasetError('episodes and followup must be nonempty')
    last_departure = max(e.icu_actual_departure_at for e in ep)
    if last_departure > manifest.extracted_at:
        raise LocalDatasetError('extraction timestamp predates an observed ICU episode')
    if any(
        (row.hospitalisation_final_departure_at or row.followup_observation_end_at) > manifest.extracted_at
        for row in fu
    ):
        raise LocalDatasetError('extraction timestamp predates observed hospital followup or separation')
    for episode in ep:
        _validate_token(episode.hospitalisation_pseudonym, 'hospitalisation pseudonym')
        _validate_token(episode.index_icu_episode_id, 'ICU episode key')
    keys = [e.index_icu_episode_id for e in ep]
    if len(keys) != len(set(keys)):
        raise LocalDatasetError('duplicate ICU episode identifier')
    seen_hosp = [f.hospitalisation_pseudonym for f in fu]
    if len(seen_hosp) != len(set(seen_hosp)):
        raise LocalDatasetError('duplicate hospitalisation followup')
    by_hosp: dict[str, list[Episode]] = defaultdict(list)
    for episode in ep:
        by_hosp[episode.hospitalisation_pseudonym].append(episode)
    followup = {f.hospitalisation_pseudonym: f for f in fu}
    if set(by_hosp) != set(followup):
        raise LocalDatasetError('hospitalisation followup linkage missing or orphaned')
    by_episode = {e.index_icu_episode_id: e for e in ep}
    ordered: dict[str, list[Episode]] = {}
    for h, episodes in by_hosp.items():
        timeline = sorted(episodes, key=lambda e: (e.icu_admission_at, e.index_icu_episode_id))
        for left, right in zip(timeline, timeline[1:]):
            if right.icu_admission_at < left.icu_actual_departure_at:
                raise LocalDatasetError('overlap between ICU episodes in same hospitalisation')
        observation_end = followup[h].followup_observation_end_at
        if timeline[-1].icu_actual_departure_at > observation_end:
            raise LocalDatasetError('ICU episode outside hospital followup interval')
        ordered[h] = timeline

    seen_contacts = set()
    for contact in contacts:
        ep_ref = by_episode.get(contact.index_icu_episode_id)
        if ep_ref is None or ep_ref.hospitalisation_pseudonym != contact.hospitalisation_pseudonym:
            raise LocalDatasetError('orphaned liaison contact episode')
        if not (ep_ref.icu_admission_at <= contact.liaison_contact_at <= followup[contact.hospitalisation_pseudonym].followup_observation_end_at):
            raise LocalDatasetError('liaison contact outside permitted hospital episode')
        contact_key=(contact.index_icu_episode_id,contact.liaison_contact_at,contact.liaison_intervention_type)
        if contact_key in seen_contacts:
            raise LocalDatasetError('duplicate liaison contact')
        seen_contacts.add(contact_key)

    seen_lines = set()
    seen_components = set()
    use_segments: dict[str, str] = {}
    for cost in costs:
        ep_ref = by_episode.get(cost.index_icu_episode_id)
        if ep_ref is None or ep_ref.hospitalisation_pseudonym != cost.hospitalisation_pseudonym:
            raise LocalDatasetError('orphaned cost ledger episode')
        _validate_token(cost.cost_ledger_entry_id, 'cost ledger key')
        if cost.cost_ledger_entry_id in seen_lines:
            raise LocalDatasetError('duplicate cost line identity')
        seen_lines.add(cost.cost_ledger_entry_id)
        component=(cost.cost_use_id,cost.cost_component_id)
        if component in seen_components:
            raise LocalDatasetError('duplicate cost component for resource use')
        seen_components.add(component)
        if cost.cost_use_id in use_segments and use_segments[cost.cost_use_id] != cost.cost_resource_segment:
            raise LocalDatasetError('resource use spans incompatible cost segments')
        use_segments[cost.cost_use_id] = cost.cost_resource_segment

    cohort=Counter({
        key: 0 for key in (
            'eligible_index_discharges', 'index_with_readiness',
            'index_exit_block_ge12h', 'index_after_hours_departure',
            'unplanned_return_within_72h', 'early_return_unknown',
            'early_return_observed_no_event', 'followup_complete_72h',
            'competing_death_before_return',
        )
    })
    cohort['all_icu_episodes']=len(ep)
    cohort['hospitalisations']=len(by_hosp)
    reasons: Counter[str] = Counter()
    expected=0
    index_delay_hours = 0.0
    for hospital, episodes in ordered.items():
        eligible=[e for e in episodes if e.adult_age_at_icu_admission_years >= 16 and
                  e.destination_category in {'ward_same_hospital','ward_same_hhs'}]
        if not eligible:
            continue
        index=eligible[0]
        observed=followup[hospital]
        expected += 1
        if index.icu_actual_departure_at > observed.followup_observation_end_at:
            raise LocalDatasetError('index episode discharge after followup end')
        subsequent=[e for e in episodes if e.icu_admission_at >= index.icu_actual_departure_at
                    and e.index_icu_episode_id != index.index_icu_episode_id]
        returns=[ReturnEvent(at=e.icu_admission_at,planned=(e.readmission_planned_status if
                        e.readmission_planned_status != 'not_applicable' else 'unknown')) for e in subsequent]
        try:
            result=classify_transition(TransitionObservation(
                clinically_ready_at=index.icu_medically_ready_at,
                physical_departure_at=index.icu_actual_departure_at,
                observed_until=observed.followup_observation_end_at,
                returns=returns,
                censor_reason=observed.censor_reason,
            ))
        except ValueError as e:
            raise LocalDatasetError('clinical transition timing or followup invalid') from e
        cohort['index_with_readiness'] += result.delay_hours is not None
        if result.delay_hours is not None:
            index_delay_hours += result.delay_hours
        cohort['index_exit_block_ge12h'] += result.exit_block_ge12h is True
        cohort['index_after_hours_departure'] += result.after_hours_departure
        cohort['unplanned_return_within_72h'] += result.unplanned_return_within_72h is True
        cohort['early_return_unknown'] += result.unplanned_return_within_72h is None
        cohort['early_return_observed_no_event'] += result.unplanned_return_within_72h is False
        cohort['followup_complete_72h'] += result.followup_complete_72h
        cohort['competing_death_before_return'] += result.competing_death
        reasons[observed.censor_reason] += 1
    cohort['eligible_index_discharges']=expected
    cohort['index_discharge_denominator_differs_from_CCR']=True

    # All field names are registered from the P2 dictionary. Missing feeds are
    # explicitly not observed; these counts are audit indicators, not approval.
    identity_feeds = {'hospitalisation_pseudonym': 'followup', 'index_icu_episode_id': 'episodes'}
    observed_by_field: dict[str, dict[str,int|str|None]]={}
    for name, model in FEED_MODELS.items():
        if name in feeds:
            for field in model.model_fields:
                if field in identity_feeds and identity_feeds[field] != name:
                    continue
                values=[getattr(row,field) for row in feeds[name]]
                observed_by_field[field]={
                    'source_feed':name,'present':sum(v is not None for v in values),
                    'missing':sum(v is None for v in values), 'status':'synthetic_or_unvalidated_import',
                }
    # The P2 dictionary may be supplied only in the destination repository;
    # report fields that this bounded source profile cannot derive.
    from .protocol import load_data_dictionary
    dictionary_path = (Path(data_dictionary_path) if data_dictionary_path is not None else
                       Path(__file__).resolve().parents[2] / 'model-inputs/clinical-data-dictionary.json')
    dictionary=load_data_dictionary(dictionary_path)
    fields={}
    for f in dictionary['fields']:
        key=f['name']
        fields[key]=observed_by_field.get(key,{
            'source_feed':None,'present':0,'missing':None,'status':'not_supplied_or_not_mapped',
        })
    if cohort['eligible_index_discharges'] and cohort['index_with_readiness'] > cohort['eligible_index_discharges']:
        raise LocalDatasetError('invalid readiness denominator')
    return {
        'schema_version':1,'data_class':manifest.data_class,
        'source_reference_sha256':hashlib.sha256(manifest.source_id.encode('utf-8')).hexdigest(),
        'interpretation':'aggregate_data_quality_report_not_local_clinical_or_economic_approval',
        'input_provenance':{
            'manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest(),
            'feed_sha256':{k:v.sha256 for k,v in manifest.files.items()},
        },
        'cohort':dict(cohort),
        'index_ready_delay': {
            'metric_id': 'M31', 'population_id': 'D03', 'denominator_id': 'D14',
            'eligible': expected, 'valid': cohort['index_with_readiness'],
            'missing': expected - cohort['index_with_readiness'],
            'mean_hours': index_delay_hours / cohort['index_with_readiness']
            if cohort['index_with_readiness'] else None,
        },
        'quality':{'field_completeness':fields, 'followup_censor_reason_counts':dict(reasons),
                   'missing_source_classes':['CHHHS_incident_MET','CHHHS_workforce',
                                             'CHHHS_patient_experience'],
                   'no_missing_as_zero_imputation':True,
                   'cost_basis_and_price_year_need_finance_approval':True,
                   'source_freshness':{
                       'source_extracted_at':manifest.extracted_at.isoformat(),
                       'days_since_last_episode_at_extraction':(manifest.extracted_at-last_departure).days,
                       'freshness_admission':'threshold_not_approved',
                   }},
        'safety_outcomes_qualified':False,
        'investment_ready':False,
        'reference_benchmark_role':'public_external_context_never_local_denominator',
    }
