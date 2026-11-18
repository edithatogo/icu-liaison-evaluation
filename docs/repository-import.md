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

The source suite runs on Python 3.13 with pinned source/test/report dependency
versions. The hosted [Source CI workflow](../.github/workflows/ci.yml) checks the
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
