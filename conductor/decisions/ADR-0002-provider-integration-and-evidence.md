# ADR-0002 — Dapane and Voiage, only at their qualified interfaces

Status: **accepted at source and local synthetic-contract level only**, 18 Nov 2026.

## Decision

Do not create generic cost allocators, exact-decimal valuation engines, or
health-economic value-of-information solvers. Use **Dapane** for exact resource
quotation application and **Voiage** for decision analysis. Maintain a narrow,
versioned consumer adapter that maps the clinical service comparison to those
provider contracts. Keep the existing NumPy/SciPy cohort PSA as an exploratory
scenario generator until the native providers and input calibration are
qualified; this is not duplication of a general simulation framework.

The first Dapane integration uses two positive-only *incremental* ledgers: one
for eligible index ICU delay and avoided return events, the other for the added
liaison service and any additional returns. It intentionally does not infer
complete hospital costs. Native Dapane performs valuation; only the difference
between two completed Dapane monetary totals is computed locally. The decimal
quantity mapping avoids binary NumPy artefacts in the exact provider input.

Voiage receives a two-strategy (current care versus liaison) table with annual
resource net-benefit draws. It alone owns EVPI; this is neither QALY-based nor
population-scaled and must not be presented as cost-effectiveness evidence.

## Gate

Source contract tests using injected dummy providers cannot establish an
installed integration. Actual installed Dapane and Voiage must match their
versioned contracts and pass independent oracles, with wheel/extension hashes
and full dependency resolution retained. Unavailable providers fail closed.
The draft PR in CareOps Sim is not merged or closed until a dedicated owner
repository preserves all accepted work and can carry its own qualification.
