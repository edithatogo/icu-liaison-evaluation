"""Release-facing P6 boundary checks: public source != installed qualification."""
from __future__ import annotations

import json
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_track_metadata_records_local_replay_and_outstanding_qualification() -> None:
    metadata = json.loads((ROOT / 'conductor/tracks/P6-kairos-capacity-validation/metadata.json').read_text())
    assert metadata['status'] == 'in_progress'
    assert metadata['native_execution'] == 'locally_qualified_fictional_macos_arm64'
    assert metadata['clinical_validation'] is False
    assert 'P6.3-local-native-Kairos-producer-and-replay' in metadata['accepted_phases']
    assert 'P6.3-independent-native-build-attestation' in metadata['accepted_phases']
    assert metadata['current_build_attestation'] == 'pending'
    attestation = metadata['previous_independent_build_attestation']
    assert attestation['consumer_revision'] == '4b6e704c4d1561d6b19b94456031f0b9951a6d3d'
    assert attestation['provider_revision'] == 'b60c422b9fa90751b6a5349b9aefab2bf272e25e'
    assert attestation['platform'] == 'macos_arm64'
    assert 'P6.3-ward-costing-and-safety-integration' in metadata['blocked_phases']
    assert 'P6.4-CHHHS-calibration' in metadata['blocked_phases']


def test_source_lock_is_immutable_but_does_not_fake_an_installed_binary() -> None:
    lock = json.loads((ROOT / 'model-inputs/p6/kairos-provider-lock.json').read_text())
    revision = lock['source_commit']
    assert revision == '9d76ca7f4b7f4b5898f2ec77515a7a7639f1478b'
    track = ROOT / 'conductor/tracks/P6-kairos-capacity-validation/metadata.json'
    assert json.loads(track.read_text())['source_provider_revision'] == revision
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
