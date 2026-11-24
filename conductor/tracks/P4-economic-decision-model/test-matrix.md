# P4 acceptance tests

- `.venv/bin/python -m pytest -q tests/test_p4_economic_model.py tests/test_p4_cli.py tests/test_p4_dapane_bridge.py tests/test_p4_admission.py`
- `.venv/bin/python -m icu_liaison.p4_cli model-inputs/p4/illustrative.json --one-way-strategy liaison_service`
- `.venv/bin/python -m pytest -q` — all inherited P0–P3 + P4 tests.

Require reference accounting identities; multi-run same-seed parity; no effect;
negative effects; source-benchmark and protocol crosswalk; bounds, copula and
finite-result guards; distinct Voiage/Dapane semantics; no clinical or investment
claim. P4.4 records the remaining provider and CHHHS empirical gates. P1 records
the scoped native results.

## P4/P5 admission rerun on 24 November 2026

On CPython 3.15.2, 83 focused tests passed across P4, P5, P7 and P11.
The four new cases first reproduced acceptance of the wrong benchmark period
and of local priors for return risk, marginal costs and staffing costs.
Both CLI entry points exited with status 2 on the mismatched period and the
local-aggregate case, before creating the requested output.

At seed `20261118`, the P4 summary with one-way sensitivity and the P5
report bundle matched the baseline bytes. The P5 report reviewer checked
5,000 draws for three strategies and retained illustrative status.

- P4 JSON SHA-256 `f9d1e305e0a1777db0faa47573120b52bc952f4840e5cfb955184a76dd4be2c0`
- P4 decision CSV SHA-256 `4e4e4986549fdb825e1bc58f74d1bcc0c959c5db20916d6c3ebf514cf312b16d`

## P4 review rerun on 24 November 2026

On CPython 3.15.2, the nine regression cases failed before the fixes and
passed as part of the 103 focused tests. The adverse-return stress case
breaks even at 75% coverage in both the simulation and the threshold report.
A cost-free neutral strategy permits break-even. The decision surface rejects
unknown objectives, and both readiness flags refuse file export. An
interrupted CSV write leaves the destination available for a retry.

At seed `20261118`, the standard decision draws and report tables matched
the previous bytes. The JSON summaries use the current provider status
wording. The P5 reviewer again checked 5,000 draws across three strategies.
