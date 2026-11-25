# Synthetic and provider boundary checks

Portable test commands using the repository runtime and dependency pins:

    PYTHONPATH=src .venv/bin/python -m pytest -q
    PYTHONPATH=src .venv/bin/python -m icu_liaison.cli model-inputs/illustrative.json

Expected: replay same seed exactly within supported local stack; central fixed
accounting matches independent equation; no-effect equals negative staffing
cost; negative readmission effect represents more returns; invalid source,
unit/probability and raw patient fields rejected; Dapane request exact decimal
strings/unique use; financial Voiage draws 2 strategy columns.

## Installed provider and hosted checks

The [installed-consumer receipt](../../../verification/p0-native-providers-py315-2026-11-19.json)
records passing Dapane 0.1.0 exact-quotation and Voiage 3.1.0 expected-value
oracles on CPython 3.15.2. The [P1 plan](../P1-provider-reuse/plan.md) records
independent acceptance of the corrected Dapane artifacts for the three tested
environments. The exact Voiage macOS arm64 wheel is admitted. Broader
Dapane release review remains in P1/P7.

The [migration comparison](../../../docs/pr215-migration-comparison.md)
links the preserved exploratory revision to the standalone merge and its
passing synthetic CI. The repository owner approved release of that migration.
[Portable source release](../../../docs/pr215-migration-comparison.md#portable-source-release)

## Strict source and Git checks

| Entry point | Acceptance evidence |
| --- | --- |
| `.venv/bin/python -m mypy` | Every active Python file under `src`, `tools` and `tests` passes strict checks on the pinned interpreter. |
| `.venv/bin/python -m pytest -q` | Strict pytest rejects duplicate parameter IDs. Fictional inputs exercise unexpected keys, invalid types, missing authority and favourable financial outcomes. |
| Ordinary commit, merge and push | A staged type error is rejected even with a repaired working file. A valid staged revision succeeds with a failing unstaged edit. The merge and push fixtures check each proposed tree and ref. |
| Hosted privacy checks | The egress audit, Gitleaks, Presidio and TruffleHog jobs retain their own run receipts. |
