"""P9 negative admission and Clinical Director request regression."""
from pathlib import Path
from typing import Any
import json
import pytest
from tools.validate_reporting_contracts import ROOT, CATALOGUE, validate_catalogue

def load() -> dict[str, Any]:
    value = json.loads(CATALOGUE.read_text())
    assert isinstance(value, dict)
    return value

def test_catalogue_structural_contract() -> None:
    c=load();validate_catalogue(c)
    assert len(c["tables"])==7 and len(c["figures"])==24

def test_fake_plot_rejected() -> None:
    c=load()
    next(x for x in c["figures"] if x["id"]=="F03")["artifact"]="pretend.svg"
    with pytest.raises(ValueError,match="placeholder"):
        validate_catalogue(c)

def test_wrong_nwau_financial_classification_rejected() -> None:
    c=load()
    next(x for x in c["tables"] if x["id"]=="T06")["perspective"]="actual_revenue"
    with pytest.raises(ValueError,match="NWAU"):
        validate_catalogue(c)

def test_missing_figure_source_rejected() -> None:
    c=load();c["figures"][0]["source_table"]="absent"
    with pytest.raises(ValueError,match="source table"):
        validate_catalogue(c)

def test_director_two_tables_source_consistent() -> None:
    d=(ROOT/"docs/clinical-director-data-request.md").read_text()
    src=json.loads((ROOT/"model-inputs/chhhs-data-request.json").read_text())
    assert len(src["datasets"])==11
    assert d.count("## Table ")==2
    assert "first eligible adult" in d and "all live ward/home" in d
    assert "72" in d and "NWAU" in d


def test_p5_generated_report_matches_p9_table_contract(tmp_path: Path) -> None:
    """Exercise the registered table schema on a real synthetic report bundle."""
    from icu_liaison.p4_model import EconomicScenario
    from icu_liaison.p5_reporting import build_report
    from tools.validate_reporting_contracts import validate_report

    scenario = EconomicScenario.model_validate_json(
        (ROOT / "model-inputs/p4/illustrative.json").read_text()
    )
    report = tmp_path / "report"
    build_report(scenario, report, voiage_mode="skip")
    result = validate_report(report, load())
    assert result["status"] == "synthetic_source_consistent_not_clinically_validated"
    assert {"T01", "T02", "T03", "T04"} <= set(result["checked"])
    assert "T05" not in result["checked"] and "T06" not in result["checked"]


def test_p9_contract_rejects_unregistered_report_artifact(tmp_path: Path) -> None:
    """Report-file membership rejects a fabricated clinical results table."""
    from icu_liaison.p4_model import EconomicScenario
    from icu_liaison.p5_reporting import build_report
    from tools.validate_reporting_contracts import validate_report

    scenario = EconomicScenario.model_validate_json(
        (ROOT / "model-inputs/p4/illustrative.json").read_text()
    )
    report = tmp_path / "report"
    build_report(scenario, report, voiage_mode="skip")
    (report / "unregistered-clinical-effect.csv").write_text(
        "effect,value\nreturn_rate,0.5\n"
    )
    with pytest.raises(ValueError, match="file-set mismatch"):
        validate_report(report, load())


def test_reporting_schema_is_valid_and_admits_existing_catalogue() -> None:
    from jsonschema import Draft202012Validator
    from tools.validate_reporting_contracts import SCHEMA

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert list(Draft202012Validator(schema).iter_errors(load())) == []


def test_reporting_schema_rejects_unrecognised_table_metadata() -> None:
    c = load()
    c["tables"][0]["claimed_clinical_approval"] = True
    with pytest.raises(ValueError, match="schema"):
        validate_catalogue(c)


def test_reporting_schema_rejects_path_traversal() -> None:
    c = load()
    c["tables"][0]["artifact"] = "../../private/patient-records.csv"
    with pytest.raises(ValueError, match="schema"):
        validate_catalogue(c)


def test_reporting_schema_requires_figure_axis() -> None:
    c = load()
    del c["figures"][0]["x"]
    with pytest.raises(ValueError, match="schema"):
        validate_catalogue(c)


def test_reporting_schema_rejects_falsely_promoted_placeholder() -> None:
    c = load()
    c["tables"][4].update(status="implemented", artifact="invented.csv", required_columns=["value"])
    with pytest.raises(ValueError, match="schema"):
        validate_catalogue(c)


@pytest.mark.parametrize("table_id", ["T05", "T06", "T07"])
def test_existing_synthetic_csv_cannot_promote_a_blocked_table(table_id: str) -> None:
    catalogue = load()
    table = next(row for row in catalogue["tables"] if row["id"] == table_id)
    table.update(status="implemented", privacy="synthetic_only",
                 artifact="cost-consequence.csv", required_columns=["strategy_id"])
    with pytest.raises(ValueError, match=table_id):
        validate_catalogue(catalogue)


def test_registered_table_cannot_claim_another_report_csv() -> None:
    catalogue = load()
    sensitivity = next(row for row in catalogue["tables"] if row["id"] == "T03")
    sensitivity["artifact"] = "paired-comparisons.csv"
    with pytest.raises(ValueError, match="T03"):
        validate_catalogue(catalogue)


def test_optional_f01_cannot_point_to_an_unproduced_file() -> None:
    catalogue = load()
    catalogue["figures"][0]["artifact"] = "invented.svg"
    with pytest.raises(ValueError, match="F01"):
        validate_catalogue(catalogue)


