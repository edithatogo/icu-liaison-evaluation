# ADR-0001: Own the clinical decision; consume existing calculation engines

**Status:** accepted for portable migration only — 18 November 2026.

## Decision

A dedicated, eventually private project owns intervention definition, cohort,
source evidence, scenario assumptions, validation and economic outputs.
Dapane owns exact quotations/allocation; Voiage owns VOI methods; Searchright
owns evidence search; optional Kairos owns event timing/resources. CareOps Finance
is an optional reporting consumer. Avoid a mandatory simulation/runtime
framework and do not vendor full upstream repositories.

Replace custom triangular samplers and quantile arithmetic from the exploratory
CareOps Sim PR #215 with SciPy and NumPy. Pydantic validates tagged inputs.
Model-specific cost-consequence identities remain here; they are scientific
policy, not a general-purpose numerical library. Dapane and Voiage adapters
fail closed if providers are unavailable. No library migration is accepted
without installed provider evidence.

## Rationale and alternatives

The initial model is annual cohort expected resource use and uncertainty—not
patient-level event simulation. Placing it in CareOps Sim would couple a narrow
health-economic application to a generic DES engine unnecessarily. The archived
legacy CareOps Costing repository is not the canonical exact valuation engine;
Dapane has the more directly applicable nonnegative usage and quotation model.

Alternative rejected: fork/write an in-house statistical or cost kernel.
Alternative deferred: Kairos temporal DES (requires bed-level observation).
Alternative deferred: Paignia static games (not needed to evaluate one service).

## Consequences

Price, perspective, relative cost and readmission inputs must be tied to
source, unit and decision context; negative early returns are allowed in the
relative-effect model but never passed as negative resource quantities to
Dapane. Voiage financial-only draws are not QALYs. Each additional provider
must be pinned and independently qualified, and direct patient data remain private.
