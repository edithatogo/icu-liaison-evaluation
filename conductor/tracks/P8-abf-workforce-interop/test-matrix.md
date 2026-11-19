# P8 acceptance matrix

| Scope | Required evidence | Status |
| --- | --- | --- |
| Source admission | Five exact provider commit references, contract ownership and no installed claim | Inspected, local-only |
| Synthetic crosswalk | JSON Schema 2020-12, null fixture, incompatible funding and nursing data rejected | Executable test candidate |
| MCHS consumer | Synthetic paired cases, 2024/2025 year/edition, no NWAU-to-revenue claim | Implemented; injected negative/positive tests pass; installed annual parity not run |
| Nursing consumer | Exact quoted roster segments, overlap/component guards, source pin and no payroll formula | Implemented; injected contract tests pass; award and complete-roster checks not run |
| Dapane/Voiage | Exact installed binary/wheel checks, sample-and-price parity, decision draw alignment | Not run |
| Kairos | Native usage event replay only if used | Optional and unqualified |
| CHHHS | Clinical/Finance approval, actual episode and staffing data, causal effect and capacity review | Not obtained |

Local focused check: `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_p8_provider_roadmap.py`.
Run inherited source suites without interpreting them as provider binaries or
hospital validation. No price, funding, clinical or native provider is admitted
by accepting source-only tests.

Additional source tests: `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_p8_mchs_pair.py tests/test_p8_roster_bridge.py tests/test_p8_cli_and_schemas.py`. Generated JSON Schema uses `PYTHONPATH=src .venv/bin/python tools/export_p8_schemas.py`. Native provider checks remain blocked until installed/qualified packages and official references are available.

| P8.4 source-only crosswalk | 29 synthetic/CLI/schema tests; P4 means and budget outputs remain unchanged; NWAU stays case-level; unvalued roster cost stays null | Implemented, injected and static; native provider not qualified |
