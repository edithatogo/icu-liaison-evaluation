"""P4 probabilistic cost-consequence programme decision model.

The package owns ICU-specific causal *assumptions* and accounting identities,
not generic samplers, valuation kernels or an EVPI/EVPPI implementation.
P4 runs only synthetic scenarios; no clinical outcome, budget, resource or
capacity estimate has been approved by CHHHS.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from scipy.stats import beta as beta_distribution
from scipy.stats import lognorm, norm, triang


class _Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, validate_assignment=True)


# Cost quantities and cash-realisability use entirely separate measures.
BASE_UNITS = {
    'baseline.exit_block_rate': 'proportion',
    'baseline.unplanned_72h_return_rate': 'proportion',
    'resource.addressable_delay_fraction': 'proportion',
    'resource.hours_released_per_improved_case': 'hours_per_case',
    'resource.net_index_delay_cost_aud_per_day': 'AUD_per_icu_day',
    'resource.incremental_return_cost_aud_per_return': 'AUD_per_readmission',
    'resource.usable_released_capacity_fraction': 'proportion',
    'resource.index_cash_realisability_fraction': 'proportion',
    'resource.return_cash_realisability_fraction': 'proportion',
}
STRATEGY_UNITS = {
    'coverage_fraction': 'proportion',
    'delay_success_fraction': 'proportion',
    'relative_return_effect': 'signed_proportion',
    'annual_incremental_cost_aud': 'AUD_per_year',
}
REQUIRED_SAFETY = frozenset({
    'post_icu_death', 'ward_cardiac_arrest', 'delayed_escalation',
    'return_severity_and_appropriateness', 'ward_workload', 'treatment_limitations',
})


class Prior(_Strict):
    family: Literal['fixed', 'triangular', 'beta', 'lognormal']
    params: dict[str, float]
    unit: str = Field(min_length=1)
    evidence_status: Literal['public_proxy', 'illustrative_assumption', 'local_aggregate_unvalidated']
    source_ref: str = Field(min_length=1)

    @model_validator(mode='after')
    def valid_distribution(self) -> 'Prior':
        wanted = {
            'fixed': {'value'},
            'triangular': {'low', 'mode', 'high'},
            'beta': {'alpha', 'beta'},
            'lognormal': {'median', 'log_sigma'},
        }[self.family]
        if set(self.params) != wanted:
            raise ValueError('distribution parameter names do not match family')
        if not all(np.isfinite(v) for v in self.params.values()):
            raise ValueError('nonfinite prior parameters')
        p = self.params
        if self.family == 'triangular' and not (
            p['low'] < p['high'] and p['low'] <= p['mode'] <= p['high']
        ):
            raise ValueError('invalid triangular shape')
        if self.family == 'beta' and (p['alpha'] <= 0 or p['beta'] <= 0):
            raise ValueError('invalid beta shape')
        if self.family == 'lognormal' and (p['median'] <= 0 or p['log_sigma'] < 0):
            raise ValueError('invalid lognormal median or spread')
        if not self.source_ref.strip():
            raise ValueError('empty source reference')
        return self

    def support(self) -> tuple[float, float]:
        p = self.params
        if self.family == 'fixed':
            return p['value'], p['value']
        if self.family == 'triangular':
            return p['low'], p['high']
        if self.family == 'beta':
            return 0.0, 1.0
        return 0.0, float('inf')

    def nominal(self) -> float:
        p = self.params
        if self.family == 'fixed':
            return p['value']
        if self.family == 'triangular':
            return p['mode']
        if self.family == 'beta':
            return p['alpha'] / (p['alpha'] + p['beta'])
        return p['median']

    def sample(self, quantiles: np.ndarray) -> np.ndarray:
        if self.family == 'fixed':
            return np.full(len(quantiles), self.params['value'], dtype=np.float64)
        # The lower-level library owns the numerical inverse CDF. Endpoint
        # clipping only avoids unbounded lognormal values from norm.cdf(large z).
        q = np.clip(quantiles, np.nextafter(0.0, 1.0), np.nextafter(1.0, 0.0))
        p = self.params
        if self.family == 'triangular':
            span = p['high'] - p['low']
            return np.asarray(triang.ppf(q, (p['mode'] - p['low']) / span, loc=p['low'], scale=span))
        if self.family == 'beta':
            return np.asarray(beta_distribution.ppf(q, p['alpha'], p['beta']))
        if p['log_sigma'] == 0:
            return np.full(len(quantiles), p['median'], dtype=np.float64)
        return np.asarray(lognorm.ppf(q, s=p['log_sigma'], scale=p['median']))


def _check_unit_and_support(path: str, parameter: Prior, expected_unit: str) -> None:
    low, high = parameter.support()
    if parameter.unit != expected_unit:
        raise ValueError(f'{path}: invalid unit')
    if expected_unit == 'proportion' and not (0 <= low <= high <= 1):
        raise ValueError(f'{path}: proportion outside 0..1')
    if expected_unit == 'signed_proportion' and not (-1 <= low <= high <= 1):
        raise ValueError(f'{path}: signed effect outside -1..1')
    if expected_unit.startswith('AUD_') or expected_unit == 'hours_per_case':
        if low < 0:
            raise ValueError(f'{path}: negative resource or expenditure')
    if expected_unit == 'signed_proportion' and parameter.family == 'beta':
        # A Beta prior on 0..1 is valid, though it cannot express increases in
        # readmission; use triangular if negative effects are plausible.
        pass


class Baseline(_Strict):
    exit_block_rate: Prior
    unplanned_72h_return_rate: Prior


class Resources(_Strict):
    addressable_delay_fraction: Prior
    hours_released_per_improved_case: Prior
    net_index_delay_cost_aud_per_day: Prior
    incremental_return_cost_aud_per_return: Prior
    usable_released_capacity_fraction: Prior
    index_cash_realisability_fraction: Prior
    return_cash_realisability_fraction: Prior


class Strategy(_Strict):
    id: str = Field(min_length=1, pattern=r'^[a-z][a-z0-9_]{1,48}$')
    role: Literal['comparator', 'proposed']
    coverage_fraction: Prior
    delay_success_fraction: Prior
    relative_return_effect: Prior
    annual_incremental_cost_aud: Prior


class DependenceGroup(_Strict):
    variables: list[str] = Field(min_length=2)
    gaussian_correlation: list[list[float]]

    @model_validator(mode='after')
    def check_matrix(self) -> 'DependenceGroup':
        n = len(self.variables)
        if len(set(self.variables)) != n or len(self.gaussian_correlation) != n or any(len(row) != n for row in self.gaussian_correlation):
            raise ValueError('Gaussian copula matrix dimensions or variables invalid')
        a = np.asarray(self.gaussian_correlation, dtype=np.float64)
        if not np.isfinite(a).all() or not np.allclose(a, a.T, rtol=0, atol=1e-12):
            raise ValueError('Gaussian copula correlation matrix must be symmetric and finite')
        if not np.allclose(np.diag(a), 1, rtol=0, atol=1e-12) or np.max(np.abs(a)) > 1 + 1e-12:
            raise ValueError('invalid diagonal or correlation coefficient')
        if np.linalg.eigvalsh(a).min() < -1e-10:
            raise ValueError('non-positive-semidefinite correlation matrix')
        return self


class Safety(_Strict):
    assessment_status: Literal['unmeasured']
    required_outcomes: list[str]
    noninferiority_margins: Literal['not_defined']
    safety_not_monetised: Literal[True]

    @model_validator(mode='after')
    def full_balancing_set(self) -> 'Safety':
        if set(self.required_outcomes) != REQUIRED_SAFETY or len(self.required_outcomes) != len(REQUIRED_SAFETY):
            raise ValueError('incomplete post-ICU safety balancing outcomes')
        return self


class EconomicScenario(_Strict):
    schema_version: Literal[1]
    scenario_id: str = Field(min_length=1)
    data_class: Literal['synthetic']
    currency: Literal['AUD']
    price_year: int = Field(ge=2000, le=2100)
    horizon_months: Literal[12]
    annual_eligible_discharges: int = Field(ge=1, le=10_000_000)
    annual_volume_provenance: str = Field(min_length=1)
    seed: int = Field(ge=0, le=2**64 - 1)
    iterations: int = Field(ge=2, le=100_000)
    baseline: Baseline
    resource: Resources
    strategies: list[Strategy] = Field(min_length=2, max_length=8)
    dependence_groups: list[DependenceGroup]
    safety: Safety
    decision_claim: Literal['illustrative_only_no_investment_or_clinical_claim']
    notes: str = Field(min_length=1)

    def all_priors(self) -> dict[str, Prior]:
        result = {f'baseline.{name}': value for name, value in vars(self.baseline).items()}
        result.update({f'resource.{name}': value for name, value in vars(self.resource).items()})
        for arm in self.strategies:
            result.update({f'strategy.{arm.id}.{name}': getattr(arm, name)
                           for name in STRATEGY_UNITS})
        return result

    @model_validator(mode='after')
    def model_boundaries(self) -> 'EconomicScenario':
        if len({arm.id for arm in self.strategies}) != len(self.strategies):
            raise ValueError('duplicate strategy identifiers')
        if self.strategies[0].id != 'current_care' or self.strategies[0].role != 'comparator':
            raise ValueError('first strategy must be current-care comparator')
        if any(arm.role != 'proposed' for arm in self.strategies[1:]):
            raise ValueError('all subsequent strategies must be proposed variants')
        for path, expected in BASE_UNITS.items():
            section, name = path.split('.', 1)
            _check_unit_and_support(path, getattr(getattr(self, section), name), expected)
        for arm in self.strategies:
            for name, unit in STRATEGY_UNITS.items():
                _check_unit_and_support(f'strategy.{arm.id}.{name}', getattr(arm, name), unit)
        for name in STRATEGY_UNITS:
            p = getattr(self.strategies[0], name)
            if p.family != 'fixed' or p.params['value'] != 0:
                raise ValueError('current-care reference must have no incremental effect or cost')
        if self.baseline.exit_block_rate.evidence_status == 'public_proxy':
            p = self.baseline.exit_block_rate
            if not (p.family == 'fixed' and p.params['value'] == 0.204
                    and p.source_ref == 'CCR_2024_25_EXIT_BLOCK'):
                raise ValueError('unverified 2024/25 public proxy cannot be changed or relabelled')
        for path, p in self.all_priors().items():
            if p.evidence_status == 'public_proxy' and path != 'baseline.exit_block_rate':
                raise ValueError(f'{path}: public CCR proxy is not a local 72-hour clinical effect')
        known = self.all_priors()
        used: set[str] = set()
        for group in self.dependence_groups:
            for path in group.variables:
                if path not in known or path in used:
                    raise ValueError(f'{path}: unknown or multiply assigned copula variable')
                if known[path].family == 'fixed':
                    raise ValueError('a fixed distribution cannot have estimated correlation')
                used.add(path)
        return self


@dataclass(frozen=True)
class StrategyDraws:
    icu_bed_days_released: np.ndarray
    usable_bed_days: np.ndarray
    readmissions_avoided: np.ndarray
    gross_resource_benefit_aud: np.ndarray
    net_resource_benefit_aud: np.ndarray
    net_budget_impact_aud: np.ndarray


@dataclass(frozen=True)
class P4Run:
    scenario: EconomicScenario
    input_digest_sha256: str
    sampled_inputs: dict[str, np.ndarray]
    strategies: dict[str, StrategyDraws]


def _calculate_arrays(n: int, parameters: dict[str, np.ndarray], arm: str) -> StrategyDraws:
    def read(path: str) -> np.ndarray:
        return parameters[path]
    coverage = read(f'strategy.{arm}.coverage_fraction')
    days = (n * read('baseline.exit_block_rate') * read('resource.addressable_delay_fraction')
            * coverage * read(f'strategy.{arm}.delay_success_fraction')
            * read('resource.hours_released_per_improved_case') / 24)
    risk = read('baseline.unplanned_72h_return_rate')
    effects = read(f'strategy.{arm}.relative_return_effect')
    new_risk = (1 - coverage) * risk + coverage * np.clip(risk * (1 - effects), 0, 1)
    avoided = n * (risk - new_risk)
    index_resource_value = days * read('resource.net_index_delay_cost_aud_per_day')
    return_resource_value = avoided * read('resource.incremental_return_cost_aud_per_return')
    gross_resource = index_resource_value + return_resource_value
    service = read(f'strategy.{arm}.annual_incremental_cost_aud')
    return StrategyDraws(
        icu_bed_days_released=days,
        usable_bed_days=days * read('resource.usable_released_capacity_fraction'),
        readmissions_avoided=avoided,
        gross_resource_benefit_aud=gross_resource,
        net_resource_benefit_aud=gross_resource - service,
        net_budget_impact_aud=(
            index_resource_value * read('resource.index_cash_realisability_fraction')
            + return_resource_value * read('resource.return_cash_realisability_fraction')
            - service
        ),
    )


def evaluate_scenarios(scenario: EconomicScenario) -> P4Run:
    """Run paired multi-arm probabilistic *parameter* sensitivity analysis.

    A Gaussian copula is used only for declared groups. Correlations are
    **assumptions**, not inferred empirical covariance or correlated patients.
    All arms share common baseline and resource draws (paired comparison).
    """
    validated = EconomicScenario.model_validate(scenario.model_dump(mode='json'))
    priors = validated.all_priors()
    paths = list(priors)
    rng = np.random.default_rng(validated.seed)
    normals = rng.standard_normal((validated.iterations, len(paths)))
    for group in validated.dependence_groups:
        indices = [paths.index(path) for path in group.variables]
        a = np.asarray(group.gaussian_correlation, dtype=np.float64)
        eigenvalues, vectors = np.linalg.eigh(a)
        factor = vectors @ np.diag(np.sqrt(np.maximum(eigenvalues, 0)))
        normals[:, indices] = normals[:, indices] @ factor.T
    quantiles = norm.cdf(normals)
    samples = {path: priors[path].sample(quantiles[:, index]) for index, path in enumerate(paths)}
    if any(not np.isfinite(values).all() for values in samples.values()):
        raise ValueError('nonfinite sampled parameter output')
    with np.errstate(over='ignore', invalid='ignore'):
        outcomes = {arm.id: _calculate_arrays(validated.annual_eligible_discharges, samples, arm.id)
                    for arm in validated.strategies}
    for arm in outcomes.values():
        if any(not np.isfinite(getattr(arm, name)).all() for name in StrategyDraws.__dataclass_fields__):
            raise ValueError('nonfinite model outcome; review input scales and parameter distributions')
    source = json.dumps(validated.model_dump(mode='json'), sort_keys=True, separators=(',', ':'))
    return P4Run(validated, hashlib.sha256(source.encode()).hexdigest(), samples, outcomes)


def nominal_counterfactual(scenario: EconomicScenario) -> dict[str, dict[str, float]]:
    """Exact input-point accounting oracle (no stochastic sampling)."""
    validated = EconomicScenario.model_validate(scenario.model_dump(mode='json'))
    nominal = {path: np.array([p.nominal()], dtype=np.float64)
               for path, p in validated.all_priors().items()}
    with np.errstate(over='ignore', invalid='ignore'):
        outcomes = {arm.id: _calculate_arrays(validated.annual_eligible_discharges, nominal, arm.id)
                    for arm in validated.strategies}
    for arm in outcomes.values():
        if any(not np.isfinite(getattr(arm, name)).all() for name in StrategyDraws.__dataclass_fields__):
            raise ValueError('nonfinite model outcome at nominal inputs')
    return {arm_id: {name: float(getattr(result, name)[0]) for name in StrategyDraws.__dataclass_fields__}
            for arm_id, result in outcomes.items()}


def financial_decision_surface(run: P4Run, *, objective: Literal['net_resource', 'budget'] = 'net_resource') -> tuple[np.ndarray, list[str]]:
    """Produce Voiage's row-draw/column-strategy input; **not EVPI code**."""
    field = 'net_resource_benefit_aud' if objective == 'net_resource' else 'net_budget_impact_aud'
    labels = [arm.id for arm in run.scenario.strategies]
    array = np.column_stack([getattr(run.strategies[arm], field) for arm in labels])
    if not np.isfinite(array).all():
        raise ValueError('invalid financial decision surface')
    return array, labels


