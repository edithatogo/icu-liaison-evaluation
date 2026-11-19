# Pre-registration and service fidelity draft

The [draft contract](preregistration.json) and [schema](preregistration.schema.json) define the intervention, actual current-care comparator, intention-to-cover primary exposure, realised-contact secondary analysis, candidate controlled interrupted time-series design, case mix and negative controls.

The contract identifies an **unresolved estimand gap**: the intended primary local discharge-delay population is the first eligible adult ward discharge per hospitalisation (D03); the existing M05 descriptive measure uses the all-live, readiness-valid denominator (D04). Do not silently treat these as the same estimand. A D03 readiness-valid metric and field completeness crosswalk must be versioned before any site analysis is locked.

Run `python tools/validate_preregistration.py`. Source-only checks cannot register a study, validate a causal effect, approve a clinical intervention or authorise patient-data extraction. All sensitive dates, rosters and actual contacts remain null.
