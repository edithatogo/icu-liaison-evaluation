"""Source-derived CHHHS request pack; headers only, no patient records."""
from pytest import MonkeyPatch
from pathlib import Path
from typing import IO, Any
import json
import sys
import pytest

from icu_liaison.data_request import DataRequestCatalogue, render_request_markdown, render_request_csv
from tools import export_chhhs_data_request

ROOT = Path(__file__).resolve().parents[1]


def test_request_is_structured_with_owners_priority_and_privacy() -> None:
    request = DataRequestCatalogue.model_validate_json((ROOT/'model-inputs/chhhs-data-request.json').read_text())
    assert request.status == 'request_only_no_local_data_obtained'
    assert len(request.datasets) >= 9
    assert {'icu_episodes','hospital_outcomes','bed_capacity','ward_flow','clinical_safety','staffing_costs', 'cost_resource_ledger'} <= {x.id for x in request.datasets}
    assert all(x.owner_role and x.fields and x.grain and x.delivery_tier in {'minimal','enhanced','optional'} for x in request.datasets)
    assert all(x.data_class in {'approved_pseudonymised','aggregate_only'} for x in request.datasets)


def test_request_renderers_include_denominators_and_explicit_missingness() -> None:
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


def test_catalogue_rejects_duplicate_dataset_and_unsafe_data_class() -> None:
    data = json.loads((ROOT/'model-inputs/chhhs-data-request.json').read_text())
    data['datasets'].append(dict(data['datasets'][0]))
    with pytest.raises(ValueError,match='duplicate'):
        DataRequestCatalogue.model_validate(data)
    data = json.loads((ROOT/'model-inputs/chhhs-data-request.json').read_text())
    data['datasets'][0]['data_class'] = 'unrestricted_patient_identifiers'
    with pytest.raises(ValueError):
        DataRequestCatalogue.model_validate(data)


def test_request_export_recovers_after_a_failed_second_write(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    output = tmp_path / 'request'
    output.mkdir()
    monkeypatch.setattr(sys, 'argv', ['export-request', '--output-dir', str(output)])
    original_open = Path.open

    def fail_csv(path: Path, mode: str='r', buffering: int=-1, encoding: str | None=None,
                 errors: str | None=None, newline: str | None=None) -> IO[Any]:
        if path.suffix == '.csv' and mode in {'w', 'x'}:
            raise OSError('fictional export failure')
        return original_open(path, mode, buffering, encoding, errors, newline)

    with monkeypatch.context() as patch:
        patch.setattr(Path, 'open', fail_csv)
        with pytest.raises(SystemExit) as stopped:
            export_chhhs_data_request.main()
        assert stopped.value.code == 2
    assert not list(output.iterdir())
    assert export_chhhs_data_request.main() == 0
    assert {item.suffix for item in output.iterdir()} == {'.md', '.csv'}


def test_request_export_preserves_a_file_created_during_publication(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    output = tmp_path / 'request'
    output.mkdir()
    csv_path = output / 'CHHHS_ICU_Liaison_Fields.csv'
    monkeypatch.setattr(sys, 'argv', ['export-request', '--output-dir', str(output)])
    original_open = Path.open

    def existing_csv(path: Path, mode: str='r', buffering: int=-1, encoding: str | None=None,
                 errors: str | None=None, newline: str | None=None) -> IO[Any]:
        if path == csv_path and mode in {'w', 'x'}:
            with original_open(path, 'x', encoding='utf-8') as stream:
                stream.write('Fictional contents from another writer')
        return original_open(path, mode, buffering, encoding, errors, newline)

    monkeypatch.setattr(Path, 'open', existing_csv)
    with pytest.raises(SystemExit) as stopped:
        export_chhhs_data_request.main()
    assert stopped.value.code == 2
    assert list(output.iterdir()) == [csv_path]
    assert csv_path.read_text(encoding='utf-8') == 'Fictional contents from another writer'
