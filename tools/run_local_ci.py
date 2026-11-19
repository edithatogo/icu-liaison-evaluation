"""Run local CI/CD validation mirroring .github/workflows/ci.yml and AGENTS.md."""
from __future__ import annotations

import argparse
from collections.abc import Iterable
from datetime import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Literal

FORBIDDEN_SUFFIXES = frozenset({".xlsx", ".xlsm", ".parquet", ".npz"})
FORBIDDEN_PREFIXES = ("private/", "outputs/", "results/")
FORBIDDEN_BASENAMES = frozenset({".env"})

Mode = Literal["pre-commit", "full", "manifest-only"]


def find_forbidden_paths(paths: Iterable[str]) -> list[str]:
    """Return sorted paths violating privacy, data-output, or secret file exclusions."""
    violations: list[str] = []
    for raw in paths:
        norm = raw.replace("\\", "/")
        while norm.startswith("./"):
            norm = norm[2:]
        norm = norm.lstrip("/")
        if not norm:
            continue
        basename = Path(norm).name
        suffix = Path(norm).suffix.lower()
        if (
            norm.startswith(FORBIDDEN_PREFIXES)
            or suffix in FORBIDDEN_SUFFIXES
            or basename in FORBIDDEN_BASENAMES
            or basename.startswith(".env.")
        ):
            violations.append(norm)
    return sorted(set(violations))


