"""P2 independent negative and positive clinical/economic contract oracles."""
from __future__ import annotations
from typing import Any
from dataclasses import replace

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from icu_liaison.protocol import EvaluationProtocol, admit_protocol, load_data_dictionary
from icu_liaison.endpoints import ReturnEvent, TransitionObservation, classify_transition
from icu_liaison.schemas import Scenario

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / 'model-inputs' / 'clinical-economic-protocol.json'
SCENARIO = ROOT / 'model-inputs' / 'illustrative.json'
DICTIONARY = ROOT / 'model-inputs' / 'clinical-data-dictionary.json'


def original() -> dict[str, Any]:
    value = json.loads(PROTOCOL.read_text(encoding='utf-8'))
    assert isinstance(value, dict)
    return value


def test_protocol_and_scenario_admit_illustrative_only() -> None:
    proto = EvaluationProtocol.model_validate(original())
    sim = Scenario.model_validate_json(SCENARIO.read_text(encoding='utf-8'))
    result = admit_protocol(proto, sim)
    assert result['status'] == 'ADMITTED_ILLUSTRATIVE_ONLY'
    assert result['can_run_illustrative'] is True
    assert result['ready_for_local_claims'] is False
    assert result['ready_for_clinical_safety_claim'] is False
    assert result['ready_for_cash_savings_claim'] is False
    assert result['local_inputs_requiring_verification']
    assert result['protocol_sha256'] == admit_protocol(proto, sim)['protocol_sha256']
    assert result['public_rate_role'] == 'external_comparator_not_CHHHS_observed'


def test_comparator_requires_distinct_incremental_strategies() -> None:
    proto = original()
    proto['strategies'][1]['id'] = 'current_care'
    with pytest.raises(ValueError):
        EvaluationProtocol.model_validate(proto)


def test_baseline_must_not_be_assumed_zero_current_liaison_coverage() -> None:
    proto = original()
    proto['strategies'][0]['funded_fte'] = 0
    with pytest.raises(ValueError, match='verified'):
        EvaluationProtocol.model_validate(proto)


def test_protocol_rejects_nonfinite_staffing_even_with_a_source_reference() -> None:
    proto = original()
    proto['strategies'][0].update(
        funded_fte=float('inf'), evidence_status='locally_verified', site_source_reference='fictional-source',
    )
    with pytest.raises(ValueError, match='finite number'):
        EvaluationProtocol.model_validate(proto)


def test_eligibility_index_discharge_and_denominator_are_pinned() -> None:
    proto = original()
    proto['eligibility']['analysis_unit'] = 'all_icu_admissions'
    with pytest.raises(ValueError):
        EvaluationProtocol.model_validate(proto)
    proto = original()
    proto['endpoints']['unplanned_72h_return']['denominator'] = 'all_icu_admissions'
    with pytest.raises(ValueError):
        EvaluationProtocol.model_validate(proto)


def test_wrong_icu_return_window_and_clock_rejected() -> None:
    proto = original()
    proto['endpoints']['unplanned_72h_return']['window_hours'] = 48
    with pytest.raises(ValueError):
        EvaluationProtocol.model_validate(proto)
    proto = original()
    proto['endpoints']['unplanned_72h_return']['start_event'] = 'clinical_discharge_readiness'
    with pytest.raises(ValueError):
        EvaluationProtocol.model_validate(proto)


@pytest.mark.parametrize(('endpoint', 'field', 'value'), [
    ('unplanned_72h_return', 'role', 'context'),
    ('unplanned_72h_return', 'threshold_hours', 12),
    ('ready_to_physical_departure_hours', 'window_hours', 48),
])
def test_required_endpoint_roles_and_optional_clocks_are_pinned(endpoint: str, field: str, value: int | str) -> None:
    proto = original()
    proto['endpoints'][endpoint][field] = value
    with pytest.raises(ValueError, match=endpoint):
        EvaluationProtocol.model_validate(proto)


