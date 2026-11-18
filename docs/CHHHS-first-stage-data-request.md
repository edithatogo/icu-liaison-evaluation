# CHHHS ICU liaison — first-stage data request (18 November 2026)

**Decision:** assess whether an incremental ICU liaison nurse service improves ICU discharge, ward rescue and cost/resource outcomes relative to actual existing services. **Status:** no observed local data in the model; this is a proposed extraction specification, not authority to access data or a request to transfer patient data to ChatGPT.

## Initial request — 24 months of complete baseline data

**Window:** 1 July 2024 to 30 June 2026, or the most recent 24 complete months with full 72-hour follow-up. Specify extract date, timezone, source version and completeness by month. Start with a **governed aggregate feasibility report**; move to approved pseudonymised episode linkage only when the custodian, Privacy and clinical governance approve.

| Priority | Ask and owner to approach | Minimum result | Why it matters |
| --- | --- | --- | --- |
| 1 | ICU Director / ANZICS CORE submitting site lead / hospital clinical information | Monthly counts of all ICU episodes and live ICU-to-ward/home discharges, separately first adult eligible ward discharge per hospitalisation; clinical-ready and physical-departure times; destination; missingness; >=12h exit block | Estimate the real denominator and quantify how many ICU hours are delayed |
| 2 | ICU/Health Information and hospital data analytics | Linked same-hospital admission and 72h unplanned ICU return, planned-vs-unplanned, death/transfer/separation and follow-up completeness | Avoid confusing CCR all-episode returns with early unplanned returns; preserve competing death |
| 3 | ICU NUM / Nursing Workforce / Performance | Staffed ICU beds per shift or hour, physical/open beds, occupied beds, existing liaison/transition nurse hours and MET coverage | Estimate demand/capacity and the *incremental* staffing requirement |
| 4 | Patient Flow/Bed Management / receiving wards | Ward bed requested, accepted, assigned, ready and patient physically transferred; coded reasons for delay and preventability/amenability | Identify delay causes the liaison service could actually influence |
| 5 | Clinical Costing / Finance business partner | Fully loaded current/proposed staffing cost, patient-level ICU and ward resource-cost components, readmission cost, and estimates of marginal avoidable versus allocated average expense; AUD price year | Prevent unsupported claims of cash savings from released bed-days |
| 6 | Clinical Governance / MET / ICU/ward morbidity meetings | Ward arrests, MET activations, escalation intervals, deaths, early return severity/appropriateness, treatment limitations and ward burden | Ensure better recognition and rescue is not mislabelled as service harm |

**Second-stage validation request:** all ICU admission requests including delayed/declined/redirected cases, elective theatre cancellations and ED critical-care boarding; detailed shift-level nursing skill-mix and ward staffing; service-rollout schedule and changes to practice; approved patient/family outcomes and equity analyses. Data access, small-cell disclosure controls and Aboriginal and Torres Strait Islander data-governance requirements need relevant approval.

## Minimum metadata with every dataset

- Custodian, source system and codebook, data refresh/extraction timestamp, timezone, revision and versioned data dictionary.
- Stable pseudonymised hospitalisation/ICU episode keys **inside approved CHHHS infrastructure**; never names, full DOB, MRN/UR number, addresses or staff identifiers in this portable package.
- Numerator/denominator counts, unknowns, duplicates, ward destination exclusions, timestamp missingness, 72-hour right-censoring and death/transfer status.
- Proposed rostered FTE, coverage hours, award classification, penalties, on-costs, relief/backfill, training/implementation and *existing* comparator staffing.
- Price year and unit basis of every economic quotation; actual direct expenditure changes distinguished from merely released capacity and from ABF/funding transfers.
- Signed scope decision for source use (quality activity, registry use or research), clinical reviewer and Finance reviewer identities recorded in existing organisational systems.

**Initial decision threshold for extraction:** first reconcile monthly aggregate CCR-style exit-block, eligible index cohort, discharge timestamp completeness and 72-hour readmission ascertainment. Do not calibrate the P4 service effect, ready-to-transfer hours or marginal costs until these have passed quality review. A 12-hour threshold is an indicator of *frequency*, not the hours saved by a liaison nurse.

The complete field-level specification is machine-readable at `model-inputs/chhhs-data-request.json` and rendered in `CHHHS_ICU_Liaison_Data_Extraction_Request.md` and `CHHHS_ICU_Liaison_Fields.csv`.
