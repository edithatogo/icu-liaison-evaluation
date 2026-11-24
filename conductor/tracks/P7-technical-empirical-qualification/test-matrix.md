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
| Voiage independent admission | Publisher signature, signed tag, wheel and installed bytes, licence, dependency checks and native EVPI verified | Exact macOS arm64 wheel on CPython 3.15.2. [P1 admission](../P1-provider-reuse/plan.md#voiage-macos-artifact-admission) |
| Kairos | `tools/qualify_p6_native.py` | Requires Rust, reviewed Cargo.lock and exact source pin |
| ANZICS 2024/25 | Reconcile the recorded six locators and check the retained PDF's SHA-256 offline | Intended-use reviewer and licensing decision pending |
| CHHHS readiness | Approved local extraction, calibration, independent safety, Finance, clinical and equity review | No check-box alone constitutes approval |
| Dedicated Git | Pinned source, hosted synthetic and privacy checks, and recorded migration disposition | Portable source gate verified. [Import record](../../../docs/repository-import.md) |

## Repeat the current qualification

```sh
PYTHONPATH=src .venv/bin/python tools/qualify_current_portable.py
```

Add `--publisher-document /secure/evidence/ANZICS-CCR-2024-25.pdf` to verify
an already retained copy against the recorded size and SHA-256. The command
runs offline. It records the UTC run date and input identities and verifies
the CHHHS request specification and the hashes of its UTF-8 Markdown and CSV
renderings.

On 24 November 2026 the receipt reconciled six ANZICS locators and matched the
saved publisher PDF. Both exported request files matched their recorded digests
and contained specifications for 11 datasets and 115 fields. On CPython 3.15.2,
the independent oracle checked 18 strategy draws at seed `20261118`.
All 127 focused Python tests passed. Repeated portable receipts and the
illustrative model result matched byte for byte in the local run.

Both fictional eligible-cohort ranges are one-third to two-thirds. The delay
proportion among records with valid readiness is one-half. The cohort ranges
assign all unresolved records to each extreme, keeping competing deaths
separately counted within unresolved returns. The ranges describe the
uncertainty from missing outcomes in this fixture. Clinical or competing-risk
estimation requires the approved observations and analysis method.

## P7 review on 24 November 2026

Ten checks failed before the fixes and passed in the 137 focused tests.
The synthetic P3 feed now exercises a
return with unresolved planned status despite complete observation time.
The audit keeps the outcome unresolved, reports complete follow-up
separately and rejects contradictory counts or invalid source fingerprints.
The P4 oracle checks valid short simulations with each selected draw counted once.

The request exporter uses exclusive file creation. The tests exercise a
failed second write and a file appearing during export. The exporter removes
the files it created on failure and preserves the other writer’s file.
The successful Markdown and CSV exports reproduced their previous bytes.
The qualification still matched six ANZICS locators and the retained PDF
digest, and the standard fixture still passed all 18 draw checks.