def test_reporting_schema_prohibits_approved_aggregate_classification_of_synthetic_output() -> None:
    c = load()
    c["tables"][0]["privacy"] = "approved_aggregates_only"
    with pytest.raises(ValueError, match="schema"):
        validate_catalogue(c)


def test_generated_svg_metadata_matches_registered_accessibility_text(tmp_path: Path) -> None:
    from xml.etree import ElementTree
    from icu_liaison.p4_model import EconomicScenario
    from icu_liaison.p5_reporting import build_report
    from tools.validate_reporting_contracts import validate_report

    scenario = EconomicScenario.model_validate_json(
        (ROOT / 'model-inputs/p4/illustrative.json').read_text()
    )
    folder = tmp_path / 'report'
    build_report(scenario, folder, plots=True)
    expected = next(f for f in load()['figures'] if f['id'] == 'F01')['alt_text']
    svg = ElementTree.parse(folder / 'scenario-comparison.svg').getroot()
    description = svg.find('.//{http://purl.org/dc/elements/1.1/}description')
    assert description is not None and description.text == expected
    assert 'F01' in validate_report(folder, load())['checked']


def test_rehashed_svg_cannot_fake_its_accessibility_description(tmp_path: Path) -> None:
    import hashlib
    from icu_liaison.p4_model import EconomicScenario
    from icu_liaison.p5_reporting import build_report
    from tools.validate_reporting_contracts import validate_report

    scenario = EconomicScenario.model_validate_json(
        (ROOT / 'model-inputs/p4/illustrative.json').read_text()
    )
    folder = tmp_path / 'report'
    build_report(scenario, folder, plots=True)
    path = folder / 'scenario-comparison.svg'
    alt = next(f for f in load()['figures'] if f['id'] == 'F01')['alt_text']
    original = path.read_text(encoding='utf-8')
    assert alt in original
    path.write_text(
        original.replace(alt, 'A misleading clinical outcome claim'),
        encoding='utf-8',
    )
    manifest_path = folder / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['files_sha256'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match='accessibility description'):
        validate_report(folder, load())


def test_p9_expanded_figure_programme_and_priorities() -> None:
    c = load()
    validate_catalogue(c)
    assert [f["id"] for f in c["figures"]] == [f"F{i:02d}" for i in range(1, 25)]
    assert {f["id"] for f in c["figures"] if f.get("bundle") == "p9" and f["evidence_tier"] == "synthetic_implemented"} == {"F02", "F10", "F11", "F15", "F20", "F24"}
    assert {f["id"] for f in c["figures"] if f.get("bundle") == "p9_supplement"} == {
        "F05", "F06", "F07", "F08", "F09", "F13", "F18"}


def test_external_figures_cannot_be_falsely_promoted() -> None:
    c = load()
    f = c["figures"][4]
    assert f["artifact"] == "f05.svg" and f["exploratory_reference"]["in_repo"] is False
    f["artifact"] = "fabricated.svg"
    f["status"] = "implemented_optional"
    with pytest.raises(ValueError, match="schema|unqualified"):
        validate_catalogue(c)


def test_missing_empirical_followup_cannot_be_assumed_complete() -> None:
    c = load()
    c["figures"][16]["missingness"] = "synthetic_no_observed_missingness"
    with pytest.raises(ValueError, match="schema|unknown"):
        validate_catalogue(c)


def test_future_figure_denominator_is_required() -> None:
    c = load()
    del c["figures"][10]["denominator"]
    with pytest.raises(ValueError, match="schema"):
        validate_catalogue(c)


@pytest.mark.parametrize('key', ['F03', 'F04', 'F12', 'F14', 'F16', 'F17', 'F19', 'F21', 'F22', 'F23'])
def test_site_and_provider_outputs_require_admitted_sources(key: str) -> None:
    catalogue = load()
    figure = next(f for f in catalogue['figures'] if f['id'] == key)
    figure.update(artifact=f'{key.lower()}.svg', status='implemented_optional',
                  evidence_tier='synthetic_implemented', privacy='synthetic_only', bundle='p9_supplement')
    with pytest.raises(ValueError):
        validate_catalogue(catalogue)


def test_joint_figure_inventory_preserves_contract_status() -> None:
    from tools.validate_reporting_contracts import DECK_PROFILE, figure_inventory

    result = figure_inventory(load(), json.loads(DECK_PROFILE.read_text()))
    by_id = {row["id"]: row for row in result}
    assert len(result) == len(by_id) == 28
    assert sum(row["status"] == "placeholder" for row in result) == 10
    assert by_id["F03"]["artifacts"] == []
    assert by_id["F03"]["evidence_tier"] == "empirical_blocked"
    assert by_id["E01"]["related_catalogue_ids"] == ["F03", "F09"]
    assert by_id["E01"]["status"] == "renderer_available"
    assert by_id["E04"]["status"] == "private_deck_chart"


def test_joint_figure_inventory_rejects_unknown_reference() -> None:
    from tools.validate_reporting_contracts import DECK_PROFILE, figure_inventory

    deck = json.loads(DECK_PROFILE.read_text())
    deck["figures"][0]["related_catalogue_ids"] = ["F99"]
    with pytest.raises(ValueError, match="unknown P9 figure reference"):
        figure_inventory(load(), deck)
