"""Verify an edition's saved artefacts and four independent editorial evidence records."""
from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

NonEmpty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Digest = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
CHECKS = ("citeweft", "sourceright", "authentext", "textstat")


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class EventDate(Record):
    date: str | None
    basis: NonEmpty


class Dates(Record):
    authored: EventDate
    issued: EventDate
    accessed: EventDate
    catalogued: EventDate


class Artefact(Record):
    id: NonEmpty
    role: Literal["source", "output"]
    label: NonEmpty
    kind: NonEmpty
    edition: NonEmpty
    location: NonEmpty
    saved_path: NonEmpty
    provenance: NonEmpty
    dates: Dates
    sha256: Digest


class ReceiptRef(Record):
    path: NonEmpty
    sha256: Digest


class Edition(Record):
    schema_version: Literal[1]
    artefacts: list[Artefact]
    checks: dict[str, ReceiptRef]


class Check(Record):
    id: NonEmpty
    sha256: Digest
    status: Literal["checked", "manual_reconciled", "inapplicable"]
    detail: NonEmpty
    extract_path: NonEmpty | None = None
    extract_sha256: Digest | None = None
    language: NonEmpty | None = None
    scores: dict[str, int | float] | None = None


class Receipt(Record):
    tool: Literal["citeweft", "sourceright", "authentext", "textstat"]
    version: NonEmpty
    rows: list[Check]


def _saved_path(base: Path, locator: str, roots: tuple[Path, ...]) -> Path:
    path = base / locator
    resolved = path.resolve(strict=True)
    if path.is_symlink() or not resolved.is_file() or not any(
        resolved.is_relative_to(root) for root in roots
    ):
        raise ValueError("saved file is outside the authorised roots or is a symlink")
    return resolved


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _dates(dates: Dates) -> None:
    if dates.catalogued.date is None:
        raise ValueError("catalogued date is required")
    for value in (dates.authored, dates.issued, dates.accessed, dates.catalogued):
        if value.date is not None and date.fromisoformat(value.date).isoformat() != value.date:
            raise ValueError("dates use ISO YYYY-MM-DD")


def verify_edition(path: Path, *, artefact_roots: tuple[Path, ...] = ()) -> dict[str, int | str]:
    """Verify local bytes and receipted coverage, without fetching or releasing any artefact."""
    base = path.resolve().parent
    roots = (base, *(root.resolve(strict=True) for root in artefact_roots))
    edition = Edition.model_validate_json(path.read_bytes())
    records = {row.id: row for row in edition.artefacts}
    if len(records) != len(edition.artefacts) or not records:
        raise ValueError("expected a nonempty catalogue with unique artefact IDs")
    if {row.role for row in records.values()} != {"source", "output"}:
        raise ValueError("catalogue must identify sources and outputs")
    if set(edition.checks) != set(CHECKS):
        raise ValueError("all four independent reporting check receipts are required")

    for row in records.values():
        _dates(row.dates)
        if _digest(_saved_path(base, row.saved_path, roots)) != row.sha256:
            raise ValueError(f"artefact changed: {row.id}")

    for tool, reference in edition.checks.items():
        file = _saved_path(base, reference.path, (base,))
        if _digest(file) != reference.sha256:
            raise ValueError(f"check receipt changed: {tool}")
        receipt = Receipt.model_validate_json(file.read_bytes())
        reviewed = {row.id: row for row in receipt.rows}
        if receipt.tool != tool or len(reviewed) != len(receipt.rows) or set(reviewed) != set(records):
            raise ValueError(f"incomplete or incorrectly attributed {tool} receipt")
        for key, row_check in reviewed.items():
            if row_check.sha256 != records[key].sha256:
                raise ValueError(f"review did not cover the saved bytes: {tool} {key}")
            if row_check.status != "inapplicable":
                if row_check.extract_path is None or row_check.extract_sha256 is None:
                    raise ValueError(f"missing reviewed passage fingerprint: {tool} {key}")
                extract = _saved_path(base, row_check.extract_path, (base,))
                if _digest(extract) != row_check.extract_sha256:
                    raise ValueError(f"scoped extract changed: {tool} {key}")
            if tool == "textstat" and row_check.status != "inapplicable":
                if not row_check.language or not row_check.scores:
                    raise ValueError(f"missing scoped language or scores: {key}")
    return {"status": "catalogue_and_editorial_receipts_verified", "artefacts": len(records), "checks": len(CHECKS)}
