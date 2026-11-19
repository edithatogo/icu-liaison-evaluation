# Acceptance controls

| Gate | Executed or pending control | Admission limit |
| --- | --- | --- |
| P3 quality | `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_qualification_independent.py` | Aggregate descriptive uncertainty only; unknown retained |
| P4 oracle | Independent Decimal accounting over selected stochastic draws | Numeric calculation only, not a causal or cost-source validation |
| CHHHS fields | `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_data_request_pack.py` | Request schema, not a processed clinical extract |
| Existing Python | All test modules, partitioned P0–P4/P5/P6 | No inference about native binaries |
| Earlier rebuilt Dapane macOS wheel | Build owner verified pinned source, locked SBOM, wheel digests and contents, Cargo outputs and installed files | Independent sign-off was withheld for the earlier build. [Earlier decision](plan.md#p75-independent-provider-review) |
| Dapane independent binary-pin approval | Corrected Rust 1.99.1 wheel and extension verified against an independent build. The installed P1/P5 checks passed | Exact macOS arm64 CPython 3.15.2 pair. [Artifact decision](plan.md#corrected-dapane-artifact-decision) |
| Dapane independent macOS native execution receipt | Counterfactual pricing, component conservation and deterministic replay verified using the pinned wheel and loaded extension | macOS arm64 CPython 3.15.2. [Execution decision](plan.md#dapane-native-execution-decision) |
| Dapane independent Linux and Windows artifact and execution receipts | Verified the exact wheels, installed native extensions, six ledger replays on each platform and the Windows test fixture correction | Ubuntu 24.04.5 LTS and Windows Server 2025 Datacenter x86-64 on CPython 3.15.2. Broader release approval remains open. [Platform decisions](plan.md#linux-and-windows-dapane-decisions) |
| Dapane Windows upstream rebuild | Independently matched all 215 passing vendor cases and verified the exact rebuilt wheel, installed extension and native receipt | Windows Server 2025 Datacenter x86-64 build 26100 and CPython 3.15.2. [Upstream rebuild decision](plan.md#windows-upstream-rebuild-decision) |
| Voiage independent admission | Pending exact artifact provenance, platform scope and outstanding dependency and licence review | Voiage `binary_sha256` remains null |
| Kairos | `tools/qualify_p6_native.py` | Requires Rust, reviewed Cargo.lock and exact source pin |
| ANZICS 2024/25 | Retain and independently inspect publisher PDF and SHA | Unverified until actual document admission |
| CHHHS readiness | Approved local extraction, calibration, independent safety, Finance, clinical and equity review | No check-box alone constitutes approval |
| Dedicated Git | Target repo, pinned dependencies, hosted tests/reviews and explicit privacy boundaries | Not yet supplied |
