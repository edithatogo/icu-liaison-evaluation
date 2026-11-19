"""Verify project source hashes and separately pinned Git submodules.

The manifest intentionally excludes itself to avoid a self-referential digest.
No patient data, private configuration or generated caches are admitted.
"""
from __future__ import annotations

import argparse
import configparser
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

EXCLUDED_DIRS = frozenset({".git", ".pytest_cache", "__pycache__", ".venv", "private", "outputs", "results", "dist", "build"})
EXCLUDED_FILES = frozenset({"SOURCE_MANIFEST.json", ".git"})
EXCLUDED_SUFFIXES = frozenset({".pyc", ".xlsx", ".xlsm", ".parquet", ".npz"})
SUBMODULE_URLS = {
    "extensions/conductor": "https://github.com/gemini-cli-extensions/conductor.git",
}


def source_files(root: Path, *, submodule_paths: frozenset[str] = frozenset()) -> dict[str, str]:
    """Hash project files, excluding build metadata and explicit dependency trees."""
    result = {}
    for directory, dirs, filenames in os.walk(root, followlinks=False):
        current = Path(directory)
        dirs[:] = sorted(
            name for name in dirs
            if name not in EXCLUDED_DIRS
            and not name.endswith('.egg-info')
            and (current / name).relative_to(root).as_posix() not in submodule_paths
        )
        for name in sorted(filenames):
            path = current / name
            if path.is_symlink() or name in EXCLUDED_FILES or path.suffix in EXCLUDED_SUFFIXES:
                continue
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _submodule_paths(manifest: dict) -> frozenset[str]:
    pins = manifest.get('git_submodules', {})
    if not isinstance(pins, dict):
        return frozenset()
    # A manifest entry cannot hide an arbitrary project directory from hashing.
    return frozenset(path for path in pins if path in SUBMODULE_URLS)


def verify_git_submodules(root: Path, manifest: dict) -> list[str]:
    """Check declared path/URL and the Git index's exact mode and commit.

    A normal clone need not initialise the dependency to verify its gitlink.
    Installed Gemini commands and native providers are separate acceptance gates.
    """
    pins = manifest.get('git_submodules', {})
    if not isinstance(pins, dict):
        return ['git_submodules must be an object']
    problems = []
    for path, sha in pins.items():
        if path not in SUBMODULE_URLS:
            problems.append(f'unexpected submodule path: {path}')
        if not isinstance(sha, str) or re.fullmatch(r'[0-9a-f]{40}', sha) is None:
            problems.append(f'invalid submodule commit: {path}')
    modules_file = root / '.gitmodules'
    if not modules_file.exists():
        return problems + (['missing .gitmodules for pinned dependencies'] if pins else [])
    if modules_file.is_symlink():
        return problems + ['.gitmodules must be a regular project file']
    config = configparser.ConfigParser(interpolation=None)
    try:
        config.read_string(modules_file.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, configparser.Error):
        return problems + ['invalid .gitmodules']
    declared = {}
    if config.defaults():
        problems.append('unexpected .gitmodules defaults')
    for section in config.sections():
        if re.fullmatch(r'submodule "[^"\n]+"', section) is None:
            problems.append('invalid .gitmodules section')
            continue
        path = config.get(section, 'path', fallback='')
        url = config.get(section, 'url', fallback='')
        if path in declared:
            problems.append(f'duplicate submodule path: {path}')
        declared[path] = url
    if set(declared) != set(pins):
        problems.append('.gitmodules paths do not match manifest pins')
    for path, url in declared.items():
        if path not in SUBMODULE_URLS or url != SUBMODULE_URLS[path]:
            problems.append(f'unexpected submodule URL or path: {path}')
    if not pins or problems:
        return problems
    try:
        top = subprocess.run(
            ['git', '-C', str(root), 'rev-parse', '--show-toplevel'],
            capture_output=True, text=True, check=False, timeout=10,
        )
        if top.returncode != 0 or Path(top.stdout.strip()).resolve() != root.resolve():
            return ['pinned dependencies require this project Git index']
        for path, sha in pins.items():
            entry = subprocess.run(
                ['git', '-C', str(root), 'ls-files', '--stage', '--', path],
                capture_output=True, text=True, check=False, timeout=10,
            )
            expected = f'160000 {sha} 0\t{path}'
            if entry.returncode != 0 or entry.stdout.strip() != expected:
                problems.append(f'submodule gitlink mode or commit mismatch: {path}')
    except (OSError, subprocess.SubprocessError):
        problems.append('could not verify pinned submodule Git index')
    return problems


def verify_manifest(root: Path, manifest: dict) -> list[str]:
    declared = manifest.get('file_sha256')
    if not isinstance(declared, dict):
        return ['manifest has no file_sha256 object']
    observed = source_files(root, submodule_paths=_submodule_paths(manifest))
    problems = [f'unexpected file: {p}' for p in sorted(observed.keys() - declared.keys())]
    problems += [f'missing file: {p}' for p in sorted(declared.keys() - observed.keys())]
    problems += [f'hash mismatch: {p}' for p in sorted(declared.keys() & observed.keys())
                 if declared[p] != observed[p]]
    return problems + verify_git_submodules(root, manifest)


def main() -> int:
    parser=argparse.ArgumentParser(description='Exact project source and dependency inventory')
    parser.add_argument('--write',action='store_true',help='Regenerate after reviewing the diff')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    manifest_path=root/'SOURCE_MANIFEST.json'
    doc=json.loads(manifest_path.read_text())
    if args.write:
        doc['file_sha256']=source_files(root, submodule_paths=_submodule_paths(doc))
        manifest_path.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n')
    errors=verify_manifest(root,doc)
    print(json.dumps({'status':'VERIFIED' if not errors else 'FAILED',
                      'file_count':len(doc['file_sha256']), 'errors':errors},sort_keys=True))
    return 0 if not errors else 1


if __name__=='__main__':
    raise SystemExit(main())
