# P6 test matrix

- Synthetic fixture (`model-inputs/p6/synthetic-trace.json`) integrates exact
  180 vs 150 occupied bed-minutes and 60 vs 30 admission-wait minutes.
- Staffing change 1→2 beds at minute 120 increases bed-minutes, not staffing
  workload acceptance or cash savings.
- Missing capacity intervals, overbooking, invalid horizons and duplicate
  episodes fail closed.
- Admission requests must link to physical occupancy and share request times
  across strategy arms; statuses admitted, declined and censored remain distinct.
- Source class and identifiers permit synthetic-only input and reject direct
  Kairos provenance claims without installed native provider qualification.
- CLI emits aggregate-only JSON with source hash and never publishes source IDs.

Commands: `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_p6_capacity_trace.py`
then the repository's full test suite and deterministic CLI smoke.

## Native source and holdout extension

- `pytest -q tests/test_p6_native_contract.py tests/test_p6_native_source_boundary.py`
  covers source revision, independent fixed one-bed oracle, exact denominator
  and provenance refusal. This is *not* an actual Rust-run acceptance test.
- `pytest -q tests/test_p6_holdout.py tests/test_p6_qualification_gates.py`
  covers SciPy holdout metrics, data-leakage refusal and missing-provider failure.
- Native replay: `PYTHONPATH=src .venv/bin/python tools/qualify_p6_native.py` validates the installed
  Rust compiler, reviewed lock, `cargo fmt/clippy/test/build`, real Kairos output,
  independent oracle and byte-identical replay. The local run passed on Rust
  1.100.0 against the updated Kairos pin.
- Site gate: validated CHHHS input sources, holdout, clinical safety/governance
  and Finance review cannot be substituted by synthetic fixtures.
