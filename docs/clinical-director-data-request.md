# Cairns Hospital ICU liaison: Clinical Director data request

**Period:** 1 July 2024 to 30 June 2026, or the latest 24 complete months. **Purpose:** baseline discharge performance, patient safety, capacity, workforce and economic evaluation. Begin with monthly aggregates/ANZICS CORE. Patient-level linked extracts require separately approved CHHHS processing.

## Table 1. Datasets

| Dataset | Required content | Suggested custodian |
|---|---|---|
| ICU activity and case mix | Admissions, live discharges, destination, severity and ICU LOS | ICU / ANZICS CORE |
| Discharge delays | Clinical readiness, actual departure, exit block and reason for delay | ICU / Patient Flow |
| Returns and outcomes | Planned/unplanned ICU returns, death, transfers, 72-hour follow-up | ICU / Clinical Information |
| Ward flow | Referral, acceptance, bed ready, transport and physical transfer | Patient Flow / Bed Management |
| ICU capacity and demand | Staffed/open/occupied/physical beds, admission requests, refusals and delays | ICU / Bed Management |
| Liaison and outreach | Current FTE, hours, contacts, follow-up, MET/outreach arrangements | ICU Nursing |
| Clinical safety | MET calls, ward arrests, escalations, mortality, appropriateness of ICU return | Clinical Governance |
| Nursing workforce/cost | Existing/proposed grade, pay point, FTE, shift coverage, on-costs and backfill | Workforce / Finance |
| Patient-level costs | ICU, ward, readmission and marginal versus allocated costs | Clinical Costing / Finance |
| ABF and coding | AR-DRG/edition, hospital LOS, eligible ICU hours, NWAU and pricing year | Coding / ABF / Finance |
| Implementation and equity | Rollout/control periods, governed experience and equity outcomes | ICU / Consumer / First Nations governance |

## Table 2. Specific inputs and KPIs

| Input / KPI | Definition | Preferred reporting |
|---|---|---|
| ICU admissions | All episodes, distinguishing first and subsequent admissions | Monthly count |
| Eligible discharges | **Separately:** all live ward/home discharges for ANZICS, and first eligible adult ward discharge per hospitalisation for the study | Monthly count/denominator |
| ICU length of stay | Admission to physical departure | Mean, median, IQR, P90 |
| Discharge-ready delay | Clinically ready to actual physical departure; retain unknown readiness | Median, P90, total hours and missing |
| Exit block ≥12 hours | ≥12-hour delay among live ward/home discharges with valid ready timestamp | Number, percentage, observed denominator |
| After-hours discharge | 18:00-05:59 live ICU discharge | Number and percentage |
| Delay causes | Ward bed, staffing, transport, clinical, administration, unknown | Count and percentage |
| Unplanned 72-hour ICU return | First eligible ward discharge to unplanned return within 72 hours | Number, denominator, unknown, competing death |
| All-episode readmission | Repeat ICU/HDU episodes in the same hospitalisation, not 72-hour unplanned return | Number and percentage |
| Staffed beds and occupancy | Physical/open/staffed/occupied beds by contemporaneous interval | Shift/daily, monthly occupancy |
| Admission demand | ICU admission requests, delays, refusals and diversions | Count, median/P90 waiting time |
| Ward transfer intervals | Referral, accepted, bed ready and physical transfer | Median and P90 |
| MET after ICU discharge | MET within 24 and 72 hours | Per 100 eligible discharges |
| Clinical safety | Arrest, death, escalation time, return appropriateness/severity | Count, rate, timing |
| Existing liaison service | FTE, roster, patient contacts, contact time | FTE, weekly hours, monthly contacts |
| Proposed liaison cost | Grade/pay, incremental FTE, productive/paid hours, penalties, relief, setup | Annual AUD and price year |
| ICU/ward unit cost | Allocated average vs marginal avoidable resource cost | AUD per hour/day |
| Return ICU cost | Incremental cost following return, no overlap with index cost | AUD per event |
| ABF inputs | DRG/edition, whole-stay LOS, eligible ICU hours, NWAU | Episode/group and year |
| Clinical case mix | Age, diagnosis, severity, ventilation, elective status | Monthly distribution |

**Governance and data quality:** State source, numerator, denominator, exclusions and missingness. An unknown return status is not a negative event; death/transfer may compete or censor observation. NWAU, capacity released and realised cash are not interchangeable. No patient-identifiable or confidential payroll data may be placed in this repository.

[Authoritative 115-field CHHHS request](../model-inputs/chhhs-data-request.json). All unavailable local evidence remains explicitly unresolved.
