# P6 synthetic temporal capacity inputs

`synthetic-trace.json` contains independently authored occupancy intervals for
fictional strategies. This is a numeric fixture, **not** a native Kairos run.
Its schema is `trace-schema.json` and it retains `source_engine=not_kairos`.

`kairos-synthetic-input.json` is a distinct native-consumer fixture: one staffed
bed, one initial occupant, common admission requests and strategy-specific
initial departures. The source-only Rust consumer at `native/kairos-icu-liaison`
uses Kairos `StagedResourceRuntime` for FIFO queueing and lease promotion.
It has **not been compiled** here. `kairos-provider-lock.json` pins the exact
Git source and inspected API blob identities. The manually authored
`tests/fixtures/p6_native/independent-reference.json` is a test oracle,
not an observed native output.

`synthetic-holdout.json` exercises SciPy admitted-wait holdout diagnostics.
The split does not include censored/declined patients and is not a CHHHS
clinical validation. No files here contain observed patient-level data.
