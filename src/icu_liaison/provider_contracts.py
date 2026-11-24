"""Exact source/version gating for optional Dapane/Voiage native consumers.

A version match is necessary, but not sufficient, for installed-provider
qualification: the executing wheel, interpreter, numeric oracle and ABI must
also be recorded by the operational qualification tool.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Callable


def load_provider_lock(path: str | Path) -> dict:
    return parse_provider_lock(Path(path).read_bytes())


def parse_provider_lock(contents: bytes) -> dict:
    """Validate the same lock bytes that will be identified in the receipt."""
    data = json.loads(contents)
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('unsupported or incomplete provider source lock')
    providers = data.get('providers')
    if not isinstance(providers, dict) or set(providers) != {'dapane', 'voiage'}:
        raise ValueError('unsupported or incomplete provider source lock')
    for name, item in providers.items():
        if not isinstance(item, dict) or item.get('distribution') != name or not isinstance(item.get('version'), str):
            raise ValueError(f'{name}: invalid distribution/version')
        commit = item.get('source_commit' if name == 'dapane' else 'tag_commit')
        if not isinstance(commit, str) or len(commit) != 40 or any(c not in '0123456789abcdef' for c in commit):
            raise ValueError(f'{name}: invalid immutable commit')
    return data


def require_provider_python(python_version: tuple[int, int, int]) -> None:
    if not (3, 15, 2) <= python_version < (3, 16, 0):
        raise RuntimeError('Provider qualification requires Python 3.15.2 through 3.15.x')


def qualify_runtime_versions(
    lock: dict, installed_version: Callable[[str], str | None],
    python_version: tuple[int, int, int],
) -> dict:
    """Fail closed on incompatible interpreter or distribution versions.

    This does not claim native numerical validation. Pass the separately executed
    provider oracles after this compatibility check.
    """
    require_provider_python(python_version)
    checked = {}
    for name, entry in lock['providers'].items():
        actual = installed_version(entry['distribution'])
        if actual != entry['version']:
            raise RuntimeError(f'{name}: expected distribution {entry["version"]}, got {actual!r}')
        checked[name] = {'distribution': name, 'version': actual}
    return {'status': 'candidate_environment_compatible', 'installed_versions': checked}
