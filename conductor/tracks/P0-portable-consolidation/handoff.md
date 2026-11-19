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
live interactive slash-command execution remain open). Native Dapane 0.1 and
Voiage 3.1 qualification and CareOps Sim PR #215 retirement remain pending.
