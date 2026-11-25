"""Audit pinned extensions/conductor submodule against installed Gemini CLI extension."""
from __future__ import annotations
from typing import Any

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tomllib

DEFAULT_IGNORE_NAMES = frozenset({".git", ".gemini-extension-install.json", ".DS_Store"})
NON_RUNTIME_REPO_PACKAGING_FILES = frozenset(
    {
        ".github/workflows/release-please.yml",
        ".gitignore",
        ".release-please-manifest.json",
        "CONTRIBUTING.md",
        "release-please-config.json",
    }
)


def normalize_display_path(path: Path) -> str:
    """Redact user home directory prefix so receipts never leak local usernames."""
    resolved = path.expanduser().resolve()
    home = Path.home().resolve()
    try:
        rel = resolved.relative_to(home)
        return "~" if str(rel) == "." else f"~/{rel.as_posix()}"
    except ValueError:
        return resolved.as_posix()


def _display_pinned_path(pinned_path: Path) -> str:
    repo_root = Path(__file__).resolve().parents[1].resolve()
    resolved = pinned_path.expanduser().resolve()
    try:
        rel = resolved.relative_to(repo_root)
        return "." if str(rel) == "." else rel.as_posix()
    except ValueError:
        return normalize_display_path(pinned_path)


def hash_tree(
    root: Path,
    *,
    ignore_names: frozenset[str] = DEFAULT_IGNORE_NAMES,
) -> dict[str, str]:
    """Return sorted relative-path -> SHA-256 digests under root, rejecting escaping symlinks."""
    root_path = Path(root)
    if not root_path.is_dir():
        raise FileNotFoundError(f"Extension directory not found: {normalize_display_path(root_path)}")
    root_resolved = root_path.resolve()
    digests: dict[str, str] = {}

    for directory, dirs, filenames in os.walk(root_path, followlinks=False):
        current = Path(directory)
        kept_dirs = []
        for name in sorted(dirs):
            if name in ignore_names:
                continue
            candidate = current / name
            if candidate.is_symlink():
                target = candidate.resolve(strict=True)
                if not target.is_relative_to(root_resolved):
                    raise ValueError(
                        f"Symlink escapes extension root: {candidate.relative_to(root_path).as_posix()}"
                    )
                continue
            kept_dirs.append(name)
        dirs[:] = kept_dirs

        for name in sorted(filenames):
            if name in ignore_names:
                continue
            candidate = current / name
            rel = candidate.relative_to(root_path).as_posix()
            if candidate.is_symlink():
                target = candidate.resolve(strict=True)
                if not target.is_relative_to(root_resolved):
                    raise ValueError(f"Symlink escapes extension root: {rel}")
                if not target.is_file():
                    continue
                digests[rel] = hashlib.sha256(target.read_bytes()).hexdigest()
            elif candidate.is_file():
                digests[rel] = hashlib.sha256(candidate.read_bytes()).hexdigest()

    return dict(sorted(digests.items()))


def inspect_policies(extension_root: Path) -> dict[str, Any]:
    """Parse policies/*.toml and flag any rule whose decision is not 'ask_user'."""
    root_path = Path(extension_root)
    policies_dir = root_path / "policies"
    rules: list[dict[str, Any]] = []
    unapproved: list[dict[str, Any]] = []
    policy_files: dict[str, str] = {}

    if policies_dir.is_dir():
        for policy_file in sorted(policies_dir.glob("*.toml")):
            raw = policy_file.read_bytes()
            rel = policy_file.relative_to(root_path).as_posix()
            policy_files[rel] = hashlib.sha256(raw).hexdigest()
            parsed = tomllib.loads(raw.decode("utf-8"))
            for idx, rule in enumerate(parsed.get("rule", [])):
                entry = {
                    "file": rel,
                    "rule_index": idx,
                    "toolName": rule.get("toolName"),
                    "commandPrefix": rule.get("commandPrefix"),
                    "decision": rule.get("decision"),
                    "modes": rule.get("modes"),
                }
                rules.append(entry)
                if entry["decision"] != "ask_user":
                    unapproved.append(entry)

    return {
        "policy_files_sha256": policy_files,
        "rules": rules,
        "unapproved_auto_allow_rules": unapproved,
    }


def _commands_summary(pinned_hashes: dict[str, str], installed_hashes: dict[str, str]) -> dict[str, dict[str, Any]]:
    command_paths = sorted(
        p for p in (set(pinned_hashes) | set(installed_hashes))
        if p.startswith("commands/conductor/") and p.endswith(".toml")
    )
    return {
        Path(p).name: {
            "path": p,
            "pinned_sha256": pinned_hashes.get(p),
            "installed_sha256": installed_hashes.get(p),
            "matches": pinned_hashes.get(p) is not None and pinned_hashes.get(p) == installed_hashes.get(p),
        }
        for p in command_paths
    }


