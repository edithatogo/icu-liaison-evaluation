# P11 — Scenario workflows and versioned runs

[Specification](spec.md) · [Plan](plan.md) · [Verification matrix](test-matrix.md) ·
[Metadata](metadata.json) · [Ownership and handoff](handoff.md)

The synthetic P11 implementation provides a recurring scenario suite,
content-addressed inputs and outputs, paired comparisons and a local Snakemake
pilot. It reuses the P4 model, P5 reporting and review, P10 assurance contracts
and P7 evidence boundaries. Local rerun and recovery evidence is recorded in
[the verification receipt](../../../verification/p11-synthetic-workflow-2026-11-20.json).

The independent P9 six-figure companion remains in its own unmerged PR and is
not included in the P11 scheduler. Integration and exact-revision hosted CI
remain open; this is synthetic source qualification, not local clinical or
provider acceptance.
