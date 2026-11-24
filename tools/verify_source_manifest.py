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
from pathlib import Path, PurePosixPath
import re
import subprocess

EXCLUDED_DIRS = frozenset({".git", ".local", ".pytest_cache", ".snakemake", "__pycache__", ".venv", "private", "outputs", "results", "dist", "build"})
EXCLUDED_FILES = frozenset({"SOURCE_MANIFEST.json", ".git"})
EXCLUDED_SUFFIXES = frozenset({".pyc", ".xlsx", ".xlsm", ".parquet", ".npz"})
SUBMODULE_URLS = {
    "extensions/conductor": "https://github.com/gemini-cli-extensions/conductor.git",
}


def _excluded_dir(name: str) -> bool:
    return name in EXCLUDED_DIRS or name.endswith('.egg-info')


def _excluded_file(path: Path | PurePosixPath) -> bool:
    return path.name in EXCLUDED_FILES or path.suffix in EXCLUDED_SUFFIXES


def source_files(root: Path, *, submodule_paths: frozenset[str] = frozenset()) -> dict[str, str]:
    """Hash project files, excluding build metadata and explicit dependency trees."""
    result = {}
    for directory, dirs, filenames in os.walk(root, followlinks=False):
        current = Path(directory)
        dirs[:] = sorted(
            name for name in dirs
            if not _excluded_dir(name)
            and (current / name).relative_to(root).as_posix() not in submodule_paths
        )
        for name in sorted(filenames):
            path = current / name
            if path.is_symlink() or _excluded_file(path):
                continue
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _submodule_paths(manifest: dict) -> frozenset[str]:
    pins = manifest.get('git_submodules', {})
    if not isinstance(pins, dict):
        return frozenset()
    # A manifest entry cannot hide an arbitrary project directory from hashing.
    return frozenset(path for path in pins if path in SUBMODULE_URLS)


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ['git', '-C', str(root), *args], capture_output=True, check=True, timeout=10,
    ).stdout


def _index_entries(root: Path) -> dict[str, tuple[str, str]]:
    top = Path(os.fsdecode(_git(root, 'rev-parse', '--show-toplevel').rstrip(b'\n')))
    if top.resolve() != root.resolve():
        raise ValueError('source verification requires this project Git index')
    entries = {}
    for raw in _git(root, 'ls-files', '--stage', '-z').split(b'\0')[:-1]:
        metadata, name = raw.split(b'\t', 1)
        mode, oid, stage = metadata.decode('ascii').split()
        if stage != '0':
            raise ValueError('resolve the unmerged Git index before verifying source')
        entries[os.fsdecode(name)] = (mode, oid)
    return entries


def verify_git_submodules(
    root: Path, manifest: dict, *, staged: dict[str, tuple[str, str]] | None = None,
) -> list[str]:
    """Check declared path/URL and the Git index's exact mode and commit.

    A normal clone need not initialise the dependency to verify its gitlink.
    Installed agent plugins and native providers require runtime verification.
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
    entry = staged.get('.gitmodules') if staged is not None else None
    exists = entry is not None if staged is not None else modules_file.exists()
    if not exists:
        return problems + (['missing .gitmodules for pinned dependencies'] if pins else [])
    regular = entry[0] in {'100644', '100755'} if entry else not modules_file.is_symlink()
    if not regular:
        return problems + ['.gitmodules must be a regular project file']
    config = configparser.ConfigParser(interpolation=None)
    try:
        data = _git(root, 'cat-file', 'blob', entry[1]) if entry else modules_file.read_bytes()
        config.read_string(data.decode('utf-8'))
    except (OSError, UnicodeError, configparser.Error, subprocess.SubprocessError):
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
        entries = staged if staged is not None else _index_entries(root)
    except (OSError, ValueError, subprocess.SubprocessError):
        return ['could not verify pinned submodule Git index']
    for path, sha in pins.items():
        if entries.get(path) != ('160000', sha):
            problems.append(f'submodule gitlink mode or commit mismatch: {path}')
    return problems


def _inventory_errors(manifest: dict, observed: dict[str, str]) -> list[str]:
    declared = manifest.get('file_sha256')
    if not isinstance(declared, dict):
        return ['manifest has no file_sha256 object']
    problems = [f'unexpected file: {p}' for p in sorted(observed.keys() - declared.keys())]
    problems += [f'missing file: {p}' for p in sorted(declared.keys() - observed.keys())]
    problems += [f'hash mismatch: {p}' for p in sorted(declared.keys() & observed.keys())
                 if declared[p] != observed[p]]
    return problems


def verify_manifest(root: Path, manifest: dict) -> list[str]:
    observed = source_files(root, submodule_paths=_submodule_paths(manifest))
    return _inventory_errors(manifest, observed) + verify_git_submodules(root, manifest)


def verify_staged_manifest(root: Path) -> tuple[int, list[str]]:
    """Bind the staged manifest to the exact index blobs and gitlinks."""
    entries = _index_entries(root)
    manifest = entries.get('SOURCE_MANIFEST.json')
    if manifest is None or manifest[0] not in {'100644', '100755'}:
        return 0, ['stage SOURCE_MANIFEST.json as a regular file']
    doc = json.loads(_git(root, 'cat-file', 'blob', manifest[1]))
    if not isinstance(doc, dict):
        return 0, ['staged source manifest must be an object']
    observed = {}
    for name, (mode, oid) in entries.items():
        path = PurePosixPath(name)
        if mode == '160000' or _excluded_file(path) or any(_excluded_dir(part) for part in path.parts[:-1]):
            continue
        if mode not in {'100644', '100755'}:
            return 0, ['staged source inventory requires regular files']
        observed[name] = hashlib.sha256(_git(root, 'cat-file', 'blob', oid)).hexdigest()
    errors = _inventory_errors(doc, observed) + verify_git_submodules(root, doc, staged=entries)
    gitlinks = {name for name, (mode, _) in entries.items() if mode == '160000'}
    if gitlinks != _submodule_paths(doc):
        errors.append('staged Git links do not match the manifest paths')
    return len(observed), errors


def main() -> int:
    parser = argparse.ArgumentParser(description='Exact project source and dependency inventory')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--write', action='store_true', help='Regenerate after reviewing the diff')
    mode.add_argument('--staged', action='store_true', help='Verify the exact staged source')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.staged:
        try:
            count, errors = verify_staged_manifest(root)
        except (OSError, ValueError, subprocess.SubprocessError):
            count, errors = 0, ['could not verify the source manifest from the Git index']
    else:
        manifest_path = root / 'SOURCE_MANIFEST.json'
        doc = json.loads(manifest_path.read_text())
        if args.write:
            doc['file_sha256'] = source_files(root, submodule_paths=_submodule_paths(doc))
        errors = verify_manifest(root, doc)
        if args.write and not errors:
            manifest_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + '\n')
        inventory = doc.get('file_sha256')
        count = len(inventory) if isinstance(inventory, dict) else 0
    print(json.dumps({'status': 'FAILED' if errors else 'VERIFIED',
                      'file_count': count, 'errors': errors}, sort_keys=True))
    return 1 if errors else 0


if __name__=='__main__':
    raise SystemExit(main())
