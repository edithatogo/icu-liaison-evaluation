"""Pure timing-oracle cases for P2; no identifiable patient data ingestion.

A single index transition only: P3 will own real episode linkage, censoring,
confounding and health-service-specific completeness validation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

BRISBANE = ZoneInfo('Australia/Brisbane')
WINDOW = timedelta(hours=72)


@dataclass(frozen=True)
class ReturnEvent:
    at: datetime
    planned: Literal['planned', 'unplanned', 'unknown']


@dataclass(frozen=True)
class TransitionObservation:
    clinically_ready_at: datetime | None
    physical_departure_at: datetime
    observed_until: datetime
    returns: list[ReturnEvent]
    censor_reason: Literal['completed_72h', 'hospital_discharge', 'interhospital_transfer', 'death', 'unknown']


@dataclass(frozen=True)
class TransitionResult:
    delay_hours: float | None
    exit_block_ge12h: bool | None
    after_hours_departure: bool
    unplanned_return_within_72h: bool | None
    followup_complete_72h: bool
    competing_death: bool


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f'{name}: timezone-aware datetime required')


def classify_transition(value: TransitionObservation) -> TransitionResult:
    """Classify explicitly observed transition facts without imputing missingness.

    Unplanned return is an ANY-event within [departure, departure + 72h).
    Events at exactly 72 hours are excluded. If follow-up is truncated or a
    return's planned status is unknown, no-return remains unknown rather than
    false. Death before full follow-up is a competing event, not non-readmission.
    """
    t = value.physical_departure_at
    _aware(t, 'physical_departure_at')
    _aware(value.observed_until, 'observed_until')
    if value.observed_until < t:
        raise ValueError('observation ends before ICU departure')
    if value.censor_reason == 'completed_72h' and value.observed_until - t < WINDOW:
        raise ValueError('completed_72h label requires at least 72 hours observed')
    delay = None
    if value.clinically_ready_at is not None:
        _aware(value.clinically_ready_at, 'clinically_ready_at')
        if value.clinically_ready_at > t:
            raise ValueError('readiness after ICU departure')
        delay = (t - value.clinically_ready_at).total_seconds() / 3600

    for event in value.returns:
        _aware(event.at, 'return.at')
        if event.at < t or event.at > value.observed_until:
            raise ValueError('ICU return outside observed interval')
        if event.planned not in {'planned', 'unplanned', 'unknown'}:
            raise ValueError('unrecognised ICU return planned status')

    within = [event for event in value.returns if event.at - t < WINDOW]
    any_unplanned = any(event.planned == 'unplanned' for event in within)
    unknown_within = any(event.planned == 'unknown' for event in within)
    full_followup = (value.observed_until - t >= WINDOW)
    early_return: bool | None
    if any_unplanned:
        early_return = True
    elif unknown_within or not full_followup:
        early_return = None
    else:
        early_return = False

    local_hour = t.astimezone(BRISBANE).hour
    return TransitionResult(
        delay_hours=delay,
        exit_block_ge12h=(delay >= 12 if delay is not None else None),
        after_hours_departure=(local_hour >= 18 or local_hour < 6),
        unplanned_return_within_72h=early_return,
        followup_complete_72h=full_followup,
        competing_death=(value.censor_reason == 'death' and not full_followup and not any_unplanned),
    )
