"""Voiage financial-only VOI adapter.

Clinical effects and QALYs are not in this input. Do not describe the resulting
cost-only information value as healthcare cost-effectiveness or utility.
"""
from __future__ import annotations
import numpy as np
from ..model import PSADraws


def financial_decision_array(draws: PSADraws) -> tuple[np.ndarray, list[str]]:
    """Rows are parameter-uncertainty draws; columns are decision strategies.

    The standard-care strategy is the zero incremental reference; the new
    liaison strategy is the resource benefit relative to standard care.
    """
    net = np.asarray(draws.net_resource_benefit_aud, dtype=np.float64)
    if net.ndim != 1 or not np.isfinite(net).all():
        raise ValueError('invalid net benefit draws')
    return np.column_stack((np.zeros(len(net)), net)), ['current_care', 'liaison_service']


def make_voiage_analysis(draws: PSADraws, *, value_array_factory=None, analysis_factory=None):
    """Use supported Voiage API; injected factories are for boundary tests.

    Voiage v3.1 currently requires a separate Python >=3.15.2 environment.
    This environment may not have the runtime installed. There is no fallback
    or homemade EVPI / EVPPI implementation.
    """
    if value_array_factory is None or analysis_factory is None:
        try:
            from voiage.schema import ValueArray
            from voiage.analysis import DecisionAnalysis
        except ImportError as exc:
            raise RuntimeError('Voiage is not installed in a qualified Python >=3.15.2 environment') from exc
        if value_array_factory is None:
            value_array_factory = ValueArray.from_numpy
        if analysis_factory is None:
            analysis_factory = DecisionAnalysis
    array, labels = financial_decision_array(draws)
    return analysis_factory(value_array_factory(array, labels))


def evaluate_financial_information(
    draws: PSADraws, *, value_array_factory=None, analysis_factory=None,
) -> dict:
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
    evpi = float(analysis.evpi())
    if not np.isfinite(evpi) or evpi < -1e-9:
        raise ValueError('Voiage returned an invalid financial EVPI')
    return {
        'evpi_per_decision_aud': max(evpi, 0.0),
        'decision_strategies': ['current_care', 'liaison_service'],
        'value_type': 'financial_resource_only_not_qaly',
        'population_scale': 'one_annual_programme_decision_not_population_scaled',
        'provider_evidence': (
            'native_provider_executed'
            if value_array_factory is None and analysis_factory is None
            else 'injected_contract_test_only'
        ),
    }
