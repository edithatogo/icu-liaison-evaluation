# P0 handoff

18 November 2026. This directory is a portable, local-only checkpoint for the
user-supplied future repository. It does not change any GitHub source or merge,
close, or install an existing PR/extension.

Prior work: CareOps Sim draft PR #215 at inspected source head
`e6caa16c5b87cbfadd2b10588ed10b7c6d60b637`; the original source contains
an unaccepted example build/formatting failure. New portable code deliberately
replaces duplicate SciPy/NumPy algorithms; exact seeded trajectories are not
identical to the earlier Rust draft, while its central fixed-input accounting
identity remains. Workbook preserved in Library under SHA in migration manifest.

This local environment runs Python 3.13.5 with NumPy 2.3.5, SciPy 1.17.0,
Pydantic 2.13.5 and pytest 9.0.2; it does not have Rust, Dapane native 0.1,
Voiage native Python 3.15.2 or installed Gemini CLI. Do not report native
provider tests or Conductor installation as passed. Use the test matrix for
completed scope, then qualify full providers on supported platforms.

## Local CI/CD and Conductor parity addendum (19 November 2026)

PR #1 was merged into `main` (`4644bb4f5c2597cfc5e07cabe4de0b33e9dfb558`) while
hosted GitHub Actions remained blocked on account billing/spending limit (merge
run `44434804695`, 0 steps executed). This machine now runs an isolated `.venv`
(CPython 3.13.18 with `requirements-ci.txt` pins), `tools/run_local_ci.py`,
`.pre-commit-config.yaml`, and active `.githooks/` (`pre-commit`,
`pre-merge-commit`, `pre-push`). `extensions/conductor` is initialized at
`7a5c560a4fdf5297be58594cc37527eb12790272` and matches all 22 runtime/command/
policy files of `~/.gemini/extensions/conductor` (`autoUpdate: true` caveat and
live interactive slash-command execution remain open).

## Public CI, gitleaks, Python 3.15.2 native oracles, and PR #215 comparison (19 November 2026)

`edithatogo/icu-liaison-evaluation` was changed to public visibility with GitHub
Secret Scanning and Push Protection enabled, and hosted GitHub Actions CI
passed on `main` (`1c7f640`, run `44444785989`, `verification/hosted-ci-public-2026-11-19.json`).
Local `gitleaks protect --staged` scanning is wired into `pre-commit` and
`pre-merge-commit`. In an external Python 3.15.2 environment, pinned Dapane
`0.1.0` (`0658d94ad772023a0185a000b5254f9c2f4a63a9`) and PyPI Voiage `3.1.0`
passed `tools/qualify_providers.py --provider all` (`verification/p0-native-providers-py315-2026-11-19.json`,
lockfile `verification/p0-py315-native-lock-2026-11-19.txt`); 319/321 unchanged
tests passed in Python 3.15.2, with only the 2 P5 absent-Dapane assertion
tests failing because real Dapane executed. A read-only 19-file comparison
against CareOps Sim PR #215 is recorded in `docs/pr215-migration-comparison.md`
and `verification/p0-pr215-migration-comparison-2026-11-19.json`; PR #215 remains
open pending independent sign-off, and independent wheel-provenance adjudication
(`providers.lock.json`) remains open in P1.4/P7.

## CPython 3.15.2 migration — 19 November 2026

P0.5 pins local development, packaging, Git hooks and the hosted synthetic
workflow to CPython 3.15.2. Both full local runs and the Ubuntu workflow
passed 342 tests. The two corrected P5 tests also passed in a focused run
with Dapane 0.1.0 rebuilt from the locked revision. The
[migration receipt](../../../verification/python-315-migration-2026-11-19.json)
records the GitHub run, the Dapane wheel and native extension digests, and the
synthetic P5 reconciliation. Independent artifact adjudication remains in P1.4/P7.
