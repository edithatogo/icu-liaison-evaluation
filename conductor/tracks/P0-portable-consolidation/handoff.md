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

## Renovate onboarding follow-through — 20 November 2026

Chat 01a1f64b-ef56-75f3-a2dc-bafc0180b28e owns the scoped onboarding
replacement in the managed worktree
`/Users/doughnut/.codex/worktrees/icu-renovate-onboarding/icu-liaison-evaluation`
on `codex/icu-renovate-onboarding`. Its scope is the project Renovate
configuration, policy test, verification receipt, source manifest, this
handoff, and P11's synthetic acceptance closeout; native scope is none.
The existing bot-owned PR #2 fails the source inventory and inherits automated
patch and digest merges from the shared preset. The replacement preserves the
shared preset at its verified commit while requiring review of those updates. The next operation is
local validation and hosted checks, then reconciliation with PR #2 after the
replacement is integrated. The hosted bot's branch remains under its owner.

PR #29 merged at `fecca029eebdb7e2c81948038869f7a4f745bd6f` after hosted
checks passed, and PR #2 was closed as superseded. The hosted Renovate bot
created [its dependency dashboard](https://github.com/edithatogo/icu-liaison-evaluation/issues/30)
on 20 November. Its proposed upgrades remain subject to review and qualification.

## StepSecurity quality follow-through — 20 November 2026

Chat 01a1f64b-ef56-75f3-a2dc-bafc0180b28e owns the scoped replacement for
PR #25 in the managed worktree
`/Users/doughnut/.codex/worktrees/icu-liaison-scenario-workflow-plan/icu-liaison-evaluation`
on `codex/icu-stepsecurity-quality`. Its scope is the existing CI workflow,
quality-hook configuration, isolated Python 3.15 quality environment lock,
Dependabot configuration, setup guidance, verification evidence, Renovate
readback and the source manifest. Native clinical/provider scope is none. Existing Git hooks
and the bot-owned PR branch remain intact. The next operation is to qualify
the quality checks with a repository-local interpreter and validate the
pinned runner audit action in hosted CI.

The replacement retains the requested egress-audit action and Dependabot
monitoring. The added ShellCheck and formatting hooks use a separately locked,
repository-local Python 3.15.2 environment; the existing staged gitleaks and
Git hooks remain enabled. The local hooks passed against an isolated source
fixture. Hosted execution of the exact candidate remains the merge gate.
The initial hosted attempt passed the runner-audit step but its quality-env
`pip check` picked up the project source metadata from the job-wide
`PYTHONPATH`. The quality steps now clear that variable for their own isolated
environment. Hosted run 44677310647 passed the pinned audit action, all three
quality checks and the synthetic Snakemake recovery suite on candidate commit
`19e971d1ef1b40aedc37f20039ef27ed26619f7a`. The final evidence-only revision
is subject to its own hosted checks before merging.

PR #31 subsequently passed its exact-head hosted checks and merged at
`32545bd1f7335373314b264ab7e70a6da560e2a7`; PR #25 was closed as superseded.
The post-merge synthetic validation also passed in run 44678495849.

## GitHub Actions update follow-through — 20 November 2026

Chat 01a1f64b-ef56-75f3-a2dc-bafc0180b28e owns the scoped update in
`/Users/doughnut/.codex/worktrees/icu-liaison-scenario-workflow-plan/icu-liaison-evaluation`
on `codex/icu-actions-qualification`. Its scope is the two action pins in the
synthetic CI workflow, this handoff and the source manifest; native scope is
none. The next operation is to qualify the combined candidate in hosted CI.

Dependabot PRs #32 and #33 each failed hosted validation because the workflow
file changed without its source-manifest hash. Their action steps reached the
manifest check. The upstream version tags were checked against the proposed
commit hashes and both actions use Node 24. The combined candidate preserves
the workflow's Python version file, checkout options and permissions; it does
not use the removed setup-python pip input or a pull-request-target checkout.
The original bot branches remain untouched until the candidate is qualified.

## Conductor plugin migration on 23 November 2026

Chat 01a1f64b-ef56-75f3-a2dc-bafc0180b28e owns the dependency pin and registry
format on `codex/icu-conductor-plugin` in
`/Users/doughnut/.codex/worktrees/icu-remaining-schedule.ZuYzD4/conductor`. Native scope is
readback of the installed Antigravity Conductor plugin and validation of the
pinned workspace files. Antigravity 1.5.14 loaded all six skills and the project
rule from `6e8f9a8`, and its installed files matched the Git checkout. All 13
track plans resolve from the registry in the plugin's current format.

## Interactive status check on 24 November 2026

Antigravity CLI 1.5.15 prompted for trust in a disposable workspace archived
from `27b53f82140a306ff0534935bd4ce1b8d3ea8dcb`. The Conductor plugin was
enabled. The interactive `/conductor-status` request in sandboxed Plan mode
reported the expected 13 registry entries, including P11 complete. Comparing
all 429 archived files to their Git bytes after the session found an exact match.

## Privacy runner audit on 24 November 2026

The privacy workflow now starts the pinned Harden-Runner action in egress
audit mode. PR #43 restored the pre-commit configuration to the existing
hook definitions and refreshed the source manifest. Both synthetic CI runs
and the privacy scan passed before the merge at `1206a5a`.
[PR #43](https://github.com/edithatogo/icu-liaison-evaluation/pull/43)

## P0 migration review on 24 November 2026

Chat 01a1f64b-ef56-75f3-a2dc-bafc0180b28e owns the P0 plan, metadata, test
matrix, this handoff and the source manifest on
`codex/icu-p0-portable-closeout` in
`/Users/doughnut/.codex/worktrees/icu-remaining-schedule.ZuYzD4/conductor`.
The scope is source and fictional checks. The next acceptance step is an
independent migration release decision.

The 19 source files match the Git blob IDs from CareOps Sim PR #215. The
mapping resolves on standalone `main`. CPython 3.15.2 reproduced the fixed-input
accounting from the original parameter values at seed `20261117`.
PR #215 is closed with its source revision preserved. Standalone PR #5 merged
at `1ff7ca4` and its synthetic CI passed. P0.4, P1.5 and the two P7 plans
still track the independent release decision.
[Migration comparison](../../../docs/pr215-migration-comparison.md) ·
[Standalone CI](https://github.com/edithatogo/icu-liaison-evaluation/actions/runs/44455595345)

## Portable migration release decision on 24 November 2026

Chat 01a1f64b-ef56-75f3-a2dc-bafc0180b28e owns the release-status update on
`codex/icu-p0-release-approval` in
`/Users/doughnut/.codex/worktrees/icu-remaining-schedule.ZuYzD4/conductor`.
The scope covers the source migration comparison, the P0/P1/P7 plans and
metadata, and the source manifest. The next source operation is hosted CI.

The repository owner approved the verified portable source migration.
P0.4's remaining dependency is provider acceptance in P1.4 and P7.5.
[Portable source release](../../../docs/pr215-migration-comparison.md#portable-source-release)

## Portable consolidation review on 24 November 2026

Chat 01a1f64b-ef56-75f3-a2dc-bafc0180b28e owns the P0 review on
`codex/icu-p0-review-fixes` in
`/Users/doughnut/.codex/worktrees/icu-remaining-schedule.ZuYzD4/conductor`.
The scope covers the portable CLI, source manifest and public-data
checks, their tests, and these Conductor records. The next operation is
the hosted synthetic and privacy validation.

Commit `873ea0d` binds the staged manifest to the Git index, expands the
public-data check to tenant root links, and rejects invalid and non-finite
scenarios without echoing their data. The 48 focused tests passed and the
standard fictional output kept its SHA-256 at seed `20261117`. P0.4 tracks
the outstanding provider acceptance from P1.4 and P7.5 in its checklist.

## Repository reconciliation on 24 November 2026

The same chat and source worktree carry this Conductor reconciliation on
`codex/icu-reconcile-conductor`. The scope is source records, GitHub issue
and branch disposition, and the source manifest. The next operation is
hosted validation of the reconciliation commit.

At `a5fa2fa` all nine local worktrees were clean. The dedicated repository
had 51 merged pull requests, six closed pull requests and no open pull
requests. Both the synthetic and privacy workflows passed after PR #58.
[Synthetic run](https://github.com/edithatogo/icu-liaison-evaluation/actions/runs/45360450060) ·
[Privacy run](https://github.com/edithatogo/icu-liaison-evaluation/actions/runs/45360450058)

- Of the 40 local branch tips besides `main`, 32 were reachable from `main`
  and four had patch-equivalent commits already integrated through PRs #15,
  #17, #23 and #24. The Dapane pin branch's additional hosted P9 verification
  is recorded in [P1](../P1-provider-reuse/plan.md#corrected-rust-1991-candidate).
- PR #43's privacy workflow matched the merged source exactly. The detached
  public-data branch's changes were carried by `c8a85b4` and the later P0
  staged-manifest and privacy checks.
- The two Dapane runner branches contain one-time qualification workflows.
  Their scoped native results are recorded separately in PRs #23 and #24.
  Keep the runner checkouts with their evidence and ownership.
- GitHub's only open issue was Renovate's Dependency Dashboard. It tracks
  workflow dependency proposals and a scheduled Kairos update.
  [Dependency Dashboard](https://github.com/edithatogo/icu-liaison-evaluation/issues/30)

Conductor now records the admitted P5 Voiage scope, the synthetic P10
lineage checks and the completed repository migration and hosted runs.
The separate review receipt required by P7, broader provider qualification
and CHHHS empirical and governance acceptance remain open.

## Repository reconciliation on 25 November 2026

At `c730eb8`, synthetic and privacy checks passed on `main`. GitHub
showed 66 merged pull requests, seven closed as superseded and none open.
The P5–P10 implementation and review PRs, including the P7 companion, are
integrated, and P11's fictional acceptance is complete.
[Merged PRs](https://github.com/edithatogo/icu-liaison-evaluation/pulls?q=is%3Apr+is%3Amerged) ·
[Synthetic run](https://github.com/edithatogo/icu-liaison-evaluation/actions/runs/45426382962) ·
[Privacy run](https://github.com/edithatogo/icu-liaison-evaluation/actions/runs/45426382984)

- PRs #15, #17, #23 and #24 carry the scoped Dapane changes. The extra P9
  verification on the Dapane candidate is historical and the later P9 and P10
  PRs carry the current contracts. The one-time Dapane runner commits and
  checkout material were preserved locally for recovery. The published
  qualification is recorded in [P1](../P1-provider-reuse/plan.md#linux-and-windows-x86-64-qualification).
- PRs #29, #31, #34, #38 and #43 cover Renovate, the qualified quality hooks,
  current GitHub Actions pins, hosted privacy scans and the egress audit. The closed
  StepSecurity branches propose duplicate hooks. The earlier public-data
  boundary commit is superseded by `c8a85b4` and `873ea0d`.
- GitHub issue #30 is the standing Renovate dashboard. The
  [P11 dependency record](../P11-scenario-workflows/handoff.md#dependency-reconciliation-on-25-november-2026)
  identifies compatible updates and the remaining version constraints.

P7 tracks the independent review receipt for the original receiving revision.
The other evidence-dependent work includes governed CHHHS episode linkage,
staffing and paid costs, clinical and Finance review, and the remaining
provider and evidence admission checks in P1, P3, P6 and P8.
