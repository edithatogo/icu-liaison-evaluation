# P4 implementation and external acceptance

## P4.1 — Reuse previously implemented probabilistic model
- [x] Reconcile existing multi-strategy SciPy/NumPy model rather than building another statistical engine.
- [x] Preserve scenario distributions, shared baseline draws, Gaussian-copula PSD checks, fixed seed and explicit cost/resource terms.
- [x] Preserve negative relative readmission effects, service coverage, readiness guard and non-overlap cost segments.

## P4.2 — Close source-admission and model reporting
- [x] Add executable P2/P3 crosswalk to P4 CLI and P5 report; source consistency and source verification remain separately represented.
- [x] Keep one-way prior-quantile, threshold, structural strategy comparison, cash and capacity consequences separate.
- [x] Reuse P4 Dapane nonnegative nominal quotation requests and Voiage matrix; no provider substitution.

## P4.3 — Source-level qualification
- [x] Write independent normal/invalid test cases and verify no-effect, adverse-effect, stochastic, conservation, source/currency/safety rejection, overflow and CLI outcomes.
- [x] Run full inherited P0–P4 suite and a P4 CLI smoke; record exact commands, versions, counts and file digests in verification receipt.

## P4.4 — Empirical/provider acceptance (blocked)
- [ ] Independently admit the 2024/25 source and denominator for model use.
  The publisher byte and value checks are recorded by P7.
  [Publisher receipt](../../../verification/p7-anzics-2024-25-publisher-2026-11-24.json)
- [ ] Reconcile actual CHHHS activity, case mix, readmission/safety outcomes, workforce/Finance costs, risk adjustment and causal effect.
- [ ] Execute installed Dapane/Voiage and independent hosted checks at exact revision in future dedicated repository.