def make_p4_voiage_analysis(run: P4Run, *, value_array_factory=None, analysis_factory=None):
    """Call the *installed* Voiage v3.1 API, never a bespoke VOI solver."""
    if value_array_factory is None or analysis_factory is None:
        try:
            from voiage.schema import ValueArray
            from voiage.analysis import DecisionAnalysis
        except ImportError as exc:
            raise RuntimeError('Voiage 3.1 provider unavailable; use >=Python 3.15.2') from exc
        value_array_factory = value_array_factory or ValueArray.from_numpy
        analysis_factory = analysis_factory or DecisionAnalysis
    values, labels = financial_decision_surface(run)
    return analysis_factory(value_array_factory(values, labels))


def _stats(values: np.ndarray) -> dict[str, float]:
    p05, p50, p95 = np.quantile(values, [0.05, 0.50, 0.95])
    return {'mean': float(np.mean(values)), 'p05': float(p05),
            'p50': float(p50), 'p95': float(p95)}


def _thresholds(scenario: EconomicScenario, arm: Strategy) -> dict[str, float | None]:
    n = scenario.annual_eligible_discharges
    x = {path: p.nominal() for path, p in scenario.all_priors().items()}
    delay_per_covered = (n * x['baseline.exit_block_rate']
                         * x['resource.addressable_delay_fraction']
                         * x[f'strategy.{arm.id}.delay_success_fraction']
                         * x['resource.hours_released_per_improved_case'] / 24
                         * x['resource.net_index_delay_cost_aud_per_day'])
    return_per_covered = (n * x['baseline.unplanned_72h_return_rate']
                          * x[f'strategy.{arm.id}.relative_return_effect']
                          * x['resource.incremental_return_cost_aud_per_return'])
    value_at_full_coverage = delay_per_covered + return_per_covered
    service = x[f'strategy.{arm.id}.annual_incremental_cost_aud']
    coverage = x[f'strategy.{arm.id}.coverage_fraction']
    threshold = (service / value_at_full_coverage) if value_at_full_coverage > 0 else None
    return {
        'threshold_annual_service_cost_aud': float(coverage * value_at_full_coverage),
        'break_even_coverage_fraction': (float(threshold) if threshold is not None else None),
        'break_even_coverage_feasible_at_point_inputs': bool(threshold is not None and 0 <= threshold <= 1),
    }


