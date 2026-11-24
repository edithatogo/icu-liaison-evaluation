"""Consumer of existing Health Workforce dated-quotation -> Dapane bridge.

This module performs no payroll, award interpretation, price multiplication or
unit conversion. It checks explicit roster exposure identities and delegates
source selection, exact pricing and valuation to the owning libraries.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from importlib import import_module
import json
from typing import Any, Callable, Literal, Mapping

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RosterExposure(_Strict):
    quantity_id: str = Field(min_length=2, max_length=128)
    shift_id: str = Field(min_length=2, max_length=128)
    quote_id: str = Field(min_length=2, max_length=128)
    unit: str = Field(min_length=1, max_length=32)
    quantity: Decimal
    kind: Literal["analyst_assumption"]
    component: str = Field(min_length=1, max_length=100)
    segment_start: datetime
    segment_end: datetime
    valued_on: date

    @field_validator("quantity", mode="before")
    @classmethod
    def exact_quantity(cls, value: Any) -> Decimal:
        if type(value) is not str or value.strip() != value:
            raise ValueError("workforce quantity must be exact decimal text, not float")
        try:
            result = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError("invalid workforce quantity") from exc
        if not result.is_finite() or result < 0:
            raise ValueError("workforce quantity must be finite and nonnegative")
        return result

    @model_validator(mode="after")
    def segment(self) -> "RosterExposure":
        start, end = self.segment_start, self.segment_end
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("roster interval requires a timezone offset")
        if start.utcoffset() != timedelta(hours=10) or end.utcoffset() != timedelta(hours=10):
            raise ValueError("Queensland roster timestamps must use +10:00")
        if end <= start:
            raise ValueError("roster segment must end after its start")
        if not start.date() <= self.valued_on <= end.date():
            raise ValueError("valued_on must fall in the explicit roster segment")
        return self


class RosterScenario(_Strict):
    schema_version: Literal[1]
    data_class: Literal["synthetic"]
    scenario_id: str = Field(min_length=2, max_length=128, pattern=r"^synthetic-[a-zA-Z0-9_-]+$")
    jurisdiction: Literal["Queensland"]
    classification: str = Field(min_length=2, max_length=150)
    classification_status: Literal["candidate_unverified"]
    expected_artifact_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_artifact_json: str = Field(min_length=2, max_length=2_000_000)
    financial_price_year: int = Field(ge=2024, le=2100)
    knowledge_cutoff: date
    exposures: tuple[RosterExposure, ...] = Field(min_length=1, max_length=5000)
    contains_superannuation: bool
    contains_leave_relief: bool
    contains_penalties: bool
    completeness_status: Literal["partial", "full"]

    @model_validator(mode="after")
    def scope_and_overlap(self) -> "RosterScenario":
        if self.completeness_status == "full" and not (
            self.contains_superannuation and self.contains_leave_relief and self.contains_penalties
        ):
            raise ValueError("full roster completeness requires explicit superannuation, leave relief and penalty coverage")
        ids = [x.quantity_id for x in self.exposures]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate roster quantity identity")
        # Different components may be stacked by an explicitly qualified rate
        # provider. The *same* component must not be priced twice for one shift.
        for i, a in enumerate(self.exposures):
            if (a.segment_start.date().year != self.financial_price_year
                or a.segment_end.date().year != self.financial_price_year):
                raise ValueError("roster exposure may not cross the financial price-year boundary without source segmentation")
            if a.valued_on > self.knowledge_cutoff:
                raise ValueError("workforce price knowledge cutoff precedes use")
            for b in self.exposures[i+1:]:
                if (a.shift_id == b.shift_id and a.component == b.component
                    and max(a.segment_start,b.segment_start) < min(a.segment_end,b.segment_end)):
                    raise ValueError("overlap in the same shift and charged workforce component")
        return self


def validate_workforce_quote_dates(
    quote: Mapping[str, Any], service_date: date, knowledge_cutoff: date,
) -> None:
    """Require a dated quote to apply on the service date and at the cutoff."""
    try:
        starts_on = date.fromisoformat(quote.get("valid_from"))
        ends_on = date.fromisoformat(quote.get("valid_to"))
        known_from = date.fromisoformat(quote.get("known_from"))
    except (TypeError, ValueError) as exc:
        raise ValueError("workforce quote requires explicit effective and knowledge dates") from exc
    if not starts_on <= service_date < ends_on:
        raise ValueError("workforce quote is outside its effective window on the service date")
    if known_from > knowledge_cutoff or service_date > knowledge_cutoff:
        raise ValueError("workforce quote or service date is after the knowledge cutoff")


def prepare_workforce_dapane_request(
    scenario: RosterScenario,
    *,
    builder: Callable[..., dict[str, Any]] | None = None,
    quantity_type: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Transport explicit quantities through provider-owned dated source logic.

    An injected builder is only a test seam. A validated request does not prove
    a worker's classification or actual annual workforce expenditure.
    """
    scenario = RosterScenario.model_validate_json(scenario.model_dump_json())
    injected = builder is not None or quantity_type is not None
    if builder is None or quantity_type is None:
        try:
            provider = import_module("microcosting_healthworkforce.dapane_adapter")
            types = import_module("microcosting_healthworkforce.unit_quotes")
        except ImportError as exc:
            raise RuntimeError("workforce source-quotation provider not installed; native qualification unavailable") from exc
        builder = builder or provider.build_dapane_request
        quantity_type = quantity_type or types.QuoteQuantity

    artifact = json.loads(scenario.source_artifact_json)
    release = artifact.get("release_snapshot") if isinstance(artifact, dict) else None
    if (not isinstance(release, dict) or release.get("jurisdiction") not in ("QLD", "Queensland")
            or release.get("classification") != scenario.classification):
        raise ValueError("workforce release jurisdiction or classification differs from the roster")

    quantities = tuple(quantity_type(
        quantity_id=e.quantity_id,
        quote_id=e.quote_id,
        unit=e.unit,
        quantity=e.quantity,
        valued_on=e.valued_on,
        quantity_kind=e.kind,
        basis=f"synthetic-roster:{e.shift_id}:{e.component}",
    ) for e in scenario.exposures)
    result = builder(
        scenario.source_artifact_json,
        quantities,
        expected_sha256=scenario.expected_artifact_sha256,
        run_id=scenario.scenario_id,
        knowledge_cutoff=scenario.knowledge_cutoff,
    )
    if not isinstance(result, dict) or result.get("schema_version") != "0.1" or result.get("run_id") != scenario.scenario_id:
        raise ValueError("workforce bridge returned an incompatible Dapane request identity")
    policy = result.get("policy")
    if not isinstance(policy, dict) or policy.get("basis") != "financial_cost":
        raise ValueError("workforce source bridge must produce a Dapane financial_cost request")
    if policy.get("currency") != "AUD" or policy.get("price_year") != scenario.financial_price_year:
        raise ValueError("workforce source bridge currency or price year mismatch")
    quotes, usage = result.get("quotes"), result.get("usage")
    if not isinstance(quotes, list) or not isinstance(usage, list):
        raise ValueError("workforce bridge must return explicit Dapane quote and usage arrays")
    if len(usage) != len(scenario.exposures):
        raise ValueError("workforce bridge lost or duplicated a roster exposure")
    quote_by_id = {q.get("id"): q for q in quotes if isinstance(q, dict)}
    if len(quote_by_id) != len(quotes):
        raise ValueError("workforce bridge returned duplicate quotation identities")
    use_by_id = {u.get("id"): u for u in usage if isinstance(u, dict)}
    if len(use_by_id) != len(usage):
        raise ValueError("workforce bridge returned duplicate usage identities")
    for exposure in scenario.exposures:
        use = use_by_id.get(exposure.quantity_id)
        quote = quote_by_id.get(exposure.quote_id)
        if not isinstance(use, dict) or not isinstance(quote, dict):
            raise ValueError("workforce bridge omitted an expected source-bound use or quotation")
        if (use.get("quote_id") != exposure.quote_id or use.get("unit") != exposure.unit
                or quote.get("unit") != exposure.unit):
            raise ValueError("workforce bridge changed a roster quotation or unit")
        if use.get("service_date") != exposure.valued_on.isoformat():
            raise ValueError("workforce bridge changed a roster valuation date")
        if quote.get("basis") != "financial_cost" or quote.get("components") != [exposure.component]:
            raise ValueError("workforce bridge changed cost component or financial valuation basis")
        if RosterExposure.exact_quantity(use.get("quantity")) != exposure.quantity:
            raise ValueError("workforce bridge changed the exact roster quantity")
        source = use.get("source")
        if not isinstance(source, dict) or source.get("evidence") != "synthetic":
            raise ValueError("workforce bridge must preserve synthetic exposure evidence")
        validate_workforce_quote_dates(quote, exposure.valued_on, scenario.knowledge_cutoff)
    return {
        "provider_evidence": "injected_contract_test_only" if injected
        else "unqualified_installed_workforce_source",
        "scenario_id": scenario.scenario_id,
        "financial_cost_status": "not_valued",
        "annual_workforce_cost_aud": None,
        "classification_eligibility": "unverified",
        "roster_completeness": scenario.completeness_status,
        "request": result,
    }
