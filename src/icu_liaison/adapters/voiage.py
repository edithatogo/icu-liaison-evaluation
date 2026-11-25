"""Voiage financial-only VOI adapter.

Clinical effects and QALYs are not in this input. Do not describe the resulting
cost-only information value as healthcare cost-effectiveness or utility.
"""
from __future__ import annotations
from numpy import float64
from numpy.typing import NDArray
from collections.abc import Callable
from importlib import import_module
from typing import Any
import numpy as np
from ..model import PSADraws


type ValueArrayFactory = Callable[[NDArray[float64], list[str]], Any]
type AnalysisFactory = Callable[[Any], Any]


def financial_decision_array(draws: PSADraws) -> tuple[NDArray[float64], list[str]]:
    """Rows are parameter-uncertainty draws; columns are decision strategies.

    The standard-care strategy is the zero incremental reference; the new
    liaison strategy is the resource benefit relative to standard care.
    """
    net = np.asarray(draws.net_resource_benefit_aud, dtype=np.float64)
    if net.ndim != 1 or not net.size or not np.isfinite(net).all():
        raise ValueError('net benefit draws must be a nonempty, finite vector')
    return np.column_stack((np.zeros(len(net)), net)), ['current_care', 'liaison_service']


def make_voiage_decision(
    values: NDArray[float64], strategies: list[str], *, value_array_factory: ValueArrayFactory | None = None, analysis_factory: AnalysisFactory | None = None,
) -> Any:
    """Pass a selected financial decision surface to the supported Voiage API.

    Voiage v3.1 currently requires a separate Python >=3.15.2 environment.
    This environment may not have the runtime installed. There is no fallback
    or homemade EVPI / EVPPI implementation.
    """
    if value_array_factory is None or analysis_factory is None:
        try:
            ValueArray = import_module('voiage.schema').ValueArray
            DecisionAnalysis = import_module('voiage.analysis').DecisionAnalysis
        except ImportError as exc:
            raise RuntimeError('Voiage is not installed in a qualified Python >=3.15.2 environment') from exc
        if value_array_factory is None:
            value_array_factory = ValueArray.from_numpy
        if analysis_factory is None:
            analysis_factory = DecisionAnalysis
    if analysis_factory is None or value_array_factory is None:
        raise RuntimeError("Voiage factories unavailable")
    return analysis_factory(value_array_factory(values, strategies))


def make_voiage_analysis(draws: PSADraws, *, value_array_factory: ValueArrayFactory | None = None, analysis_factory: AnalysisFactory | None = None) -> Any:
    array, labels = financial_decision_array(draws)
    return make_voiage_decision(
        array, labels, value_array_factory=value_array_factory, analysis_factory=analysis_factory,
    )


def financial_evpi_aud(analysis: Any) -> float:
    """Validate Voiage's returned EVPI in the input surface's monetary units."""
    if not callable(getattr(analysis, 'evpi', None)):
        raise ValueError('invalid Voiage EVPI interface: evpi method unavailable')
    evpi = float(analysis.evpi())
    if not np.isfinite(evpi) or evpi < -1e-9:
        raise ValueError('Voiage returned an invalid financial EVPI')
    return max(evpi, 0.0)


def evaluate_financial_information(
    draws: PSADraws, *, value_array_factory: ValueArrayFactory | None = None, analysis_factory: AnalysisFactory | None = None,
) -> dict[str, Any]:
    """Ask Voiage for EVPI using a two-strategy, financial-only surface.

    The EVPI calculation is *entirely* Voiage-owned. No bespoke VOI method or
    analytic approximation is substituted. A native provider must first pass
    the separate exact-version/runtime qualification gate.
    """
    analysis = make_voiage_analysis(
        draws,
        value_array_factory=value_array_factory,
        analysis_factory=analysis_factory,
    )
    return {
        'evpi_per_decision_aud': financial_evpi_aud(analysis),
        'decision_strategies': ['current_care', 'liaison_service'],
        'value_type': 'financial_resource_only_not_qaly',
        'population_scale': 'one_annual_programme_decision_not_population_scaled',
        'provider_evidence': (
            'native_provider_executed'
            if value_array_factory is None and analysis_factory is None
            else 'injected_contract_test_only'
        ),
    }
