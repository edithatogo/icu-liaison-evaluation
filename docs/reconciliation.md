# Reconciled source and methodological decisions

## Starting evidence and measure definitions

The preserved Library workbook (SHA in the migration manifest) contains public
reference measures and a deliberately blank CHHHS input section. It does not
contain an observed Cairns early readmission effect, local avoidable daily cost,
local 72-hour readmission rate, annual eligible discharges, or priced staffing.
It should not be copied into public source repositories without review.

CCR 2024/25 pooled all-age discharge delay of >=12h: 20.4%. This requires
live ward/home discharges as denominator, and provides a reference count of
204 flagged cases per 1,000 such discharges; 102 bed-days is a *lower bound*
on flagged delay, not reducible hours. The CCR 4.5% is a return **episode**
measure over total ICU/HDU admissions; the CORE/APD adult 4.0% is readmitted
**patients** relative to eligible first ICU survivors. Neither is the desired
locally-defined *unplanned within 72h* readmission rate. These populations
must be kept distinct in validation and any reported figures.

The user-selected economic question is marginal value of a specified **new or
expanded ICU liaison service** compared with actual current practice. Do not
conflate post-ICU follow-up, advanced nurse practitioner MET response and
outpatient ICU recovery follow-up. Report incremental hospital resources,
capacity released, costs, and post-ICU clinical safety separately.

## Distinguish economic mechanisms

- Discharge-ready ICU hours released may produce capacity, not cash.
- Ward labour and resources may be displaced into an earlier transfer.
- Early appropriate ICU return might rise when deterioration is recognised.
- Avoided return costs are **incremental** compared with care otherwise
  received, excluding index ICU delay already valued.
- A formally cost-saving result is not required for a cost-effective clinical
  service: outcomes and patient preferences must ultimately be assessed.
- Valuation perspective, currency, price year and discounting are separate
  contracts. In the current one-year illustrative pilot, no discounting applies.
- Dapane prices observed/derived resources; Voiage evaluates decision uncertainty;
  neither supplies a causal estimate of the liaison effect.

## Data-quality and causal evaluation prerequisites

Obtain approved CHHHS cohort counts, ADP readiness / discharge timestamps,
ward movement linkage, review coverage and after-hours shifts, delay reasons,
current MET and ICU staffing, 72-hour unplanned returns, level/severity of
return, ward arrests/deaths, appropriate escalation, direct/allocated costs,
ward costs, vacant staffed ICU beds and capacity-constrained admissions.

Prospectively plan a case-mix-adjusted controlled interrupted time series,
stepped implementation or another suitably identified comparison if feasible.
Use pre-specified safety and opportunity-cost outcomes, not readmission rate
as a standalone efficacy surrogate. Preserve human governance of actual care.

## Prioritised migration acceptance

1. Source integrity: match original ANZICS report values/denominators,
   workbook SHA and source PR head; no unpublished/PHI material.
2. Reproducible model: tests fail on missing provenance, invalid units,
   no-effect and adverse readmission assumptions; compare central deterministic
   identity to the original illustrative calculation.
3. Independent providers: validate Dapane request against its exact published
   JSON Schema and installed kernel, then prove Voiage EVPI on a specified
   financial-only decision surface in Python >=3.15.2.
4. After destination repo is known: create true Conductor gitlink at reviewed
   SHA, code owner rules, CI integration and private data boundaries.
5. Only then close exploratory PR #215 with migration reference; do not merge
   duplicated modelling into CareOps Sim.
