"""Independent minute-by-minute reference for NumPy P6 trace integration.

Not an alternative event scheduler: input traces are static, explicitly supplied
occupancy intervals. The scalar oracle only checks the numeric auditor.
"""
import random

from icu_liaison.p6_capacity import TraceBundle, audit_trace_bundle


def test_randomised_shift_boundaries_equal_independent_integer_minute_sweep():
    rng = random.Random(20261118)
    for i in range(80):
        horizon = rng.randrange(12, 240)
        split = rng.randrange(1, horizon)
        caps = [rng.randint(1, 4), rng.randint(1, 4)]
        end_current = rng.randrange(1, horizon + 1)
        end_proposed = rng.randrange(1, horizon + 1)
        bundle = TraceBundle.model_validate({
            'schema_version': 1,
            'data_class': 'synthetic',
            'source_engine': 'not_kairos',
            'trace_source': 'synthetic_fixture',
            'scenario_id': f'syn-capacity-test-{i}',
            'horizon_minutes': horizon,
            'capacity': [
                {'start_minute': 0, 'end_minute': split, 'staffed_beds': caps[0]},
                {'start_minute': split, 'end_minute': horizon, 'staffed_beds': caps[1]},
            ],
            'strategies': [
                {'strategy_id': 'current_care', 'occupancies': [
                    {'episode_id': 'syn-index-1', 'start_minute': 0, 'end_minute': end_current}
                ], 'requests': []},
                {'strategy_id': 'liaison_service', 'occupancies': [
                    {'episode_id': 'syn-index-1', 'start_minute': 0, 'end_minute': end_proposed}
                ], 'requests': []},
            ],
            'qualification': 'source_fixture_only_not_native_DES',
            'notes': 'Non-patient static boundary audit fixture',
        })
        report = audit_trace_bundle(bundle)
        naive_staffed = sum(caps[0] if minute < split else caps[1]
                            for minute in range(horizon))
        for arm, end in [('current_care', end_current), ('liaison_service', end_proposed)]:
            metrics = report['strategies'][arm]
            assert report['staffed_bed_minutes'] == naive_staffed
            assert metrics['occupied_bed_minutes'] == sum(minute < end for minute in range(horizon))
            assert metrics['spare_staffed_bed_minutes'] == naive_staffed - end
            assert metrics['staffed_capacity_conserved'] is True
