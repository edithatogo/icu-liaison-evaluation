"""Validate the Git index or outgoing commit in an isolated, disposable checkout."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Literal


Stage = Literal["pre-commit", "pre-merge-commit", "pre-push"]


def git(root: Path, *args: str, env: dict[str, str] | None = None) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), *args], env=env)


def run_hook(root: Path, stage: Stage, updates: bytes) -> int:
    python = root / ".venv/bin/python"
    guard = [str(python), str(root / "tools/publication_guard.py")]
    checked = subprocess.run(
        guard + (["--pre-push"] if stage == "pre-push" else []), input=updates, cwd=root,
    )
    if checked.returncode:
        return checked.returncode

    # A commit or merge may supply a temporary index. Read that index in the
    # source checkout, then remove its Git environment for all disposable clones.
    local_keys = set(git(root, "rev-parse", "--local-env-vars").decode().splitlines())
    clean_env = {key: value for key, value in os.environ.items()
                 if key not in local_keys and key not in {"PYTHONPATH", "SKIP"}}
    clean_env["PYTHONDONTWRITEBYTECODE"] = "1"
    patch = b""
    if stage == "pre-push":
        commits = list(dict.fromkeys(
            git(root, "rev-parse", f"{oid}^{{commit}}").decode().strip()
            for line in updates.decode().splitlines() if line.strip()
            for oid in [line.split()[1]] if oid.strip("0")
        ))
    else:
        head = subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", "HEAD"],
                              capture_output=True, text=True)
        commits = [head.stdout.strip() if head.returncode == 0 else ""]
        patch = git(root, "diff", "--cached", "--binary", "--full-index", "--no-ext-diff", "--no-renames", "--")

    for commit in commits:
        with tempfile.TemporaryDirectory(prefix="icu-staged-") as temp:
            shadow = Path(temp) / "source"
            subprocess.run(["git", "clone", "--quiet", "--shared", "--no-checkout",
                            str(root), str(shadow)], env=clean_env, check=True)
            if commit:
                git(shadow, "checkout", "--quiet", "--detach", commit, env=clean_env)
            if patch:
                subprocess.run(["git", "-C", str(shadow), "apply", "--index", "--binary", "-"],
                               input=patch, env=clean_env, check=True)
            for dirname in (".venv", "private/venv-quality", "private/venv-p11"):
                target = root / dirname
                if target.is_dir():
                    link = shadow / dirname
                    link.parent.mkdir(parents=True, exist_ok=True)
                    link.symlink_to(target, target_is_directory=True)
            quality = shadow / "private/venv-quality/bin/python"
            if not quality.is_file():
                print("The repository quality environment is required. See README.md.", file=sys.stderr)
                return 2
            result = subprocess.run(
                [str(quality), "-m", "pre_commit", "run", "--hook-stage", stage, "--all-files"],
                cwd=shadow, env={**clean_env, "PYTHONPATH": str(shadow / "src")},
            )
            if result.returncode:
                return result.returncode
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("pre-commit", "pre-merge-commit", "pre-push"))
    stage: Stage = parser.parse_args().stage
    root = Path(__file__).resolve().parents[1]
    return run_hook(root, stage, sys.stdin.buffer.read() if stage == "pre-push" else b"")


if __name__ == "__main__":
    raise SystemExit(main())
