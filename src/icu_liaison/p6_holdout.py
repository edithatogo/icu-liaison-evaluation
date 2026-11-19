"""Synthetic holdout diagnostics for the P6 time-aware modelling interface.

This module does not fit a queue model and does not claim CHHHS validation.
SciPy owns the distribution comparisons. Separate censoring/decline profiles
and patient-level correlation require authorised study data and methods.
"""
from __future__ import annotations

from typing import Literal, Mapping

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from scipy.stats import ks_2samp, wasserstein_distance


class _Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class WaitSample(_Strict):
    sample_id: str = Field(pattern=r'^syn-[a-z0-9_-]{1,80}$')
    observed_wait_minutes: float = Field(ge=0, allow_inf_nan=False)
    predicted_wait_minutes: float = Field(ge=0, allow_inf_nan=False)


class HoldoutBundle(_Strict):
    schema_version: Literal[1]
    data_class: Literal['synthetic']
    scenario_id: str = Field(pattern=r'^syn-[a-z0-9_-]{1,80}$')
    endpoint: Literal['admission_wait_minutes_among_admitted']
    training: list[WaitSample] = Field(min_length=2, max_length=10000)
    holdout: list[WaitSample] = Field(min_length=2, max_length=10000)
    note: str = Field(min_length=1, max_length=400)

    @model_validator(mode='after')
    def distinct_fixtures(self) -> 'HoldoutBundle':
        a = [x.sample_id for x in self.training]
        b = [x.sample_id for x in self.holdout]
        if len(set(a)) != len(a) or len(set(b)) != len(b):
            raise ValueError('duplicate record identity within training or holdout')
        if set(a).intersection(b):
            raise ValueError('training/holdout identity leakage')
        return self


def compare_holdout(bundle: HoldoutBundle) -> dict:
    """Compare a held-out synthetic admitted cohort, preserving separate samples."""
    b = HoldoutBundle.model_validate(bundle.model_dump())
    obs = np.array([r.observed_wait_minutes for r in b.holdout], dtype=np.float64)
    predicted = np.array([r.predicted_wait_minutes for r in b.holdout], dtype=np.float64)
    ks = ks_2samp(obs, predicted, alternative='two-sided', method='exact')
    return {
        'status': 'synthetic_holdout_diagnostics_only',
        'source': 'independent_scipy_distribution_methods',
        'scenario_id': b.scenario_id,
        'endpoint': b.endpoint,
        'training_count': len(b.training),
        'holdout_count': len(b.holdout),
        'paired_mean_absolute_error_minutes': float(np.mean(np.abs(obs - predicted))),
        'paired_mean_signed_error_minutes': float(np.mean(predicted - obs)),
        'holdout_mean_observed_wait_minutes': float(np.mean(obs)),
        'holdout_mean_predicted_wait_minutes': float(np.mean(predicted)),
        'wasserstein_distance_minutes': float(wasserstein_distance(obs, predicted)),
        'ks_statistic': float(ks.statistic),
        'ks_p_value': float(ks.pvalue),
        'clinical_case_mix_validated': False,
        'censoring_analysed': False,
        'local_CHHHS_data_used': False,
        'investment_ready': False,
    }


REQUIRED_GATES = frozenset({
    'authorised_local_extract', 'paired_demand', 'staffed_calendar',
    'destination_ward_capacity', 'adjudicated_readmission',
    'patient_level_costing', 'clinical_safety_review', 'finance_review',
    'first_nations_data_governance', 'independent_native_provider_receipt',
})


def gate_readiness(declarations: Mapping[str, bool]) -> dict:
    """Return an evidence request list; self-declarations never grant approval."""
    if any(k not in REQUIRED_GATES for k in declarations):
        raise ValueError('unrecognised readiness declaration')
    if any(type(v) is not bool for v in declarations.values()):
        raise ValueError('readiness fields must be booleans')
    unmet = sorted(k for k in REQUIRED_GATES if declarations.get(k) is not True)
    return {
        'status': 'not_clinically_validated',
        'unmet': unmet,
        'all_declarations_present': not unmet,
        'independent_approval_verified': False,
        'investment_ready': False,
        'notes': 'Boolean self-declarations are not independently validated sources or approvals',
    }
