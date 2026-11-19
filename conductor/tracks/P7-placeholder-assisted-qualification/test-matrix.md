# P7 verification matrix

| Contract | Positive test | Negative test | Qualification limit |
| --- | --- | --- | --- |
| Source inventory | All 33 IDs and paths resolve | Missing/duplicate/unsafe source or altered JSON pointer rejected | No independent source verification |
| P4 evidence labels | Synthetic prior status retained | Local prior promotion without review rejected | No causal effect evidence |
| Replacement candidates | SHA-256 private byte matches | Hash drift or public synthetic fixture rejected | Even matching candidates not approved |
| Cross-track dry run | P3, P4/P5 and P6 generate synthetic report | Missing P6 source refuses partial output | Not a native DES or CHHHS data calibration |
| Provider readiness | Explicit open gate and source lock | `--require-site-ready` returns 2 | External Dapane/Voiage/Kairos runtimes absent |
| Output integrity | All released hashes verified | Tampered output or overwrite rejected | Not a signed release |

Run `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_p7_placeholder_progress.py`.
Run all P0–P6 tests (possibly in non-overlapping partitions) before delivery.
