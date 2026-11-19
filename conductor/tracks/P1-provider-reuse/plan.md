# P1 — implementation and acceptance

## P1.1 — Source and interface qualification
- [x] Inspect current Dapane contract 0.1 and installed Python/API requirements;
  record immutable source revision without implying wheel provenance.
- [x] Inspect Voiage v3.1.0 released tag/DecisionAnalysis/ValueArray interfaces;
  record supported Python version and source reference.
- [x] Introduce `providers.lock.json` and strict source/version gates. Do not
  treat compatible metadata as completed native integration.

## P1.2 — Dapane cost ledger consumer
- [x] Generate pairwise scenario requests with exact nonnegative decimal use,
  separating index delay and subsequent return episodes, allowing adverse
  readmission changes and explicit price-year/perspective/basis.
- [x] Call Dapane for cost valuation and reject wrong run, currency, basis,
  method/version, non-finite or negative output. No alternate production kernel.
- [x] Establish independent two-line cost identity and zero/adverse-effect
  regression cases with injected boundary providers.

## P1.3 — Voiage decision-analysis consumer
- [x] Reuse the supported two-strategy financial decision array and
  `DecisionAnalysis.evpi()` rather than implementing EVPI.
- [x] Check output finiteness, strategies, scope and financial-only meaning;
  regression with provider injection and an independent 2-state native oracle.

## P1.4 — Installed runtime qualification
- [x] Obtain an authorised, exact-source Dapane 0.1 native wheel and released
  Voiage 3.1.0 distribution in an isolated CPython 3.15.2 environment; save
  inspected wheel and native-extension SHA-256 plus dependency resolution
  (`verification/p0-native-providers-py315-2026-11-19.json`,
  `verification/p0-py315-native-lock-2026-11-19.txt`,
  `verification/p1-native-qualification-2026-11-19.json`).
- [~] Run `private/venv-p1/bin/python tools/qualify_providers.py --provider all`
  in the reviewed provider environment,
  record installed numerical reference outputs, compatibility, vendor tests,
  security/licence results and exact source attestations:
  macOS arm64 oracles (`NATIVE_ORACLES_PASSED_ARTIFACT_PROVENANCE_PENDING`),
  GitHub PGP + PyPI PEP 740 attestations, Dapane `dapane-core` (54 passed) /
  Python wheel (196 passed), Voiage core wheel tests (13 passed), and Python
  3.15.2 `pip-audit` (0 CVEs) all passed (`verification/p1-native-qualification-2026-11-19.json`);
  kept `[~]` because `dapane-cli` had 1 macOS APFS non-UTF-8 filename test
  failure, `cargo deny` flagged unmaintained `RUSTSEC-2026-0543` (`chrono 0.4.45`),
  `requirements-ci.txt` flagged `setuptools==82.0.1` (`PYSEC-2026-3447`, `GHSA-xmj3-9gf7-h52w`),
  Linux/Windows qualification is pending, and independent P7 adjudication of
  `providers.lock.json` `binary_sha256` remains open.
- [x] Run unchanged full tests using that runtime, compare cross-environment
  reproducibility/precision, record remaining qualification findings:
  `icu_liaison.cli` produced byte-identical JSON across Python `3.13.18` vs
  `3.15.2` (`max_abs_diff = 0.0`), `qualify_current_portable.py` matched
  (`max_abs_difference_aud: 8.1709665315e-11`), P5 `--dapane --voiage` +
  `p5_review_cli` reconciled cleanly, and unchanged `pytest` reported
  `319 passed, 2 failed` strictly on the two P5 absent-Dapane tests.
  After the tests were corrected, the full suite passed (342 tests) and the
  two P5 regressions passed as a focused run with Dapane 0.1.0 installed on
  macOS arm64 and CPython 3.15.2.
  [Migration receipt](../../../verification/python-315-migration-2026-11-19.json)

### Rebuilt Dapane wheel evidence review

On 19 November 2026, the build owner checked the macOS arm64 CPython 3.15
wheel identified by SHA-256 `89e11980964c7bb4ff07398d6db748c03f165f8efef0209565416826048eec26`.
All 301 retained source entries matched the archive from GitHub-verified
commit `0658d94ad772023a0185a000b5254f9c2f4a63a9`. The archived
`Cargo.lock` matched the build receipt. The wheel's 37 SBOM dependency
entries matched the lock, including checksums for all 36 registry crate
archives verified in the local cache.

ZIP integrity and all 10 hashed `RECORD` entries checked out, and all 10
files matched the existing installation. The Python package files and
three licence and notice files matched pinned source bytes. The native
extension matched both retained Cargo products and the extension SHA-256
recorded in the earlier P1 receipt. The earlier full wheel SHA-256 starts
with `5343c7b2`, and the two wheel archives have distinct digests. The
macOS arm64 binary has an ad-hoc signature. GitHub returned HTTP 404 for an
artifact attestation lookup against the exact rebuilt wheel digest.
[Migration receipt](../../../verification/python-315-migration-2026-11-19.json) ·
[Earlier P1 receipt](../../../verification/p1-native-qualification-2026-11-19.json)

