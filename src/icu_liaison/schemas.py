"""Conservative provenance and model input contracts.

Unknown fields fail closed. These schema checks cannot establish that any
source document actually supports a claimed local value.
"""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator


def _integer_version(value: object) -> object:
    # Literal comparisons alone equate True and 1.0 with version 1.
    if type(value) is not int:
        raise ValueError("schema version must be a JSON integer")
    return value


SchemaVersion = Annotated[Literal[1], BeforeValidator(_integer_version)]


class Parameter(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid', allow_inf_nan=False)
    value: float
    low: float
    high: float
    status: Literal['public_benchmark', 'illustrative_assumption', 'local_input_unvalidated']
    source: str = Field(min_length=1)
    url: str | None = None
    unit: str = Field(min_length=1)

    @model_validator(mode='after')
    def verify_bounds(self) -> 'Parameter':
        if not 0 <= self.low <= self.value <= self.high and self.unit != 'signed_proportion':
            raise ValueError('parameter requires nonnegative low <= value <= high')
        if self.unit == 'signed_proportion' and not -1 <= self.low <= self.value <= self.high <= 1:
            raise ValueError('signed proportion must remain between -1 and 1')
        if self.status == 'public_benchmark' and not (self.url and self.url.startswith('https://')):
            raise ValueError('public benchmark requires a source URL')
        if not self.source.strip():
            raise ValueError('empty provenance')
        return self


class Inputs(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    delayed_discharge_ge12h_rate: Parameter
    delayed_cases_addressable_fraction: Parameter
    addressable_cases_improved_fraction: Parameter
    hours_released_per_improved_case: Parameter
    unplanned_72h_readmission_risk: Parameter
    relative_readmission_reduction: Parameter
    additional_cost_per_readmission_aud: Parameter
    net_avoidable_cost_per_icu_day_aud: Parameter
    annual_incremental_service_cost_aud: Parameter

    @model_validator(mode='after')
    def validate_names_units_ranges(self) -> 'Inputs':
        requirements = {
            'delayed_discharge_ge12h_rate': ('proportion', 0, 1),
            'delayed_cases_addressable_fraction': ('proportion', 0, 1),
            'addressable_cases_improved_fraction': ('proportion', 0, 1),
            'hours_released_per_improved_case': ('hours_per_case', 0, float('inf')),
            'unplanned_72h_readmission_risk': ('proportion', 0, 1),
            'relative_readmission_reduction': ('signed_proportion', -1, 1),
            'additional_cost_per_readmission_aud': ('AUD_per_readmission', 0, float('inf')),
            'net_avoidable_cost_per_icu_day_aud': ('AUD_per_icu_day', 0, float('inf')),
            'annual_incremental_service_cost_aud': ('AUD_per_year', 0, float('inf')),
        }
        for name, (expected_unit, minimum, maximum) in requirements.items():
            p = getattr(self, name)
            if p.unit != expected_unit or p.low < minimum or p.high > maximum:
                raise ValueError(f'{name} has incorrect unit or parameter range')
        return self


class Scenario(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid')
    schema_version: SchemaVersion
    scenario_id: str = Field(min_length=1)
    data_class: Literal['synthetic']
    seed: int = Field(ge=0, le=2**64 - 1)
    iterations: int = Field(ge=1, le=100_000)
    annual_eligible_discharges: int = Field(ge=1, le=10_000_000)
    annual_eligible_discharges_source: str = Field(min_length=1)
    inputs: Inputs