def test_extra_endpoint_cannot_reuse_a_required_endpoint_identity() -> None:
    proto = original()
    proto['endpoints']['context_metric'] = dict(proto['endpoints']['post_icu_death'], role='context')
    with pytest.raises(ValueError, match='endpoint identity'):
        EvaluationProtocol.model_validate(proto)


def test_missing_safety_endpoint_or_guardrail_is_rejected() -> None:
    proto = original()
    del proto['endpoints']['post_icu_death']
    with pytest.raises(ValueError, match='missing'):
        EvaluationProtocol.model_validate(proto)
    proto = original()
    proto['safety']['required_endpoints'].remove('ward_cardiac_arrest')
    with pytest.raises(ValueError):
        EvaluationProtocol.model_validate(proto)


def test_duplicate_required_safety_endpoint_is_rejected() -> None:
    proto = original()
    proto['safety']['required_endpoints'].append('ward_cardiac_arrest')
    with pytest.raises(ValueError, match='clinical safety endpoints'):
        EvaluationProtocol.model_validate(proto)


def test_safety_thresholds_cannot_be_silently_invented() -> None:
    proto = original()
    proto['safety']['approved_noninferiority_margins'] = {'post_icu_death': 0.01}
    with pytest.raises(ValueError):
        EvaluationProtocol.model_validate(proto)


def test_economic_resource_segments_cannot_overlap() -> None:
    proto = original()
    proto['economics']['cost_components'][1]['resource_segment'] = 'index_ready_to_departure'
    with pytest.raises(ValueError, match='overlap'):
        EvaluationProtocol.model_validate(proto)


def test_average_annual_bed_cost_not_accepted_as_incremental_unit_cost() -> None:
    proto = original()
    proto['economics']['index_delay_valuation'] = 'annual_average_cost_per_available_icu_bed'
    with pytest.raises(ValueError):
        EvaluationProtocol.model_validate(proto)


def test_cash_and_opportunity_cost_remain_separate() -> None:
    proto = original()
    proto['economics']['capacity_monetisation'] = 'assume_cash_savings'
    with pytest.raises(ValueError):
        EvaluationProtocol.model_validate(proto)
    proto = original()
    proto['economics']['apply_discounting_within_12_months'] = True
    with pytest.raises(ValueError):
        EvaluationProtocol.model_validate(proto)


def test_protocol_and_scenario_cost_year_and_units_must_match() -> None:
    proto = EvaluationProtocol.model_validate(original())
    sim = Scenario.model_validate_json(SCENARIO.read_text(encoding='utf-8'))
    sim.inputs.net_avoidable_cost_per_icu_day_aud.unit = 'dollars_per_admission'
    with pytest.raises(ValueError):
        admit_protocol(proto, sim)
    proto_data = original()
    proto_data['economics']['price_year'] = 2025
    with pytest.raises(ValueError):
        EvaluationProtocol.model_validate(proto_data)


def test_data_dictionary_has_required_fields_with_no_identifiable_examples() -> None:
    dictionary = load_data_dictionary(DICTIONARY)
    assert dictionary['status'] == 'unvalidated_local_source_mapping'
    required = {x['name'] for x in dictionary['fields']}
    assert {'hospitalisation_pseudonym', 'index_icu_episode_id', 'icu_medically_ready_at',
            'icu_actual_departure_at', 'icu_readmission_at', 'readmission_planned_status',
            'cost_ledger_entry_id', 'liaison_contact_at', 'ward_cardiac_arrest_at'} <= required
    for field in dictionary['fields']:
        assert field['source_class'] in {'ANZICS_APD', 'CHHHS_hospital_movements',
                                         'CHHHS_incident_MET', 'CHHHS_costing', 'CHHHS_workforce',
                                         'CHHHS_liaison_activity', 'CHHHS_patient_experience'}
        assert field['availability'] == 'not_verified'
    with pytest.raises(ValueError):
        load_data_dictionary({'schema_version': 1, 'fields': []})


AEST = timezone(timedelta(hours=10))