Independent adjudication of the exact wheel and its build provenance is
open under [technical P7.5](../P7-technical-empirical-qualification/plan.md#p75-independent-provider-review).
The Dapane `binary_sha256` field was unset after this review. The 342-test run and the two
focused P5 regressions in the migration receipt apply to the rebuilt wheel.

### Independent Dapane technical review

On 19 November 2026 AEST, Codex reviewer `dapane_reviewer` worked independently
of the original build lane. The reviewer confirmed the pinned source, wheel
digest, `RECORD` contents and installed bytes. The retained
`dapane/_native.cpython-315-darwin.so` digest is
`d5ece8d154d56f007fc25486d5b27225de81e24696a527b46e8946e98b17ff3a`.
The reviewer verified the loaded extension's digest before both Dapane
oracles passed at AUD 100.00 and AUD −168,730.00.

The migration receipt's Rust 1.99.1 values came from preflight version probes.
The retained Cargo compiler metadata and native extension identify Homebrew
Rust 1.100.0. The historical P1 receipt records that toolchain for the
same extension digest. Replaying the launcher set `RUSTUP_TOOLCHAIN=1.99.1`.
Maturin's environment resolved `cargo` and `rustc` to Homebrew via `PATH`.
Two independently controlled Rust 1.99.1 builds produced different wheel
and extension bytes, including executable-section differences after
build-path remapping.

The reviewer **withheld binary-pin sign-off**. The recorded notices cover the
pinned Rust 1.99.1 build inputs and the effective 1.100.0 toolchain inventory
remains unreviewed. The previous test results still record the behavior of the
exact installed candidate. The Dapane `binary_sha256` was unset at that checkpoint.
[P7.5 decision](../P7-technical-empirical-qualification/plan.md#p75-independent-provider-review)
· [Corrected build procedure](../../../docs/providers-p1.md#source-dependent-runtime-setup-on-a-network-enabled-authorised-workstation)

### Corrected Rust 1.99.1 candidate

On 19 November 2026 AEST, the pinned Dapane 0.1.0 source and 36 locked
registry crates were rebuilt for macOS arm64 using CPython 3.15.2 and
Maturin 1.16.0. The effective Cargo and Rust compiler were 1.99.1. The Cargo
product, wheel member and installed native extension matched. The private
build receipt binds the exact artifact digests to the compiler metadata,
build log and installed checks. The out-of-space first attempt and prior
Homebrew 1.100.0 wheel remain historical evidence.

P1 ran both providers in the new environment. The Dapane oracles returned
AUD 100.00 and AUD −168,730.00, and the Voiage two-state EVPI returned
AUD 5.00. The P5 synthetic report used both providers and reconciled
5,000 draws across three strategies. The focused P1/P5 suite passed 43
tests, including the Dapane-unavailable regressions. The full installed
suite passed 342 tests.

On 19 November 2026 AEST, separate Codex reviewer `dapane_reviewer` signed off
on the exact candidate for macOS arm64 and CPython 3.15.2. An independent
Rust 1.99.1 build matched all native code and data. Accounting for the
linker UUID, its derived code-page hash and the generated wheel metadata
reproduced both complete artifacts byte for byte. All ten hashed wheel
members matched the installed files. The
[provider lock](../../../providers.lock.json) records the extension SHA-256
as `binary_sha256` and the paired archive SHA-256 in `reviewed_wheel`.

Release review remains open. [P7.5 binary-pin decision](../P7-technical-empirical-qualification/plan.md#corrected-dapane-artifact-decision)

### Native counterfactual pricing and component conservation

On 19 November 2026 AEST, separate Codex reviewer `dapane_reviewer` verified
the pinned Dapane 0.1.0 wheel and the loaded native extension on macOS 27.2.1
arm64 and CPython 3.15.2. The reviewer froze independent synthetic
expectations before execution. The P1 counterfactual entry point priced
current care less liaison at AUD +779.13 for the benefit case and AUD
−1,471.62 for the adverse-return case.

The separate native pricing pair used distinct labour and oncost quotes
for the same use, repeated consumables and sub-cent amounts. Separately
priced components reconciled to native line and ledger amounts in both
exact values and rounded cents, including rounding adjustments. The
rounded ledgers were AUD 289.69 and AUD 292.69, giving a signed difference
of AUD −3.00. The exact difference before rounding was −1807/600 AUD.
A duplicate same-use oncost was rejected as `component_overlap`. Across
the three pairs, all 15 lines matched the frozen expectations and all six
ledgers replayed byte for byte. The standard P1 native qualifier passed
with both providers.

The reviewer signed off on the exact receipt for that artifact and host.
The lock records its digest in `native_execution_receipt_sha256`.
The detailed receipt and dated verdict are retained privately. Broader Dapane
platform and release qualification and Voiage admission remain open.
[Provider lock](../../../providers.lock.json) ·
[P7.5 native execution decision](../P7-technical-empirical-qualification/plan.md#dapane-native-execution-decision)

### Linux and Windows x86-64 qualification

Both x86-64 builds used Dapane source commit `0658d94ad772023a0185a000b5254f9c2f4a63a9`,
Rust and Cargo 1.99.1, Maturin 1.16.0 and CPython 3.15.2. Each runner
verified the 36 crate archives against `Cargo.lock` and built offline.
The reviewer replayed the exact installed wheel in a fresh environment on
each build runner, then independently checked the sealed evidence.

On 19 November 2026 AEST, separate Codex reviewer `dapane_reviewer` approved
the Linux wheel, loaded ELF extension and native execution receipt for
Ubuntu 24.04.5 LTS x86-64 with glibc 2.39. The wheel's scope is the
tested `linux_x86_64` environment. The Linux qualifier, 21 focused P1/P5
tests, 62 vendor Rust tests and 196 vendor Python tests passed.
[Linux native job](https://github.com/edithatogo/icu-liaison-evaluation/actions/runs/44507492909/job/135502789559)

On Windows Server 2025 Datacenter x86-64, the native qualifier, 21 focused
P1/P5 tests and 61 vendor Rust tests passed. The unmodified vendor Python
suite recorded 166 passes and 30 `KeyError` failures. Two test fixtures
created dictionary keys with Windows path separators, then looked them up
using forward slashes. A disposable test copy normalized those two keys
with `.as_posix()` and ran all 196 tests against the wheel built from the
unchanged pinned source. All 196 passed. The sealed evidence includes both
test logs and the two-line fixture diff.
[First Windows native job](https://github.com/edithatogo/icu-liaison-evaluation/actions/runs/44507492909/job/135502789920) ·
[Windows rerun](https://github.com/edithatogo/icu-liaison-evaluation/actions/runs/44508599306/job/135506594520)

The independent reviewer approved the exact follow-up Windows wheel,
loaded PE32+ extension and native execution receipt on 19 November 2026
AEST. The first Windows build produced different bytes. Both earlier
Windows runs are retained as historical results.
[P7.5 platform decisions](../P7-technical-empirical-qualification/plan.md#linux-and-windows-dapane-decisions)

The three synthetic pairs exercised beneficial and adverse returns through
the P1 entry point and distinct cost components through the native
extension. Current care minus liaison was AUD +762.35, AUD −2,356.40 and
AUD +1.53 respectively. The replay checked 15 lines, exact and rounded
component conservation, rounding adjustments and six deterministic
ledgers. Duplicate same-use component pricing failed closed.

### Windows rebuild after the upstream fixture fix

Dapane PR #32 normalized schema fixture keys in the two reported test
modules and the newer QLD NBS module, which used the same path-key
construction. The Windows wheel was rebuilt from landed commit
`33941aa22616629a26b58220f7e05ae615855072` with Rust and Cargo 1.99.1
and CPython 3.15.2. The full vendor suite ran directly from that checkout
on Windows Server 2025 Datacenter x86-64 build 26100. All 215 Python
tests passed, including the original 196 and 19 QLD NBS cases. The Dapane
qualifier, 21 focused P1/P5 checks and 61 vendor Rust tests also passed.
[Upstream fixture fix](https://github.com/edithatogo/dapane/pull/32) ·
[Windows rebuild](https://github.com/edithatogo/icu-liaison-evaluation/actions/runs/44513181631/job/135522336234)

On 19 November 2026 AEST, separate Codex reviewer `dapane_reviewer`
matched the full set of hosted pass results to independently collected
test IDs. The reviewer verified the exact wheel, loaded PE32+ extension
and all six pricing ledger replays, including component conservation. The
Windows lock entry now records this source revision and the three signed
digests. [Provider lock](../../../providers.lock.json) ·
[P7.5 Windows decision](../P7-technical-empirical-qualification/plan.md#windows-upstream-rebuild-decision)

## P1.5 — Dedicated repository integration (in progress)
- [~] Import P0/P1 into the user-provided repository, reconcile its
  Conductor track registry, run hosted exact-head checks and independent review:
  imported into `edithatogo/icu-liaison-evaluation`, Conductor reconciled, green
  hosted CI verified on `main` (`44444785989`) and PRs; independent external
  review remains open.
- [~] Retire exploratory CareOps Sim PR #215 only after equivalent source,
  evidence and test outcomes have been verified in the new repository:
  19-file comparison completed (`docs/pr215-migration-comparison.md`); closing
  PR #215 runs immediately after this P1 PR passes hosted CI and merges.

Source-only completion is not native acceptance and is not a clinical or
investment recommendation. Keep P1.4 and P1.5 unaccepted until their actual
receipts exist.
