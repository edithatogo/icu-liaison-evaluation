# P8 implementation sequence and independent acceptance

## P8.0 — Source and ownership reconciliation (source-only)

- [x] P8.0.1 Inspect live provider repository heads, primary contracts, existing
  Conductor tracks and explicit ownership; freeze the inspected refs in
  `model-inputs/p8/provider-capabilities.json`.
- [x] P8.0.2 Distinguish ABF activity, marginal resource cost, workforce cost,
  possible budget savings and capacity in a dedicated P8 crosswalk and ADR.

## P8.1 — Contract and risk design (source-only)

- [x] P8.1.1 Establish a synthetic-only separated ledgers schema and null-value
  fixture; no policy or source amount invented.
- [x] P8.1.2 Add negative controls rejecting direct NWAU-to-revenue, wrong
  currency/valuation basis, unqualified nursing rates and premature approval.

## P8.2 — MCHS annual paired acute episode consumer (source adapter implemented; installed parity pending)

- [x] P8.2.0 Implement a synthetic-only single-episode counterfactual consumer that calls existing annual `calculate_acute` twice, holds every non-ICU-hour column fixed, rejects wrong annual output labels/errors, and never converts NWAU into revenue. Source-level tests only.

- [ ] P8.2.1 Record pricing-year, AR-DRG/coding edition and hospital episode
  identity, ICU-eligible hours, whole-stay LOS, patient and establishment
  eligibility, HAC/AHR adjustments; freeze complete current-care and intervention
  input vectors without inventing DRG/LOS changes.
- [ ] P8.2.2 Call *existing* `nwau_py` supported annual calculator twice on
  identical cases other than an explicit admitted counterfactual, compare NWAU
  and separate technically modelled AUD; reject unsupported 2026–27 paths until
  official calculator parity is proven. Preserve official SAS/Excel golden outputs.
- [ ] P8.2.3 Keep actual CHHHS funding/revenue `unknown` until local ABF/Finance
  authorises applicable contract and realised-allocation interpretation.

## P8.3 — Queensland nursing roster and wage consumer (source adapter implemented; award qualification pending)

- [x] P8.3.0 Implement the thin, exact-decimal synthetic roster segment -> `QuoteQuantity` -> existing workforce `build_dapane_request` consumer, with component/overlap/source/price-year and request-integrity guards. Synthetic source tests only.

- [ ] P8.3.1 Confirm nursing award/enterprise agreement, position grade, band,
  pay point, coverage hours, skill mix, effective/knowledge dates, employer
  conditions and salary components; do not reuse the HP3 health-practitioner
  wage example as a Clinical Nurse rate.
- [ ] P8.3.2 Map rostered productive and paid exposure, superannuation,
  allowances/penalties, leave relief, backfill and training in the existing
  workforce `UnitQuoteRelease`/conditions-costing interfaces; preserve unique
  component IDs and adverse/out-of-hours cases.
- [ ] P8.3.3 Reconcile nominal and uncertainty-based staff cost through Dapane,
  independently match payroll/HR source and avoid salary-oncost duplication.

## P8.4 — Provider-aware economic shadow composition (source-side partial; native valuation pending)

- [x] P8.4.0 Add a synthetic-only, typed sidecar that binds source-level MCHS
  paired NWAU and workforce/Dapane financial-cost requests to an existing
  proposed P4 strategy without changing P4 draws or multiplying a case-level
  NWAU change into a programme or cash result. Reject duplicate, unsigned,
  inconsistent, misclassified or promoted provider outputs. Publish a JSON
  Schema, small synthetic fixtures, CLI and reproducibility/negative tests.
  This **does not** perform Dapane valuation or Voiage EVPI.


- [ ] P8.4.1 Preserve separate economic/financial/funding runs and exact resource
  quantities in Dapane. Do not treat MCHS NWAU or an inpatient tariff as extra
  physical resources; no negative usage for cost offsets.
- [ ] P8.4.2 Inject source-bound annual staffing cost, resource benefit and
  modelled funding shadow as distinct typed fields into P4/P5. Voiage consumes
  explicitly selected strategy/perspective draws; no automatic revenue addition.

## P8.5 — Native, independent and clinical gates (pending)

- [ ] P8.5.1 Execute installed MCHS 2024–25/2025–26 parity fixtures, current-year
  qualification where supported, workforce full-roster cases, Dapane and Voiage
  native consumers; record SHA/lock/host and independent numeric results.
- [ ] P8.5.2 Receive authorised CHHHS linkable hospitalisation and costing data,
  approved nursing classification/roster/leave cover and funding mechanism.
  Verify direct resource costs, incremental budgets and activity shadows
  independently, including negative effect and double-counting oracles.
- [ ] P8.5.3 Obtain clinical/Finance/data-governance and equity review and
  integrate in the *user-supplied* dedicated repository with hosted CI. Only
  then consider intervention effect and financial approval.

P8.0–P8.1 and the narrow source-adapter subincrements P8.2.0/P8.3.0 are implemented. Annual official-calculator parity, real nursing source/roster qualification, native providers and CHHHS acceptance are **not accepted**.
Existing provider owners retain their code and their historical track IDs.
