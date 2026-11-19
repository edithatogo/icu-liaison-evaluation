# P2 clinical and economic evaluation protocol — unapproved draft v1

**Study decision:** whether the *incremental* establishment, expansion, or
reconfiguration of an inpatient ICU liaison nurse service at Cairns and
Hinterland HHS is clinically acceptable and economically worthwhile relative
to **actual existing services**. This is a prospective decision model and
candidate evaluation protocol, **not** an approved CHHHS model of care,
intervention effect estimate, clinical trial registration or financial proposal.

## 1. Population, estimands and the comparator

The intended initial evaluation is the adult ICU-to-ward transition at **Cairns
Hospital**, with the geographic reach and remote/interhospital review model to
be confirmed. The working analytical adult age threshold is **16 years**, to
be reconciled against CHHHS activity classification and the actual service
eligibility; it is not an assertion that every 16-year-old is admitted to an
adult ICU.

The **analytic unit** for primary clinical rates and process outcomes is the
**first eligible live discharge from an index ICU stay to an eligible ward,
per continuous hospitalisation**. ICU deaths, direct-to-home departures,
ICU-to-ICU transfers, and out-of-network transfers without observation are
not eligible for that primary index-discharge cohort. Other subsequent ICU
admissions must still be linked for return outcomes and all relevant resource
use; avoid selecting only hospitalisations with subsequent 72-hour survival.

The counterfactual is the **observed pre-existing care configuration**:
ICU medical/ward handover, current liaison activity (if any), existing MET,
advanced practice, outreach and receiving-ward nursing support. Do not assume
that present liaison coverage is zero. The intervention is the separately
costed *incremental* package of coordinated discharge planning, structured
handover, risk-targeted post-discharge reviews, ward support, escalation and
education. Actual hours, FTE, eligible wards, after-hours operation, patients
per contact, and overlapping staff activities require local source verification.

The package is not equivalent to 24-hour NP-led MET response or outpatient
post-ICU recovery clinics: those would be different comparator strategies.
Implementation reach, timing, safety and degree of displacement of existing
work must be described before a causal attribution is defensible.

### Primary decision estimands

- Annual **incremental CHHHS resource cost** (or saving) comparing current
  against proposed service, with uncertainty and measured harms visible.
- **Difference in total index discharge-ready ICU hours** per eligible index
  transition and annually; delay cause and ward-offset cost separated.
- **Difference in unplanned 72-hour ICU return risk**, interpreted jointly
  with mortality, severity, ward arrest, goals of care and quality of rescue.

A confirmatory causal analysis, co-primary-testing strategy, safety margins
and statistical power are **not** approved by this draft. Cost and clinical
outcomes must not be collapsed into a cost-effectiveness ratio without a
justified common effectiveness measure and the corresponding evidence.

## 2. Endpoint clocks, denominators and missingness

The versioned canonical definitions are in
[`model-inputs/clinical-economic-protocol.json`](../model-inputs/clinical-economic-protocol.json).
`icu_liaison.endpoints.classify_transition` gives executable single-case
reference behaviour for synthetic test cases only; P3 owns the hospital-level
episode linker and measurement completeness evaluation.

