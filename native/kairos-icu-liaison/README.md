# ICU liaison: optional native Kairos consumer

The pinned consumer passed local synthetic replay on Rust 1.100.0.
Independent build attestation and CHHHS calibration remain open.

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

## Repeat the local replay

From the repository root, use the reviewed Cargo.lock and a supported Rust toolchain.

```bash
cargo fetch --locked --manifest-path native/kairos-icu-liaison/Cargo.toml
PYTHONPATH=src .venv/bin/python tools/qualify_p6_native.py
```

The qualification runner checks formatting and lint, runs the Rust tests,
builds the consumer into `build/debug` under this directory, and checks the
binary, replay and independent fixture. See the
[P6 qualification guide](../../docs/p6-native-qualification.md) for scope and sources.
