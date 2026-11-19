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

## P1.4 — Installed runtime qualification (macOS arm64 executed; open gates remain)
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
