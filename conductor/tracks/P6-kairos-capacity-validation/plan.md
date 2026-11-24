# P6 implementation plan

## P6.1 — Specify need and neutral event trace
- [x] Record why annual exit-block counts do not measure usable staffed capacity.
- [x] Implement versioned, synthetic-only observed-event admission contract,
  including common demand and explicit censored/declined outcomes.
- [x] Record governance and no-new-scheduler boundary against Kairos.

## P6.2 — Synthetic time-aware conformance checks
- [x] Implement half-open occupancy and shift-capacity conservation with NumPy.
- [x] Reject overlap, overbooking, ghost occupancy, calendar gaps, invalid
  horizons, fabricated Kairos provenance, or unpaired demand timestamps.
- [x] Provide CLI and synthetic fixture demonstrating discharge/access timing
  without monetisation or generalisation to CHHHS.
- [x] Report paired request dispositions and wait changes among requests
  admitted in both arms. Retain the original wait comparison for identical
  admitted cohorts.

## P6.3 — Kairos native source and local replay

- [x] Inspect immutable upstream Kairos staged runtime API and file blob SHAs;
  pin a single-ICU-bed Rust consumer to commit `273bf44956dfadd31336a9f9f645eba6b39779f9`.
- [x] Author native source, synthetic fixture and independent consumer contract,
  with standalone Cargo format, build and test qualification runner.
- [x] Review Cargo.lock against its sources and pass the Rust format, lint,
  test and build checks. Match the one-bed reference and repeat the replay.
- [x] Implement strict native-output normalisation into the existing NumPy
  trace audit with paired-demand and physical conservation checks.
- [x] Check FIFO order, vacant-bed waits and horizon censoring. Verify the
  pinned provider source before compilation and repeat both reference cases.
  [Verification](test-matrix.md#fifo-contention-and-paired-access)
- [ ] Independently attest the built artifact and runner.
- [x] Preserve synthetic-only provider/seed/input/source identity and refuse
  conversion of capacity to cash or clinical benefit; require source-byte proof
  and reject false direct native claims.
- [ ] Qualify physical ward/costing/clinical rescue interoperability with a
  real provider run and observed approved data.

## P6.4 — Synthetic holdout diagnostics and site evaluation (site blocked)
- [ ] Obtain approved, de-identified CHHHS timing, staff calendars, bed demand,
  ward availability, case-mix and clinical outcomes with source completeness.
- [x] Implement independent SciPy Wasserstein/KS and paired-error comparison
  for strictly synthetic, disjoint training/holdout admitted-request times;
  include explicit unverified status, data-gate list and censoring exclusions.
- [ ] Qualify and calibrate real CHHHS trajectories (including censored/declined
  admission demand, ward friction and risk adjustment); reconcile with P4
  only after source/denominator and causality acceptance.
- [ ] Independent clinical/Finance/research review, operational risk analysis,
  exact-head CI and decision on whether temporal DES adds incremental value.

A future native simulation must reuse Kairos rather than creating another
DES/scheduler in the study. Completion of P6.1/2 does not accept P6.3/4.
