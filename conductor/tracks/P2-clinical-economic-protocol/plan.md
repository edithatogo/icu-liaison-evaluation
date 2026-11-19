# P2 implementation and acceptance plan

## P2.1 — Clinical scope and causal comparators
- [x] Preserve the first eligible live adult ICU-to-ward discharge within a
  continuous hospitalisation as the local denominator, with exact exclusions
  and subsequent return episodes retained for outcomes and cost.
- [x] Specify observed current care separately from proposed incremental
  liaison nursing without inventing existing service hours/FTE.
- [x] Record the target decision, draft approval status, prespecified
  confounders, proposed observational design and equity domains.

## P2.2 — Independent endpoint and safety contracts
- [x] Define primary/process/secondary/safety outcomes, time anchors and
  denominators, including explicit CCR/APD incompatibility with unplanned 72h.
- [x] Implement synthetic endpoint reference for exact >=12h, [0,72h),
  Australia/Brisbane after-hours, planned status, incomplete follow-up and death.
- [x] Fail closed on missing safety outcomes or unapproved numeric margins.

## P2.3 — Economic and data boundaries
- [x] Specify 12-month CHHHS provider resource and separate financial
  perspectives, currency/price year and unapproved longer-run horizons.
- [x] Enforce distinct index, return and additional staffing segments;
  distinguish economic resource value, actual cash expenditure and capacity.
- [x] Produce a 32-field source/grain/completeness dictionary; no local
  patient or financial data are copied.

## P2.4 — Verification and handoff
- [x] Write regression cases before implementation and prove the failing
  interface, then make focused and entire existing suite pass.
- [x] Add P2 protocol admission CLI; preserve source and candidate findings
  in a machine-readable report and portable package.
- [x] Reconcile Conductor track register/ADR and record provider and
  clinical-data blockers without changing P1 acceptance status.

## P2.5 — Required external gates (not complete)
*Preparation artifacts ready for stakeholder review (`docs/p2-stakeholder-review-pack.md`,
`model-inputs/p2-chhhs-field-crosswalk.json`, `model-inputs/p2-governance-signoff-TEMPLATE.json`,
`verification/p2-governance-crosswalk-2026-11-19.json`); external CHHHS sign-offs remain open.*
- [ ] Obtain Clinical/ICU/Nursing/Finance and appropriate consumer/stakeholder
  review of eligibility, comparator, realistic staffing, outcomes and costing.
- [ ] Approve analytic design, safety margins and minimum acceptable data
  quality; determine governance/ethics authority and secure CHHHS data route.
- [ ] Qualify local timestamps, returns, costs and actual intervention effect;
  complete P1.4 provider runtime and future P3/P4 validation before investment
  claims, report deployment or definitive decision.

These source milestones are local acceptance only. No site/hospital assertion,
clinical deployment, GitHub merge or HREC approval is implied.

## P2.6: P10 source-only safety decision integration
- [x] The [P10 decision contract](../../../contracts/clinical/safety-decision.json) lists all six P2 safety outcomes and leaves unavailable measurements, noninferiority margins and site authority explicitly null.
- [x] An illustrative positive net resource benefit cannot grant clinical safety or rollout acceptance.
- [ ] Site clinical review of acceptable harm margins, endpoint ascertainment, early appropriate return interpretation and formal decision authority remains required.

## P2.7: pre-registration and service fidelity
- [x] Source-only [pre-registration draft](../../../contracts/clinical/preregistration.json) defines intention-to-cover, exploratory contact association, phased/controlled ITS, covariates and negative controls without observed data.
- [ ] Before site implementation, clinically approve index validity definitions, current-care activity and exposure/roster recordings, proposed controls, minimum age, analysis locking and linked endpoints. The public draft is not registration.
