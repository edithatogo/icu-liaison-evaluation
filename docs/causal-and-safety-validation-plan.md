# ICU liaison evaluation: independent empirical and causal validation plan

Status: methodological specification only. No site records analysed, no local outcome effect estimated, and no clinical/Finance/research authorisation granted. Pre-register the target estimands and data access before using restricted datasets.

## Question and interventions

**Decision:** whether incremental nurse-led discharge coordination and post-ICU ward liaison, at specified staffing and coverage, offers enough clinical/safety and health-service value compared with **actual existing practice** to justify expansion. Distinguish: (i) ICU discharge liaison, (ii) early ward follow-up, (iii) MET/rapid-response model, and (iv) NP-led expanded scope. These are not interchangeable treatments. Model actual baseline services including ICU discharge coordinator, critical-care outreach, MET and ward educators; cost only incremental FTE and activities.

**Population:** first eligible live ICU-to-ward discharge per hospitalisation for the primary episode outcome; all ICU admissions and eligible live ward/home discharges are separately required to reproduce ANZICS CCR rates. Confirm inclusion threshold (draft ≥16 years) and geographical/ward service eligibility with ICU clinical lead. Use index date at *physical ICU departure* for 72h returns and readiness date for exit-block hours. Study 12-month service costs and annual volume using at least 24 months baseline for seasonality, where sources permit.

**Primary operational estimand:** change in elapsed discharge-ready-to-physical-departure hours (continuous and ≥12h) among eligible cases with valid timestamps; missing readiness treated as unknown and audited by case mix/period. Pre-specify an intention-to-cover analysis based on service roster and a secondary realised-contact analysis, acknowledging indication bias in contact receipt.

**Clinical co-primary/safety balancing:** unplanned ICU returns strictly before 72 hours, return severity and clinical appropriateness; MET / clinical deterioration response time; ward cardiac arrest; ward/hospital death; treatment limitations; care-team workload; patient/family experience. Increased appropriate ICU returns may represent improved surveillance. Do not treat lower readmission as beneficial absent safety review.

## Design, identification and threats

Preferred if phased service introduction is feasible: prospective controlled interrupted time series, segmented event study, or stepped introduction with contemporaneous comparable wards/sites. Document pre-period trends and time of intervention; compare aggregate flow and patient-level risk-adjusted outcomes, allowing clustering by unit and calendar week. If implementation is simultaneous, use controls where contamination and treatment eligibility are understood; otherwise use interrupted time series with explicit warnings against attributing every contemporaneous change to liaison.

**Controls/covariates (pre-specified):** age, admission diagnosis and severity (ANZROD/APACHE where available), surgical/elective status, ventilation, ward, transfer origin, weekday/season/shift, staffing and occupancy, ICU strain, transport and bed-management state, clinical limitations and interhospital transfer. Avoid adjusting for variables downstream of service exposure as though they were baseline confounders. Do not use propensity matching as a substitute for exchangeability, overlap or temporal confounding.

**Negative controls and falsification:** compare pre-intervention differences and slopes, check shifts with no liaison coverage, evaluate outcomes unlikely to be affected by ward liaison, test anticipatory trends, sensitivity to exact index definition, missing data, readmission-planned adjudication, policy/ward reorganisation and competing deaths. Treat multiple hospital episodes per person with stable linkage/clustering if permitted; the public extract must not carry reidentification keys.

**Censoring:** classify early return as observed event, verified no event with adequate follow-up, unknown/incomplete, transfer or death competing before event. Follow-up across hospitals only when authorised. Use a competing-risk cumulative incidence method when death or hospital separation prevents complete observation; never equate `unknown` or death to `no readmission`. Report denominators and missingness for each endpoint rather than one universal cohort denominator.

## Validation stages

1. **Data lineage:** checksum inputs, reconcile APD/ICU and ward/hospital movements, compare locally replicated CCR numerator/denominator with CORE output. Validate midnight/DST/offset conversions, duplicate admission episodes and date completeness. Confirm extract cut-off and minimum 72-hour follow-up.
2. **Descriptive:** age/diagnosis case-mix, admissions, first eligible departures, ≥12h delay, median/p90 readiness delay, ICU occupancy with staffed-bed denominator, after-hours transfer, unplanned returns, mortality, MET, ward arrest and censoring by period and ward. Distinguish no event vs unknown.
3. **External calibration:** validate baseline P4 prior ranges on held-out *CHHHS* aggregates when approved. Keep observed local estimates separate from public ANZICS benchmarks. Fit appropriate uncertainty distributions and dependence using SciPy/NumPy, with audit trails. No plausible-looking synthetic fit counts as validation.
4. **P6 holdout:** compare paired actual ICU demand/referral, discharge and staffed-bed intervals to native Kairos traces. Hold out hospitalisations/time blocks to avoid same-person leakage, report MAE, Wasserstein/KS for admitted waits, plus overflow/refusal/censoring and capacity conservation. Queue lengths and declined demand cannot be validated from accepted admissions alone.
5. **Economic validation:** independently reconcile Dapane exact resources against internal clinical costing cost components and GL/Finance; separate fully allocated average cost, marginal avoidable cost, realisable cash budget changes and released capacity. Double-count index ICU exit-block and subsequent ICU return nowhere. Compare current and proposed service with prospective resource utilisation.
6. **Clinical safety and governance:** blinded review of representative delayed escalations and readmissions, planned rescue, ward workload, First Nations/equity and patient-experience implications. A risk-adjusted association does not independently certify clinical noninferiority, nor does an optimistic economic result authorise rollout.
7. **Uncertainty and decision:** paired PSA with prespecified empirical distributions and correlation assumptions, threshold/sensitivity and Voiage EVPI/EVPPI/EVSI when installed qualified. Present uncertainty due to unmeasured service effectiveness and structural model choices separately.

## Acceptance and approval boundary

No local clinical, Finance, patient-experience or First Nations governance approval is presently established. Classify whether each data use is routinely governed quality improvement, a clinical registry use or research requiring HREC/SSA; only authorised custodians may grant permissions. Maintain restricted extracts, source keys and records in the approved health-service environment; give this project only approved summaries or governed pseudonymised data. Assign clinical/Finance reviewers and keep dated, signed acceptance in the organisation's existing processes; no editable YAML Boolean is proof of approval.

**Go/no-go must consider clinical safety first.** Positive economic net benefit does not override a safety signal; release of ICU hours is not a realised cost reduction without an evidenced change in spending or capacity-constrained demand.
