# P2 specification — model meaning before numerical extension

Goal: a reusable, machine-checkable, local-source-free clinical and economic
specification for the CHHHS adult ICU-to-ward liaison service decision, with
explicit comparator, estimation unit, index and return timing, reporting
outcomes, economic valuation boundary, mandatory safety and equity balance,
missing-data/censoring handling, and a substantive evidence-to-application gate.

Outputs:

- Version 1 JSON protocol and Pydantic runtime validation, separate from P1
  assumptions so the same code can be reconfigured after governance review.
- Reference endpoint classifier for synthetic transitions only; exact 12h
  exit-block and [0,72)h unplanned return, time zone, completeness and death.
- Nonoverlapping Dapane-ready cost semantics (index delay; post-ICU returns;
  incremental liaison operations), distinct physical and financial value.
- Versioned local-source requirements with grain/owner/missingness, no data.
- Admission CLI and tests that reject false clinical/budget authority and
  contradictory definitions, record stable version/provenance and return
  nonzero when local-readiness is demanded.
- Run the P2.5 field-crosswalk and sign-off audits from the admission CLI
  against the same versioned sources. A form's declared decisions and
  matching hashes leave site authority and readiness unverified.
- Prespecified potential observational study and safety constraints, no
  invented numeric margins, staffing or local effects, and transparent
  outstanding evidence and HREC/data governance gates.

Out of scope: data extraction, patient-level linkage, clinical risk prediction,
causal effect estimation, patient-level survival analysis, Dapane/Voiage
installed qualification, new statistical libraries, implementation decisions,
hospital spending commitments, GitHub repo creation and Kairos DES.

Dependencies: P0 portable architecture and P1 source contract. Installed native
provider runs are independent P1.4 gates, not prerequisites for pure P2
clinical definition tests. Clinical/Finance approvals and real local records
are prerequisites for P3/P4 empirical claims.
