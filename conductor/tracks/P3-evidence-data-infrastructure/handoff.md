# P3 handoff and unresolved external gates

18 November 2026. The portable project has no user-provided dedicated GitHub destination. P3 source adapters, CLI, negative-case tests, public metadata crosswalk, versioned synthetic fixtures, source provenance and data-quality documentation are implemented locally, with verification results retained separately under `verification/p3-local-receipt.json`.

The P2 clinical protocol and 32-field dictionary are unchanged and remain draft/unapproved. The existing P1 Dapane and Voiage runtime integration is still unverified. The exploratory CareOps Sim PR #215 remains unmerged as historical source and is not a destination for this feature.

## Blockers

1. Obtain source PDF binary/reviewer evidence for the 2024/25 CCR report, and reassess any conflicting value without guessing.
2. Obtain CHHHS data steward and clinical/Finance governance, appropriate privacy and Indigenous data-governance approvals, site-specific source mappings, permitted processing and disclosure limits.
3. Qualify actual producer feeds and timestamps, 32-field source completeness and cross-site followup; fit ascertainment/clinical effects with independent comparators in P4.
4. Run provider-native P1 gates, repository-hosted checks and independent review after a dedicated repository is supplied.

No claim of completed document verification, live source integration, clinical risk adjustment, local cost saving or project deployment is made by the source tests.

## P3 verified preservation

The prior 15 P0–P2 source/input files compared byte-for-byte with the original P2 ZIP have no differences; the illustrative simulation JSON is byte-for-byte equivalent at the JSON-object level to the inherited P2 source receipt. `conductor/evidence/source-register.json`, the migration manifest, and documentation have append-only P3 source qualification updates and therefore intentionally differ from P2.

The 2023/24 publisher text was independently inspected via ANZICS' public PDF search text; the 2024/25 publisher report link could not be retrieved in this source pass. `public_evidence.py` fails closed if the machine catalogue's benchmark numerators/denominators/amounts/page/contributors disagree with its source register, and a required full-document verification is still blocked.

## P3 evidence and intake update on 24 November 2026

The [source worktree and chat recorded for P1](../P1-provider-reuse/handoff.md#p1-artifact-review-on-24-november-2026)
carried the P3 CLI, source reconciliation and intake changes on
`codex/icu-p3-evidence-admission`. The offline check matched all six
2024/25 locators and the saved PDF digest. The intake audit used one
manifest for privacy and provenance and ran on fictional fixtures.
Independent admission, approved local feeds and empirical checks remain
with their existing owners. The publisher PDF and run outputs stay private.
[Source and intake guide](../../../docs/p3-source-and-data-infrastructure.md)