def one_way_sensitivity(scenario: EconomicScenario, strategy_id: str) -> list[dict]:
    """One-at-a-time 5th/95th marginal parameter diagnostic.

    This is NOT a conditional posterior, variance decomposition, causal
    sensitivity or a recommendation. Correlated input groups are deliberately
    held at nominal values except for the one varied parameter.
    """
    s = EconomicScenario.model_validate(scenario.model_dump(mode='json'))
    if strategy_id == 'current_care' or strategy_id not in {arm.id for arm in s.strategies}:
        raise ValueError('one-way diagnostic needs a declared intervention arm')
    priors = s.all_priors()
    nominal = {name: np.array([p.nominal()], dtype=np.float64) for name, p in priors.items()}
    rows = []
    for name, prior in priors.items():
        if prior.family == 'fixed':
            continue
        low, high = prior.sample(np.asarray([0.05, 0.95], dtype=np.float64))
        values = dict(nominal)
        values[name] = np.array([low], dtype=np.float64)
        below = float(_calculate_arrays(s.annual_eligible_discharges, values, strategy_id)
                      .net_resource_benefit_aud[0])
        values[name] = np.array([high], dtype=np.float64)
        above = float(_calculate_arrays(s.annual_eligible_discharges, values, strategy_id)
                      .net_resource_benefit_aud[0])
        if not np.isfinite([below, above]).all():
            raise ValueError('nonfinite model outcome in one-way analysis')
        rows.append({
            'parameter':name,
            'lower_prior_quantile':float(low),
            'upper_prior_quantile':float(high),
            'low_net_resource_aud':min(below, above),
            'high_net_resource_aud':max(below, above),
            'absolute_net_resource_swing_aud':abs(above-below),
            'interpretation':'one_at_a_time_prior_quantile_not_joint_posterior',
        })
    return sorted(rows, key=lambda row: row['absolute_net_resource_swing_aud'], reverse=True)


