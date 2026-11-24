"""Check P9 contracts and the artifacts in a verified synthetic run."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "contracts/reporting/catalogue.json"
SCHEMA = ROOT / "contracts/reporting/catalogue.schema.json"
DECK_PROFILE = CATALOGUE.with_name("evaluation-deck.json")
P5_TABLES = {
    "T01": "cost-consequence.csv",
    "T02": "paired-comparisons.csv",
    "T03": "one-way-sensitivity.csv",
    "T04": "decision-surface.csv",
}


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
    from jsonschema import Draft202012Validator

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema).iter_errors(c))
    if errors:
        first = sorted(errors, key=lambda error: str(list(error.path)))[0]
        raise ValueError(f"reporting schema invalid at {list(first.path)}: {first.message}")
    if [item['id'] for item in c['tables']] != [f'T{i:02d}' for i in range(1, 8)]:
        raise ValueError('expected stable T01-T07 table ordering')
    for table in c['tables']:
        if table['artifact'] != P5_TABLES.get(table['id']):
            raise ValueError(f"unqualified table or incorrect report artifact: {table['id']}")
    expected = [f'F{i:02d}' for i in range(1, 25)]
    if [item['id'] for item in c['figures']] != expected:
        raise ValueError('expected stable F01-F24 figure ordering')
    f01 = c['figures'][0]
    if f01['artifact'] != 'scenario-comparison.svg' or f01['status'] != 'implemented_optional':
        raise ValueError('F01 must identify the optional scenario comparison SVG')
    for figure in c['figures']:
        tier = figure['evidence_tier']
        if tier != 'synthetic_implemented' and figure['status'] != 'placeholder':
            raise ValueError('unqualified figure promoted')
        if tier == 'empirical_blocked' and figure['missingness'] != 'unknown_never_zero':
            raise ValueError('unknown empirical observation misrepresented')
        if tier == 'external_exploratory_only' and figure['exploratory_reference']['in_repo']:
            raise ValueError('external image wrongly claimed as repo artifact')
    if __package__:
        from tools.validate_measurement_contracts import validate_assurance
    else:
        from validate_measurement_contracts import validate_assurance
    validate_assurance(catalogue=c)
    from icu_liaison.p9_figure_data import FIGURE_IDS
    if tuple(f["id"] for f in c["figures"] if f.get("bundle") == "p9") != FIGURE_IDS:
        raise ValueError("priority P9 figure registration differs from the renderer")
    from icu_liaison.p9_supplement_data import SUPPLEMENT_IDS
    if tuple(f["id"] for f in c["figures"] if f.get("bundle") == "p9_supplement") != SUPPLEMENT_IDS:
        raise ValueError("supplementary P9 figure registration differs from the renderer")
    rendered = {"F01", *FIGURE_IDS, *SUPPLEMENT_IDS}
    for figure in c["figures"]:
        if figure["id"] not in rendered and figure["status"] != "placeholder":
            raise ValueError("unqualified empirical or provider figure promoted")
        if figure.get("bundle") and figure["artifact"] != figure["id"].lower() + ".svg":
            raise ValueError("unqualified companion artifact path")
    byid = {t["id"]:t for t in c["tables"]}
    if byid["T06"]["perspective"] != "weighted_activity_not_actual_revenue":
        raise ValueError("NWAU must not become hospital revenue")
    if byid["T04"]["perspective"] != "resource_net_benefit_only":
        raise ValueError("decision surface must not mix funding")


def _check_table_header(path: Path, table: dict) -> None:
    with path.open(newline="", encoding="utf-8") as fp:
        header = next(csv.reader(fp), ())
    if len(header) != len(set(header)) or not set(table["required_columns"]).issubset(header):
        raise ValueError("P5 contracted header mismatch: " + table["id"])


def validate_report(folder: Path, c: dict) -> dict:
    validate_catalogue(c)
    from icu_liaison.p5_reporting import review_report, verify_manifest
    verify_manifest(folder)
    review_report(folder)
    checked = []
    for table in c["tables"]:
        if table["status"] == "placeholder":
            continue
        _check_table_header(folder / table["artifact"], table)
        checked.append(table["id"])
    for f in c["figures"]:
        if f["status"] == "placeholder":
            continue
        path=folder/f["artifact"]
        if f.get("bundle") in {"p9", "p9_supplement"}:
            if path.exists() or path.is_symlink():
                raise ValueError("P9 companion figure is misplaced in the P5 report")
            continue
        if path.exists():
            if path.suffix != ".svg" or b"<svg" not in path.read_bytes()[:5000]:
                raise ValueError("not SVG")
            if path.stat().st_size > 3_000_000:
                raise ValueError('SVG exceeds bounded reporting size')
            from xml.etree import ElementTree
            try:
                svg = ElementTree.parse(path).getroot()
            except ElementTree.ParseError as exc:
                raise ValueError('invalid SVG accessibility structure') from exc
            if svg.tag != '{http://www.w3.org/2000/svg}svg':
                raise ValueError('invalid SVG root')
            description = svg.find('.//{http://purl.org/dc/elements/1.1/}description')
            if description is None or description.text != f['alt_text']:
                raise ValueError('SVG accessibility description differs from source contract')
            checked.append(f["id"])
        elif f["status"] != "implemented_optional":
            raise ValueError("mandatory figure missing")
    return {"status":"synthetic_source_consistent_not_clinically_validated","checked":checked}


def verify_run_coverage(output: Path, catalogue: dict) -> dict:
    """Reconcile a verified P11 store with the current reporting contracts."""
    from icu_liaison.p11_records import digest_file, read_json
    from icu_liaison.p11_verify import verify_output

    validate_catalogue(catalogue)
    verified = verify_output(output, include_provenance=True)
    table_specs = [table for table in catalogue["tables"] if table["artifact"] is not None]
    figure_specs = {figure["id"]: figure for figure in catalogue["figures"] if figure["artifact"] is not None}
    scenarios = []
    for case in verified["provenance"]["scenarios"]:
        model_record = output / case["model_record"]["path"]
        model_files = read_json(model_record)["files_sha256"]
        if digest_file(model_record) != case["model_record"]["sha256"]:
            raise ValueError("P11 model record changed during coverage verification")
        tables = []
        for table in table_specs:
            relative = f"p5-report/{table['artifact']}"
            path = model_record.parent / relative
            expected = model_files.get(relative)
            if expected is None or digest_file(path) != expected:
                raise ValueError(f"P11 table missing or changed: {table['id']}")
            _check_table_header(path, table)
            tables.append({"id": table["id"], "path": path.relative_to(output).as_posix(), "sha256": expected})
        figures = []
        for record in case["figures"]:
            figure_id = record["id"]
            spec = figure_specs.get(figure_id)
            if spec is None or Path(record["figure"]["path"]).name != spec["artifact"]:
                raise ValueError(f"P11 figure disagrees with its catalogue entry: {figure_id}")
            figures.append({
                "id": figure_id, **record["figure"], "source": record["table"],
                "figure_revision": record["figure_revision"], "review": record["review"],
            })
        scenarios.append({
            "case_id": case["case_id"], "model_run_id": case["model_run_id"],
            "run_catalogue_sha256": case["catalogue_sha256"], "tables": tables, "figures": figures,
            "not_in_run": sorted(figure_specs.keys() - {figure["id"] for figure in figures}),
        })
    blocked = [{"id": row["id"], "title": row["title"], "evidence_needed": row["uncertainty"]}
               for row in catalogue["tables"] if row["status"] == "placeholder"]
    blocked.extend({"id": row["id"], "title": row["title"], "evidence_needed": row["release_gate"]}
                   for row in catalogue["figures"] if row["status"] == "placeholder")
    return {
        "status": verified["status"], "summary_id": verified["summary_id"],
        "catalogue_revision": catalogue["catalogue_revision"], "scenarios": scenarios, "blocked": blocked,
        "clinical_safety_approved": False, "investment_ready": False,
    }


def figure_inventory(catalogue: dict, deck: dict) -> list[dict]:
    """List both contracts without making the deck a P11 input."""
    figures = [
        {
            "id": row["id"],
            "title": row["title"],
            "contract": "p9",
            "status": row["status"],
            "evidence_tier": row["evidence_tier"],
            "artifacts": [row["artifact"]] if row["artifact"] else [],
            "related_catalogue_ids": [],
        }
        for row in catalogue["figures"]
    ]
    catalogue_ids = {row["id"] for row in figures}
    registered = set(catalogue_ids)
    for row in [*deck["figures"], deck["companion"]]:
        figure_id = row["id"]
        related = row["related_catalogue_ids"]
        if figure_id in registered:
            raise ValueError(f"duplicate figure inventory ID: {figure_id}")
        if not related or not set(related) <= catalogue_ids:
            raise ValueError(f"unknown P9 figure reference in {figure_id}")
        registered.add(figure_id)
        stem = row.get("artifact_stem")
        figures.append({
            "id": figure_id,
            "title": row["title"],
            "contract": "evaluation_deck",
            "status": "renderer_available" if stem else "private_deck_chart",
            "evidence_tier": "private_aggregate",
            "artifacts": [f"{stem}.png", f"{stem}.svg"] if stem else [row["kind"]],
            "related_catalogue_ids": list(related),
        })
    return figures


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--report", type=Path)
    mode.add_argument("--run", type=Path, help="Verify a P11 output directory and list reporting coverage")
    mode.add_argument("--inventory", action="store_true", help="List both figure contracts as JSON")
    args = parser.parse_args()
    catalogue = json.loads(CATALOGUE.read_text())
    if args.run is not None:
        try:
            coverage = verify_run_coverage(args.run, catalogue)
        except (OSError, RuntimeError, TypeError, ValueError, KeyError) as exc:
            parser.exit(2, f"P9 INVALID_OR_UNVERIFIED: {exc}\n")
        print(json.dumps(coverage, indent=2))
        return 0
    if args.report:
        print(json.dumps(validate_report(args.report, catalogue)))
        return 0
    validate_catalogue(catalogue)
    inventory = figure_inventory(catalogue, json.loads(DECK_PROFILE.read_text()))
    print(json.dumps(inventory, indent=2) if args.inventory else "catalogue valid")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
