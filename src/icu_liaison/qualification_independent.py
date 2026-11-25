"""Independent descriptive and numerical admission checks for ICU liaison modelling.

Never upgrades observed-data authority, causal identification, clinical safety or
provider-binary qualification. Does not infer an event from an unknown follow-up.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .p4_model import P4Run
from typing import Any

from collections.abc import Mapping, Sequence
from decimal import Decimal
from math import isfinite
import re

from scipy.stats import binomtest


def _bounded_count(counts: Mapping[str, Any], name: str, limit: int) -> int:
    value = counts.get(name)
    if type(value) is not int or not (0 <= value <= limit):
        raise ValueError(f'{name}: inconsistent aggregate count')
    return value


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def audit_local_aggregate(audit: Mapping[str, Any]) -> dict[str, Any]:
    """Admit P3 aggregate descriptions and expose actual ascertainment denominators.

    Exact intervals are *conditional on documented observations*. They cannot
    address missing-not-at-random timestamps or competing-risk censoring.
    The eligible-cohort bounds assign unresolved outcomes to each extreme.
    """
    if audit.get('investment_ready') is not False:
        raise ValueError('self-declared investment approval cannot be accepted')
    if audit.get('data_class') not in {'synthetic', 'restricted'}:
        raise ValueError('invalid data provenance class')
    provenance = audit.get('input_provenance')
    if not isinstance(provenance, Mapping) or not _is_sha256(provenance.get('manifest_sha256')):
        raise ValueError('missing or invalid manifest provenance digest')
    feeds = provenance.get('feed_sha256')
    if (not isinstance(feeds, Mapping) or not {'episodes', 'followup'} <= feeds.keys()
            or not all(_is_sha256(digest) for digest in feeds.values())):
        raise ValueError('missing or invalid feed provenance digest')
    counts = audit.get('cohort')
    if not isinstance(counts, Mapping):
        raise ValueError('missing cohort counts')
    n = counts.get('eligible_index_discharges')
    if type(n) is not int or n < 0:
        raise ValueError('eligible denominator invalid')
    if n == 0:
        raise ValueError('no eligible index discharges; descriptive estimates unavailable')
    readiness = _bounded_count(counts, 'index_with_readiness', n)
    blocked = _bounded_count(counts, 'index_exit_block_ge12h', n)
    if blocked > readiness:
        raise ValueError('exit block numerator exceeds observed readiness denominator')
    yes = _bounded_count(counts, 'unplanned_return_within_72h', n)
    no = _bounded_count(counts, 'early_return_observed_no_event', n)
    unknown = _bounded_count(counts, 'early_return_unknown', n)
    if yes + no + unknown != n:
        raise ValueError('72h return partition inconsistent: unknown outcomes must not be zeros')
    death = _bounded_count(counts, 'competing_death_before_return', n)
    if death > unknown:
        raise ValueError('competing death should be in non-ascertained-return partition')
    complete = _bounded_count(counts, 'followup_complete_72h', n)
    # No-event classifications require full follow-up. Planned status can
    # remain unknown after full follow-up. A competing death falls before 72 hours.
    if not no <= complete <= n - death:
        raise ValueError('complete follow-up conflicts with no-event or competing-death counts')
    afterhours = _bounded_count(counts, 'index_after_hours_departure', n)

    if readiness:
        ci = binomtest(blocked, readiness).proportion_ci(confidence_level=0.95, method='exact')
        delay_measure = {
            'observed_numerator': blocked,
            'observed_denominator': readiness,
            'observed_rate': blocked / readiness,
            'exact_binomial_95_interval_observed_only': [float(ci.low), float(ci.high)],
            'missing_readiness_count': n - readiness,
            'uncertainty_limitation': 'Conditional on cases with valid clinical readiness; missing-not-at-random unassessed',
        }
    else:
        delay_measure = {
            'observed_numerator': blocked,
            'observed_denominator': 0,
            'observed_rate': None,
            'exact_binomial_95_interval_observed_only': None,
            'missing_readiness_count': n,
            'uncertainty_limitation': 'No recorded clinical readiness; cannot estimate exit-block rate',
        }
    delay_measure['eligible_cohort_fraction_bounds'] = [
        blocked / n, (blocked + n - readiness) / n,
    ]
    return {
        'data_class': audit['data_class'],
        'provenance_class': audit['data_class'],
        'eligible_index_discharges': n,
        'readiness_completeness': {'numerator': readiness, 'denominator': n, 'proportion': readiness / n},
        'exit_block_ge12h': delay_measure,
        'after_hours': {'numerator': afterhours, 'denominator': n, 'rate': afterhours / n},
        'return_72h': {
            'followup_complete_72h': complete,
            'positive': yes,
            'no_event': no,
            'unknown': unknown,
            'competing_death_within_unknown': death,
            'observed_positive_fraction_of_eligible': yes / n,
            'unknown_fraction_of_eligible': unknown / n,
            # This conservative range includes the competing-death records in
            # the unresolved partition. It makes no competing-risk inference.
            'eligible_cohort_fraction_bounds': [yes / n, (yes + unknown) / n],
            'complete_cohort_risk_estimable': unknown == 0 and death == 0,
            'interpretation': 'Not a 72h cumulative-incidence estimate when followup is incomplete or death competes',
        },
        'source_provenance_present': True,
        'CHHHS_approval_verified': False,
        'clinical_or_causal_validation': False,
        'investment_ready': False,
    }


def _decimal_float(value: float) -> Decimal:
    value = float(value)
    if not isfinite(value):
        raise ValueError('nonfinite drawn economic quantity')
    return Decimal(str(value))


def _reference_one_draw(n: int, sample: Mapping[str, Decimal], arm: str) -> dict[str, Decimal]:
    """Separately authored scalar accounting using Decimal, no P4 production helpers.

    This deliberately calculates cost components from resource identities; it
    does not test the statistical validity of priors or causal intervention effects.
    """
    cover = sample[f'strategy.{arm}.coverage_fraction']
    delayed_eligible = Decimal(n) * sample['baseline.exit_block_rate'] * sample['resource.addressable_delay_fraction']
    improved = delayed_eligible * cover * sample[f'strategy.{arm}.delay_success_fraction']
    days = improved * sample['resource.hours_released_per_improved_case'] / Decimal(24)
    baseline_risk = sample['baseline.unplanned_72h_return_rate']
    effect = sample[f'strategy.{arm}.relative_return_effect']
    treated_covered = max(Decimal(0), min(Decimal(1), baseline_risk * (1 - effect)))
    new_risk = (1 - cover) * baseline_risk + cover * treated_covered
    returns_avoided = Decimal(n) * (baseline_risk - new_risk)
    index_cost = days * sample['resource.net_index_delay_cost_aud_per_day']
    future_cost = returns_avoided * sample['resource.incremental_return_cost_aud_per_return']
    service = sample[f'strategy.{arm}.annual_incremental_cost_aud']
    return {
        'icu_bed_days_released': days,
        'usable_bed_days': days * sample['resource.usable_released_capacity_fraction'],
        'readmissions_avoided': returns_avoided,
        'gross_resource_benefit_aud': index_cost + future_cost,
        'net_resource_benefit_aud': index_cost + future_cost - service,
        'net_budget_impact_aud': index_cost * sample['resource.index_cash_realisability_fraction']
                                 + future_cost * sample['resource.return_cash_realisability_fraction'] - service,
    }


def audit_p4_draws(run: P4Run, sampled_indices: Sequence[int] | None = None, tolerance_aud: float = 1e-6) -> dict[str, Any]:
    """Cross-check sampled P4 outputs against a separately implemented decimal oracle.

    Uses immutable draw selections, not a new RNG or independent clinical model.
    A mismatched output fails closed, including a budget-only discrepancy.
    """
    n = run.scenario.annual_eligible_discharges
    iterations = run.scenario.iterations
    chosen = list(sampled_indices if sampled_indices is not None else sorted({0, iterations // 2, iterations - 1}))
    if not chosen or len(chosen) != len(set(chosen)) or any(type(i) is not int or i < 0 or i >= iterations for i in chosen):
        raise ValueError('invalid draw selection')
    if not 0 < tolerance_aud <= 1e-3:
        raise ValueError('tolerance must be strictly positive and <= 0.001')
    max_money = 0.0
    checked = 0
    for i in chosen:
        parameters = {key: _decimal_float(values[i]) for key, values in run.sampled_inputs.items()}
        for arm in run.scenario.strategies:
            expected = _reference_one_draw(n, parameters, arm.id)
            actual = run.strategies[arm.id]
            for name, reference in expected.items():
                observed = _decimal_float(getattr(actual, name)[i])
                delta = abs(observed - reference)
                # Do not interpret a 1e-6 day error as an economic amount;
                # use same absolute numerical oracle tolerance across units.
                if delta > Decimal(str(tolerance_aud)):
                    raise ValueError(f'{arm.id}.{name}: independent P4 accounting mismatch')
                if name.endswith('_aud'):
                    max_money = max(max_money, float(delta))
            checked += 1
    return {
        'status': 'independently_recalculated_draw_accounting',
        'draws_checked': checked,
        'selected_draw_indices': chosen,
        'max_abs_difference_aud': max_money,
        'oracle': 'separate_decimal_resource_ledger_no_P4_production_formula_called',
        'clinical_or_causal_validation': False,
        'investment_ready': False,
    }
