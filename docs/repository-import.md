# Initial repository import

Prepared 19 November 2026 (Australia/Brisbane) for the user-selected private
repository [edithatogo/icu-liaison-evaluation](https://github.com/edithatogo/icu-liaison-evaluation).
The user authorised proceeding with placeholders for missing information.

## Reconciled material

The import uses the P8.4 source-composition archive as its base and adds every
P7-only file from the later placeholder-progress archive. Both P7 track histories
are retained and cross-linked. The placeholder ADR is renumbered to ADR-0007
to preserve the existing P8 ADR-0006 without an identifier collision.

The [import provenance](../conductor/evidence/repository-import-2026-11-19.json)
records the exact input archive names and SHA-256 hashes. The current
[source inventory](../SOURCE_MANIFEST.json) covers the reconciled project files.
Conductor is a separately verified gitlink at its reviewed 0.4.1 commit.

The original workbook, publisher report binaries, private CHHHS data and raw
conversation material are not imported. Earlier verification receipts remain
unaltered historical records, including their original missing-repository
statements. Current ownership and import state are defined by the root README,
Conductor index and migration manifest.

## Placeholder policy

The [33-entry register](../model-inputs/placeholders/registry.json) retains
missing source, local-data, provider and approval obligations. The repository
URL is known and is recorded separately from its unresolved release-review
receipt. CI output is technical evidence for subsequent review; it does not
self-approve this receipt or any site-ready gate.

P8 additionally retains null/unqualified activity, workforce and funding inputs.
MCHS NWAU is not monetised, workforce quotation requests are not valued, and
the existing synthetic P4 result is not altered by their attachment. Qualified
workforce costs must later replace or reconcile the service-cost prior.

## Verification and practical limits

The source suite uses the CPython pin in [`.python-version`](../.python-version)
and the constraints in [`requirements-ci.txt`](../requirements-ci.txt).
The hosted [Source CI workflow](../.github/workflows/ci.yml) checks the
source manifest and Conductor gitlink, all Python tests and a synthetic CLI
workflow. The latter verifies the independently reviewed P5 report, rejects a
tampered readiness claim and requires site-ready/qualified admission to remain
blocked. Current hosted results are available in [Actions](https://github.com/edithatogo/icu-liaison-evaluation/actions).

Native Dapane, Voiage and Kairos execution, MCHS official parity, local workforce
qualification, CHHHS data/calibration and clinical/Finance/cultural-governance
reviews remain separate obligations. No clinical effect, actual funding, cash
saving or investment readiness is established by the initial source import.

The original CareOps Sim PR #215 is preserved. Its closure requires a separate
source comparison and accepted migration record.

## Initial push outcome

The source is pushed in [PR #1](https://github.com/edithatogo/icu-liaison-evaluation/pull/1).
All 314 local tests and the synthetic CLI workflow passed. The first push and
pull-request Actions runs were blocked before any job step by account billing
or spending-limit availability. This is recorded in the [hosted attempt receipt](../verification/hosted-ci-2026-11-19.json).
The PR remains open; rerun hosted checks after runner availability is restored
and inspect the latest head before integration. Source-only review and local
validation do not replace that hosted result.

## Local CI/CD and merge update (2026-11-19)

[PR #1](https://github.com/edithatogo/icu-liaison-evaluation/pull/1) was merged
into `main` (`4644bb4f5c2597cfc5e07cabe4de0b33e9dfb558`). The hosted merge run
(`44434804695`) again failed before any job step due to account billing/spending
limit availability. To enforce CI locally without altering hosted gates, track
`P0-portable-consolidation` added `tools/run_local_ci.py`, `.pre-commit-config.yaml`,
versioned `.githooks/` (`pre-commit`, `pre-merge-commit`, `pre-push`), and
`tools/audit_conductor_extension.py`. Local receipts are recorded in
`verification/p0-local-ci-2026-11-19.json` and
`verification/p0-gemini-conductor-audit-2026-11-19.json`; hosted CI, native
providers, and CareOps Sim PR #215 retirement remain separate open gates.

## Public visibility, hosted CI, native oracles, and PR #215 comparison (2026-11-19)

After auditing the repository for private/confidential data, visibility was
switched to public with GitHub Secret Scanning and Push Protection enabled, and
`gitleaks protect --staged` was wired into `pre-commit` and `pre-merge-commit`.
Hosted GitHub Actions (`Synthetic source validation`) passed on `main` (`1c7f640`,
run `44444785989`), recorded in `verification/hosted-ci-public-2026-11-19.json`.
Isolated Python 3.15.2 native Dapane `0.1.0` (`0658d94ad772023a0185a000b5254f9c2f4a63a9`)
and PyPI Voiage `3.1.0` numerical oracles passed in
`verification/p0-native-providers-py315-2026-11-19.json` (lockfile
`verification/p0-py315-native-lock-2026-11-19.txt`), and the 19-file read-only
comparison with CareOps Sim PR #215 is documented in `docs/pr215-migration-comparison.md`
(`verification/p0-pr215-migration-comparison-2026-11-19.json`). Independent
wheel-provenance adjudication and PR #215 retirement remain separate open gates.
