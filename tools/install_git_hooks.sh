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

PY="$ROOT/.venv/bin/python"
expected_version="$(cat .python-version)"
if [[ -x "$PY" && "$("$PY" --version)" == "Python $expected_version" ]]; then
  printf 'Ready: %s (Python %s)\n' "$PY" "$expected_version"
else
  printf 'Set up %s with Python %s using README.md before committing.\n' "$PY" "$expected_version"
fi
