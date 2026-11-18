# ADR-0003 — Separate clinical estimands, resource consequences and cash budget

**Status:** accepted for *portable source prototype* only, 18 November 2026;
local clinical, governance and financial approval pending.

## Decision

Maintain a machine-readable P2 protocol with an index-live-ward-discharge
analytic unit, physically timed clocks and case-specific censoring. Do not
pass CCR or APD readmission rates as local unplanned 72h risks. Separate
current, unmeasured usual care from a proposed incremental liaison package.
Mandatory safety outcomes accompany process efficiency and early returns.

Partition costs into mutually exclusive index-discharge-ready interval,
subsequent ICU-return episodes and incremental programme expenditure. Record
opportunity cost, actual cash savings and capacity hours as different economic
objects; Dapane values resource quantities rather than reimplementing costing.
Use the existing P1 NumPy/SciPy PSA as an *illustrative* scenario and Voiage
for optional decision analysis after provider verification. Avoid a custom
survival analysis or a custom DES; P3 owns episode linkage and P6/Kairos owns
optional temporal simulation.

## Consequences and gates

- A synthetic scenario may execute after P2 protocol admission. Admission
  report always states that local claims are blocked until separately
  approved empirical data, causal study, finance and clinical safety reviews.
- Missing readiness, unverified planned status, incomplete follow-up and
  competing death remain unknown rather than a favourable denominator.
- Draft protocol defaults are versioned and replaceable, never evidence of
  CHHHS FTE, clinical workload, measured effectiveness or budget effect.
- Endpoints are independently testable without loading patient data or
  installing Dapane/Voiage/Kairos.
- A material local change to cohort, price year, comparator, safety criteria
  or cost scope requires a versioned protocol update and renewed qualification.
