"""P9 negative admission and Clinical Director request regression."""
import json
import pytest
from tools.validate_reporting_contracts import ROOT, CATALOGUE, validate_catalogue

def load():
    return json.loads(CATALOGUE.read_text())

def test_catalogue_structural_contract():
    c=load();validate_catalogue(c)
    assert len(c["tables"])==7 and len(c["figures"])==4

def test_fake_plot_rejected():
    c=load()
    next(x for x in c["figures"] if x["id"]=="F03")["artifact"]="pretend.svg"
    with pytest.raises(ValueError,match="placeholder"):
        validate_catalogue(c)

def test_wrong_nwau_financial_classification_rejected():
    c=load()
    next(x for x in c["tables"] if x["id"]=="T06")["perspective"]="actual_revenue"
    with pytest.raises(ValueError,match="NWAU"):
        validate_catalogue(c)

def test_missing_figure_source_rejected():
    c=load();c["figures"][0]["source_table"]="absent"
    with pytest.raises(ValueError,match="source table"):
        validate_catalogue(c)

def test_director_two_tables_source_consistent():
    d=(ROOT/"docs/clinical-director-data-request.md").read_text()
    src=json.loads((ROOT/"model-inputs/chhhs-data-request.json").read_text())
    assert len(src["datasets"])==11
    assert d.count("## Table ")==2
    assert "first eligible adult" in d and "all live ward/home" in d
    assert "72" in d and "NWAU" in d


def test_p5_generated_report_matches_p9_table_contract(tmp_path):
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


def test_p9_contract_rejects_unregistered_report_artifact(tmp_path):
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
