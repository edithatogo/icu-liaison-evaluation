"""P3 offline verification of public ICU benchmark provenance and denominators.

Publisher receipts and saved documents can be matched offline. Independent
admission requires separate reviewer and licensing evidence.
"""
from __future__ import annotations
from typing import Any

from datetime import date
import hashlib
import json
from pathlib import Path

from .schemas import SchemaVersion
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Literal


class _Strict(BaseModel):
    model_config = ConfigDict(strict=True, extra='forbid', validate_assignment=True)


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
    'CCR_2024_25_EXIT_BLOCK': ('ANZICS-CCR-2024-25', 'live_ward_home_discharge_delay_ge12h'),
    'CCR_2024_25_AFTER_HOURS': ('ANZICS-CCR-2024-25', 'live_ward_home_after_hours_discharge'),
    'CCR_2024_25_RETURN_EPISODES': ('ANZICS-CCR-2024-25', 'return_icu_hdu_admission_episodes'),
    'APD_2023_24_ADULT_READMITTED': ('ANZICS-CORE-2024', 'adult_readmitted_patients'),
    'CCR_2023_24_EXIT_BLOCK': ('ANZICS-CCR-2023-24', 'live_ward_home_discharge_delay_ge12h'),
    'CCR_2023_24_AFTER_HOURS': ('ANZICS-CCR-2023-24', 'live_ward_home_after_hours_discharge'),
}

