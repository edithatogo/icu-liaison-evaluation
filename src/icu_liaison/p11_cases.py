"""Versioned fictional scenario definitions using the existing P10 variants."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .p4_model import EconomicScenario
from tools.p10_falsification import _variant


class ScenarioCase(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

    schema_version: Literal[1]
    case_id: str = Field(pattern=r'^[a-z][a-z0-9_]{0,47}$')
    variant: Literal[
        'base', 'no_effect', 'harmful_returns', 'zero_addressable_delay',
        'zero_usable_capacity', 'zero_cash_realisability',
    ]
    description: str = Field(min_length=1, max_length=240)
    data_class: Literal['synthetic']
    seed: int | None = Field(default=None, ge=0, le=2**64 - 1)
    iterations: int | None = Field(default=None, ge=2, le=100_000)
    overrides: dict[str, dict] = Field(default_factory=dict)


def materialise(case_bytes: bytes, base_bytes: bytes) -> tuple[ScenarioCase, EconomicScenario]:
    case = ScenarioCase.model_validate_json(case_bytes)
    raw = json.loads(base_bytes)
    base = EconomicScenario.model_validate(raw)
    scenario = base if case.variant == 'base' else _variant(raw, case.variant)
    data = scenario.model_dump(mode='json')
    if case.seed is not None:
        data['seed'] = case.seed
    if case.iterations is not None:
        data['iterations'] = case.iterations
    known = scenario.all_priors()
    for key, value in case.overrides.items():
        if key not in known:
            raise ValueError(f'unknown scenario prior: {key}')
        parts = key.split('.')
        if parts[0] == 'strategy':
            arm = next(item for item in data['strategies'] if item['id'] == parts[1])
            arm[parts[2]] = value
        else:
            data[parts[0]][parts[1]] = value
    result = EconomicScenario.model_validate(data)
    if any(prior.evidence_status == 'local_aggregate_unvalidated'
           for prior in result.all_priors().values()):
        raise ValueError('P11 public scenario suite accepts synthetic assumptions only')
    return case, result
