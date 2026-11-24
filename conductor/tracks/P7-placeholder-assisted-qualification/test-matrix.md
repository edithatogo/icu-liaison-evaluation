# P7 verification matrix

| Contract | Positive test | Negative test | Qualification limit |
| --- | --- | --- | --- |
| Source inventory | All 33 IDs and paths resolve | Missing/duplicate/unsafe source or altered JSON pointer rejected | No independent source verification |
| P4 evidence labels | Synthetic prior status retained | Local prior promotion without review rejected | No causal effect evidence |
| Replacement candidates | Submission in private storage and SHA-256 matches for each artifact | Public submission, hash drift or public synthetic fixture rejected | Matches identify candidate bytes only |
| Cross-track dry run | P3, P4/P5 and P6 generate synthetic report | Missing P6 source refuses partial output | Not a native DES or CHHHS data calibration |
| Provider and site readiness | Source lock records scoped Dapane and Voiage artifact decisions | `--require-site-ready` returns 2 | See P7.4 for outstanding provider and site qualification |
| Output integrity | Progress receipt, checklist and P5 report inventory and hashes verified | Empty manifest, incomplete nested report, tampered file or overwrite rejected | Hash and completeness check only |

Run `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_p7_placeholder_progress.py`.
Run all P0–P6 tests (possibly in non-overlapping partitions) before delivery.

## Implementation checkpoint

On 24 November 2026 the three added regressions failed on the previous
implementation and passed with the fixes. The fictional dry run produced
the same bundle bytes and the audit still reported all 33 obligations open.
The 18 November receipt remains the historical source checkpoint.
