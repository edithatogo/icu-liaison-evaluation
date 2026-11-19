# P5 implementation and independent gates

## P5.1 — Report outputs and uncertainty presentation
- [x] Use existing P4 outcomes to create distinct consequence, budget, capacity, paired comparison and one-way-sensitivity tables.
- [x] Add nominal resource break-even, required coverage and safety caveats to readable decision brief.
- [x] Provide optional Matplotlib SVG with clear synthetic/non-CHHHS labeling.

## P5.2 — Provider interoperability
- [x] Emit synthetic Voiage decision surface (one annual programme decision per draw) and nonnegative Dapane nominal costing requests.
- [x] Implement opt-in provider-backed EVPI; absent provider is `not_executed` by default or fail-closed when required.
- [ ] Qualify exact native Dapane and Voiage wheel/binary outputs in supported runtime.

## P5.3 — Evidence, privacy and reproducibility
- [x] Preserve P2/P3 source admission, protocol and input digests; prevent readiness claims.
- [x] Add independently checked accounting equations, SHA-256 file-set manifest, atomic publication and overwrite rejection.
- [x] Run independent report-reader checks against exported decision draws, rejecting rehashed semantic tampering.
- [x] Add opt-in native Dapane valuation and strict nominal reconciliation (installed execution remains separately blocked).
- [x] Run negative tests for invalid provider output, mutated manifest, invalid P2/P3 evidence and no-effect/negative-effect cases.
  Both corrected Dapane-unavailable tests passed with Dapane 0.1.0 installed
  on CPython 3.15.2. The installed-provider synthetic report also reconciled
  across all three strategies.
  [Migration receipt](../../../verification/python-315-migration-2026-11-19.json)

## P5.4 — External clinical/financial review (blocked)
- [ ] Obtain independent clinician/nursing/Finance/health-economics review, approved safety balancing, actual local data and signed costing interpretation.
- [ ] Run exact-head hosted CI, independent code review, supply chain and real installed-provider tests after migrating to the dedicated repository.
