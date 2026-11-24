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
  request counts and admission delays. The comparison reports transitions
  among admitted, declined and censored requests and the wait difference
  for requests admitted in both arms. The original overall wait comparison
  remains available when both arms admit the same cohort.
- No costs/QALYs/readmissions are inferred; this trace cannot be substituted for
  annual P4 estimated capacity, local clinical validation or a Kairos execution.
- No real identifiers permitted: `syn-` fixture IDs only. No unrestricted
  local patient data or raw queue traces admitted to a public report.

## Pinned native consumer

Kairos owns the scheduler and resource allocation. The optional native
consumer uses the pinned `StagedResourceRuntime` for one staffed bed, fixed
durations and FIFO demand. The typed adapter checks occupancy and paired
requests, including simultaneous arrivals, admission at the next available
bed and censoring at the horizon. The locked local build and both synthetic
replays passed. Independent build attestation, approved site data and case-mix
calibration are required for site evaluation. A site producer must also cover
staff calendars, ward acceptance, cancellation and preemption.

The separate SciPy synthetic holdout describes waits among admitted requests.
See [ADR-0005](../../decisions/ADR-0005-p6-kairos-staged-resource-consumer.md).
