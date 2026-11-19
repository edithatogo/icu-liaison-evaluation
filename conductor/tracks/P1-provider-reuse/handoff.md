# P1 portable implementation handoff — 18 November 2026

Existing P0 package recovered from the prior portable archive. The original
ANZICS Library workbook remains outside this archive; the original CareOps Sim
PR #215 remains unmerged and is not modified in this source-only increment.

Changes:
- Portable P1 source-reference lock for Dapane `0658d94...` and Voiage
  release `v3.1.0`/commit `d40af027...`, with binary hashes unset.
- Dapane nominal incremental counterfactual bridge, exact Decimal quantities,
  return increase accounting, real-provider call and report admission.
- Voiage financial-only EVPI consumer and native two-state reference oracle.
- Version-gated explicit `qualify_providers` with JSON statuses, installed
  extension SHA observations and no silent fallback.
- Regression tests and a reproducible provider-environment setup guide.

**Open gates:** native Dapane/Voiage distributions are not available in the
local container; full P1 release acceptance cannot be claimed. Exact wheel
source provenance, installed native execution, other supported platforms and
independent source review remain pending. P0.4 and P1.5 are blocked until a
user-provided dedicated repository can receive the portable implementation.

Source labels from previous conversation material remain curated, rather than
raw private chat exports. Hospital observations are not introduced. Downstream
P2 clinical/economic specification should not be inferred as completed by P1.

## macOS arm64 / Python 3.15.2 native qualification update — 19 November 2026

Executed P1.4 in an external Python 3.15.2 environment with Dapane `0.1.0`
(`0658d94ad772023a0185a000b5254f9c2f4a63a9`) and PyPI Voiage `3.1.0`
(`v3.1.0` / `d40af0276019a7d63657349b53dad96845e2b4c1`), recorded in
`verification/p1-native-qualification-2026-11-19.json`,
`verification/p0-native-providers-py315-2026-11-19.json`, and
`verification/p0-py315-native-lock-2026-11-19.txt`.

Observed outcomes and open caveats:
- Native numerical oracles, PyPI PEP 740 + GitHub PGP attestations, cross-env
  CLI byte-parity (`3.13.18` vs `3.15.2`), P5 `--dapane --voiage` +
  `p5_review_cli` reconciliation, Dapane `dapane-core` (54/54) + Python (196/196),
  Voiage core wheel tests (13/13), and Python 3.15.2 PyPI `pip-audit` (0 CVEs)
  all passed.
- Caveats kept open: `dapane-cli` had 1 macOS APFS non-UTF-8 filename test
  failure, `cargo deny` flagged unmaintained `RUSTSEC-2026-0543` (`chrono 0.4.45`),
  `requirements-ci.txt` flagged `setuptools==82.0.1` (`PYSEC-2026-3447`, `GHSA-xmj3-9gf7-h52w`),
  unchanged `pytest` in Python 3.15.2 failed only the 2 P5 absent-Dapane tests,
  Linux/Windows qualification is pending, and independent P7 adjudication of
  `providers.lock.json` `binary_sha256` remains open.

## Independent Dapane native execution approval — 19 November 2026

Separate Codex reviewer `dapane_reviewer` approved the native
counterfactual pricing and component conservation receipt on the corrected,
pinned Dapane 0.1.0 installation. The lock records the receipt digest for
macOS 27.2.1 arm64 and CPython 3.15.2. Broader platform and release
qualification and Voiage admission remain open.
[P1.4 findings](plan.md#native-counterfactual-pricing-and-component-conservation)

## Linux and Windows Dapane decisions — 19 November 2026

The independent reviewer approved the pinned-source Rust 1.99.1 builds
for Ubuntu 24.04.5 LTS x86-64 and Windows Server 2025 Datacenter x86-64
with CPython 3.15.2. The lock records each approved wheel, loaded extension
and native pricing receipt. The Windows evidence includes the original
vendor fixture failures and the full rerun with corrected path keys in
a disposable test copy. Broader release qualification and Voiage
admission remain open. [P1.4 platform findings](plan.md#linux-and-windows-x86-64-qualification)
