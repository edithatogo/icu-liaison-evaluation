# P7 small independently executable tasks

## P7.1 — Explicit dependency inventory
- [x] 1. Record all unresolved ANZICS, site input, native provider and governance dependencies by stable ID and source JSON pointer.
- [x] 2. Record prospective owner role, replacement type, acceptance criteria and blocked decisions.
- [x] 3. Reject missing, duplicated or unknown IDs and false observed/native/approval promotion.

## P7.2 — Synthetic source and model orchestration
- [x] 1. Provide canonical synthetic P3 episode/follow-up/contact/cost CSV fixtures with SHA-256 and no real identifiers.
- [x] 2. Run P3 aggregate QA, P4/P5 probabilistic report and P6 trace/holdout without new computation engines.
- [x] 3. Publish atomically, refuse overwrites and verify all hashes.
- [x] 4. Prove synthetic P3 fixture does not recalibrate P4 annual cohort or validate native Kairos.
- [x] 5. Require the progress receipt, replacement checklist and complete P5
  report when verifying the dry-run bundle. Reuse the P5 manifest verifier.

## P7.3 — Safe future-source handoff
- [x] 1. Define strict, private-only candidate receipt contract with file SHA-256 and source role.
- [x] 2. Implement a candidate-byte check that **never** returns independent source or site approval.
- [x] 3. Export a per-placeholder evidence replacement checklist and registration JSON Schema.
- [x] 4. Reconcile with P0–P6 Conductor and document how to substitute real inputs privately.
- [x] 5. Check the candidate submission's location before reading it. Apply the
  same private-file rules to the submission and each referenced artifact.

## P7.4 — External qualifications (blocked, not accepted)
- [~] 1. Qualify the ANZICS PDF and page-specific denominators. The direct
  publisher and page checks are recorded. Independent admission remains open.
  [P7.6 evidence](../../../verification/p7-anzics-2024-25-publisher-2026-11-24.json)
- [ ] 2. Obtain approved CHHHS cohort, workforce, cost, ward and clinical safety data with competent oversight.
- [ ] 3. Execute and independently qualify pinned Dapane/Voiage/Kairos provider artifacts.
  Dapane's approved wheels, extensions and native pricing receipts are
  scoped to the environments recorded in the lock. The Dapane and Voiage
  placeholders track broader qualification through their respective
  `provider_qualification_receipt_sha256` fields.
  Voiage's admitted macOS arm64 artifact is recorded in the P1 lock.
  [Provider lock](../../../providers.lock.json) ·
  [Technical P7.5](../P7-technical-empirical-qualification/plan.md)
  The pinned Kairos consumer passed local replay and awaits independent build
  attestation.
- [ ] 4. Perform controlled comparison and clinical/Finance/research/cultural governance reviews.
- [x] 5. Integrate the portable source into the selected repository and verify
  hosted checks. CareOps Sim PR #215 is closed and the repository owner
  approved release of the verified migration.
  [Portable source release](../../../docs/pr215-migration-comparison.md#portable-source-release) ·
  [Receiving commit CI](https://github.com/edithatogo/icu-liaison-evaluation/actions/runs/44455595345)
- [ ] 5a. Record the independent PR review receipt for the receiving commit
  `1ff7ca460ac135a3cd545701d22ddf82d2d97d90` required by the `dedicated_repo_ci`
  placeholder. The only submitted review on PR #5 was an automated comment on
  the earlier `6757546` head. The hosted pass and owner release approval are
  recorded separately.
  [Evidence register](../../../model-inputs/placeholders/registry.json) ·
  [PR #5 review](https://github.com/edithatogo/icu-liaison-evaluation/pull/5#pullrequestreview-5969092662)

**P7.1–P7.3 passing means only synthetic implementation progress.** It cannot
waive P7.4 or any other repository's validation and release gate.

## Phase — Review fixes

- [x] Applied in `16b5ba2`. Check candidate files against the containing Git
  checkout, keep private paths out of the public audit and verify the dry-run
  receipt and checklist retain their synthetic scope and 33 open obligations.
  [Review verification](test-matrix.md#review-checkpoint)
