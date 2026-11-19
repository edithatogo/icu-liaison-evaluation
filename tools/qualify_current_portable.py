#!/usr/bin/env python3
"""Execute only source-independent synthetic numerical/aggregate oracles.

This is not a native-provider or CHHHS clinical qualification runner. It cannot
promote status beyond SOURCE_ORACLES_PASSED_SYNTHETIC_ONLY.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform

import numpy
import scipy
import pydantic

from icu_liaison.local_data import load_and_audit
from icu_liaison.public_evidence import load_benchmark_catalogue
from icu_liaison.qualification_independent import audit_p4_draws, audit_local_aggregate
from icu_liaison.p4_model import EconomicScenario, evaluate_scenarios

ROOT=Path(__file__).resolve().parents[1]


def qualify() -> dict:
    scenario_path=ROOT/'model-inputs/p4/illustrative.json'
    scenario=EconomicScenario.model_validate_json(scenario_path.read_text())
    if scenario.data_class != 'synthetic':
        raise ValueError('this source-level report may use synthetic P4 scenarios only')
    benchmark=ROOT/'model-inputs/anzics-benchmarks.json'
    register=ROOT/'conductor/evidence/source-register.json'
    sources=load_benchmark_catalogue(benchmark, register)
    data=load_and_audit(ROOT/'tests/fixtures/p3_episodes/manifest.json')
    if data['data_class']!='synthetic':
        raise ValueError('this source-level QA may only consume the committed synthetic fixture')
    local=audit_local_aggregate(data)
    run=evaluate_scenarios(scenario)
    numerical=audit_p4_draws(run, sampled_indices=[0,1,7,53,scenario.iterations//2, scenario.iterations-1])
    return {
      'status':'SOURCE_ORACLES_PASSED_SYNTHETIC_ONLY',
      'date':'2026-11-18',
      'python':platform.python_version(),
      'numerical_libraries':{'numpy':numpy.__version__,'scipy':scipy.__version__,'pydantic':pydantic.__version__},
      'scenario_sha256':hashlib.sha256(scenario_path.read_bytes()).hexdigest(),
      'source_register_sha256':hashlib.sha256(register.read_bytes()).hexdigest(),
      'benchmark_catalogue_sha256':hashlib.sha256(benchmark.read_bytes()).hexdigest(),
      'p4_independent_accounting':numerical,
      'p3_synthetic_quality':local,
      'anzics_external_sources':{m['id']:{'status':m['verification_status'],'value':m['value']}
                                  for m in sources['metrics']},
      'native_kairos_executed':False,
      'dapane_native_executed':False,
      'voiage_native_executed':False,
      'CHHHS_approved_local_records_used':False,
      'clinical_or_causal_validation':False,
      'finance_approval':False,
      'investment_ready':False,
    }


if __name__=='__main__':
    print(json.dumps(qualify(), indent=2, sort_keys=True))
