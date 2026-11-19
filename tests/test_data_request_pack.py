"""Source-derived CHHHS request pack; headers only, no patient records."""
from pathlib import Path
import json
import pytest

from icu_liaison.data_request import DataRequestCatalogue, render_request_markdown, render_request_csv

ROOT = Path(__file__).resolve().parents[1]


def test_request_is_structured_with_owners_priority_and_privacy():
    request = DataRequestCatalogue.model_validate_json((ROOT/'model-inputs/chhhs-data-request.json').read_text())
    assert request.status == 'request_only_no_local_data_obtained'
    assert len(request.datasets) >= 9
    assert {'icu_episodes','hospital_outcomes','bed_capacity','ward_flow','clinical_safety','staffing_costs', 'cost_resource_ledger'} <= {x.id for x in request.datasets}
    assert all(x.owner_role and x.fields and x.grain and x.delivery_tier in {'minimal','enhanced','optional'} for x in request.datasets)
    assert all(x.data_class in {'approved_pseudonymised','aggregate_only'} for x in request.datasets)


def test_request_renderers_include_denominators_and_explicit_missingness():
    doc = DataRequestCatalogue.model_validate_json((ROOT/'model-inputs/chhhs-data-request.json').read_text())
    md = render_request_markdown(doc)
    csv = render_request_csv(doc)
    assert '72-hour' in md and '12-hour' in md
    assert 'ICU' in md and 'not yet obtained' in md
    assert 'Null' in md or 'null' in md
    assert 'icu_admission_at' in csv
    assert 'reason_for_transfer_delay' in csv
    assert 'source_system' in csv
    assert 'hospitalisation_pseudonym' in csv
    assert 'patient_name' not in csv
    assert 'DOB' not in csv
    assert len(csv.splitlines()) > 40


def test_catalogue_rejects_duplicate_dataset_and_unsafe_data_class():
    data = json.loads((ROOT/'model-inputs/chhhs-data-request.json').read_text())
    data['datasets'].append(dict(data['datasets'][0]))
    with pytest.raises(ValueError,match='duplicate'):
        DataRequestCatalogue.model_validate(data)
    data = json.loads((ROOT/'model-inputs/chhhs-data-request.json').read_text())
    data['datasets'][0]['data_class'] = 'unrestricted_patient_identifiers'
    with pytest.raises(ValueError):
        DataRequestCatalogue.model_validate(data)