def observation(**patch: Any) -> TransitionObservation:
    depart = datetime(2026, 7, 1, 18, 0, tzinfo=AEST)
    record = TransitionObservation(
        clinically_ready_at=depart - timedelta(hours=12),
        physical_departure_at=depart,
        observed_until=depart + timedelta(hours=72),
        returns=[],
        censor_reason='completed_72h',
    )
    return replace(record, **patch)


def test_threshold_12_hours_and_after_hours_boundaries() -> None:
    out = classify_transition(observation())
    assert out.delay_hours == pytest.approx(12.0)
    assert out.exit_block_ge12h is True
    assert out.after_hours_departure is True
    depart = datetime(2026, 7, 1, 17, 59, 59, tzinfo=AEST)
    out2 = classify_transition(observation(physical_departure_at=depart,
                     clinically_ready_at=depart-timedelta(hours=11, minutes=59)))
    assert out2.exit_block_ge12h is False
    assert out2.after_hours_departure is False


def test_72h_return_window_exact_boundary_excluded() -> None:
    depart = observation().physical_departure_at
    returns=[ReturnEvent(at=depart+timedelta(hours=72), planned='unplanned')]
    out=classify_transition(observation(returns=returns, observed_until=depart+timedelta(hours=73)))
    assert out.unplanned_return_within_72h is False
    out2=classify_transition(observation(returns=[ReturnEvent(at=depart+timedelta(hours=71, minutes=59), planned='unplanned')]))
    assert out2.unplanned_return_within_72h is True


def test_planned_return_excluded_but_unplanned_later_in_window_counts() -> None:
    depart = observation().physical_departure_at
    vals=[ReturnEvent(at=depart+timedelta(hours=3),planned='planned'),
          ReturnEvent(at=depart+timedelta(hours=12),planned='unplanned')]
    out=classify_transition(observation(returns=vals))
    assert out.unplanned_return_within_72h is True
    out2=classify_transition(observation(returns=[vals[0]]))
    assert out2.unplanned_return_within_72h is False


def test_incomplete_followup_and_unknown_planning_are_not_false_negatives() -> None:
    depart=observation().physical_departure_at
    out=classify_transition(observation(observed_until=depart+timedelta(hours=24),censor_reason='hospital_discharge'))
    assert out.unplanned_return_within_72h is None
    assert out.followup_complete_72h is False
    out2=classify_transition(observation(returns=[ReturnEvent(at=depart+timedelta(hours=6),planned='unknown')]))
    assert out2.unplanned_return_within_72h is None
    out3=classify_transition(observation(observed_until=depart+timedelta(hours=10),censor_reason='death'))
    assert out3.unplanned_return_within_72h is None
    assert out3.competing_death is True


def test_missing_readiness_stays_missing_and_timestamps_aware() -> None:
    out=classify_transition(observation(clinically_ready_at=None))
    assert out.delay_hours is None and out.exit_block_ge12h is None
    with pytest.raises(ValueError):
        classify_transition(observation(physical_departure_at=datetime(2026, 7, 1, 18, 0)))
    with pytest.raises(ValueError):
        classify_transition(observation(clinically_ready_at=observation().physical_departure_at+timedelta(minutes=1)))


def test_utc_timestamps_respect_australia_brisbane_evening() -> None:
    depart=datetime(2026, 7, 1, 8, 0, tzinfo=timezone.utc) # 18:00 Brisbane
    out=classify_transition(observation(physical_departure_at=depart,
        clinically_ready_at=depart-timedelta(hours=1),observed_until=depart+timedelta(hours=72)))
    assert out.after_hours_departure is True


def test_readiness_delay_uses_elapsed_hours_through_a_clock_change() -> None:
    sydney = ZoneInfo('Australia/Sydney')
    ready = datetime(2026, 10, 3, 21, 30, tzinfo=sydney)
    depart = datetime(2026, 10, 4, 9, 30, tzinfo=sydney)
    result = classify_transition(observation(
        clinically_ready_at=ready, physical_departure_at=depart,
        observed_until=datetime(2026, 10, 7, 10, 30, tzinfo=sydney),
    ))
    assert result.delay_hours == 11.0
    assert result.exit_block_ge12h is False


