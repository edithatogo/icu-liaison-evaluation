# P6 synthetic temporal capacity inputs

`synthetic-trace.json` contains independently authored occupancy intervals for
fictional strategies. This is a numeric fixture, **not** a native Kairos run.
Its schema is `trace-schema.json` and it retains `source_engine=not_kairos`.

`kairos-synthetic-input.json` is a distinct native-consumer fixture: one staffed
bed, one initial occupant, common admission requests and strategy-specific
initial departures. The Rust consumer at `native/kairos-icu-liaison` uses
Kairos `StagedResourceRuntime` for FIFO queueing and lease promotion. The local
qualification compares the actual output with the hand-authored reference
in `tests/fixtures/p6_native/independent-reference.json` and repeats the
contention case in the same fixture directory. `kairos-provider-lock.json`
pins the Git source and inspected API blob identities.

`synthetic-holdout.json` exercises SciPy admitted-wait holdout diagnostics.
The split does not include censored/declined patients and is not a CHHHS
clinical validation. No files here contain observed patient-level data.
