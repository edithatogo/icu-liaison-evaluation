"""P9 table/figure metadata; existing P5 reader owns numerical validation."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "contracts/reporting/catalogue.json"


def validate_catalogue(c: dict) -> None:
    if c.get("schema_version") != 1 or c.get("source_class") != "synthetic_only":
        raise ValueError("unqualified reporting catalogue")
    for group in ("tables", "figures"):
        rows = c.get(group)
        if not isinstance(rows, list) or not rows:
            raise ValueError("missing reporting records")
        ids = [r.get("id") for r in rows]
        if len(ids) != len(set(ids)) or any(not isinstance(i, str) or not i for i in ids):
            raise ValueError("invalid or duplicate IDs")
        for row in rows:
            if not row.get("title") or not row.get("privacy") or not row.get("uncertainty"):
                raise ValueError("missing semantics")
            if row.get("status") == "placeholder" and row.get("artifact") is not None:
                raise ValueError("placeholder claimed as produced")
            if row.get("status") != "placeholder" and not row.get("artifact"):
                raise ValueError("missing implemented artifact")
            if group == "tables" and (not row.get("denominator") or not row.get("perspective")):
                raise ValueError("missing denominator or perspective")
            if group == "figures" and (not row.get("alt_text") or not row.get("y_unit")):
                raise ValueError("missing accessibility or units")
    table_ids = {r["id"] for r in c["tables"]}
    if any(f.get("source_table") not in table_ids for f in c["figures"]):
        raise ValueError("unknown figure source table")
    byid = {t["id"]:t for t in c["tables"]}
    if byid["T06"]["perspective"] != "weighted_activity_not_actual_revenue":
        raise ValueError("NWAU must not become hospital revenue")
    if byid["T04"]["perspective"] != "resource_net_benefit_only":
        raise ValueError("decision surface must not mix funding")


def validate_report(folder: Path, c: dict) -> dict:
    validate_catalogue(c)
    from icu_liaison.p5_reporting import review_report, verify_manifest
    verify_manifest(folder)
    review_report(folder)
    checked = []
    for table in c["tables"]:
        if table["status"] == "placeholder":
            continue
        with (folder/table["artifact"]).open(newline="",encoding="utf-8") as fp:
            header = next(csv.reader(fp))
        if len(header)!=len(set(header)) or not set(table["required_columns"]).issubset(header):
            raise ValueError("P5 contracted header mismatch: "+table["id"])
        checked.append(table["id"])
    for f in c["figures"]:
        if f["status"] == "placeholder":
            continue
        path=folder/f["artifact"]
        if path.exists():
            if path.suffix != ".svg" or b"<svg" not in path.read_bytes()[:5000]:
                raise ValueError("not SVG")
            checked.append(f["id"])
        elif f["status"] != "implemented_optional":
            raise ValueError("mandatory figure missing")
    return {"status":"synthetic_source_consistent_not_clinically_validated","checked":checked}


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--report",type=Path)
    args=p.parse_args()
    c=json.loads(CATALOGUE.read_text())
    print(json.dumps(validate_report(args.report,c)) if args.report else "catalogue valid")
    if not args.report:
        validate_catalogue(c)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
