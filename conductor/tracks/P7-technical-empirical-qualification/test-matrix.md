# Acceptance controls

| Gate | Executed or pending control | Admission limit |
| --- | --- | --- |
| P3 quality | `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_qualification_independent.py` | Aggregate descriptive uncertainty only; unknown retained |
| P4 oracle | Independent Decimal accounting over selected stochastic draws | Numeric calculation only, not a causal or cost-source validation |
| CHHHS fields | `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_data_request_pack.py` | Request schema, not a processed clinical extract |
| Existing Python | All test modules, partitioned P0–P4/P5/P6 | No inference about native binaries |
| Earlier rebuilt Dapane macOS wheel | Build owner verified pinned source, locked SBOM, wheel digests and contents, Cargo outputs and installed files | Independent sign-off was withheld for the earlier build. [Earlier decision](plan.md#p75-independent-provider-review) |
| Dapane independent binary-pin approval | Corrected Rust 1.99.1 wheel and extension verified against an independent build. The installed P1/P5 checks passed | Exact macOS arm64 CPython 3.15.2 pair. [Artifact decision](plan.md#corrected-dapane-artifact-decision) |
| Dapane independent native execution receipt | Counterfactual pricing, component conservation and deterministic replay verified using the pinned wheel and loaded extension | macOS arm64 CPython 3.15.2. Intended-platform qualification and release review remain open. [Execution decision](plan.md#dapane-native-execution-decision) |
| Voiage independent admission | Pending exact artifact provenance, platform scope and outstanding dependency and licence review | Voiage `binary_sha256` remains null |
| Kairos | `tools/qualify_p6_native.py` | Requires Rust, reviewed Cargo.lock and exact source pin |
| ANZICS 2024/25 | Retain and independently inspect publisher PDF and SHA | Unverified until actual document admission |
| CHHHS readiness | Approved local extraction, calibration, independent safety, Finance, clinical and equity review | No check-box alone constitutes approval |
| Dedicated Git | Target repo, pinned dependencies, hosted tests/reviews and explicit privacy boundaries | Not yet supplied |
