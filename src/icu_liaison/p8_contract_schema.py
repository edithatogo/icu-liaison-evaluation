"""Machine-readable strict P8 input contracts derived from the consumer types."""
from __future__ import annotations

from .adapters.p8_mchs import MchsPair
from .adapters.p8_workforce import RosterScenario

EXACT = {"type": "string", "pattern": r"^(0|[1-9][0-9]*)(\.[0-9]+)?$"}


def schema_for(kind: str) -> dict:
    if kind not in ("mchs", "roster"):
        raise ValueError("unsupported schema kind")
    model = MchsPair if kind == "mchs" else RosterScenario
    result = model.model_json_schema()
    result["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    result["$id"] = f"urn:icu-liaison:p8:{kind}:1"
    if kind == "mchs":
        for name in ("icu_hours_current", "icu_hours_intervention", "icu_other_hours"):
            result["properties"][name] = {**EXACT, "title": result["properties"][name]["title"]}
    else:
        result["$defs"]["RosterExposure"]["properties"]["quantity"] = {
            **EXACT, "title": "Quantity",
        }
    return result
