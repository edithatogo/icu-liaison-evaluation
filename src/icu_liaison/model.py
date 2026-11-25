"""Probabilistic *input* uncertainty using established NumPy/SciPy.

This is not an ICU discrete-event simulation, causal estimate, QALY model,
or valuation ledger. All model-effect and cost assumptions remain in JSON.
"""
from __future__ import annotations
from numpy import float64
from numpy.typing import NDArray
from typing import Any
from dataclasses import dataclass
import hashlib
import json
import numpy as np
from scipy.stats import triang
from .schemas import Parameter, Scenario


@dataclass(frozen=True)
class PSADraws:
    scenario_id: str
    seed: int
    input_digest: str
    icu_bed_days_released: NDArray[float64]
    readmissions_avoided: NDArray[float64]
    gross_resource_benefit_aud: NDArray[float64]
    net_resource_benefit_aud: NDArray[float64]


def _sample(p: Parameter, rng: np.random.Generator, count: int) -> NDArray[float64]:
    if p.low == p.high:
        return np.full(count, p.value)
    # scipy.stats.triang is a maintained distribution implementation;
    # the original PR's custom inverse-CDF sampler is not carried over.
    width = p.high - p.low
    c = (p.value - p.low) / width
    return np.asarray(triang.rvs(c, loc=p.low, scale=width, size=count, random_state=rng))


def simulate(scenario: Scenario) -> PSADraws:
    # Revalidate after any in-memory edits; silently admitting malformed
    # mutation would make an exploratory run impossible to audit.
    s = Scenario.model_validate(scenario.model_dump())
    rng = np.random.default_rng(s.seed)
    i = s.inputs
    vars = {name: _sample(p, rng, s.iterations) for name, p in i.__dict__.items()}
    n = s.annual_eligible_discharges
    with np.errstate(over='ignore', invalid='ignore'):
        days = (n * vars['delayed_discharge_ge12h_rate'] * vars['delayed_cases_addressable_fraction']
                * vars['addressable_cases_improved_fraction'] * vars['hours_released_per_improved_case'] / 24)
        risk = vars['unplanned_72h_readmission_risk']
        new_risk = np.clip(risk * (1.0 - vars['relative_readmission_reduction']), 0, 1)
        returns = n * (risk - new_risk)
        gross = days * vars['net_avoidable_cost_per_icu_day_aud'] + returns * vars['additional_cost_per_readmission_aud']
        net = gross - vars['annual_incremental_service_cost_aud']
    if not all(np.isfinite(outcome).all() for outcome in (days, returns, gross, net)):
        raise ValueError('scenario produced non-finite outcome draws')
    canonical_json = json.dumps(s.model_dump(), sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return PSADraws(
        scenario_id=s.scenario_id, seed=s.seed,
        input_digest=hashlib.sha256(canonical_json.encode()).hexdigest(),
        icu_bed_days_released=days, readmissions_avoided=returns,
        gross_resource_benefit_aud=gross, net_resource_benefit_aud=net,
    )


def _stats(values: NDArray[float64]) -> dict[str, float]:
    with np.errstate(over='ignore', invalid='ignore'):
        mean = np.mean(values)
        p05, p50, p95 = np.quantile(values, [0.05, 0.5, 0.95])
    if not np.isfinite((mean, p05, p50, p95)).all():
        raise ValueError('scenario produced non-finite summary statistics')
    return dict(mean=float(mean), p05=float(p05), p50=float(p50), p95=float(p95))


def summarise(draws: PSADraws) -> dict[str, Any]:
    return dict(
        schema_version=1,
        scenario_id=draws.scenario_id,
        input_digest_sha256=draws.input_digest,
        seed=draws.seed,
        iterations=len(draws.net_resource_benefit_aud),
        result_class='illustrative_not_chhhs_observed',
        uncertainty='independent_triangular_parameter_uncertainty_not_predictive_interval',
        interpretation='annual economic resource scenario; not a claim of budget savings, health gain, or staffed ICU capacity',
        icu_bed_days_released=_stats(draws.icu_bed_days_released),
        readmissions_avoided=_stats(draws.readmissions_avoided),
        gross_resource_benefit_aud=_stats(draws.gross_resource_benefit_aud),
        net_resource_benefit_aud=_stats(draws.net_resource_benefit_aud),
        probability_net_resource_benefit_nonnegative=float(np.mean(draws.net_resource_benefit_aud>=0)),
    )
