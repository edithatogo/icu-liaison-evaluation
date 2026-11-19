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
7. Reconcile the track's plan and metadata against actual evidence. Retain
   historical receipts without changing their claimed runtime or test results.

## Source verification

```sh
python -m pip install -c requirements-ci.txt '.[test,report]'
python tools/verify_source_manifest.py
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python tools/ci_smoke.py
```

The smoke run uses temporary synthetic outputs and requires both site-ready
and provider-qualified admission to fail with exit 2. These expected rejections
are part of acceptance, not failures to be bypassed.

## Local CI/CD and Git hooks

When hosted Actions runners are unavailable or before pushing changes, install the
versioned Git hooks (`pre-commit`, `pre-merge-commit`, `pre-push`) and run the
local synthetic CI suite inside the isolated Python 3.13 environment:

```sh
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -c requirements-ci.txt '.[test,report]'
bash tools/install_git_hooks.sh
.venv/bin/python tools/run_local_ci.py --mode full
```

`.pre-commit-config.yaml` mirrors the same `tools/run_local_ci.py` entrypoints
(`--mode pre-commit --check-staged` on `pre-commit` and `--mode full` on
`pre-push`). Local CI enforces forbidden-path checks, `SOURCE_MANIFEST.json`
integrity, `pytest`, `tools/ci_smoke.py`, `tools/qualify_current_portable.py`,
and `icu_liaison.cli` output contracts. Passing local CI does not close hosted,
native-provider, empirical, or governance gates.

## Evidence and release boundaries

Source CI does not close native, empirical or governance gates. Candidate data
receipts require the separately authorised owners' review. All real data stay
outside tracked fixtures. A successful repository import does not retire the
exploratory CareOps Sim PR #215; that requires its own exact source comparison
and independent migration acceptance.
