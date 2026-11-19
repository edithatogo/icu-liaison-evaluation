# ADR-0005 — Use Kairos staged resource runtime for bounded ICU occupancy DES

**Date:** 2026-11-18
**Status:** Accepted for *source-level experimental consumer*; native and clinical acceptance pending.

## Problem

Annual ANZICS exit-block rates cannot establish time-aligned staffed capacity.
P6 therefore needs an optional time-aware resource/queue producer while avoiding
creation of a second event engine or the transfer of CHHHS patient records to a
public model repository.

## Selected existing dependency

The exact inspected upstream source is `edithatogo/kairos` commit
`a1f6283575ad26918230adc122a99b5c08fc4da3`. The API
`kairo-ecs-des::StagedResourceRuntime` supplies simulation time, resource
leases, queuing, release, promotion, and bounded `run_for` dispatch. Core
`kairo-ecs-types::SimTime` is used for fixed minute ticks. The input/output
boundary is a portable JSON document validated independently with Pydantic/
NumPy. The pinned provider source/API files and Git blob SHAs are listed in
`model-inputs/p6/kairos-provider-lock.json`.

The application owns scenario admission, synthetic identifiers, index ICU
resident discharge times, deterministic request schedules, end-of-horizon
censoring, interval export and resource-accounting reconciliation. It does
not implement another scheduler or resource queue.

## Narrow accepted *source* scope

One initially occupied staffed bed, two or more strategies, common exogenous
arrival requests, explicitly specified service durations, and one independent
native Kairos runtime per arm. No stochastic clinical behaviour is inferred;
`seed` is retained as declared provenance but the fixed-duration reference
scenario does not consume RNG draws. Queueing is a consequence of existing
Kairos staged leases and event ordering, not a hand-written process loop.

The native producer source is under `native/kairos-icu-liaison`, but the authoring
container lacks Rust tooling and network. **It has not been compiled or run.**
`tools/qualify_p6_native.py` fails closed until the exact Cargo.lock exists,
resolved Git packages match the pinned commit, format/Clippy/tests/build pass,
actual binary replay is stable and independent fixture results match. These
are necessary but not sufficient for independent build provenance.

## Exclusions / future extension

A real ICU model needs a variable staffed-bed calendar, ward acceptance,
readmission/return states, escalation, transfer friction, staffing interactions,
separate clinical rescue outcomes and observation censoring. The one-bed model
is not a CHHHS effect estimate, cannot be combined numerically with P4 annual
expected effects and does not certify cost savings. P6.4 local measurement,
clinical/Finance approval, First Nations data governance and independent
calibration remain separate.

## Rejected alternatives

- New event-scheduler/heap and bespoke resource queue: duplicates Kairos.
- Treating a manually authored trace as a native Kairos run: false provenance.
- Adopting the full CareOps Sim implementation as a hard dependency: broader
  clinical/source ownership and unrelated experimental backend requirements.
- Treating the source SHA or a self-supplied binary hash as a signed reproducible
  build attestation: inadequate assurance.
