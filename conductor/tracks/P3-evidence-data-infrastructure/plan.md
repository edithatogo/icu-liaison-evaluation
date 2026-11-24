# P3 executable implementation and gates

## P3.1 — Public benchmarks and provenance
- [x] Record versioned ANZICS values, page, period, denominators and source-specific verification status without treating historical transcription as a newly reverified report.
- [x] Implement metadata/source-register integrity checks, incompatible denominators and no public 72-hour unplanned-return assumption.
- [x] Check the 2024/25 benchmark against the PDF served by ANZICS and record
  its document digest and page. [Publisher receipt](../../../verification/p7-anzics-2024-25-publisher-2026-11-24.json)
- [x] Reconcile all six saved publisher locators against the source register
  and check the retained PDF with the offline P3 CLI. Keep the independent
  admission gate open. [P3 source guide](../../../docs/p3-source-and-data-infrastructure.md#public-reference-data-and-source-status)
- [ ] Independently admit the report for the intended use with licensing and
  reviewer evidence.

## P3.2 — Local source profiles and safe loading
- [x] Create canonical CSV and Pydantic-JSON-Schema contracts with editable source column mapping, extraction freshness and SHA-256-pinned feed manifests.
- [x] Implement fail-closed restricted processing gate with private aggregate output; synthetic fixtures are the only committed data.
- [x] Use one captured manifest for the privacy decision, feed selection
  and provenance hash. Check the required private destination before
  opening restricted feeds, including when the CLI is installed.
- [ ] Verify actual CHHHS/ANZICS feed structure and privacy/ethics/cultural governance with custodians in an approved environment.

## P3.3 — Episode linkage and data quality
- [x] Select first eligible adult ward transfer per hospitalisation while retaining later ICU episodes, censor/competing-risk statuses and readiness missingness.
- [x] Reject duplicate/overlapping episodes, invalid/naive times, orphaned contacts/cost lines, incompatible resource segments and repeated use components.
- [x] Provide 32-field dictionary completeness/availability and non-overlapping local-vs-public denominators.
- [ ] Reconcile observed CHHHS data quality, case-mix, risk adjustment, full incident/outreach/workforce/cost feeds, temporal stability and source-level minimum completeness thresholds.

## P3.4 — Reproducibility and handoff
- [x] Write failing negative tests before implementation and test synthetic output, provenance, flags, privacy and source-schema publication.
- [x] Package the portable consumer and append-only Conductor source/migration receipt without overwriting earlier P0/P1/P2 evidence.
- [x] Pass the hosted source and synthetic admission checks in the dedicated
  repository. [Hosted record](../../../docs/repository-import.md)
- [x] Record the native Dapane approval for the exact P1 artifacts and their
  tested environments. [P1 platform evidence](../P1-provider-reuse/plan.md#linux-and-windows-x86-64-qualification)
- [x] Reconcile the admitted Voiage 3.1.0 macOS arm64 wheel and its
  CPython 3.15.2 scope. [P1 Voiage evidence](../P1-provider-reuse/plan.md#voiage-macos-artifact-admission)
- [ ] Complete independent acceptance of the repaired Dapane artifact
  and qualify other provider environments as needed through P1 and P7.

This source handoff does not authorise reading real CHHHS data or label any clinical or financial result empirically validated.

## Phase — Review fixes

- [x] Pin the retained receipt, validate each benchmark's report edition
  and period, reject observations after extraction, count identifiers
  at the dictionary grain and reject an existing output before restricted
  intake (`abf3c91`).

On CPython 3.15.2, 95 focused tests passed. The pinned receipt and retained
PDF matched the six registered outcomes. The fictional audit counted four
hospitalisations and seven ICU episodes for identifier completeness. The
illustrative model reproduced byte for byte. Independent source admission
and approved linked CHHHS inputs and validation remain open.
[P3 test matrix](test-matrix.md)
