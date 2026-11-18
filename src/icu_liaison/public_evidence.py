"""P3 offline verification of public ICU benchmark provenance and denominators.

This does *not* scrape or authenticate publisher PDFs: documentary verification
needs an independently retained document/hash and substantive review receipt.
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Literal


class _Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', validate_assignment=True)


class Metric(_Strict):
    id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    value: float = Field(ge=0)
    unit: Literal['proportion', 'days']
    denominator_key: str = Field(min_length=1)
    numerator_definition: str = Field(min_length=1)
    outcome_definition: str = Field(min_length=1)
    cohort: str = Field(min_length=1)
    period: str = Field(min_length=1)
    page: int = Field(ge=1)
    reporting_icus: int | None = Field(default=None, ge=1)
    verification_status: Literal[
        'previous_transcription_not_independently_reverified',
        'publisher_text_inspected_no_pdf_sha',
        'publisher_text_and_page_image_inspected_no_pdf_sha',
        'document_hash_attested_and_substantively_reviewed',
    ]
    note: str = Field(min_length=1)
    document_sha256: str | None = None

    @model_validator(mode='after')
    def enforce_document_admission(self) -> 'Metric':
        if self.unit == 'proportion' and self.value > 1:
            raise ValueError('proportion exceeds 1')
        if self.verification_status == 'document_hash_attested_and_substantively_reviewed':
            import re
            if not self.document_sha256 or not re.fullmatch(r'[0-9a-f]{64}', self.document_sha256):
                raise ValueError('document verified requires SHA-256 and independent review')
        elif self.document_sha256 is not None:
            raise ValueError('unverified document may not claim a SHA-256 admission')
        return self


REGISTER_OUTCOMES = {
    'CCR_2024_25_EXIT_BLOCK': 'live_ward_home_discharge_delay_ge12h',
    'CCR_2024_25_AFTER_HOURS': 'live_ward_home_after_hours_discharge',
    'CCR_2024_25_RETURN_EPISODES': 'return_icu_hdu_admission_episodes',
    'APD_2023_24_ADULT_READMITTED': 'adult_readmitted_patients',
    'CCR_2023_24_EXIT_BLOCK': 'live_ward_home_discharge_delay_ge12h',
    'CCR_2023_24_AFTER_HOURS': 'live_ward_home_after_hours_discharge',
}

METRIC_DENOMINATORS = {
    'CCR_2024_25_EXIT_BLOCK': ('all_live_ward_home_discharges', 'all_age_binational_reporting_units', 'exit_block_ge12h'),
    'CCR_2024_25_AFTER_HOURS': ('all_live_ward_home_discharges', 'all_age_binational_reporting_units', 'after_hours_discharge'),
    'CCR_2024_25_RETURN_EPISODES': ('all_icu_hdu_admissions', 'all_age_binational_reporting_units', 'all_return_admission_episodes'),
    'APD_2023_24_ADULT_READMITTED': ('adult_survivors_first_icu_episode', 'adult_australian_reporting_population', 'all_readmitted_patients'),
    'CCR_2023_24_EXIT_BLOCK': ('all_live_ward_home_discharges', 'all_age_binational_reporting_units', 'exit_block_ge12h'),
    'CCR_2023_24_AFTER_HOURS': ('all_live_ward_home_discharges', 'all_age_binational_reporting_units', 'after_hours_discharge'),
}


class Catalogue(_Strict):
    schema_version: Literal[1]
    purpose: Literal['external_comparators_never_site_observations']
    metrics: list[Metric] = Field(min_length=1)

    @model_validator(mode='after')
    def validate_denominator_contract(self) -> 'Catalogue':
        found = set()
        for metric in self.metrics:
            if metric.id in found:
                raise ValueError('duplicate benchmark id')
            found.add(metric.id)
            if metric.id not in METRIC_DENOMINATORS:
                raise ValueError('unsupported benchmark id')
            denominator, cohort, measure = METRIC_DENOMINATORS[metric.id]
            if (metric.denominator_key, metric.cohort, metric.outcome_definition) != (denominator, cohort, measure):
                raise ValueError(f'{metric.id}: denominator, cohort or measure mismatch')
        return self


def reconcile_catalogue(catalogue: Catalogue, registry: dict) -> dict:
    """Pure P3 source and denominator reconciliation, also reused by P4/P5.

    Metadata reconciliation is not publisher-document authentication.
    """
    catalogue = Catalogue.model_validate(catalogue.model_dump(mode='json'))
    sources = {s['id']: s for s in registry['sources']}
    for m in catalogue.metrics:
        if m.source_id not in sources:
            raise ValueError(f'{m.id}: missing source reference')
        if not sources[m.source_id].get('url', '').startswith('https://'):
            raise ValueError(f'{m.id}: source lacks HTTPS publisher link')
        if not m.source_id.startswith('ANZICS-'):
            raise ValueError('non-ANZICS record in ANZICS benchmark catalogue')
        matches = [x for x in sources[m.source_id].get('outcomes', [])
                   if x.get('name') == REGISTER_OUTCOMES[m.id]]
        if len(matches) != 1:
            raise ValueError(f'{m.id}: source register outcome missing or duplicated')
        observed = matches[0]
        if (float(observed['value']) != m.value or observed.get('unit') != m.unit or
            observed.get('page') != m.page or
            observed.get('contributors') != m.reporting_icus):
            raise ValueError(f'{m.id}: source register outcome value, page or cohort conflict')
        status = sources[m.source_id].get('verification_status',
            'previous_transcription_not_independently_reverified')
        if status != m.verification_status:
            raise ValueError(f'{m.id}: source verification status conflict')
        if m.verification_status == 'document_hash_attested_and_substantively_reviewed':
            # A self-declared hash cannot satisfy independent publisher admission.
            raise ValueError(f'{m.id}: document verification needs external SHA-256 and reviewer receipt')
    return catalogue.model_dump(mode='json')


def load_benchmark_catalogue(path: Path, source_register_path: Path) -> dict:
    """Read verified metadata contracts from versioned source files."""
    catalogue = Catalogue.model_validate_json(Path(path).read_text(encoding='utf-8'))
    registry = json.loads(Path(source_register_path).read_text(encoding='utf-8'))
    return reconcile_catalogue(catalogue, registry)


def select_external_benchmark(catalogue: dict, benchmark_id: str, *, require_document_verified: bool = False) -> dict:
    """Return an external comparator; never supply an unplanned 72h risk."""
    for metric in catalogue['metrics']:
        if metric['id'] == benchmark_id:
            if require_document_verified and metric['verification_status'] != 'document_hash_attested_and_substantively_reviewed':
                raise ValueError(f'{benchmark_id}: unverified document source')
            return metric
    raise ValueError(f'{benchmark_id}: unavailable public benchmark / unsupported outcome')
