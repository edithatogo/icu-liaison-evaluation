# Pre-registration and service fidelity draft

The [draft contract](preregistration.json) and [schema](preregistration.schema.json) define the intervention, actual current-care comparator, intention-to-cover primary exposure, realised-contact secondary analysis, candidate controlled interrupted time-series design, case mix and negative controls.

M31 measures the mean hours from clinical readiness to physical departure on
the first eligible adult ICU-to-ward discharge per hospitalisation. D14 is
the readiness-valid subset of D03. The adapter selects the index first, reports
missing readiness among all eligible indices and returns a null mean when none
have valid times. M05 retains D04 for the all-live-discharge description. The
contract links eligibility and timing fields to the P2 source crosswalk.

Run `.venv/bin/python -m tools.validate_preregistration`. Source-only checks cannot register a study, validate a causal effect, approve a clinical intervention or authorise patient-data extraction. All sensitive dates, rosters and actual contacts remain null.
