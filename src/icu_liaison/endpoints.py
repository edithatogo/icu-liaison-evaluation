"""Pure timing-oracle cases for P2; no identifiable patient data ingestion.

A single index transition only: P3 will own real episode linkage, censoring,
confounding and health-service-specific completeness validation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal, get_args
from zoneinfo import ZoneInfo

BRISBANE = ZoneInfo('Australia/Brisbane')
WINDOW = timedelta(hours=72)
CensorReason = Literal['completed_72h', 'hospital_discharge', 'interhospital_transfer', 'death', 'unknown']


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
    censor_reason: CensorReason


@dataclass(frozen=True)
class TransitionResult:
    delay_hours: float | None
    exit_block_ge12h: bool | None
    after_hours_departure: bool
    unplanned_return_within_72h: bool | None
    followup_complete_72h: bool
    competing_death: bool


def _utc(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f'{name}: timezone-aware datetime required')
    return value.astimezone(UTC)


def classify_transition(value: TransitionObservation) -> TransitionResult:
    """Classify explicitly observed transition facts without imputing missingness.

    Unplanned return is an ANY-event within [departure, departure + 72h).
    Events at exactly 72 hours are excluded. If follow-up is truncated or a
    return's planned status is unknown, no-return remains unknown rather than
    false. Death before full follow-up is a competing event, not non-readmission.
    """
    departure = _utc(value.physical_departure_at, 'physical_departure_at')
    observed_until = _utc(value.observed_until, 'observed_until')
    if value.censor_reason not in get_args(CensorReason):
        raise ValueError('unrecognised follow-up censor reason')
    if observed_until < departure:
        raise ValueError('observation ends before ICU departure')
    full_followup = observed_until - departure >= WINDOW
    if value.censor_reason == 'completed_72h' and not full_followup:
        raise ValueError('completed_72h label requires at least 72 hours observed')
    delay = None
    if value.clinically_ready_at is not None:
        ready = _utc(value.clinically_ready_at, 'clinically_ready_at')
        if ready > departure:
            raise ValueError('readiness after ICU departure')
        delay = (departure - ready).total_seconds() / 3600

    early_statuses = set()
    for event in value.returns:
        at = _utc(event.at, 'return.at')
        if not departure <= at <= observed_until:
            raise ValueError('ICU return outside observed interval')
        if event.planned not in {'planned', 'unplanned', 'unknown'}:
            raise ValueError('unrecognised ICU return planned status')
        if at - departure < WINDOW:
            early_statuses.add(event.planned)

    any_unplanned = 'unplanned' in early_statuses
    early_return: bool | None
    if any_unplanned:
        early_return = True
    elif 'unknown' in early_statuses or not full_followup:
        early_return = None
    else:
        early_return = False

    local_hour = departure.astimezone(BRISBANE).hour
    return TransitionResult(
        delay_hours=delay,
        exit_block_ge12h=(delay >= 12 if delay is not None else None),
        after_hours_departure=(local_hour >= 18 or local_hour < 6),
        unplanned_return_within_72h=early_return,
        followup_complete_72h=full_followup,
        competing_death=(value.censor_reason == 'death' and not full_followup and not any_unplanned),
    )
