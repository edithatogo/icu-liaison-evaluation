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
- [!] Complete hosted CI before integration. Initial push/PR runs and merge
  run `44434804695` were blocked before any job step by account
  billing/spending-limit availability. See
  [hosted receipt](../../../verification/hosted-ci-2026-11-19.json).
- [x] Implement local CI/CD runner (`tools/run_local_ci.py`), `.pre-commit-config.yaml`,
  and active `.githooks/` (`pre-commit`, `pre-merge-commit`, `pre-push`) in an
  isolated Python 3.13 environment (`verification/p0-local-ci-2026-11-19.json`).
- [x] Register and check out Conductor at the reviewed SHA as a Git submodule
  (`7a5c560a4fdf5297be58594cc37527eb12790272`).
- [~] Qualify the installed Gemini extension commands and permissions: static
  SHA-256 parity of all 22 runtime, command, and `ask_user`-only policy files
  passed (`verification/p0-gemini-conductor-audit-2026-11-19.json`), while
  `autoUpdate: true` on the user `github-release` install and live interactive
  Gemini CLI slash-command execution remain open.
- [ ] Run exact installed Dapane 0.1/Python and Voiage 3.1/Python 3.15.2
  consumers with independent numerical oracles and dependency lockfiles.
- [ ] Open and complete a tested PR in the dedicated repository; independently
  verify acceptance and only then retire CareOps Sim PR #215.

P0.4 pending does not block portable source tests. Completion of P0 cannot
be claimed until target-repo and provider acceptance are obtained.