def summarise_p4(run: P4Run) -> dict:
    """Report conditional financial and operational outcomes, not clinical approval."""
    outcomes = {}
    for arm in run.scenario.strategies:
        result = run.strategies[arm.id]
        outcomes[arm.id] = {
            **{name: _stats(getattr(result, name)) for name in StrategyDraws.__dataclass_fields__},
            'p_net_resource_benefit_nonnegative': float(np.mean(result.net_resource_benefit_aud >= 0)),
            'p_net_budget_impact_nonnegative': float(np.mean(result.net_budget_impact_aud >= 0)),
            **_thresholds(run.scenario, arm),
        }
    # Financial-only argmax is labelled for analysis, never an investment recommendation.
    top = max(outcomes, key=lambda name: outcomes[name]['net_resource_benefit_aud']['mean'])
    return {
        'schema_version': 1,
        'scenario_id': run.scenario.scenario_id,
        'input_digest_sha256': run.input_digest_sha256,
        'rng': 'numpy.default_rng; Gaussian copula; scipy.stats inverse CDF',
        'draws': run.scenario.iterations,
        'currency': run.scenario.currency,
        'price_year': run.scenario.price_year,
        'horizon_months': run.scenario.horizon_months,
        'decision_class': 'illustrative_probabilistic_cost_consequence_not_CHHHS_impact_estimate',
        'uncertainty': 'assumed_marginal_priors_and_assumed_gaussian_copula_not_empirically_calibrated',
        'strategies': outcomes,
        'financially_best_mean_strategy_not_clinical_recommendation': top,
        'clinical_safety': run.scenario.safety.assessment_status,
        'required_safety_outcomes': sorted(REQUIRED_SAFETY),
        'cost_utility_evaluation_performed': False,
        'monetised_capacity_beyond_resource_cost': False,
        'investment_ready': False,
        'provider_valuation_status': 'Dapane_provider_execution_pending',
        'voiage_evpi_status': 'Voiage_installed_execution_pending',
        'p3_observed_input_status': 'no_approved_CHHHS_local_inputs',
        'caveats': [
            'No observed Cairns volumes, 72-hour unplanned return risk or causal service effect.',
            'Published CCR exit block is a pooled external proxy, not a CHHHS adult rate.',
            'Usable capacity days are distinct from cash or economic resource changes.',
            'Cash realisability fractions are hypothetical and do not establish finance savings.',
            'Mortality, cardiac arrest, escalation and ward workload have not been measured or monetised.',
            'P1 installed Dapane/Voiage validation and the dedicated GitHub repository remain external gates.',
        ],
    }
