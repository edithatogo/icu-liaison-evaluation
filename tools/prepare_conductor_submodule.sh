#!/usr/bin/env bash
# Run in the future, explicitly provided dedicated Git repository only.
set -euo pipefail
PIN=7a5c560a4fdf5297be58594cc37527eb12790272
URL=https://github.com/gemini-cli-extensions/conductor.git
if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo 'A dedicated Git repository must be provided before installing Conductor.' >&2
  exit 2
fi
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
if ! git ls-files --error-unmatch .gitmodules >/dev/null 2>&1 || \
   ! git ls-files --stage extensions/conductor | grep -q '^160000 '; then
  if test -e extensions/conductor; then
    echo 'Existing Conductor path needs manual source reconciliation.' >&2
    exit 3
  fi
  git submodule add "$URL" extensions/conductor
fi
git submodule update --init -- extensions/conductor
git -C extensions/conductor fetch --no-tags origin "$PIN"
git -C extensions/conductor checkout --detach "$PIN"
ACTUAL="$(git -C extensions/conductor rev-parse HEAD)"
if [[ "$ACTUAL" != "$PIN" ]]; then
  echo "Conductor pin mismatch: $ACTUAL" >&2
  exit 4
fi
git add .gitmodules extensions/conductor
printf 'Pinned Conductor submodule staged: %s\n' "$ACTUAL"
printf 'Review scripts and permissions; then explicitly install via Gemini CLI.\n'
