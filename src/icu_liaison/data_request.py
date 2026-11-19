"""Versioned, privacy-scoped CHHHS data request descriptions (not data extracts)."""
from __future__ import annotations

import csv
from io import StringIO
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')


class FieldSpec(_Strict):
    name: str = Field(pattern=r'^[a-z][a-z0-9_]+$')
    unit_or_type: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    null_handling: str = Field(min_length=1)
    priority: Literal['essential', 'desirable', 'optional']


class Dataset(_Strict):
    id: str = Field(pattern=r'^[a-z][a-z0-9_]+$')
    delivery_tier: Literal['minimal', 'enhanced', 'optional']
    owner_role: str = Field(min_length=2)
    likely_source: str = Field(min_length=2)
    grain: str = Field(min_length=2)
    data_class: Literal['approved_pseudonymised', 'aggregate_only']
    linkage_key: str = Field(min_length=1)
    use_and_validation: str = Field(min_length=4)
    fields: list[FieldSpec] = Field(min_length=1)

    @model_validator(mode='after')
    def no_duplicates(self) -> 'Dataset':
        names=[f.name for f in self.fields]
        if len(names) != len(set(names)):
            raise ValueError('duplicate field in dataset')
        return self


class DataRequestCatalogue(_Strict):
    schema_version: Literal[1]
    status: Literal['request_only_no_local_data_obtained']
    intended_facility: Literal['Cairns Hospital / CHHHS']
    requested_time_window: str = Field(min_length=8)
    extra_followup_period: str = Field(min_length=5)
    planned_price_year: Literal[2026]
    intended_evaluation: str = Field(min_length=4)
    privacy_boundary: str = Field(min_length=20)
    admission_conditions: list[str] = Field(min_length=1)
    datasets: list[Dataset] = Field(min_length=1)

    @model_validator(mode='after')
    def no_dataset_duplicates(self) -> 'DataRequestCatalogue':
        ids=[x.id for x in self.datasets]
        if len(ids) != len(set(ids)):
            raise ValueError('duplicate dataset IDs')
        return self


def render_request_markdown(request: DataRequestCatalogue) -> str:
    """Produce an email-ready technical extraction brief without any row values."""
    r = DataRequestCatalogue.model_validate(request.model_dump())
    out=[
        '# CHHHS ICU liaison evaluation — data-extraction specification',
        '',
        f'**Status:** {r.status.replace("_", " ")}; **facility:** {r.intended_facility}.',
        f'**Requested baseline:** {r.requested_time_window}.',
        f'**Follow-up:** {r.extra_followup_period}. **Valuation year:** AUD {r.planned_price_year}.',
        '',
        '## Clinical estimands and denominator rules',
        '',
        '- **12-hour exit block:** clinically ready to physical ICU departure >=12 hours, using eligible *live ward/home* discharges with valid readiness; report missing readiness separately. Match ANZICS CCR using all relevant live discharges, not only the first per hospitalisation.',
        '- **72-hour unplanned ICU return:** unplanned ICU admission strictly within 72 hours after the first eligible live ICU-to-ward discharge per hospitalisation; link subsequent episodes. Distinguish planned returns, competing death, interhospital transfer, incomplete follow-up and unknown event status. Do not code missing as no return.',
        '- **After-hours discharge:** live ICU-to-ward/home discharge from 18:00 through 05:59 local time, with timezone/clock-transition checks.',
        '- **Capacity:** time-indexed staffed beds and request-to-admission queue including declined requests; bed-day release is not automatically cash or effective capacity.',
        '',
        '## Access and governance',
        '',
        r.privacy_boundary,
        '',
        'Data are **not yet obtained**. Source custodians and systems below are suggested starting points, not an assertion of actual CHHHS system ownership.',
        '',
        'Required admission conditions:',
        *[f'- {s}' for s in r.admission_conditions],
        '',
        '## Requested datasets',
        '',
        '| Priority | Dataset | Likely custodian | Record grain | Preferred source |',
        '|---|---|---|---|---|',
    ]
    for d in r.datasets:
        out.append(f'| {d.delivery_tier} | `{d.id}` | {d.owner_role} | {d.grain} | {d.likely_source} |')
    out+=['','## Field specification','','Null / unknown values must be preserved rather than coded as zero or negative.','']
    for d in r.datasets:
        out += [f'### {d.id} — {d.delivery_tier}', '',
                f'**Join key:** `{d.linkage_key}`. **Privacy profile:** `{d.data_class}`. **Validation:** {d.use_and_validation}', '',
                '| Field | Type / unit | Priority | Purpose | Null rule |', '|---|---|---|---|---|']
        for f in d.fields:
            out.append(f'| `{f.name}` | {f.unit_or_type} | {f.priority} | {f.purpose} | {f.null_handling} |')
        out.append('')
    out += ['## Release and use boundary','','This is an extraction request, not an instruction to export clinical records into ChatGPT, GitHub, an unapproved cloud destination or a research environment. Counts, source definitions, linkage reconciliation, access controls and approved reporting are required before local estimates can replace synthetic assumptions.','','']
    return '\n'.join(out)


def render_request_csv(request: DataRequestCatalogue) -> str:
    r=DataRequestCatalogue.model_validate(request.model_dump())
    target=StringIO()
    writer=csv.writer(target,lineterminator='\n')
    writer.writerow(['delivery_tier','dataset','owner_role','source_system','grain','data_class','linkage_key','field','type_or_unit','priority','purpose','null_handling','validation'])
    for d in r.datasets:
        for f in d.fields:
            writer.writerow([d.delivery_tier,d.id,d.owner_role,d.likely_source,d.grain,d.data_class,d.linkage_key,f.name,f.unit_or_type,f.priority,f.purpose,f.null_handling,d.use_and_validation])
    return target.getvalue()
