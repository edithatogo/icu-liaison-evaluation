# P11 — Scenario workflows and versioned runs

[Specification](spec.md) · [Plan](plan.md) · [Verification matrix](test-matrix.md) ·
[Metadata](metadata.json) · [Ownership and handoff](handoff.md)

The synthetic P11 implementation provides a recurring scenario suite,
content-addressed inputs and outputs, paired comparisons and a local Snakemake
pilot. It reuses the P4 model, P5 reporting and review, P10 assurance contracts
and P7 evidence boundaries. Local rerun and recovery evidence is recorded in
[the original receipt](../../../verification/p11-synthetic-workflow-2026-11-20.json)
and the [P9 integration receipt](../../../verification/p11-p9-integration-2026-11-20.json).

P9 PR #26 and P11 PR #28 are merged. The P11 scheduler builds the six-figure
companion for each synthetic scenario, including fixed-input break-even displays.
The integrated local workflow and recovery tests passed, as did the
[hosted check for merge commit 4398a03](https://github.com/edithatogo/icu-liaison-evaluation/actions/runs/44675128191).
This is synthetic source qualification, not local clinical or provider acceptance.
