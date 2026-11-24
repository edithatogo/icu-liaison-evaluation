"""Release-facing P6 boundary checks: public source != installed qualification."""
from __future__ import annotations

import json
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_track_metadata_records_local_replay_and_outstanding_qualification() -> None:
    metadata = json.loads((ROOT / 'conductor/tracks/P6-kairos-capacity-validation/metadata.json').read_text())
    assert metadata['status'] == 'in_progress'
    assert metadata['native_execution'] == 'local_synthetic_replay_passed_unattested'
    assert metadata['clinical_validation'] is False
    assert 'P6.3-local-native-Kairos-producer-and-replay' in metadata['accepted_phases']
    assert 'P6.3-independent-native-build-attestation' in metadata['blocked_phases']
    assert 'P6.4-CHHHS-calibration' in metadata['blocked_phases']


def test_source_lock_is_immutable_but_does_not_fake_an_installed_binary() -> None:
    lock = json.loads((ROOT / 'model-inputs/p6/kairos-provider-lock.json').read_text())
    revision = lock['source_commit']
    assert revision == 'b60c422b9fa90751b6a5349b9aefab2bf272e25e'
    consumer = ROOT / 'native/kairos-icu-liaison'
    manifest = tomllib.loads((consumer / 'Cargo.toml').read_text())
    resolved = tomllib.loads((consumer / 'Cargo.lock').read_text())
    names = {'kairo-ecs-des', 'kairo-ecs-types'}
    assert all(manifest['dependencies'][name]['rev'] == revision for name in names)
    kairos = {package['name']: package['source'] for package in resolved['package']
              if package.get('source', '').startswith('git+')}
    assert names <= kairos.keys()
    assert set(kairos.values()) == {f"git+{lock['repository']}?rev={revision}#{revision}"}
    assert lock['binary_sha256'] is None
    assert lock['clinical_or_occupancy_validation'] is False
    assert set(lock['inspected_upstream_blob_shas']) == {
        'crates/kairo-ecs-des/src/staged_runtime.rs',
        'crates/kairo-ecs-types/src/lib.rs',
        'crates/kairo-ecs-des/Cargo.toml',
    }


def test_public_project_excludes_restricted_inputs_and_outputs() -> None:
    lines = (ROOT / '.gitignore').read_text().splitlines()
    for forbidden in ('private/', 'outputs/', '.env', '*.parquet', '*.xlsx', '.venv/'):
        assert forbidden in lines
    policy = (ROOT / 'docs/p6-native-qualification.md').read_text().lower()
    assert 'chhhs' in policy and 'not' in policy
    assert 'independent build attestation' in policy
