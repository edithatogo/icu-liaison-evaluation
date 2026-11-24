# Workflow

1. Read `AGENTS.md`, this index and the full directory for the selected track.
   Both P7 histories are retained; identify them by directory, not just number.
2. Inspect the current branch, working tree and active ownership. Keep changes
   scoped to one accepted task and preserve upstream provider boundaries.
3. Record the task as in progress. Use registered placeholders for missing
   local evidence; do not manufacture approvals, native receipts or observations.
4. Implement and run the smallest relevant checks, then the full source suite
   when merging changes across tracks. Update schemas, context and receipts
   when the changed contract requires it.
5. Regenerate `SOURCE_MANIFEST.json` after reviewing intended source changes.
   Its separately pinned submodule entry must match the staged/committed gitlink.
6. Review the final diff and open a scoped PR. Check the exact PR head's hosted
   results before integration. Record any unavailable qualification separately.
7. Confirm the GitHub merge and fast-forward the clean local `main`. Reconcile
   worktree and branch tips against the merged source. Record whether residual
   changes were integrated, superseded or retained for a separate scope.
8. Reconcile the track's plan and metadata against actual evidence. Close
   GitHub issues when their requested work has verified completion, and record
   the evidence still needed for open items. Retain historical receipts with
   their original runtime and test results.

## Source verification

Use the [README setup](../README.md#tested-basic-workflow) to create `.venv`
from `.python-version`, verify the actual patch and install the pinned
runtime and build dependencies.

```sh
.venv/bin/python tools/verify_source_manifest.py
PYTHONPATH=src .venv/bin/python -m pytest -q
PYTHONPATH=src .venv/bin/python tools/ci_smoke.py
```

The smoke run uses temporary synthetic outputs and requires both site-ready
and provider-qualified admission to fail with exit 2. These expected rejections
are part of acceptance, not failures to be bypassed.

## Local CI/CD and Git hooks

Install the versioned Git hooks (`pre-commit`, `pre-merge-commit`, `pre-push`)
and run the local synthetic CI suite with the verified repository interpreter:

```sh
bash tools/install_git_hooks.sh
.venv/bin/python tools/run_local_ci.py --mode full
```

`.pre-commit-config.yaml` mirrors the same `tools/run_local_ci.py` entrypoints
(`--mode pre-commit --check-staged --gitleaks` on `pre-commit` and `--mode full`
on `pre-push`; `.githooks/pre-commit` and `.githooks/pre-merge-commit` also
require `gitleaks protect --staged`). Stage the reviewed source and refreshed manifest together. Commit hooks
verify the manifest against Git's staged blobs and gitlinks. Local CI enforces
forbidden-path checks, `pytest`, `tools/ci_smoke.py`,
`tools/qualify_current_portable.py`, and `icu_liaison.cli` output contracts.
Passing local CI does not close hosted, native-provider, empirical, or
governance gates.

## Evidence and release boundaries

Candidate data receipts require the separately authorised owners' review.
Native, empirical and governance acceptance have their own evidence.
All real data stay outside tracked fixtures. Preserve the comparison and
release decision for the closed exploratory CareOps Sim PR #215.
[Migration disposition](../docs/pr215-migration-comparison.md#source-pr-disposition)