def test_return_exactly_72_elapsed_hours_after_departure_is_excluded_across_clock_change() -> None:
    sydney = ZoneInfo('Australia/Sydney')
    depart = datetime(2026, 4, 4, 18, tzinfo=sydney)
    event = datetime(2026, 4, 7, 17, tzinfo=sydney)
    result = classify_transition(observation(
        clinically_ready_at=None, physical_departure_at=depart,
        observed_until=event, returns=[ReturnEvent(event, 'unplanned')],
    ))
    assert result.followup_complete_72h is True
    assert result.unplanned_return_within_72h is False


def test_completed_followup_requires_72_elapsed_hours_across_clock_change() -> None:
    sydney = ZoneInfo('Australia/Sydney')
    depart = datetime(2026, 10, 3, 18, tzinfo=sydney)
    with pytest.raises(ValueError, match='at least 72 hours observed'):
        classify_transition(observation(
            clinically_ready_at=None, physical_departure_at=depart,
            observed_until=datetime(2026, 10, 6, 18, tzinfo=sydney),
        ))


def test_invalid_return_precedes_discharge_and_missing_censor_reason_rejected() -> None:
    depart=observation().physical_departure_at
    with pytest.raises(ValueError):
        classify_transition(observation(returns=[ReturnEvent(at=depart-timedelta(minutes=1),planned='unplanned')]))
    with pytest.raises(ValueError):
        classify_transition(observation(observed_until=depart+timedelta(hours=30),censor_reason='completed_72h'))
    with pytest.raises(ValueError, match='censor reason'):
        classify_transition(observation(censor_reason=None))


def test_published_exit_block_proxy_must_match_explicit_source_and_value() -> None:
    proto = EvaluationProtocol.model_validate(original())
    sim = Scenario.model_validate_json(SCENARIO.read_text(encoding='utf-8'))
    sim.inputs.delayed_discharge_ge12h_rate.value = 0.25
    sim.inputs.delayed_discharge_ge12h_rate.low = 0.25
    sim.inputs.delayed_discharge_ge12h_rate.high = 0.25
    with pytest.raises(ValueError, match='public benchmark'):
        admit_protocol(proto, sim)


def test_other_model_effects_cannot_be_relabelled_public_benchmarks() -> None:
    proto = EvaluationProtocol.model_validate(original())
    sim = Scenario.model_validate_json(SCENARIO.read_text(encoding='utf-8'))
    sim.inputs.relative_readmission_reduction.status = 'public_benchmark'
    sim.inputs.relative_readmission_reduction.url = 'https://www.anzics.org/'
    with pytest.raises(ValueError, match='public benchmark'):
        admit_protocol(proto, sim)


def test_death_after_observed_unplanned_return_is_not_a_competing_pre_event_death() -> None:
    depart = observation().physical_departure_at
    result = classify_transition(observation(
        observed_until=depart+timedelta(hours=40),censor_reason='death',
        returns=[ReturnEvent(at=depart+timedelta(hours=4),planned='unplanned')]
    ))
    assert result.unplanned_return_within_72h is True
    assert result.competing_death is False


def test_safety_endpoint_role_must_not_be_downgraded_to_context() -> None:
    proto = original()
    proto['endpoints']['ward_cardiac_arrest']['role'] = 'context'
    with pytest.raises(ValueError):
        EvaluationProtocol.model_validate(proto)


def test_duplicate_required_scenario_binding_is_rejected() -> None:
    proto = original()
    proto['required_local_scenario_inputs'].append('unplanned_72h_readmission_risk')
    with pytest.raises(ValueError):
        EvaluationProtocol.model_validate(proto)


def test_age_below_adult_registry_threshold_is_rejected() -> None:
    proto = original()
    proto['eligibility']['minimum_age_years'] = 14
    with pytest.raises(ValueError):
        EvaluationProtocol.model_validate(proto)
