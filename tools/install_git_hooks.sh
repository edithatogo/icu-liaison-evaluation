#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "ERROR: Run inside the icu-liaison-evaluation Git repository." >&2
  exit 2
fi

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

for hook in pre-commit pre-merge-commit pre-push; do
  path=".githooks/$hook"
  if [[ ! -f "$path" || ! -x "$path" ]]; then
    echo "ERROR: Hook missing or not executable: $path" >&2
    exit 3
  fi
done

git config --local core.hooksPath .githooks
printf 'Configured local core.hooksPath=%s\n' "$(git config --local core.hooksPath)"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  printf 'Ready: %s (%s)\n' "$ROOT/.venv/bin/python" "$("$ROOT/.venv/bin/python" --version)"
else
  printf 'WARNING: %s not found. Create it before committing:\n' "$ROOT/.venv/bin/python"
  printf "  uv venv --python 3.13 .venv && uv pip install --python .venv/bin/python -c requirements-ci.txt '.[test,report]'\n"
fi
