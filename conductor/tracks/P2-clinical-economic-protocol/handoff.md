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
