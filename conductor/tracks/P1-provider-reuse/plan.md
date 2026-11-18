# P1 — implementation and acceptance

## P1.1 — Source and interface qualification
- [x] Inspect current Dapane contract 0.1 and installed Python/API requirements;
  record immutable source revision without implying wheel provenance.
- [x] Inspect Voiage v3.1.0 released tag/DecisionAnalysis/ValueArray interfaces;
  record supported Python version and source reference.
- [x] Introduce `providers.lock.json` and strict source/version gates. Do not
  treat compatible metadata as completed native integration.

## P1.2 — Dapane cost ledger consumer
- [x] Generate pairwise scenario requests with exact nonnegative decimal use,
  separating index delay and subsequent return episodes, allowing adverse
  readmission changes and explicit price-year/perspective/basis.
- [x] Call Dapane for cost valuation and reject wrong run, currency, basis,
  method/version, non-finite or negative output. No alternate production kernel.
- [x] Establish independent two-line cost identity and zero/adverse-effect
  regression cases with injected boundary providers.

## P1.3 — Voiage decision-analysis consumer
- [x] Reuse the supported two-strategy financial decision array and
  `DecisionAnalysis.evpi()` rather than implementing EVPI.
- [x] Check output finiteness, strategies, scope and financial-only meaning;
  regression with provider injection and an independent 2-state native oracle.

## P1.4 — Installed runtime qualification (blocked)
- [ ] Obtain an authorised, exact-source Dapane 0.1 native wheel and released
  Voiage 3.1.0 distribution in an isolated CPython 3.15.2 environment; save
  inspected wheel and native-extension SHA-256 plus dependency resolution.
- [ ] Run `python tools/qualify_providers.py --provider all` in that environment,
  record installed numerical reference outputs, compatibility, vendor tests,
  security/licence results and exact source attestations.
- [ ] Run unchanged full tests using that runtime, compare cross-environment
  reproducibility/precision, record remaining qualification findings.

## P1.5 — Dedicated repository integration (blocked)
- [ ] Import P0/P1 into the user-provided private repository, reconcile its
  Conductor track registry, run hosted exact-head checks and independent review.
- [ ] Retire exploratory CareOps Sim PR #215 only after equivalent source,
  evidence and test outcomes have been verified in the new repository.

Source-only completion is not native acceptance and is not a clinical or
investment recommendation. Keep P1.4 and P1.5 unaccepted until their actual
receipts exist.