REPORT_PERIODS = {
    'ANZICS-CCR-2024-25': ('2024-07-01/2025-06-30', 'period', '2024-07-01/2025-06-30'),
    'ANZICS-CCR-2023-24': ('2023-07-01/2024-06-30', 'period', '2023-07-01/2024-06-30'),
    'ANZICS-CORE-2024': ('2023-07-01/2024-06-30', 'data_period', '2023/24'),
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
    schema_version: SchemaVersion
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


class PublisherDocument(_Strict):
    http_status: Literal[200]
    content_type: Literal['application/pdf']
    pages: int = Field(gt=0)
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')


class PublisherLocator(_Strict):
    outcome: str = Field(min_length=1)
    page: int = Field(gt=0)
    table: int | None = Field(default=None, gt=0)
    value: float = Field(ge=0, allow_inf_nan=False)
    contributors: int = Field(gt=0)


class PublisherReceipt(_Strict):
    schema_version: SchemaVersion
    source_id: Literal['ANZICS-CCR-2024-25']
    publisher: str = Field(min_length=1)
    publisher_url: str = Field(pattern=r'^https://')
    checked_on: date
    document: PublisherDocument
    checked_locators: list[PublisherLocator] = Field(min_length=1)
    scope: Literal['direct_publisher_retrieval_and_page_checks']
    independent_source_admission: Literal['pending']
    local_calibration: Literal[False]


def _index_sources(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = registry['sources']
    sources = {source['id']: source for source in entries}
    if len(sources) != len(entries):
        raise ValueError('duplicate source ID in benchmark register')
    return sources


def audit_publisher_receipt(
    receipt_path: Path, registry: dict[str, Any], *, document_path: Path | None = None,
) -> dict[str, Any]:
    """Reconcile the retained 2024/25 publisher check with the source register."""
    raw = receipt_path.read_bytes()
    receipt = PublisherReceipt.model_validate_json(raw)
    source = _index_sources(registry).get(receipt.source_id)
    if source is None:
        raise ValueError('publisher receipt needs a registered source')
    if (receipt.publisher, receipt.publisher_url) != (source.get('publisher'), source.get('url')):
        raise ValueError('publisher receipt source identity mismatch')
    outcomes = source['outcomes']
    expected = {row['name']: row for row in outcomes}
    observed = {row.outcome: row for row in receipt.checked_locators}
    if (
        len(expected) != len(outcomes) or len(observed) != len(receipt.checked_locators)
        or set(observed) != set(expected)
    ):
        raise ValueError('publisher locator coverage mismatch')
    for outcome, locator in observed.items():
        row = expected[outcome]
        if locator.page > receipt.document.pages or (
            locator.value, locator.page, locator.table, locator.contributors
        ) != (row['value'], row['page'], row.get('table'), row['contributors']):
            raise ValueError(f'{outcome}: publisher locator disagrees with the source register')

    receipt_digest = hashlib.sha256(raw).hexdigest()
    if receipt_digest != source.get('publisher_receipt_sha256'):
        raise ValueError('publisher receipt SHA-256 disagrees with the source register')
    if document_path is not None:
        if document_path.stat().st_size != receipt.document.size_bytes:
            raise ValueError('saved publisher document size mismatch')
        with document_path.open('rb') as document:
            digest = hashlib.file_digest(document, 'sha256').hexdigest()
        if digest != receipt.document.sha256:
            raise ValueError('saved publisher document SHA-256 mismatch')
    return {
        'status': 'PUBLISHER_RECEIPT_RECONCILED',
        'source_id': receipt.source_id,
        'checked_on': receipt.checked_on.isoformat(),
        'checked_outcome_count': len(observed),
        'receipt_sha256': receipt_digest,
        'receipt_document_sha256': receipt.document.sha256,
        'document_sha256_matched': document_path is not None,
        'independent_source_admission': receipt.independent_source_admission,
        'local_calibration': False,
    }


def reconcile_catalogue(catalogue: Catalogue, registry: dict[str, Any]) -> dict[str, Any]:
    """Pure P3 source and denominator reconciliation, also reused by P4/P5.

    Metadata reconciliation is not publisher-document authentication.
    """
    catalogue = Catalogue.model_validate(catalogue.model_dump(mode='json'))
    sources = _index_sources(registry)
    for m in catalogue.metrics:
        source_id, outcome = REGISTER_OUTCOMES[m.id]
        if m.source_id != source_id:
            raise ValueError(f'{m.id}: source report edition mismatch')
        if m.source_id not in sources:
            raise ValueError(f'{m.id}: missing source reference')
        source = sources[source_id]
        expected_period, period_field, registered_period = REPORT_PERIODS[source_id]
        if m.period != expected_period or source.get(period_field) != registered_period:
            raise ValueError(f'{m.id}: source reporting period mismatch')
        if not source.get('url', '').startswith('https://'):
            raise ValueError(f'{m.id}: source lacks HTTPS publisher link')
        matches = [x for x in source.get('outcomes', []) if x.get('name') == outcome]
        if len(matches) != 1:
            raise ValueError(f'{m.id}: source register outcome missing or duplicated')
        observed = matches[0]
        if (float(observed['value']) != m.value or observed.get('unit') != m.unit or
            observed.get('page') != m.page or
            observed.get('contributors') != m.reporting_icus):
            raise ValueError(f'{m.id}: source register outcome value, page or cohort conflict')
        status = source.get('verification_status',
            'previous_transcription_not_independently_reverified')
        if status != m.verification_status:
            raise ValueError(f'{m.id}: source verification status conflict')
        if m.verification_status == 'document_hash_attested_and_substantively_reviewed':
            # A self-declared hash cannot satisfy independent publisher admission.
            raise ValueError(f'{m.id}: document verification needs external SHA-256 and reviewer receipt')
    return catalogue.model_dump(mode='json')


def load_benchmark_catalogue(path: Path, source_register_path: Path) -> dict[str, Any]:
    """Read verified metadata contracts from versioned source files."""
    catalogue = Catalogue.model_validate_json(Path(path).read_text(encoding='utf-8'))
    registry = json.loads(Path(source_register_path).read_text(encoding='utf-8'))
    return reconcile_catalogue(catalogue, registry)


def select_external_benchmark(catalogue: dict[str, Any], benchmark_id: str, *, require_document_verified: bool = False) -> dict[str, Any]:
    """Return an external comparator; never supply an unplanned 72h risk."""
    for metric in catalogue['metrics']:
        if isinstance(metric, dict) and metric.get('id') == benchmark_id:
            if require_document_verified:
                raise ValueError(f'{benchmark_id}: unverified document source needs independent admission')
            return metric
    raise ValueError(f'{benchmark_id}: unavailable public benchmark / unsupported outcome')
