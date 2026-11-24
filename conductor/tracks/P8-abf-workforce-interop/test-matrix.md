# P8 acceptance matrix

| Scope | Required evidence | Status |
| --- | --- | --- |
| Source admission | Five exact provider commit references, contract ownership and no installed claim | Inspected, local-only |
| Synthetic crosswalk | JSON Schema 2020-12, null fixture, incompatible funding and nursing data rejected | Executable test candidate |
| MCHS consumer | Reference SHA-256, same-year fictional case pairs, unchanged-case control | Pinned 2024–25 and 2025–26 inlier replays match saved SAS oracles. Full parity remains open. |
| Nursing consumer | Exact quantity and quote scope, component overlap, date and source guards | Three fictional quotes passed the installed bridge. Mismatched classifications and observed-use claims are rejected. |
| Dapane/Voiage | Exact artifact checks, separate replay of each financial perspective | Scoped financial and resource valuations and four selected EVPI comparisons match independent calculations. |
| Kairos | Native usage event replay only if used | Optional and unqualified |
| CHHHS | Clinical/Finance approval, actual episode and staffing data, causal effect and capacity review | Not obtained |

Local focused check: `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_p8_provider_roadmap.py`.
Run inherited source suites without interpreting them as provider binaries or
hospital validation. No price, funding, clinical or native provider is admitted
by accepting source-only tests.

Additional source tests: `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_p8_mchs_pair.py tests/test_p8_roster_bridge.py tests/test_p8_cli_and_schemas.py`. Generated JSON Schema uses `PYTHONPATH=src .venv/bin/python tools/export_p8_schemas.py`. Native provider checks remain blocked until installed/qualified packages and official references are available.

| P8.4 source-only crosswalk | 29 synthetic/CLI/schema tests; P4 means and budget outputs remain unchanged; NWAU stays case-level; unvalued roster cost stays null | Implemented, injected and static; native provider not qualified |

## Fictional provider workflow on 24 November 2026

The replay records the complete SAS directory fingerprints, the workforce
fixture and exported quotation identities, the reviewed native extensions,
and P4's input digest and seed. Both composed CLI outputs validate against
the schema and differ only in the selected Voiage comparison.
[Provider workflow receipt](../../../verification/p8-provider-workflow-2026-11-24.json)
