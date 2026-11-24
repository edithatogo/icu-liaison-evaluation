# P7 verification matrix

| Contract | Positive test | Negative test | Qualification limit |
| --- | --- | --- | --- |
| Source inventory | All 33 IDs and paths resolve | Missing, duplicate, private or otherwise unsafe source rejected | No independent source verification |
| P4 evidence labels | Synthetic prior status retained | Local prior promotion without review rejected | No causal effect evidence |
| Replacement candidates | Submission in private storage and SHA-256 matches for each artifact | Tracked or unignored files in a checkout, public paths and hash drift rejected | Matches identify candidate bytes only |
| Cross-track dry run | P3, P4/P5 and P6 generate synthetic report | Missing P6 source refuses partial output | Not a native DES or CHHHS data calibration |
| Provider and site readiness | Source lock records scoped Dapane and Voiage artifact decisions | `--require-site-ready` returns 2 | See P7.4 for outstanding provider and site qualification |
| Output integrity | Progress receipt, 33 unresolved checklist entries and P5 report inventory and hashes verified | Missing files or obligations, inconsistent readiness claims, tampered files and overwrites rejected | Checks file completeness, hashes and declared status |

Run `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_p7_placeholder_progress.py`.
Run all P0–P6 tests (possibly in non-overlapping partitions) before delivery.

## Implementation checkpoint

On 24 November 2026 the three added regressions failed on the previous
implementation and passed with the fixes. The fictional dry run produced
the same bundle bytes and the audit still reported all 33 obligations open.
The 18 November receipt remains the historical source checkpoint.

## Review checkpoint

Ten regressions failed before the review fixes and passed in the 29 focused
tests. The cases cover private JSON and feed bindings, a link into private
storage, ignored and tracked files in another checkout, and a bundle with
matching hashes and inconsistent readiness or missing placeholder entries.
The synthetic bundle reproduced byte for byte. The site-ready audit exited 2
and listed all 33 unresolved obligations.
