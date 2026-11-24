"""Check the public ICU repository's staged or outgoing Git objects."""
from __future__ import annotations

import argparse
from collections.abc import Iterable
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

PRIVATE_DIRECTORIES = frozenset({".local", ".venv", "private", "outputs", "results"})
EXPORT_SUFFIXES = frozenset({
    ".age", ".arrow", ".db", ".docx", ".dta", ".duckdb", ".feather", ".jsonl",
    ".ndjson", ".npy", ".npz", ".parquet", ".pdf", ".pickle", ".pkl", ".pptx",
    ".rda", ".rds", ".sas7bdat", ".sav", ".sqlite", ".sqlite3", ".tar", ".tsv",
    ".xls", ".xlsb", ".xlsm", ".xlsx", ".zip", ".7z", ".gz",
})

# Frozen fictional fixture bytes, independent of the general source manifest.
# The public manifest's regeneration cannot approve another dataset.
CSV_SHA256 = {
    "model-inputs/placeholders/p3-synthetic/cost_lines.csv": "1a50b38e6cd52c315ba9f93e43d6b20552ac2384288846b8f14238d510511ee6",
    "model-inputs/placeholders/p3-synthetic/episodes.csv": "d821175ddc6d3b6ea912c9dd7e811788bfa27df2a024ba16a0b4d47dee45d8e5",
    "model-inputs/placeholders/p3-synthetic/followup.csv": "3f7603fee21d0d7e2197429922ab140217820e918e3389172d6c72b568e95094",
    "model-inputs/placeholders/p3-synthetic/liaison_contacts.csv": "27ebb4cf11f3b3c16d251dd0cbeaf6226e017cef875f59f1e23921ed056fa907",
    "tests/fixtures/p3_episodes/cost_lines.csv": "1a50b38e6cd52c315ba9f93e43d6b20552ac2384288846b8f14238d510511ee6",
    "tests/fixtures/p3_episodes/episodes.csv": "d821175ddc6d3b6ea912c9dd7e811788bfa27df2a024ba16a0b4d47dee45d8e5",
    "tests/fixtures/p3_episodes/followup.csv": "3f7603fee21d0d7e2197429922ab140217820e918e3389172d6c72b568e95094",
    "tests/fixtures/p3_episodes/liaison_contacts.csv": "27ebb4cf11f3b3c16d251dd0cbeaf6226e017cef875f59f1e23921ed056fa907",
    "tests/fixtures/p3_synthetic/contacts.csv": "29fd29738ca2f466d5ca536db223b36f46ac1ff863a500a21f520549565ae83f",
    "tests/fixtures/p3_synthetic/cost_lines.csv": "abf676757a2bdb758cda8e5b07f01f06f054009992b4c5d2f39a5dbd4a449c31",
    "tests/fixtures/p3_synthetic/episodes.csv": "61e2541aabff0f8a8fc4a22e671dfe78a916dabe7c5e8bc20392ea5d3152b923",
    "tests/fixtures/p3_synthetic/returns.csv": "df6aeba0839e6285001f2b8349ea602375cfa8820c90b2948ca7f89a4cfa2eb7",
    "tests/fixtures/p3_synthetic/safety_events.csv": "0c64bf3c6e58f29dafbecdc4bf8e6d2fb488234d20beccc2ec55e0bc76e14729",
}
PUBLIC_DATA_CLASSES = frozenset({
    "definition_only_no_local_records", "public_aggregated_only",
    "public_synthetic_source_contract_only", "synthetic",
    "synthetic_and_public_source_metadata", "synthetic_and_public_source_metadata_only",
    "synthetic_design", "synthetic_example", "synthetic_placeholder_contract",
})
TENANT_LINK = re.compile(rb"https?://[a-z0-9.-]+\.sharepoint\.(?:com|us|cn|de)\.?(?![a-z0-9.-])", re.I)
OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")


def find_forbidden_paths(paths: Iterable[str]) -> list[str]:
    """Identify protected locations and exported data formats."""
    violations = set()
    for raw in paths:
        path = PurePosixPath(raw.replace("\\", "/").lstrip("/"))
        name = path.name.casefold()
        suffix = path.suffix.casefold()
        parents = {part.casefold() for part in path.parts[:-1]}
        if (parents & PRIVATE_DIRECTORIES or suffix in EXPORT_SUFFIXES
                or name == ".env" or name.startswith(".env.")
                or (suffix == ".csv" and str(path) not in CSV_SHA256)):
            violations.add(str(path))
    return sorted(violations)


