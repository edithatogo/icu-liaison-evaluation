# P6 specification — independent temporal capacity qualification

**Motivation:** P4 aggregates expected delays over one year but cannot establish
that a discharge-ready ICU hour corresponds to a usable staffed bed at a time
when another patient needs it. A temporal model might answer admission-delay,
queueing, elective-surgery and staffed-bed questions; it is **not automatically
justified** by aggregate ANZICS exit-block rates.

## Implemented portable contract (no new DES engine)

- Versioned synthetic-only, minute-resolution **half-open** ICU occupied intervals,
  staffed-capacity calendar, linked demand request/disposition for multiple arms.
- Same demand request identity/time across alternatives, physically complete
  capacity coverage and nonoverbooking even during capacity reductions.
- Each admitted request must correspond to an observed occupancy start; censored
  and declined requests are distinct; initial patients may have start minute zero.
- NumPy event-boundary integration returns staffed/occupied/spare bed-minutes,
  patient request counts and admission delays, and paired differences when
  *the same request cohort* is admitted in both arms.
- No costs/QALYs/readmissions are inferred; this trace cannot be substituted for
  annual P4 estimated capacity, local clinical validation or a Kairos execution.
- No real identifiers permitted: `syn-` fixture IDs only. No unrestricted
  local patient data or raw queue traces admitted to a public report.

## Deferred provider contract

Kairos remains the DES/ABM/scheduler owner. A future qualification must inspect
its **actual pinned API** and map an authenticated producer event envelope to a
neutral capacity trace, preserving resource-claim intervals, physical departure,
queue requests/acceptance, timing, cancellations, preemption and staff calendars.
No schema compatibility or native Kairos run is claimed by this pilot. Local
approval and data/case-mix calibration must precede a business-case estimate.

## Source-only native continuation

An optional native consumer now uses the exact pinned Kairos
`StagedResourceRuntime` API in one-bed, fixed-duration, synthetic-only mode.
Its typed contract is admitted by `icu_liaison.p6_native`, not directly by the
fixture-only trace schema. Provider JSON does not by itself establish execution;
compiled binaries and independent build provenance remain open. The separate
SciPy admitted-only synthetic holdout score is not a clinical validation.
See [ADR-0005](../../decisions/ADR-0005-p6-kairos-staged-resource-consumer.md).