def _git_paths(root: Path, *args: str) -> list[str]:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def staged_paths(root: Path) -> list[str]:
    """List staged files scheduled for commit/merge."""
    return _git_paths(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR")


def tracked_paths(root: Path) -> list[str]:
    """List files tracked by Git in the repository index."""
    return _git_paths(root, "ls-files")


def _git_branch(root: Path) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def _python_version_tuple(python_exe: str) -> tuple[str, tuple[int, int, int]]:
    proc = subprocess.run(
        [python_exe, "-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Could not inspect Python executable {python_exe}: {proc.stderr.strip()}")
    version_str = proc.stdout.strip()
    parts = tuple(int(x) for x in version_str.split(".")[:3])
    if len(parts) != 3:
        raise RuntimeError(f"Unexpected Python version string: {version_str}")
    return version_str, parts


def build_steps(root: Path, python_exe: str, mode: Mode) -> list[dict]:
    """Construct the ordered CI step descriptors for the requested mode."""
    manifest_step = {
        "name": "verify_source_manifest",
        "command": [python_exe, str(root / "tools/verify_source_manifest.py")],
        "pythonpath_src": False,
        "validator": "manifest",
    }
    if mode == "manifest-only":
        return [manifest_step]

    pre_commit_steps = [
        manifest_step,
        {
            "name": "pytest",
            "command": [python_exe, "-m", "pytest", "-q"],
            "pythonpath_src": True,
            "validator": "pytest",
        },
        {
            "name": "ci_smoke",
            "command": [python_exe, str(root / "tools/ci_smoke.py")],
            "pythonpath_src": True,
            "validator": "ci_smoke",
        },
    ]
    if mode == "pre-commit":
        return pre_commit_steps
    if mode != "full":
        raise ValueError(f"Unsupported local CI mode: {mode}")

    return pre_commit_steps + [
        {
            "name": "qualify_current_portable",
            "command": [python_exe, str(root / "tools/qualify_current_portable.py")],
            "pythonpath_src": True,
            "validator": "qualify_current_portable",
        },
        {
            "name": "illustrative_cli",
            "command": [
                python_exe,
                "-m",
                "icu_liaison.cli",
                str(root / "model-inputs/illustrative.json"),
            ],
            "pythonpath_src": True,
            "validator": "illustrative_cli",
        },
    ]


def _validate_step_output(step: dict, stdout: str) -> dict:
    validator = step.get("validator")
    details: dict = {}
    if validator == "manifest":
        parsed = json.loads(stdout)
        if parsed.get("status") != "VERIFIED" or parsed.get("errors"):
            raise ValueError(f"Source manifest not verified: {parsed}")
        details["file_count"] = parsed.get("file_count")
    elif validator == "pytest":
        match = re.search(r"(\d+)\s+passed", stdout)
        if match:
            details["tests_passed"] = int(match.group(1))
    elif validator == "ci_smoke":
        parsed = json.loads(stdout)
        if parsed.get("status") != "synthetic_cli_smoke_passed" or parsed.get("investment_ready") is not False:
            raise ValueError(f"Unexpected ci_smoke payload: {parsed}")
        details["investment_ready"] = parsed["investment_ready"]
    elif validator == "qualify_current_portable":
        parsed = json.loads(stdout)
        if (
            parsed.get("status") != "SOURCE_ORACLES_PASSED_SYNTHETIC_ONLY"
            or parsed.get("investment_ready") is not False
        ):
            raise ValueError(f"Unexpected qualify_current_portable payload: {parsed}")
        details["draws_checked"] = parsed.get("p4_independent_accounting", {}).get("draws_checked")
        details["investment_ready"] = parsed["investment_ready"]
    elif validator == "illustrative_cli":
        parsed = json.loads(stdout)
        digest = parsed.get("input_digest_sha256")
        if (
            parsed.get("schema_version") != 1
            or not isinstance(parsed.get("seed"), int)
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or parsed.get("result_class") != "illustrative_not_chhhs_observed"
        ):
            raise ValueError("illustrative_cli output missed required provenance or result_class fields")
        details["seed"] = parsed["seed"]
        details["input_digest_sha256"] = digest
        details["result_class"] = parsed["result_class"]
    return details


def run_gitleaks_staged(root: Path, *, gitleaks_bin: str | None = None) -> tuple[int, dict]:
    """Run gitleaks staged-changes secret scan, failing closed if missing or leaks found."""
    exe = gitleaks_bin or shutil.which("gitleaks")
    if exe is None:
        return 2, {
            "name": "gitleaks_staged",
            "status": "missing_binary",
            "exit_code": 2,
            "error": "gitleaks binary not found on PATH",
        }
    started = time.monotonic()
    proc = subprocess.run(
        [exe, "protect", "--staged", "--no-banner", "--redact"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    elapsed = round(time.monotonic() - started, 3)
    if proc.returncode == 0:
        return 0, {
            "name": "gitleaks_staged",
            "status": "passed",
            "exit_code": 0,
            "elapsed_seconds": elapsed,
        }
    record: dict = {
        "name": "gitleaks_staged",
        "status": "failed",
        "exit_code": proc.returncode,
        "elapsed_seconds": elapsed,
    }
    if proc.stderr.strip():
        record["stderr"] = proc.stderr.strip()
    if proc.stdout.strip():
        record["stdout"] = proc.stdout.strip()
    return proc.returncode, record


def run_local_ci(
    root: Path,
    *,
    mode: Mode = "full",
    check_staged: bool = False,
    check_gitleaks: bool = False,
    python_exe: str | None = None,
    quiet: bool = False,
) -> tuple[int, dict]:
    """Execute forbidden-path checks and local CI steps; return (exit_code, summary)."""
    repo_root = Path(root).resolve()
    exe = python_exe or sys.executable
    py_ver_str, py_ver_tuple = _python_version_tuple(exe)
    if py_ver_tuple < (3, 13, 0):
        raise RuntimeError(f"Python >=3.13 is required for local CI; observed {py_ver_str}")

    tracked_bad = find_forbidden_paths(tracked_paths(repo_root))
    staged_bad = find_forbidden_paths(staged_paths(repo_root)) if check_staged else []
    forbidden = sorted(set(tracked_bad) | set(staged_bad))

    summary: dict = {
        "schema_version": 1,
        "date": datetime.now().astimezone().date().isoformat(),
        "scope": "local_synthetic_ci_not_hosted_or_native",
        "mode": mode,
        "python": py_ver_str,
        "git_branch": _git_branch(repo_root),
        "check_staged": check_staged,
        "check_gitleaks": check_gitleaks,
        "forbidden_paths": forbidden,
        "hosted_ci_executed": False,
        "native_providers_executed": False,
        "investment_ready": False,
        "steps": [],
    }

    if forbidden:
        summary["status"] = "FORBIDDEN_PATHS_REJECTED"
        if not quiet:
            print(f"[local-ci] FAIL: forbidden paths detected: {', '.join(forbidden)}", file=sys.stderr)
        return 2, summary

    if check_gitleaks:
        if not quiet:
            print("[local-ci] Running gitleaks_staged...", file=sys.stderr)
        gl_code, gl_record = run_gitleaks_staged(repo_root)
        summary["steps"].append(gl_record)
        if gl_code != 0:
            summary["status"] = "LOCAL_CI_FAILED"
            if not quiet:
                detail = gl_record.get("error") or gl_record.get("stderr") or gl_record.get("stdout") or ""
                print(f"[local-ci] FAIL gitleaks_staged (exit {gl_code}): {detail}", file=sys.stderr)
            return gl_code, summary
        if not quiet:
            print(f"[local-ci] PASS gitleaks_staged ({gl_record['elapsed_seconds']:.2f}s)", file=sys.stderr)

    steps = build_steps(repo_root, exe, mode)
    for step in steps:
        env = dict(os.environ)
        if step["pythonpath_src"]:
            src_dir = str(repo_root / "src")
            existing = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{existing}" if existing else src_dir

        if not quiet:
            print(f"[local-ci] Running {step['name']}...", file=sys.stderr)
        started = time.monotonic()
        proc = subprocess.run(
            step["command"],
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
        elapsed = round(time.monotonic() - started, 3)

        step_record: dict = {
            "name": step["name"],
            "exit_code": proc.returncode,
            "elapsed_seconds": elapsed,
        }
        if proc.returncode != 0:
            step_record["status"] = "failed"
            summary["steps"].append(step_record)
            summary["status"] = "LOCAL_CI_FAILED"
            if not quiet:
                if proc.stdout.strip():
                    print(proc.stdout.strip(), file=sys.stderr)
                if proc.stderr.strip():
                    print(proc.stderr.strip(), file=sys.stderr)
                if step["name"] == "verify_source_manifest" and mode == "pre-commit":
                    print(
                        "Hint: Run: .venv/bin/python tools/verify_source_manifest.py --write && git add SOURCE_MANIFEST.json",
                        file=sys.stderr,
                    )
            return 1, summary

        try:
            details = _validate_step_output(step, proc.stdout)
        except (ValueError, json.JSONDecodeError) as exc:
            step_record["status"] = "validation_failed"
            step_record["error"] = str(exc)
            summary["steps"].append(step_record)
            summary["status"] = "LOCAL_CI_FAILED"
            if not quiet:
                print(f"[local-ci] Output validation failed in {step['name']}: {exc}", file=sys.stderr)
            return 1, summary

        step_record["status"] = "passed"
        if details:
            step_record["details"] = details
        summary["steps"].append(step_record)
        if not quiet:
            print(f"[local-ci] PASS {step['name']} ({elapsed:.2f}s)", file=sys.stderr)

    summary["status"] = "LOCAL_CI_PASSED_SYNTHETIC_ONLY"
    return 0, summary


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("pre-commit", "full", "manifest-only"),
        default="full",
    )
    parser.add_argument("--check-staged", action="store_true")
    parser.add_argument("--gitleaks", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--write-receipt", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        code, summary = run_local_ci(
            root,
            mode=args.mode,
            check_staged=args.check_staged,
            check_gitleaks=args.gitleaks,
            quiet=args.json_output,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        err = {
            "schema_version": 1,
            "status": "LOCAL_CI_ERROR",
            "reason": str(exc),
            "investment_ready": False,
        }
        print(json.dumps(err, indent=2, sort_keys=True), file=sys.stderr)
        return 2

    payload = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if args.write_receipt is not None and code == 0:
        args.write_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.write_receipt.write_text(payload, encoding="utf-8")

    if args.json_output:
        sys.stdout.write(payload)
    elif code == 0:
        print(
            f"[local-ci] {summary['status']} (mode={summary['mode']}, "
            f"steps={len(summary['steps'])}, investment_ready={summary['investment_ready']})"
        )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
