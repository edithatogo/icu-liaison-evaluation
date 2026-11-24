# P4 implementation and external acceptance

## P4.1 — Reuse previously implemented probabilistic model
- [x] Reconcile existing multi-strategy SciPy/NumPy model rather than building another statistical engine.
- [x] Preserve scenario distributions, shared baseline draws, Gaussian-copula PSD checks, fixed seed and explicit cost/resource terms.
- [x] Preserve negative relative readmission effects, service coverage, readiness guard and non-overlap cost segments.

## P4.2 — Close source-admission and model reporting
- [x] Add executable P2/P3 crosswalk to P4 CLI and P5 report; source consistency and source verification remain separately represented.
- [x] Keep one-way prior-quantile, threshold, structural strategy comparison, cash and capacity consequences separate.
- [x] Reuse P4 Dapane nonnegative nominal quotation requests and Voiage matrix; no provider substitution.
- [x] Reconcile the protocol's benchmark period with P3 and reject inputs
  labelled as local aggregates at fictional P4 and P5 admission.

## P4.3 — Source-level qualification
- [x] Write independent normal/invalid test cases and verify no-effect, adverse-effect, stochastic, conservation, source/currency/safety rejection, overflow and CLI outcomes.
- [x] Run full inherited P0–P4 suite and a P4 CLI smoke; record exact commands, versions, counts and file digests in verification receipt.
- [x] Requalify the P4/P5 admission and fictional outputs against the reviewed
  P3 contract. [Verification](test-matrix.md#p4p5-admission-rerun-on-24-november-2026)

## P4.4 — Empirical/provider acceptance (blocked)
- [ ] Independently admit the 2024/25 source and denominator for model use.
  The publisher byte and value checks are recorded by P7.
  [Publisher receipt](../../../verification/p7-anzics-2024-25-publisher-2026-11-24.json)
- [ ] Reconcile actual CHHHS activity, case mix, readmission/safety outcomes, workforce/Finance costs, risk adjustment and causal effect.
- [x] Pass the source and synthetic model checks at an exact revision in the
  dedicated repository. [Hosted record](../../../docs/repository-import.md)
- [x] Record the installed numerical checks and scope the Dapane approval to
  the exact artifacts and hosts in the P1 lock. [P1 plan](../P1-provider-reuse/plan.md)
- [ ] Complete independent model review and the outstanding P1 provider
  admission for the intended analysis.

## Phase — Review fixes

- [x] Apply the simulation's return-risk bound to break-even thresholds,
  handle cost-free neutral strategies, reject unknown decision objectives
  and local protocol strategy evidence, and publish decision CSVs only
  after validation and a complete write (`7e94f15`).

All 103 focused tests passed. The adverse-return stress case agreed with
the simulated ledger at 75% coverage. The standard decision draws and report
tables reproduced byte for byte.
[Review verification](test-matrix.md#p4-review-rerun-on-24-november-2026)
