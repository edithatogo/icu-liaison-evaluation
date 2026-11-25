"""P2 clinical/economic analysis protocol: machine-readable, fail-closed draft.

This is a *specification* and an admission gate for illustrative P1 inputs,
not a clinical service-approval, causal estimator, data reader or costing engine.
"""
from __future__ import annotations
from typing import Any

from collections.abc import Mapping
import hashlib
import json
from math import isclose
from pathlib import Path
from typing import Literal

from .schemas import SchemaVersion
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .schemas import Inputs, Scenario


class StrictContract(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid', validate_assignment=True)


class Strategy(StrictContract):
    id: Literal['current_care', 'liaison_service']
    role: Literal['observed_comparator', 'proposed_incremental']
    evidence_status: Literal['not_verified', 'locally_verified']
    activities: list[str] = Field(min_length=1)
    funded_fte: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    hours_of_coverage_per_week: float | None = Field(default=None, ge=0, le=168)
    current_work_absorbed_or_displaced: str
    site_source_reference: str | None = None

    @model_validator(mode='after')
    def guard_unverified_service(self) -> 'Strategy':
        if (self.funded_fte is not None or self.hours_of_coverage_per_week is not None) and (
            self.evidence_status != 'locally_verified' or not self.site_source_reference
        ):
            raise ValueError('funded FTE / coverage require a locally verified source')
        return self


class Eligibility(StrictContract):
    target_site: str = Field(min_length=1)
    minimum_age_years: int = Field(ge=0, le=120)
    analysis_unit: Literal['first_eligible_live_ward_discharge_per_hospitalisation']
    eligible_destinations: list[Literal['ward_same_hospital', 'ward_same_hhs']]
    excluded_dispositions: list[Literal['icu_death', 'icu_to_icu_transfer', 'direct_home', 'interhospital_transfer_without_followup']]
    repeat_episode_handling: Literal['first_index_discharge_for_primary_analysis_all_episodes_for_costing']
    hospitalisation_linkage: Literal['pseudonymous_hospitalisation_identifier_required']

    @model_validator(mode='after')
    def require_index_population(self) -> 'Eligibility':
        if (self.minimum_age_years < 16 or not self.eligible_destinations
            or len(set(self.eligible_destinations)) != len(self.eligible_destinations)):
            raise ValueError('eligibility requires nonduplicate ward destinations')
        if set(self.excluded_dispositions) != {
            'icu_death', 'icu_to_icu_transfer', 'direct_home',
            'interhospital_transfer_without_followup'
        }:
            raise ValueError('explicit excluded dispositions must be preserved')
        return self


class Endpoint(StrictContract):
    id: str = Field(min_length=1)
    role: Literal['primary_operational', 'secondary_operational', 'safety', 'context']
    denominator: str = Field(min_length=1)
    start_event: str = Field(min_length=1)
    end_event: str = Field(min_length=1)
    unit: str = Field(min_length=1)
    window_hours: int | None = Field(default=None, ge=0)
    threshold_hours: int | None = Field(default=None, ge=0)
    missing_data_policy: Literal['retain_unknown_and_report_completeness']
    interpretation: str = Field(min_length=1)


# Fixed observation semantics, not hospital-specific baseline rates.
# Keep P1 cost and denominator claims pinned to this local measurement design.
REQUIRED_ENDPOINTS: dict[str, dict[str, str | int]] = {
    'ready_to_physical_departure_hours': {
        'role': 'primary_operational',
        'denominator': 'eligible_index_live_ward_discharges',
        'start_event': 'clinical_discharge_readiness',
        'end_event': 'physical_icu_departure', 'unit': 'hours',
    },
    'exit_block_ge12h': {
        'role': 'secondary_operational',
        'denominator': 'eligible_index_live_ward_discharges',
        'start_event': 'clinical_discharge_readiness',
        'end_event': 'physical_icu_departure', 'unit': 'proportion',
        'threshold_hours': 12,
    },
    'unplanned_72h_return': {
        'role': 'primary_operational',
        'denominator': 'eligible_index_live_ward_discharges',
        'start_event': 'physical_icu_departure',
        'end_event': 'any_unplanned_icu_return_same_hospital_stay',
        'unit': 'proportion', 'window_hours': 72,
    },
    'after_hours_icu_discharge': {
        'role': 'secondary_operational',
        'denominator': 'eligible_index_live_ward_discharges',
        'start_event': 'physical_icu_departure',
        'end_event': 'local_time_1800_through_0559', 'unit': 'proportion',
    },
    'post_icu_death': {
        'role': 'safety',
        'denominator': 'eligible_index_live_ward_discharges',
        'start_event': 'physical_icu_departure',
        'end_event': 'death_before_final_hospital_discharge', 'unit': 'proportion',
    },
    'ward_cardiac_arrest': {
        'role': 'safety',
        'denominator': 'eligible_index_live_ward_discharges',
        'start_event': 'physical_icu_departure',
        'end_event': 'ward_cardiac_arrest_before_final_hospital_discharge', 'unit': 'proportion',
    },
    'delayed_escalation': {
        'role': 'safety',
        'denominator': 'eligible_index_live_ward_discharges',
        'start_event': 'ward_deterioration_recognised',
        'end_event': 'appropriate_escalation', 'unit': 'hours',
    },
    'return_severity_and_appropriateness': {
        'role': 'safety',
        'denominator': 'observed_icu_returns_after_index',
        'start_event': 'icu_return',
        'end_event': 'documented_rescue_and_severity_review', 'unit': 'clinical_review',
    },
    'ward_workload': {
        'role': 'safety',
        'denominator': 'eligible_index_live_ward_discharges',
        'start_event': 'physical_icu_departure',
        'end_event': 'ward_care_until_hospital_discharge', 'unit': 'staff_time',
    },
    'treatment_limitations': {
        'role': 'safety',
        'denominator': 'eligible_index_live_ward_discharges',
        'start_event': 'physical_icu_departure',
        'end_event': 'treatment_goals_reconciled', 'unit': 'clinical_review',
    },
}

REQUIRED_SAFETY = {
    identifier for identifier, fields in REQUIRED_ENDPOINTS.items() if fields['role'] == 'safety'
}


class Safety(StrictContract):
    required_endpoints: list[str] = Field(min_length=1)
    approved_noninferiority_margins: dict[str, float] = Field(default_factory=dict)
    measurements_status: Literal['unmeasured', 'locally_validated']
    decision_gate: Literal['safety_review_required_prior_to_investment_claim']


class CostComponent(StrictContract):
    id: str = Field(min_length=1)
    resource_segment: Literal['index_ready_to_departure', 'post_departure_return', 'incremental_service']
    calculation_role: Literal['avoided_index_delay', 'avoided_readmission', 'incremental_liaison_cost']
    valuation: Literal['incremental_net_of_ward', 'incremental_net_of_otherwise_care', 'additional_workforce_and_operations']
    price_basis: Literal['economic_cost']
    cash_status: Literal['not_assumed_realisable', 'actual_incremental_expenditure']


class Economics(StrictContract):
    primary_perspective: Literal['CHHHS_provider_cost_consequence']
    secondary_perspective: Literal['CHHHS_budget_impact_separate']
    currency: Literal['AUD']
    price_year: int = Field(ge=2000, le=2100)
    reference_input_price_year: int = Field(ge=2000, le=2100)
    evaluation_horizon_months: Literal[12]
    episode_followup: Literal['from_index_discharge_to_final_hospital_separation']
    apply_discounting_within_12_months: Literal[False]
    future_long_horizon_discount_rate_status: Literal['not_applicable_until_long_horizon_defined']
    index_delay_valuation: Literal['marginal_icu_less_incremental_ward_not_average_bed_cost']
    capacity_monetisation: Literal['physical_hours_only_until_actual_demand_and_cash_realisability_qualified']
    opportunity_cost_rule: Literal['count_once_separate_from_financial_cash']
    cost_components: list[CostComponent] = Field(min_length=3)

    @model_validator(mode='after')
    def economic_boundaries(self) -> 'Economics':
        if self.price_year != self.reference_input_price_year:
            raise ValueError('valuation price year differs from source input price year')
        scope = {c.resource_segment for c in self.cost_components}
        if len(scope) != len(self.cost_components):
            raise ValueError('overlap: resource segments must not be priced twice')
        if scope != {'index_ready_to_departure', 'post_departure_return', 'incremental_service'}:
            raise ValueError('exactly three nonoverlapping prototype cost segments required')
        by_scope: dict[str, CostComponent] = {c.resource_segment: c for c in self.cost_components}
        for segment, (role, valuation, cash) in {
            'index_ready_to_departure': ('avoided_index_delay', 'incremental_net_of_ward', 'not_assumed_realisable'),
            'post_departure_return': ('avoided_readmission', 'incremental_net_of_otherwise_care', 'not_assumed_realisable'),
            'incremental_service': ('incremental_liaison_cost', 'additional_workforce_and_operations', 'actual_incremental_expenditure'),
        }.items():
            c = by_scope[segment]
            if (c.calculation_role, c.valuation, c.cash_status) != (role, valuation, cash):
                raise ValueError(f'{segment} cost role and budget interpretation mismatch')
        return self


class Design(StrictContract):
    proposed_design: Literal['controlled_interrupted_time_series_or_phased_comparison']
    approval_status: Literal['candidate_unapproved']
    preferred_baseline_months: int = Field(ge=1, le=120)
    preferred_followup_months: int = Field(ge=1, le=120)
    confounders_to_measure: list[str] = Field(min_length=1)
    minimum_data_completeness_approved: float | None = Field(default=None, ge=0, le=1)
    governance_status: Literal['local_approval_not_established']
    equity_axes: list[str] = Field(min_length=1)


class ExternalBenchmark(StrictContract):
    source_id: str = Field(min_length=1)
    measure: Literal['exit_block_ge12h']
    value: float = Field(ge=0, le=1)
    unit: Literal['proportion']
    denominator: Literal['all_live_ward_home_discharges']
    population: Literal['pooled_all_ages_Australia_New_Zealand']
    period: str = Field(min_length=1)
    url: str = Field(pattern=r'^https://', min_length=12)
    role: Literal['external_proxy_never_CHHHS_rate']


class EvaluationProtocol(StrictContract):
    schema_version: SchemaVersion
    protocol_id: str = Field(min_length=1)
    status: Literal['draft_unapproved']
    setting: str = Field(min_length=1)
    decision_maker: Literal['Cairns_and_Hinterland_HHS']
    target_decision: Literal['incremental_icu_liaison_service_investment']
    eligibility: Eligibility
    strategies: list[Strategy] = Field(min_length=2, max_length=2)
    endpoints: dict[str, Endpoint]
    safety: Safety
    economics: Economics
    design: Design
    required_local_scenario_inputs: list[str] = Field(min_length=1)
    external_benchmark_role: Literal['external_comparator_not_CHHHS_observed']
    reference_benchmark: ExternalBenchmark
    source_register: str = Field(min_length=1)

    @model_validator(mode='after')
    def cross_field_contract(self) -> 'EvaluationProtocol':
        if {s.id for s in self.strategies} != {'current_care', 'liaison_service'}:
            raise ValueError('exactly two distinct comparator strategies required')
        roles = {s.id: s.role for s in self.strategies}
        if roles != {'current_care': 'observed_comparator', 'liaison_service': 'proposed_incremental'}:
            raise ValueError('comparator roles do not match strategy IDs')
        missing = set(REQUIRED_ENDPOINTS) - set(self.endpoints)
        if missing:
            raise ValueError(f'missing required endpoints: {sorted(missing)}')
        if any(identifier != endpoint.id for identifier, endpoint in self.endpoints.items()):
            raise ValueError('endpoint identity must match its protocol key')
        for identifier, fields in REQUIRED_ENDPOINTS.items():
            endpoint = self.endpoints[identifier]
            expected_fields = {'window_hours': None, 'threshold_hours': None, **fields}
            if any(getattr(endpoint, field) != value for field, value in expected_fields.items()):
                raise ValueError(f'{identifier}: endpoint role, denominator, clock or unit mismatch')
        safety_endpoints = self.safety.required_endpoints
        if (
            set(safety_endpoints) != REQUIRED_SAFETY or len(safety_endpoints) != len(REQUIRED_SAFETY)
            or self.safety.approved_noninferiority_margins
        ):
            raise ValueError('clinical safety endpoints must be complete; no margins may be invented')
        if self.safety.measurements_status != 'unmeasured':
            raise ValueError('clinical safety measurements have not been supplied')
        if self.design.minimum_data_completeness_approved is not None:
            raise ValueError('data quality threshold requires separately approved protocol revision')
        expected = {'annual_eligible_discharges', *Inputs.model_fields}
        # Validate explicitly against currently consumed P1 inputs, not against
        # historical CCR/APD metrics. This is schema-only, not local-source proof.
        if (set(self.required_local_scenario_inputs) != expected
            or len(set(self.required_local_scenario_inputs)) != len(self.required_local_scenario_inputs)):
            raise ValueError('P1 parameter-binding coverage mismatch')
        if '..' in Path(self.source_register).parts or Path(self.source_register).is_absolute():
            raise ValueError('unsafe source register path')
        return self


def admit_protocol(protocol: EvaluationProtocol, scenario: Scenario) -> dict[str, Any]:
    """Admit an illustrative P1 run, NEVER an observed CHHHS claim.

    The P1 Scenario schema currently permits synthetic input only. Missing local
    evidence is a *hard* barrier to an investment-effectiveness conclusion.
    """
    p = EvaluationProtocol.model_validate(protocol.model_dump())
    s = Scenario.model_validate(scenario.model_dump())
    for name in Inputs.model_fields:
        parameter = getattr(s.inputs, name)
        if parameter.status == 'public_benchmark' and name != 'delayed_discharge_ge12h_rate':
            raise ValueError(f'public benchmark is unsupported for {name}; local CHHHS evidence is required')
    if s.inputs.delayed_discharge_ge12h_rate.status == 'public_benchmark':
        benchmark = p.reference_benchmark
        if (not isclose(s.inputs.delayed_discharge_ge12h_rate.value, benchmark.value, rel_tol=0, abs_tol=1e-12)
            or s.inputs.delayed_discharge_ge12h_rate.url != benchmark.url
            or s.inputs.delayed_discharge_ge12h_rate.unit != benchmark.unit):
            raise ValueError('public benchmark value/units/URL disagree with the versioned evidence contract')
    if s.inputs.delayed_discharge_ge12h_rate.status == 'public_benchmark' and p.external_benchmark_role != 'external_comparator_not_CHHHS_observed':
        raise ValueError('benchmark must remain an external proxy')
    for name in Inputs.model_fields:
        if name not in p.required_local_scenario_inputs:
            raise ValueError(f'unbound input: {name}')
    canonical = p.model_dump_json(exclude_none=False)
    digest = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    return {
        'schema_version': 1,
        'protocol_id': p.protocol_id,
        'protocol_sha256': digest,
        'scenario_id': s.scenario_id,
        'status': 'ADMITTED_ILLUSTRATIVE_ONLY',
        'public_rate_role': p.external_benchmark_role,
        'can_run_illustrative': True,
        'ready_for_local_claims': False,
        'ready_for_clinical_safety_claim': False,
        'ready_for_cash_savings_claim': False,
        'local_inputs_requiring_verification': sorted(set(p.required_local_scenario_inputs)),
        'reasons': [
            'local cohort, staffing, discharge delay and costs have not been validated',
            'intervention causal effects and early unplanned return risk are illustrative',
            'safety guardrails and care-plan appropriateness are unmeasured',
            'Dapane/Voiage installed-provider qualification remains separate',
            'released index ICU hours are not evidence of realised cash savings',
        ],
    }


DATA_FIELD_SOURCES = {
    'ANZICS_APD', 'CHHHS_hospital_movements', 'CHHHS_incident_MET',
    'CHHHS_costing', 'CHHHS_workforce', 'CHHHS_liaison_activity',
    'CHHHS_patient_experience',
}
MINIMUM_LOCAL_FIELDS = {
    'hospitalisation_pseudonym', 'index_icu_episode_id', 'icu_medically_ready_at',
    'icu_actual_departure_at', 'icu_readmission_at', 'readmission_planned_status',
    'cost_ledger_entry_id', 'liaison_contact_at', 'ward_cardiac_arrest_at',
    'destination_category', 'followup_observation_end_at',
}


def load_data_dictionary(source: str | Path | Mapping[str, Any]) -> dict[str, Any]:
    """Read source *requirements*, not actual CHHHS patient or workforce data."""
    obj = json.loads(Path(source).read_text(encoding='utf-8')) if isinstance(source, (str, Path)) else dict(source)
    if obj.get('schema_version') != 1 or obj.get('status') != 'unvalidated_local_source_mapping':
        raise ValueError('data dictionary requires schema 1 and an unvalidated mapping status')
    rows = obj.get('fields')
    if not isinstance(rows, list) or not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError('dictionary fields must be nonempty objects')
    keys = set()
    for row in rows:
        if set(row) != {'name', 'type', 'grain', 'source_class', 'availability', 'missing_policy', 'use'}:
            raise ValueError('data dictionary field shape mismatch')
        if not isinstance(row['name'], str) or not row['name'] or row['name'] in keys:
            raise ValueError('missing/duplicate dictionary field identity')
        keys.add(row['name'])
        if row['source_class'] not in DATA_FIELD_SOURCES or row['availability'] != 'not_verified':
            raise ValueError('source identity/completeness not qualified')
        if any(not isinstance(row[k], str) or not row[k].strip() for k in ('type', 'grain', 'missing_policy', 'use')):
            raise ValueError('missing data dictionary semantics')
    if not MINIMUM_LOCAL_FIELDS.issubset(keys):
        raise ValueError('missing minimum clinical/economic data requirements')
    return obj