def _git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=False, timeout=30,
    )
    if result.returncode != 0:
        raise ValueError("could not inspect a Git object")
    return result.stdout


def _export_json(data: bytes) -> bool:
    try:
        value = json.loads(data)
    except (ValueError, UnicodeError):
        return True
    if not isinstance(value, dict):
        return True
    inventory = value.get("file_sha256")
    if isinstance(inventory, dict) and find_forbidden_paths(inventory):
        return True
    # SharePoint/Graph can return a raw array or a page of records.
    if isinstance(value.get("value"), list) or isinstance(value.get("Row"), list):
        return True
    if {"@odata.context", "@odata.nextLink", "odata.metadata"} & value.keys():
        return True
    envelope = value.get("d")
    if isinstance(envelope, dict) and isinstance(envelope.get("results"), list):
        return True
    label = value.get("data_class")
    if isinstance(label, str) and label not in PUBLIC_DATA_CLASSES:
        return True

    pending = [value]
    while pending:
        candidate = pending.pop()
        if isinstance(candidate, dict):
            # Admission contracts can describe which sets would be requested,
            # including pseudonymised or aggregate-only sets.
            label = candidate.get("data_class")
            if isinstance(label, str) and label.casefold() in {"restricted", "observed", "private", "confidential"}:
                return True
            pending.extend(candidate.values())
        elif isinstance(candidate, list):
            pending.extend(candidate)
        elif isinstance(candidate, str) and TENANT_LINK.search(candidate.encode("utf-8", errors="surrogatepass")):
            return True
    return False


def _violations(root: Path, trees: Iterable[bytes], *, index: bool) -> list[str]:
    found = set()
    checked = set()
    for tree in trees:
        for entry in tree.split(b"\0")[:-1]:
            metadata, raw_name = entry.split(b"\t", 1)
            mode, second, third = metadata.decode("ascii").split()
            oid = second if index else third
            path = raw_name.decode("utf-8", "surrogateescape")
            if (mode, oid, path) in checked:
                continue
            checked.add((mode, oid, path))
            if (find_forbidden_paths([path]) or mode == "120000"
                    or (index and third != "0")
                    or (mode == "160000" and path != "extensions/conductor")):
                found.add(path)
                continue
            if mode == "160000":
                continue
            content = _git(root, "cat-file", "blob", oid)
            if (TENANT_LINK.search(content)
                    or (path in CSV_SHA256 and hashlib.sha256(content).hexdigest() != CSV_SHA256[path])
                    or (path.casefold().endswith(".json") and _export_json(content))):
                found.add(path)
    return sorted(found)


def index_violations(root: Path) -> list[str]:
    """Check the bytes Git has staged, including unchanged tracked files."""
    return _violations(root, [_git(root, "ls-files", "--stage", "-z")], index=True)


def pending_push_violations(root: Path, updates: Iterable[str]) -> list[str]:
    """Check pushed tips and commits they add, including later-deleted files."""
    tips = set()
    old_tips = set()
    for update in updates:
        _, local, _, remote = update.split()
        if not OID.fullmatch(local) or not OID.fullmatch(remote):
            raise ValueError("unrecognised pre-push object identifier")
        if set(local) == {"0"}:
            continue
        tips.add(_git(root, "rev-parse", "--verify", f"{local}^{{commit}}").decode().strip())
        if set(remote) != {"0"}:
            try:
                old_tips.add(_git(root, "rev-parse", "--verify", f"{remote}^{{commit}}").decode().strip())
            except ValueError:
                # Without the old remote commit locally, check the full history.
                pass
    if not tips:
        return []
    new = _git(root, "rev-list", *sorted(tips), *(f"^{sha}" for sha in sorted(old_tips)))
    commits = tips.union(new.decode("ascii").splitlines())
    trees = (_git(root, "ls-tree", "--full-tree", "-r", "-z", sha) for sha in sorted(commits))
    return _violations(root, trees, index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pre-push", action="store_true", help="Read Git pre-push ref updates from stdin")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    try:
        failures = pending_push_violations(root, sys.stdin) if args.pre_push else index_violations(root)
    except (OSError, ValueError, subprocess.SubprocessError):
        print("Public-data check could not verify Git objects.", file=sys.stderr)
        return 2
    if failures:
        # Public CI logs must never repeat file paths containing private information.
        print(f"Public-data check rejected {len(failures)} path(s). Review locally.", file=sys.stderr)
        return 2
    print("Public-data check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
