# ICU liaison: optional native Kairos consumer

**NOT EXECUTED** in the portable authoring environment (Rust toolchain and
network dependency fetch unavailable). No source publication, clinical approval,
CHHHS calibration, or actual native runtime qualification is implied.

This Rust program uses `kairo-ecs-des::StagedResourceRuntime` to model a **single
staffed ICU bed with one initial occupant and scheduled synthetic demand**. The
Kairos runtime owns time, FIFO allocation, resource leases, queueing, release and
promotion. The project owns only ICU-specific input mapping, an index-discharge
scenario difference, a finite event budget and a neutral event-trace output.
There is no second scheduler or generic simulator in the application.

Only fixed capacity = one bed is supported in the first consumer. Staffing-shift
changes, detailed ward transfers, clinical readmissions, triage priorities,
interhospital transfers, goal-of-care changes and economic outcomes are outside
its supported domain. The broader Python P6 numerical auditor can examine
externally supplied time-varying capacity traces, but that does not mean this
native provider can produce them.

## Qualify after creating the dedicated repository

With a supported Rust toolchain and authenticated dependency access:

```bash
cd native/kairos-icu-liaison
cargo generate-lockfile   # review and commit exact lock; no lock is shipped before resolved
cargo build --locked
cargo fmt --all --check
cargo clippy --locked --all-targets -- -D warnings
cargo test --locked
cargo run --locked -- ../../model-inputs/p6/kairos-synthetic-input.json > native-run.json
```

The actual binary should be run through the Python `icu_liaison.p6_native_cli`
with a separately reviewed SHA256 of the compiled binary, the exact scenario,
and the committed provider lock. The adapter validates the output against the
already-independent NumPy conservation audit. A caller-supplied binary hash is
not source-build attestation, so this remains **unattested native execution**
until an independent build/runner receipt is reviewed.

A future hosted CI job should prove the exact Kairos source commit, full
resolved lock, compiler identity, binary hash, fixture output, replay identity,
negative cases, and independent review. Do not regenerate source goldens just to
pass tests. Private CHHHS operational data cannot be uploaded to public CI.
