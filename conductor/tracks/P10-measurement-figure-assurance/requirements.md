# P10 — Requirements (MoSCoW)

## Must
- **R01** One versioned metric/estimand/denominator registry with numerator, cohort, time anchors, follow-up, missingness and source references; all P9 figures/tables link by stable M-ID.
- **R02** Prevent all-live ANZICS discharges from being conflated with first eligible adult ward discharge per hospitalisation; ready-time unknowns cannot become zero delay; death/transfer/unknown 72-hour follow-up are explicit.
- **R03** Preserve distinct NWAU, resource costs, actual budget cash, usable capacity and safety units.
- **R04** Require input, renderer, model/seed, figure/output and independent-review provenance for any claim of rendered figure completion.
- **R05** Claim policy denies site/clinical/Finance/provider/investment claims unless verified by trusted external system; public JSON signatures or booleans are never enough.
- **R06** Distinguish parameter PSA, clinical-effect, structural, data-quality, operational and provider uncertainty. Label model percentiles as *not* confidence intervals.
- **R07** Visual acceptance covers mobile/tablet/desktop/A4, marks versus source, accessible SVG descriptions, contrast, greyscale, labelling and reference lines. Contract-only does not mean visually passed.
- **R08** Preserve F01–F24, T01–T07, P4/P5 scientific ownership, P7 governance boundaries, and source SHA256 inventory.

## Should
- **R09** Emit a directed source→metric→table/figure→review provenance graph for each generated output.
- **R10** Add actual rendered screenshot and independent value-to-mark QA with bounded regression tolerance.
- **R11** Add signed external-authority verification adapter only within approved CHHHS systems.
- **R12** Run distinct no-effect/harm, structural and operational uncertainty sensitivity scenarios.

## Could
- **R13** Publish searchable evidence lineage per figure and stakeholder audience.
- **R14** Implement validity dates, revocation and drift notifications for approvals, MCHS weights and Queensland employment rates.

## Won't in this source-only phase
No patient-level data ingestion, signing keys, real approvals or substitute Dapane/Voiage/Kairos/MCHS engines.

## Additional Must: safety-constrained decision
- **R15** Any positive economic value must remain non-decisive if clinical safety outcomes, acceptable harm thresholds, risk adjustment, ascertainment or independent clinical and Finance signoff are unqualified. Synthetic analyses cannot prove noninferiority.

## Additional source-validity control
- **R16** Evidence must carry an effective period, exclusive expiry, pricing/coding year, revocation state and source identifiers before use. These fields are not proof of authentication. A public metadata record always remains unverified without a trusted external verifier.

## Additional falsification requirement
- **R17** A synthetic economic demonstration must pass explicit null-effect, harmful-effect, non-addressable-delay, non-usable-capacity, non-cash-realisable and mispaired/invalid-effect negative cases. Preserve distinct physical, resource, cash and clinical-safety meanings.
