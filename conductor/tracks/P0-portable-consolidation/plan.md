# P0 — bounded portable execution

## P0.1 — Preserve and reconcile the source context
- [x] Identify the inspected draft PR head and preserve its original ownership.
- [x] Locate the preserved workbook and record its exact SHA and Library id.
- [x] Extract the verified public benchmarks and source/denominator cautions.
- [x] Record a consumer-first architecture decision and non-verbatim decisions.

## P0.2 — Replace duplicate numerical infrastructure
- [x] Keep the annual scenario JSON external to code, now with explicit units.
- [x] Use maintained NumPy/SciPy rather than handwritten triangular sampling,
  quantiles or event schedulers.
- [x] Create fail-closed provider adapters to Dapane's exact-quotation contract
  and Voiage's cost-only two-strategy decision array.
- [x] Add red-first independent tests for arithmetic, no effect, negative
  readmission effect, provenance and provider request boundaries.

## P0.3 — Provide reproducible local handoff
- [x] Add local run instructions, Conductor plan, source manifest, migration
  checklist and a Git-compatible pinned Conductor setup script.
- [x] Preserve provider and original PR release/validation limitations.
- [x] Run the portable synthetic test suite and sample CLI for this source.

## P0.4 — Initial private repository import and remaining qualification
- [x] Resolve the user-selected private repository and recover the P8.4 and P7
  placeholder source checkpoints without replacing either branch of work.
- [x] Push the reconciled source on the scoped import branch and open PR #1.
  Imported head: `ea7bdc3b75beb74cfc8f4e27a1257caec0051c5d`; remote tree matches the reviewed local tree.
- [x] Merge PR #1 into `main` (`4644bb4f5c2597cfc5e07cabe4de0b33e9dfb558`) and
  synchronise local `main`.
- [x] Complete hosted CI on the now-public repository: push to `main` (`1c7f640`)
  passed all `Synthetic source validation` steps in run `44444785989`
  ([public hosted receipt](../../../verification/hosted-ci-public-2026-11-19.json));
  initial private-repo account-limit failures remain preserved in the
  [historical hosted receipt](../../../verification/hosted-ci-2026-11-19.json).
- [x] Implement local CI/CD runner (`tools/run_local_ci.py`), `.pre-commit-config.yaml`,
  and active `.githooks/` (`pre-commit`, `pre-merge-commit`, `pre-push`) in an
  isolated Python 3.13 environment (`verification/p0-local-ci-2026-11-19.json`),
  with local `gitleaks protect --staged` hook checks and GitHub public-repo
  Secret Scanning + Push Protection enabled.
- [x] Register and check out Conductor at the reviewed SHA as a Git submodule
  (`7a5c560a4fdf5297be58594cc37527eb12790272`).
- [x] Verify the current Conductor pin in Antigravity. A fresh workspace
  session exposed all six commands and the registry links all 13 plans.
  [P0 handoff](handoff.md)
- [x] Run the live interactive `/conductor-status` check in Antigravity.
  The isolated public workspace prompted for local trust. Plan mode reported
  the registry and left all tracked files unchanged.
  [Interactive check](handoff.md#interactive-status-check-on-24-november-2026)
- [x] Run exact installed Dapane 0.1/Python and Voiage 3.1/Python 3.15.2
  consumers with independent numerical oracles and dependency lockfiles in an
  isolated Python 3.15.2 scratch environment
  ([native receipt](../../../verification/p0-native-providers-py315-2026-11-19.json),
  [lockfile](../../../verification/p0-py315-native-lock-2026-11-19.txt)). Independent
  wheel-provenance adjudication (`providers.lock.json` `binary_sha256`) remains
  open in P1.4/P7. The corrected P5 regression rerun is recorded in P0.5.
- [x] Complete the tested migration and verify that CareOps Sim PR #215 is closed.
  The exact 19-file comparison, central accounting parity and closure are recorded in
  [PR #215 migration comparison](../../../docs/pr215-migration-comparison.md)
  and the [comparison receipt](../../../verification/p0-pr215-migration-comparison-2026-11-19.json).
- [x] Record release acceptance of the verified migration from CareOps Sim
  PR #215 to standalone PR #5. The repository owner gave the release decision
  on 24 November 2026 following the technical verification.
  [Portable source release](../../../docs/pr215-migration-comparison.md#portable-source-release)

- [ ] Record Voiage artifact admission and the broader Dapane release decision.
  These are the remaining P0.4 requirements tracked in
  [P1.4](../P1-provider-reuse/plan.md) and
  [technical P7.5](../P7-technical-empirical-qualification/plan.md#p75-independent-provider-review).

## P0.5 — Python and hosted CI runtime migration

- [x] Pin the repository, builds, local hooks and hosted synthetic validation
  to CPython 3.15.2. Run the full suite and both P5 regressions with the
  P1-pinned Dapane installed and retain hosted evidence. Local portable CI,
  the full suite with Dapane and hosted synthetic CI each passed 342 tests.
  The two focused P5 regressions also passed with Dapane installed.
  [Migration receipt](../../../verification/python-315-migration-2026-11-19.json)
  · [Hosted run](https://github.com/edithatogo/icu-liaison-evaluation/actions/runs/44473577455)

## Review fixes

- [x] Apply the portable consolidation review fixes (`873ea0d`). Verify
  exact staged source hashes, reject tenant links and non-finite results, and
  keep rejected input values out of CLI errors.
