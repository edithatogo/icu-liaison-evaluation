# P5 implementation and independent gates

## P5.1 — Report outputs and uncertainty presentation
- [x] Use existing P4 outcomes to create distinct consequence, budget, capacity, paired comparison and one-way-sensitivity tables.
- [x] Add nominal resource break-even, required coverage and safety caveats to readable decision brief.
- [x] Provide optional Matplotlib SVG with clear synthetic/non-CHHHS labeling.

## P5.2 — Provider interoperability
- [x] Emit synthetic Voiage decision surface (one annual programme decision per draw) and nonnegative Dapane nominal costing requests.
- [x] Implement opt-in provider-backed EVPI; absent provider is `not_executed` by default or fail-closed when required.
- [x] Record the independent Dapane wheel, extension and pricing decisions
  for the three tested P1 environments. [Provider lock](../../../providers.lock.json)
- [x] Record admission of the exact Voiage 3.1.0 macOS arm64 wheel on
  CPython 3.15.2 and the reconciled P5 report.
  [P1 artifact admission](../P1-provider-reuse/plan.md#voiage-macos-artifact-admission)
- [ ] Complete broader Dapane release review and qualify any further provider
  environments required for the intended P5 analysis through P1 and P7.

## P5.3 — Evidence, privacy and reproducibility
- [x] Preserve P2/P3 source admission, protocol and input digests; prevent readiness claims.
- [x] Add independently checked accounting equations, SHA-256 file-set manifest, atomic publication and overwrite rejection.
- [x] Run independent report-reader checks against exported decision draws, rejecting rehashed semantic tampering.
- [x] Reconcile all cost-consequence rows and both paired comparisons in the
  standalone reader. Preserve evidence status and support fully fixed scenarios.
  [Verification](test-matrix.md#standalone-report-verification-on-24-november-2026)
- [x] Add opt-in native Dapane valuation and strict nominal reconciliation.
- [x] Run negative tests for invalid provider output, mutated manifest, invalid P2/P3 evidence and no-effect/negative-effect cases.
  Both corrected Dapane-unavailable tests passed with Dapane 0.1.0 installed
  on CPython 3.15.2. The installed-provider synthetic report also reconciled
  across all three strategies.
  [Migration receipt](../../../verification/python-315-migration-2026-11-19.json)

## P5.4 — External clinical/financial review (blocked)
- [ ] Obtain independent clinician/nursing/Finance/health-economics review, approved safety balancing, actual local data and signed costing interpretation.
- [x] Pass exact-head hosted CI and the P5 synthetic report smoke test in the
  dedicated repository. [P0.5 verification](../P0-portable-consolidation/plan.md#p05--python-and-hosted-ci-runtime-migration)
- [ ] Obtain independent code and supply-chain release acceptance for the
  intended deployment.

## Phase — Review fixes

- [x] Apply review fixes in `fb4e087`. Review the registered bundle contents,
  check the decision brief and sensitivity arithmetic, and record when empty
  nominal ledgers require no Dapane call.
  [Verification](test-matrix.md#p5-review-fixes-on-24-november-2026)
