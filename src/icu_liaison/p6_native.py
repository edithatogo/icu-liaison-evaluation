"""Strict boundary for a future independently built native Kairos consumer.

A JSON payload claiming it came from Kairos is NOT a native execution receipt.
The only executable engine is the external pinned Kairos staged resource runtime.
This module normalises its trace for independent NumPy resource conservation
without duplicating event scheduling or treating the result as causal evidence.
"""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .p6_capacity import AdmissionRequest, ArmTrace, CapacityWindow, Occupancy, TraceBundle, audit_trace_bundle


class _Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class StrategyConfig(_Strict):
    strategy_id: str = Field(pattern=r'^[a-z][a-z0-9_]{1,48}$')
    initial_departure_minute: int = Field(gt=0)


class ArrivalConfig(_Strict):
    request_id: str = Field(pattern=r'^syn-[a-z0-9_-]{1,80}$')
    request_minute: int = Field(ge=0)
    occupied_duration_minutes: int = Field(gt=0)


class KairosScenario(_Strict):
    schema_version: Literal[1]
    data_class: Literal['synthetic']
    scenario_id: str = Field(min_length=1, max_length=128, pattern=r'^syn-[a-z0-9_-]+$')
    seed: int = Field(ge=0, le=2**64 - 1)
    horizon_minutes: int = Field(ge=2, le=525_600)
    staffed_beds: Literal[1]  # initial native slice; arbitrary calendars remain pending
    strategies: list[StrategyConfig] = Field(min_length=2, max_length=8)
    arrivals: list[ArrivalConfig] = Field(min_length=1, max_length=1000)

    @model_validator(mode='after')
    def internal_consistency(self) -> 'KairosScenario':
        names = [s.strategy_id for s in self.strategies]
        if names[0] != 'current_care' or len(names) != len(set(names)):
            raise ValueError('current_care must be first and strategies must be unique')
        if any(s.initial_departure_minute > self.horizon_minutes for s in self.strategies):
            raise ValueError('index discharge outside simulation horizon')
        keys = [a.request_id for a in self.arrivals]
        if len(keys) != len(set(keys)):
            raise ValueError('duplicate request IDs')
        if any(a.request_id == 'syn-index-1' for a in self.arrivals):
            raise ValueError('resident ID cannot be reused as a request')
        if any(a.request_minute >= self.horizon_minutes for a in self.arrivals):
            raise ValueError('admission request outside simulation horizon')
        return self


class KairosProvider(_Strict):
    repository: Literal['https://github.com/edithatogo/kairos']
    source_commit: str = Field(pattern=r'^[0-9a-f]{40}$')
    api: Literal['kairo-ecs-des::StagedResourceRuntime']


class KairosProducerOutput(_Strict):
    schema_version: Literal[1]
    source_engine: Literal['kairos']
    data_class: Literal['synthetic']
    producer: Literal['icu-liaison-kairos-consumer']
    producer_contract_version: Literal['0.1.0']
    provider: KairosProvider
    scenario_id: str = Field(min_length=1, max_length=128)
    seed: int = Field(ge=0, le=2**64 - 1)
    horizon_minutes: int = Field(gt=0, le=525_600)
    capacity: list[CapacityWindow] = Field(min_length=1, max_length=10000)
    strategies: list[ArmTrace] = Field(min_length=2, max_length=8)


def _audit_single_bed_queue(arm: ArmTrace, ordered_demand: list[ArrivalConfig], horizon: int) -> None:
    """Check observed intervals against the fixed one-bed FIFO contract."""
    if any(request.disposition == 'declined' for request in arm.requests):
        raise ValueError('native one-bed consumer does not decline demand')
    occupied = sorted(arm.occupancies, key=lambda interval: interval.start_minute)
    admitted = occupied[1:]  # The physical audit has checked the initial occupant at minute zero.
    for previous, interval, request in zip(occupied, admitted, ordered_demand):
        if interval.episode_id != request.request_id:
            raise ValueError('native admissions violate FIFO demand order')
        if interval.start_minute != max(previous.end_minute, request.request_minute):
            raise ValueError('native request waited with a vacant staffed bed')
    if len(admitted) < len(ordered_demand) and occupied[-1].end_minute < horizon:
        raise ValueError('native request censored with a vacant staffed bed')


