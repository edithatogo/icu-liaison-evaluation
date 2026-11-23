#!/usr/bin/env bash
# Retrieve the Conductor revision recorded by the checked-out project.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
SUBMODULE=extensions/conductor
if ! git diff --cached --quiet -- "$SUBMODULE"; then
  echo 'Commit or reconcile the staged Conductor gitlink before preparing its checkout.' >&2
  exit 2
fi
PIN="$(git rev-parse "HEAD:$SUBMODULE")"
if [[ -e "$SUBMODULE/.git" && -n "$(git -C "$SUBMODULE" status --porcelain)" ]]; then
  echo 'Reconcile local Conductor changes before updating the checkout.' >&2
  exit 3
fi
git submodule update --init --checkout -- "$SUBMODULE"
if [[ "$(git -C "$SUBMODULE" rev-parse HEAD)" != "$PIN" ]] ||
   [[ -n "$(git -C "$SUBMODULE" status --porcelain)" ]]; then
  echo 'The Conductor checkout must match the clean, committed gitlink.' >&2
  exit 3
fi
printf 'Conductor checkout matches %s\n' "$PIN"