| Endpoint | Clock / event rule | Denominator | Treatment of missingness |
| --- | --- | --- | --- |
| Discharge-ready delay | Clinically ready for ward departure → actual physical ICU departure; elapsed hours, no imputation | Eligible first live ward ICU discharge episodes | Unknown without both timestamps, with completeness reported |
| Exit block | Duration **>=12 hours** | Same local eligible first-discharge cohort | Unknown if readiness time missing; cannot impute zero |
| Unplanned early return | **Any** unplanned ICU readmission within `[0,72)` hours after **physical** departure, including repeat returns; all episodes linked within hospitalisation | Eligible first live ward ICU discharge episodes | Return planned status unknown or incomplete surveillance ⇒ unknown, not no return |
| After-hours transfer | Actual physical departure with Australia/Brisbane local time from 18:00 through 05:59:59 | Eligible first live ward ICU discharge episodes | Physical departure time required |
| Death after live ICU departure | Death between the index transfer and final inpatient separation, with goals-of-care review | Eligible index cohort | Competing events, missing final outcomes, transfer loss separately coded |
| Ward cardiac arrest / escalation | Ward event records after physical departure; distinguish recognition and response | Eligible index cohort / event denominator reported separately | Unknown incident capture ≠ no event |
| Severity on readmission | Actual severity/organ support and independent appropriateness review | Observed ICU return events | Requires instrument, outcome completeness and reviewer protocol |
| Ward workload / experience | Additional ward staff work and patient/family transition experience | Eligible index cohort | Missing and not-applicable explicitly separated |

**Published ANZICS measures must remain distinct:** the CCR delayed-discharge
rate uses *all live ward/home discharges*; the CCR 4.5% readmission measure
concerns return admission **episodes** over all ICU/HDU admissions; the CORE
APD adult 4.0% readmission measure concerns **patients** surviving a first ICU
admission. None is an observed CHHHS 72-hour **unplanned** ward-return rate.
The pooled CCR **20.4% >=12-hour** delay rate is an external comparison proxy,
not a local rate or automatically valid as this narrower first-index ward cohort.

The synthetic endpoint reference deliberately excludes an event exactly
at 72h; non-complete 72h surveillance is right-censored. Death before
completion is a competing event, not an observed zero risk. A later method
should estimate cumulative incidence or a suitable adjusted contrast with
censoring/competing-risk handling. This Boolean classifier alone is **not**
a survival model, and the early-return numerator must be interpreted
alongside case mix and rescue outcomes.

## 3. Economic decision model and resource boundaries

**Primary analysis:** CHHHS provider cost-consequence, annual programme
horizon of 12 months, annualised volume, resource consequences from index
transfers through final inpatient separation. **Secondary:** a separately
constructed CHHHS budget-impact account showing **actual expenditure** by
financial year. Currency AUD; synthetic fixture reference price year 2026,
which must be updated as the local quotation year becomes available.
Neither the model nor a 12-month programme horizon justifies a long-run QALY
or whole-of-government net-present-value claim. A longer horizon, discount
rate, inflation/repricing and any post-discharge follow-up tail require a new
approved specification. For the present within-year scenario, discounting is
not applied.

The three explicitly **nonoverlapping cost segments** are:

1. **Index discharge-ready ICU interval:** marginal ICU resources incurred
   while the transfer-ready patient remains in ICU, *minus the additional
   ward care incurred following earlier transfer*. These quantities belong
   only to index readiness → departure and do not price the return episode.
2. **Post-departure ICU returns:** the **incremental** resource cost of a
   return episode relative to care that would otherwise have been provided;
   exclude previously valued index-delay hours and routine ward care not
   attributable to the return. More appropriate returns may increase costs.
3. **Incremental liaison service:** added staff time, loading, on-costs,
   leave/backfill, training, supervision, premises/equipment and operating
   costs **net of verifiable displaced existing work**. Do not set a new
   programme's FTE to the total existing ICU/outreach workforce.

Dapane is the preferred engine for **actual resource-use and quotation
valuation** under its exact contract; this project owns which physical
resources are used and how they map to counterfactual segments, not a
second costing kernel. Historical average expenditure per available ICU
bed is **not** an avoidable marginal price. The P1 simplified input
`net_avoidable_cost_per_icu_day_aud` is strictly an *economic resource*
value, not demonstrably a reduction in cash expenditure. Cost-effectiveness
and budget-impact outputs must remain separate; avoid counting a bed-day
both in a readmission cost and an exit-block cost.