def inspect_native_output(output: KairosProducerOutput, *, scenario: KairosScenario,
                          provider_lock: Mapping) -> dict:
    """Review self-described provider output as an UNTRUSTED synthetic contract fixture.

    No supplied JSON, revision string or hash proves a compiled Kairos execution.
    """
    if provider_lock.get('schema_version') != 1 or provider_lock.get('provider') != 'kairo-ecs-des':
        raise ValueError('unknown Kairos provider lock')
    if (output.provider.source_commit != provider_lock.get('source_commit') or
        output.provider.repository != provider_lock.get('repository') or
        output.provider.api != provider_lock.get('api')):
        raise ValueError('provider revision or API differs from source lock')
    if (output.scenario_id != scenario.scenario_id or output.seed != scenario.seed or
        output.horizon_minutes != scenario.horizon_minutes):
        raise ValueError('native source scenario/seed/horizon mismatch')
    if len(output.capacity) != 1 or output.capacity[0].start_minute != 0 or not (
        output.capacity[0].end_minute == scenario.horizon_minutes and
        output.capacity[0].staffed_beds == scenario.staffed_beds
    ):
        raise ValueError('native single-bed capacity contract mismatch')
    names = [arm.strategy_id for arm in output.strategies]
    if names != [arm.strategy_id for arm in scenario.strategies]:
        raise ValueError('native strategy contract mismatch')
    expected_demand = {r.request_id: r.request_minute for r in scenario.arrivals}
    durations = {r.request_id: r.occupied_duration_minutes for r in scenario.arrivals}
    for arm, configuration in zip(output.strategies, scenario.strategies, strict=True):
        if {r.request_id: r.request_minute for r in arm.requests} != expected_demand:
            raise ValueError('paired demand request identity/time mismatch')
        if len(arm.requests) != len(expected_demand):
            raise ValueError('duplicate or missing requests in native trace')
        index = [occ for occ in arm.occupancies if occ.episode_id == 'syn-index-1']
        if (len(index) != 1 or index[0].start_minute != 0 or
            index[0].end_minute != configuration.initial_departure_minute):
            raise ValueError('index physical departure is inconsistent with configuration')
        for obs in arm.occupancies:
            if obs.episode_id == 'syn-index-1':
                continue
            if obs.episode_id not in durations:
                raise ValueError('unexpected occupancy identity in native trace')
            expected_end = min(obs.start_minute + durations[obs.episode_id], scenario.horizon_minutes)
            if obs.end_minute != expected_end:
                raise ValueError('request occupancy duration mismatch')

    # A numeric audit uses the pre-existing trace machinery. Normalisation is
    # deliberately not exported as a fake synthetic fixture or trusted native receipt.
    neutral = TraceBundle.model_validate({
        'schema_version': 1,
        'data_class': 'synthetic',
        'source_engine': 'not_kairos',
        'trace_source': 'synthetic_fixture',
        'scenario_id': output.scenario_id,
        'horizon_minutes': output.horizon_minutes,
        'capacity': [v.model_dump() for v in output.capacity],
        'strategies': [s.model_dump() for s in output.strategies],
        'qualification': 'source_fixture_only_not_native_DES',
        'notes': 'Internal normalisation for independent numeric conservation only.',
    })
    audited = audit_trace_bundle(neutral)
    # Simultaneous arrivals are submitted in input order, which the stable sort preserves.
    ordered_demand = sorted(scenario.arrivals, key=lambda request: request.request_minute)
    for arm in output.strategies:
        _audit_single_bed_queue(arm, ordered_demand, scenario.horizon_minutes)
    return {
        'status': 'native_output_contract_checked_not_executed',
        'admission': audited,
        'native_binary_executed': False,
        'native_provenance_qualified': False,
        'investment_ready': False,
    }


def compare_native_with_reference(actual: Mapping, reference: Mapping,
                                  scenario: Mapping) -> dict:
    """Compare outputs with an independent source-side fixture, not a simulated run."""
    candidate = KairosProducerOutput.model_validate(actual)
    oracle = KairosProducerOutput.model_validate(reference)
    if candidate.scenario_id != KairosScenario.model_validate(scenario).scenario_id:
        raise ValueError('scenario identity mismatch')
    # JSON representation preserves minute timing and event/request identities.
    equal = candidate.model_dump() == oracle.model_dump()
    return {'matches_reference': equal, 'native_binary_executed': False,
            'reference': 'hand_authored_synthetic_oracle_not_native_execution'}


def check_native_binary_capability(native_source: Path) -> dict:
    rustc = shutil.which('rustc')
    cargo = shutil.which('cargo')
    return {
        'cargo_present': cargo is not None,
        'rustc_present': rustc is not None,
        'native_source_present': (native_source / 'Cargo.toml').is_file(),
        'native_execution_qualified': False,
        'blocking_reason': ('rust_toolchain_unavailable' if not rustc or not cargo
                            else 'native_build_and_installed_consumer_not_executed'),
    }


def invoke_native_binary(binary: Path, scenario_path: Path, *, expected_sha256: str,
                         provider_lock: Mapping, reference: KairosProducerOutput | None = None) -> dict:
    """Run a locally supplied binary, hash its bytes and validate output.

    A match to a caller-provided binary hash proves byte identity only. It is
    not independent supply-chain, source-build, Kairos API or clinical acceptance.
    """
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64 or any(
        c not in '0123456789abcdef' for c in expected_sha256
    ):
        raise ValueError('expected executable digest must be 64 hex characters')
    if not binary.is_file() or not scenario_path.is_file():
        raise ValueError('native executable or input missing')
    data = binary.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError('native executable hash mismatch')
    if len(data) < 8 or not (data[:4] == b'\x7fELF' or data[:4] in (b'\xfe\xed\xfa\xcf', b'\xcf\xfa\xed\xfe') or
                              data[:2] == b'MZ'):
        raise ValueError('not a platform native executable')
    content = scenario_path.read_bytes()
    scenario = KairosScenario.model_validate_json(content)
    completed = subprocess.run([str(binary.resolve()), str(scenario_path.resolve())],
                               capture_output=True, timeout=45, check=False)
    if completed.returncode != 0 or len(completed.stdout) > 2_000_000:
        raise ValueError('native consumer failed or exceeded bounded output')
    output = KairosProducerOutput.model_validate_json(completed.stdout)
    review = inspect_native_output(output, scenario=scenario, provider_lock=provider_lock)
    if reference is not None and output != reference:
        raise ValueError('actual native output differs from independent reference fixture')
    return {
        **review, 'status': 'native_executable_invoked_unattested_build',
        'native_binary_executed': True, 'native_provenance_qualified': False,
        'input_sha256': hashlib.sha256(content).hexdigest(),
        'output_sha256': hashlib.sha256(completed.stdout).hexdigest(),
        'binary_sha256': expected_sha256,
        'investment_ready': False,
    }
