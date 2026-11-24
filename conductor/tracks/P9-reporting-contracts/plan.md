# P9 acceptance plan

- [x] P9.1 Two Clinical Director tables with separate all-live-discharge and first eligible adult discharge denominators, referencing the field-level source.
- [x] P9.2 Machine-readable table/figure catalogues with stable IDs, source, granularity, denominator, uncertainty, privacy and accessibility.
- [x] P9.3 Contract validation and negative tests; independent P5 report reader remains numerical oracle.
- [x] P9.3b Execute contract validation against an actual P5 synthetic report and reject unregistered files in CI, without promoting placeholders or local clinical claims.
- [x] P9.3c Enforce versioned Draft 2020-12 reporting catalogue schema with deny-unknown-fields, safe output paths, placeholders, metadata and privacy classes; preserve the P5 numeric review.
- [x] P9.3d Embed registered synthetic accessibility description as SVG metadata and reject independently rehashed figures with mismatched descriptions; no changes to P4 numeric outputs.
- [x] P9.3e Reconcile six previously generated synthetic graphics with the reporting programme, distinguishing first-class P5 SVG from five external exploratory PNGs.
- [x] P9.3f Expand figure contract with decision question, estimand, evidence tier, denominator, paired semantics, sources, uncertainty, privacy, acceptance gates and accessibility.
- [x] P9.4 Implement the six priority synthetic figures (F02/F10/F11/F15/F20/F24) with source rows and data-mark checks.
- [x] P9.4b Qualify exploratory F05-F09 assets by rerendering from pinned source outputs, never by copying or falsely marking as in-repo.
- [ ] P9.4c Produce empirical and native-provider figures only after data/assurance admission.
- [x] P9.4d Generate a companion HTML index with accessible SVGs, source CSVs, seeded provenance and independent numerical reconciliation.
- [x] P9.4e Check the reporting catalogue against a verified P11 run. Report
  table and figure paths and hashes, figure source and review evidence, and
  pending evidence. Bind supported IDs to their actual artifacts and reject
  relabelled or invented outputs.
  [Run coverage receipt](../../../verification/p9-run-coverage-2026-11-24.json)
- [ ] P9.5 Independent clinical, statistical, Finance and relevant First Nations governance acceptance.

- [x] P9.3g Link all seven table and 24 figure contracts to P10 metric/denominator IDs and uncertainty classes.
- [x] P9.3h Enforce source-only P10 claim and provenance checks; retain separate per-artifact visual evidence.
- [x] P9.6 Record four-profile visual review and source-mark evidence for F01 and all 13 baseline P9 figures. The ten evidence-dependent figures have their own review scope.

The [24 November contract review](../../../verification/p10-p11-contract-review-2026-11-24.json)
records the previous six-scenario production check and four-profile baseline
review. The [20 November verification](../../../verification/p9-synthetic-figures-2026-11-20.json)
records the earlier figure bundle.

T05 requires the approved nursing classification and full roster reconciliation.
T06 requires verified annual calculator parity and admitted episodes. T07
requires linked outcome data and clinical safety review. F12 requires method
verification for the information-value curves. The remaining figure evidence
requirements are in the catalogue, and P9.5 retains its site acceptance gates.
