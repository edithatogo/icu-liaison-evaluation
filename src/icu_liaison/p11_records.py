"""Shared integrity and atomic-publication helpers for synthetic P11 runs."""
from __future__ import annotations
from typing import TypeGuard
from typing import Any

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import uuid


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False,
    ).encode('utf-8')


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('missing or unsafe synthetic input or output')
    return digest_bytes(path.read_bytes())


def digest_json(value: object) -> str:
    return digest_bytes(canonical(value))


def read_json(path: Path) -> dict[str, Any]:
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('missing or unsafe synthetic JSON')
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('synthetic JSON must be an object')
    return value


def inventory(directory: Path, *, exclude: str) -> dict[str, str]:
    result = {}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            raise ValueError('symlinks are not admitted into synthetic output')
        if path.is_file() and path.relative_to(directory).as_posix() != exclude:
            result[path.relative_to(directory).as_posix()] = digest_file(path)
    return result


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w', encoding='utf-8', dir=path.parent,
            prefix=f'.{path.name}.', delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def attempt(root: Path, case_id: str) -> tuple[Path, dict[str, Any]]:
    record = {
        'attempt_id': uuid.uuid4().hex,
        'case_id': case_id,
        'started_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'running',
        'data_class': 'synthetic',
    }
    path = Path(root) / 'attempts' / case_id / f"{record['attempt_id']}.json"
    atomic_json(path, record)
    return path, record


def valid_digest(value: object) -> TypeGuard[str]:
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None
