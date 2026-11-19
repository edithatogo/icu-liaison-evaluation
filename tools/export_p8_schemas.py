"""Regenerate bounded P8 schema declarations; review diffs before acceptance."""
from __future__ import annotations

import json
from pathlib import Path
from icu_liaison.p8_contract_schema import schema_for
from icu_liaison.p8_composition import P8Composition

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/"model-inputs"/"p8"
for kind, name in (("mchs", "mchs-paired-episode.schema.json"),
                   ("roster", "nursing-roster.schema.json")):
    (DATA/name).write_text(json.dumps(schema_for(kind),indent=2,sort_keys=True)+"\n",encoding="utf-8")

(DATA/"p8-composition.schema.json").write_text(
    json.dumps(P8Composition.model_json_schema(),indent=2,sort_keys=True)+"\n",encoding="utf-8"
)
