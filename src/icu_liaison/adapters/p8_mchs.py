"""Strict paired-episode consumer of MCHS's *existing* annual acute calculator.

No hospital-funding, NWAU, or ICU-hour formula is implemented here. Only the
source-controlled counterfactual mapping and inspection of provider responses.
Calling an installed provider does not on its own prove annual calculator parity.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from hashlib import file_digest, sha256
from importlib import import_module
import json
from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


_ALLOWED_CONTEXT = frozenset({
    "PAT_COVID_FLAG", "EST_ELIGIBLE_ICU_FLAG", "EST_ELIGIBLE_PAED_FLAG",
    "PAT_RADIOTHERAPY_FLAG", "PAT_DIALYSIS_FLAG", "EST_REMOTENESS",
    "STATE", "INDSTAT",
})


def _decimal_text(value: Any, *, name: str) -> Decimal:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{name} must be exact decimal text, never a binary float")
    try:
        d = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be decimal") from exc
    if not d.is_finite() or d < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return d


class MchsPair(_Strict):
    schema_version: Literal[1]
    data_class: Literal["synthetic"]
    episode_id: str = Field(min_length=11, max_length=128, pattern=r"^synthetic-[a-zA-Z0-9_-]+$")
    pricing_year: Literal[2024, 2025]
    drg: str = Field(min_length=1, max_length=20, pattern=r"^[A-Za-z0-9]+$")
    drg_edition: Literal["v11.0"]
    hospital_los_days: int = Field(gt=0, le=3650)
    icu_hours_current: Decimal
    icu_hours_intervention: Decimal
    icu_other_hours: Decimal
    pat_sameday_flag: Literal[0, 1]
    pat_private_flag: Literal[0, 1]
    context: dict[str, int | str] = Field(default_factory=dict)
    source_bundle_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_bundle_id: str = Field(min_length=3, max_length=200)

    @field_validator("icu_hours_current", "icu_hours_intervention", "icu_other_hours", mode="before")
    @classmethod
    def exact_hours(cls, value: Any) -> Decimal:
        return _decimal_text(value, name="ICU hours")

    @model_validator(mode="after")
    def check_case(self) -> "MchsPair":
        if set(self.context) - _ALLOWED_CONTEXT:
            raise ValueError("MCHS context includes reserved, unsupported or identifying columns")
        for key, value in self.context.items():
            if isinstance(value, bool) or not isinstance(value, (int, str)):
                raise ValueError(f"MCHS {key} is not a valid case-mix value")
            if key.endswith("FLAG") and value not in (0, 1):
                raise ValueError(f"MCHS {key} must be an explicit binary flag")
        return self

    def row(self, *, intervention: bool) -> dict[str, Any]:
        return {
            "DRG": self.drg,
            "LOS": self.hospital_los_days,
            "ICU_HOURS": float(self.icu_hours_intervention if intervention else self.icu_hours_current),
            "ICU_OTHER": float(self.icu_other_hours),
            "PAT_SAMEDAY_FLAG": self.pat_sameday_flag,
            "PAT_PRIVATE_FLAG": self.pat_private_flag,
            **self.context,
        }


def mchs_reference_sha256(ref_dir: Path) -> str:
    """Fingerprint the named SAS tables the annual consumer can read."""
    directory = Path(ref_dir)
    if not directory.is_dir():
        raise ValueError("MCHS reference directory must be explicitly supplied and exist")
    digests = {}
    for table in sorted(directory.glob('*.sas7bdat')):
        if table.is_symlink() or not table.is_file():
            raise ValueError("MCHS reference tables must be regular files")
        with table.open('rb') as handle:
            digests[table.name] = file_digest(handle, 'sha256').hexdigest()
    if not digests:
        raise ValueError("MCHS reference directory contains no SAS tables")
    return sha256(json.dumps(digests, sort_keys=True).encode('utf-8')).hexdigest()


def _installed_acute(ref_dir: Path, expected_digest: str) -> Callable[..., Any]:
    """Bind the existing MCHS calculator to a selected reference snapshot."""
    try:
        module = import_module("nwau_py.calculators.acute")
        pl = import_module("polars")
    except ImportError as exc:
        raise RuntimeError("MCHS annual acute provider not installed; run in its qualified environment") from exc
    if mchs_reference_sha256(ref_dir) != expected_digest:
        raise ValueError("MCHS reference bundle SHA-256 differs from the selected fixture")

    def calculate(rows: list[dict], *, year: str, ref_dir: str):
        return module.calculate_acute(
            pl.DataFrame(rows), module.AcuteParams(), year=year, ref_dir=Path(ref_dir),
        )

    return calculate


def _first_row(result: Any, *, output_column: str) -> Decimal:
    if isinstance(result, list):
        records = result
    elif hasattr(result, "to_dicts"):
        records = result.to_dicts()
    elif hasattr(result, "to_dict"):
        records = result.to_dict(orient="records")
    else:
        raise ValueError("MCHS produced an unsupported annual-calculator result")
    if len(records) != 1 or not isinstance(records[0], dict):
        raise ValueError("MCHS must return exactly one complete episode row")
    row = records[0]
    # Fail closed: a funding AUD column or a different annual label is not NWAU.
    if output_column not in row or "Error_Code" not in row or row["Error_Code"] != 0:
        raise ValueError("MCHS annual NWAU field or clean error code is missing")
    number = row[output_column]
    if isinstance(number, bool) or not isinstance(number, (str, int, float, Decimal)):
        raise ValueError("MCHS annual output is not a numeric NWAU")
    try:
        value = Decimal(str(number))
    except InvalidOperation as exc:
        raise ValueError("MCHS annual NWAU is not finite") from exc
    if not value.is_finite() or value < 0:
        raise ValueError("MCHS annual NWAU is non-finite or negative")
    return value


def run_mchs_pair(
    case: MchsPair,
    *,
    provider: Callable[..., Any] | None = None,
    ref_dir: str | None = None,
) -> dict[str, Any]:
    """Call the existing MCHS calculator *twice*; return an unqualified shadow.

    `provider` is only a test seam. Passing it marks the result as injected and
    never as installed or officially validated.
    """
    case = MchsPair.model_validate_json(case.model_dump_json())
    if provider is None:
        if not ref_dir:
            raise ValueError("MCHS installed path needs a selected annual reference bundle directory")
        directory = Path(ref_dir).resolve()
        runner = _installed_acute(directory, case.source_bundle_sha256)
        ref_dir = str(directory)
    else:
        runner = provider
    now = _first_row(runner([case.row(intervention=False)], year=str(case.pricing_year), ref_dir=ref_dir or ""),
                     output_column=f"NWAU{case.pricing_year % 100:02d}")
    proposed = _first_row(runner([case.row(intervention=True)], year=str(case.pricing_year), ref_dir=ref_dir or ""),
                          output_column=f"NWAU{case.pricing_year % 100:02d}")
    if provider is None and mchs_reference_sha256(Path(ref_dir)) != case.source_bundle_sha256:
        raise ValueError("MCHS reference bundle changed during the paired calculation")
    return {
        "schema_version": 1,
        "episode_id": case.episode_id,
        "data_class": "synthetic",
        "provider": "mchs",
        "pricing_year": case.pricing_year,
        "drg_edition": case.drg_edition,
        "source_bundle_id": case.source_bundle_id,
        "source_bundle_sha256_declared": case.source_bundle_sha256,
        "unit": "NWAU",
        "current_nwau": format(now, "f"),
        "proposed_nwau": format(proposed, "f"),
        "change_nwau": format(proposed - now, "f"),
        "actual_revenue_aud": None,
        "technical_modelled_aud": None,
        "execution_evidence": "injected_contract_test_only" if provider is not None else "installed_source_unqualified",
        "annual_calculator_parity": "unverified",
        "clinical_case_mix_qualification": "not_established",
    }
