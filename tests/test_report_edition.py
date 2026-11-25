"""Exercise the reporting edition gate on wholly fictional saved files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tools.verify_report_edition import CHECKS, verify_edition


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def worksheet(tmp: Path, *, altered: str = "") -> Path:
    prose = tmp / "extract.txt"
    prose.write_text("A fictional source supports the fictional report.", encoding="utf-8")
    dates = {k: {"date": None, "basis": "Unknown in the fictional record"}
             for k in ("authored", "issued", "accessed", "catalogued")}
    dates["catalogued"] = {"date": "2026-11-26", "basis": "Fictional catalogue date"}
    if altered == "invalid date":
        dates["issued"] = {"date": "2026-14-40", "basis": "Fictional date"}
    artefacts = []
    for role in ("source", "output"):
        saved = tmp / f"{role}.txt"
        saved.write_text(f"Fictional {role}.", encoding="utf-8")
        artefacts.append({"id": role, "role": role, "label": f"Fictional {role}", "kind": "text",
                          "location": saved.name, "edition": "test-1", "sha256": sha(saved),
                          "saved_path": saved.name, "dates": dates, "provenance": "Regression fixture"})
    checks = {}
    for tool in CHECKS:
        pending = altered == "pending" and tool == "citeweft"
        rows: list[dict[str, object]] = [{"id": record["id"], "sha256": record["sha256"],
                 "status": "pending" if pending else "checked",
                 "detail": "Fictional scoped receipt", "extract_path": prose.name,
                 "extract_sha256": sha(prose)} for record in artefacts]
        if tool == "textstat" and altered != "missing scores":
            rows = [dict(row, language="en_AU", scores={"flesch": 50.1}) for row in rows]
        if tool == "sourceright" and altered == "missing scope":
            rows.pop()
        evidence = tmp / f"{tool}.json"
        save(evidence, {"tool": tool, "version": "test-only", "rows": rows})
        checks[tool] = {"path": evidence.name, "sha256": sha(evidence)}
    if altered == "missing method":
        checks.pop("authentext")
    manifest = tmp / "catalogue.json"
    save(manifest, {"schema_version": 1, "artefacts": artefacts, "checks": checks})
    return manifest


def test_saved_edition_and_receipts(tmp_path: Path) -> None:
    assert verify_edition(worksheet(tmp_path))["artefacts"] == 2


@pytest.mark.parametrize("altered", ["invalid date", "pending", "missing scope", "missing scores", "missing method"])
def test_unresolved_edition_is_rejected(tmp_path: Path, altered: str) -> None:
    with pytest.raises(ValueError):
        verify_edition(worksheet(tmp_path, altered=altered))


@pytest.mark.parametrize("target", ["source.txt", "output.txt", "extract.txt", "textstat.json"])
def test_changed_saved_bytes_are_rejected(tmp_path: Path, target: str) -> None:
    manifest = worksheet(tmp_path)
    (tmp_path / target).write_text("Different bytes.", encoding="utf-8")
    with pytest.raises(ValueError, match="changed"):
        verify_edition(manifest)


def test_saved_files_cannot_escape_authorised_root(tmp_path: Path) -> None:
    edition = tmp_path / "catalogue"
    edition.mkdir()
    manifest = worksheet(edition)
    saved = edition / "source.txt"
    outside = tmp_path / saved.name
    saved.rename(outside)
    saved.symlink_to(outside)
    with pytest.raises(ValueError, match="outside the authorised roots or is a symlink"):
        verify_edition(manifest)