**Capacity** is reported as released *hours*, with shift and demand timing
unmeasured. The additional ability to accept admissions, reduce cancellations,
or avoid transfers is a possible nonfinancial benefit; it becomes a monetary
opportunity-cost benefit only with demonstrated constrained demand, a credible
counterfactual and no double counting of costs/funding. Annualised fractional
bed-days do not imply continuously staffed ICU beds can be closed or redeployed.

A further P4 model may incorporate ward total stay, transfers, after-hours
risks, utility and nonhospital consequences, each with a distinct, evidence
supported resource counterfactual. Those benefits are **excluded now**, not
silently set to zero in a definitive analysis.

## 4. Safety, equity and evaluation design

Mandatory balancing signals: unexpected post-ICU death, ward arrests, delayed
escalation, return severity and appropriateness, treatment goals, and ward
staff workload. Record both positive and adverse pathways. A safety claim
cannot be made solely from the early ICU return percentage, and no numerical
noninferiority margin is supplied or approved here.

Consider differential access and impact for rural and remote patients,
Aboriginal and Torres Strait Islander patients under locally agreed data
sovereignty/governance, patients requiring interpreters, high-complexity cases
and transfers. Do not assume these groups are available or sufficiently sized
for disclosure-safe subgroup estimation.

**Candidate study design:** preferably a controlled interrupted time series
or an agreed phased implementation; indicative 24-month baseline and
12-month observation after commencement if feasible. This is not an approved
sample size or statistical plan. Prespecify: case mix, seasonal demand, ICU
staffed capacity, receiving ward staffing/bed availability, concurrent MET
changes, and changes in admission/discharge policy. Check data completeness,
parallel trends (where applicable), autocorrelation, censoring, potential
selection on discharge timing and unmeasured confounding. Use a prespecified
analysis plan and local governance/ethics determination. No HREC exemption,
research authority, data access or hospital model-of-care endorsement is
asserted by this project.

## 5. Admissions and evidence required before site claims

`.venv/bin/python -m icu_liaison.protocol_cli` checks that the proposed protocol,
source-tagged P1 illustrative parameters and variable requirements agree.
It deliberately reports **ADMITTED_ILLUSTRATIVE_ONLY** and refuses
`--require-local-ready` until a future version has qualified local data,
observational design, patient safety, funding and provider execution.

**Local owner-supplied prerequisites:** eligible adult discharges; fidelity
and historic completeness of readiness and actual-departure times;
planned/unplanned readmissions and follow-up censoring; hospital outcomes;
ward and ICU resource use and cost; liaison rostering and current service;
financially realisable expenditure changes; relevant demand/capacity;
consultation with clinicians, ward staff and affected communities. All
patient-level extracts and identifiable/privileged evidence remain outside
this portable archive and Git public branches.

## References and methodological boundaries

- [ANZICS APD registry](https://www.anzics.org/advocacy/core-icu-registries/registry-datasets/adult-patient-database/) and
  [APD Dictionary version 7](https://www.anzics.org/public/311/files/PDFs/CORE/ANZICS-APD-Data-Dictionary-Version-7.pdf).
- [ANZICS CCR 2024/25](https://www.anzics.org/public/311/files/PDFs/CORE/2024_2025-CCR-Activity-Report.pdf) and
  [ANZICS CORE 2024](https://www.anzics.org/public/311/files/PDFs/CORE/2024-CORE-Report.pdf).
- [CHEERS 2022 reporting guidance](https://www.ispor.org/heor-resources/good-practices/cheers) describes transparent population, perspectives, comparators, outcomes, valuation, currency and uncertainty reporting. **It is not a methodological-quality score or approval.**
- [ISPOR 2014 budget impact good practice](https://www.ispor.org/heor-resources/good-practices) emphasises perspective-specific population and spending. The budget-impact branch is not calculated by the P1 resource PSA.

Source summaries are selective references, not redistributed original reports
or a substitute for local authorisation. All named service specifications and
thresholds remain reviewable against the versioned JSON inputs.
