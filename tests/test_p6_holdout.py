"""P6.4 synthetic holdout diagnostics; never CHHHS clinical calibration."""
from typing import Any
import copy
import json
from pathlib import Path

import pytest

from icu_liaison.p6_holdout import HoldoutBundle, compare_holdout, gate_readiness

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'model-inputs/p6/synthetic-holdout.json'


def fixture() -> dict[str, Any]:
    value = json.loads(FIXTURE.read_text())
    assert isinstance(value, dict)
    return value


def test_scoring_uses_scipy_independent_wasserstein_and_ks() -> None:
    result = compare_holdout(HoldoutBundle.model_validate(fixture()))
    assert result['status'] == 'synthetic_holdout_diagnostics_only'
    assert result['training_count'] == 3
    assert result['holdout_count'] == 3
    assert result['paired_mean_absolute_error_minutes'] == pytest.approx(5)
    assert result['holdout_mean_observed_wait_minutes'] == pytest.approx(30)
    assert result['holdout_mean_predicted_wait_minutes'] == pytest.approx(25)
    assert result['wasserstein_distance_minutes'] == pytest.approx(5)
    assert result['ks_statistic'] == pytest.approx(1 / 3)
    assert result['ks_p_value'] is None
    assert result['investment_ready'] is False


def test_train_and_holdout_identifiers_cannot_overlap() -> None:
    v = fixture(); v['holdout'][0]['sample_id'] = v['training'][0]['sample_id']
    with pytest.raises(ValueError, match='leakage'):
        HoldoutBundle.model_validate(v)


def test_missing_censored_observation_cannot_be_treated_as_zero() -> None:
    v = fixture(); v['holdout'][0]['observed_wait_minutes'] = None
    with pytest.raises(ValueError): HoldoutBundle.model_validate(v)
    v = fixture(); v['holdout'][0]['observed_wait_minutes'] = -1
    with pytest.raises(ValueError): HoldoutBundle.model_validate(v)


def test_real_chhhs_records_rejected_by_synthetic_holdout_contract() -> None:
    v = fixture(); v['data_class'] = 'chhhs_restricted'
    with pytest.raises(ValueError): HoldoutBundle.model_validate(v)


def test_evidence_gate_never_self_certifies_clinical_or_organisation_approval() -> None:
    required = ['authorised_local_extract', 'paired_demand', 'staffed_calendar',
                'destination_ward_capacity', 'adjudicated_readmission',
                'patient_level_costing', 'clinical_safety_review',
                'finance_review', 'first_nations_data_governance',
                'independent_native_provider_receipt']
    x = gate_readiness({k: False for k in required})
    assert set(x['unmet']) == set(required)
    assert x['investment_ready'] is False
    with pytest.raises(ValueError, match='unrecognised'):
        gate_readiness({'unknown': True})
    y = gate_readiness({k: True for k in required})
    assert y['all_declarations_present'] is True
    assert y['investment_ready'] is False
    assert y['independent_approval_verified'] is False
