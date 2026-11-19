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