def _read_install_metadata(installed_dir: Path) -> dict[str, Any] | None:
    meta_file = installed_dir / ".gemini-extension-install.json"
    if not meta_file.is_file():
        return None
    raw = json.loads(meta_file.read_text(encoding="utf-8"))
    return {
        "source": raw.get("source"),
        "type": raw.get("type"),
        "releaseTag": raw.get("releaseTag"),
        "autoUpdate": raw.get("autoUpdate"),
    }


def audit_extension(pinned_dir: Path, installed_dir: Path) -> dict[str, Any]:
    """Compare pinned extension tree and policies against installed Gemini extension."""
    pinned_path = Path(pinned_dir)
    installed_path = Path(installed_dir)

    missing_dirs = [
        label
        for label, p in (("pinned_dir", pinned_path), ("installed_dir", installed_path))
        if not p.is_dir()
    ]
    if missing_dirs:
        return {
            "schema_version": 1,
            "status": "AUDIT_MISMATCH",
            "reason": f"Missing extension directory: {', '.join(missing_dirs)}",
            "pinned_dir": _display_pinned_path(pinned_path),
            "installed_dir": normalize_display_path(installed_path),
        }

    pinned_hashes = hash_tree(pinned_path)
    installed_hashes = hash_tree(installed_path)

    pinned_keys = set(pinned_hashes)
    installed_keys = set(installed_hashes)
    missing_all = pinned_keys - installed_keys
    missing_runtime_files = sorted(missing_all - NON_RUNTIME_REPO_PACKAGING_FILES)
    missing_non_runtime_packaging_files = sorted(missing_all & NON_RUNTIME_REPO_PACKAGING_FILES)
    extra_in_installed = sorted(installed_keys - pinned_keys)
    hash_mismatches = sorted(
        k for k in (pinned_keys & installed_keys) if pinned_hashes[k] != installed_hashes[k]
    )
    matched_files_count = sum(
        1 for k in (pinned_keys & installed_keys) if pinned_hashes[k] == installed_hashes[k]
    )

    pinned_policies = inspect_policies(pinned_path)
    installed_policies = inspect_policies(installed_path)
    install_metadata = _read_install_metadata(installed_path)
    auto_update = bool(install_metadata and install_metadata.get("autoUpdate"))
    is_github_release = bool(install_metadata and install_metadata.get("type") == "github-release")

    # GitHub Release tarballs omit repo automation files; other install types require full file parity.
    unacceptable_missing = missing_runtime_files if is_github_release else sorted(missing_all)

    has_parity = (
        not unacceptable_missing
        and not extra_in_installed
        and not hash_mismatches
        and not pinned_policies["unapproved_auto_allow_rules"]
        and not installed_policies["unapproved_auto_allow_rules"]
        and bool(pinned_hashes)
    )
    if has_parity and auto_update:
        status = "PINNED_PARITY_VERIFIED_WITH_AUTOUPDATE_CAVEAT"
    elif has_parity:
        status = "PINNED_PARITY_VERIFIED"
    else:
        status = "AUDIT_MISMATCH"

    return {
        "schema_version": 1,
        "status": status,
        "pinned_dir": _display_pinned_path(pinned_path),
        "installed_dir": normalize_display_path(installed_path),
        "pinned_file_count": len(pinned_hashes),
        "installed_file_count": len(installed_hashes),
        "matched_files_count": matched_files_count,
        "missing_runtime_files": missing_runtime_files,
        "missing_non_runtime_packaging_files": missing_non_runtime_packaging_files,
        "extra_in_installed": extra_in_installed,
        "hash_mismatches": hash_mismatches,
        "install_metadata": install_metadata,
        "autoupdate_caveat": (
            "autoUpdate is enabled in .gemini-extension-install.json; future upstream releases could drift from the pinned submodule commit."
            if auto_update
            else None
        ),
        "commands": _commands_summary(pinned_hashes, installed_hashes),
        "policies": {
            "pinned": pinned_policies,
            "installed": installed_policies,
        },
        "runtime_commands_executed": False,
        "note": "Read-only file/policy parity audit; interactive Gemini slash-command execution remains a manual/runtime check.",
    }


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pinned", type=Path, default=root / "extensions/conductor")
    parser.add_argument(
        "--installed",
        type=Path,
        default=Path.home() / ".gemini/extensions/conductor",
    )
    parser.add_argument("--write-receipt", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = audit_extension(args.pinned, args.installed)
    except (OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "status": "AUDIT_MISMATCH",
                    "reason": str(exc),
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2

    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.write_receipt is not None:
        args.write_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.write_receipt.write_text(payload, encoding="utf-8")
    sys.stdout.write(payload)

    if report["status"] in (
        "PINNED_PARITY_VERIFIED",
        "PINNED_PARITY_VERIFIED_WITH_AUTOUPDATE_CAVEAT",
    ):
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
