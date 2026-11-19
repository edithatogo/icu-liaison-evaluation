# P2 handoff — portable candidate

The full P2 implementation is in this portable package. Actual exact local
source tests and admission receipt are in `verification/p2-local-receipt.json`
and `verification/p2-protocol-admission.json`. This handoff does not assert
site approval, clinical evidence of benefit, installed Dapane/Voiage support,
GitHub integration or deployment.

**Transfer to the user-selected private repo:** copy the source, protocol,
dictionary, ADR and tests; reconcile its existing governance/Conductor owners
before installing the pinned extension; preserve upstream P1 artifacts and
historical GitHub PR #215 until an exact-head replacement passes CI.

**P3 requirements:** verified local approval and pseudonymous episode keys;
source-by-field mapping of APD timing, movement, planned return, mortality,
MET, liaison, staff resources and patient costing. Retain quality missingness
and denominator checks; independently inspect local source definitions.

**P4 requirements:** approved causal estimand and safety margins, clinical
review, correctly priced resource-use ledger and budget-vs-economic analysis;
installed Dapane and Voiage source/binary numerical conformance.

## P2.5 preparation and P0/P1/P9 reconciliation — 19 November 2026

- Integrated into `edithatogo/icu-liaison-evaluation` (`main`), with exploratory
  CareOps Sim PR #215 retired (`CLOSED` at `e6caa16c5b87cbfadd2b10588ed10b7c6d60b637`,
  branch preserved) and macOS arm64 / Python 3.15.2 native Dapane `0.1.0` +
  Voiage `3.1.0` oracle receipts recorded in P1 (`providers.lock.json`
  `binary_sha256` independent adjudication still open).
- Added P2.5 stakeholder review deliverables without closing any external CHHHS
  gate: [stakeholder review pack](../../../docs/p2-stakeholder-review-pack.md),
  [32-to-115 CHHHS crosswalk](../../../model-inputs/p2-chhhs-field-crosswalk.json),
  [fail-closed governance sign-off template](../../../model-inputs/p2-governance-signoff-TEMPLATE.json),
  [P2 governance validators](../../../src/icu_liaison/p2_governance.py), and
  [governance/crosswalk receipt](../../../verification/p2-governance-crosswalk-2026-11-19.json).
