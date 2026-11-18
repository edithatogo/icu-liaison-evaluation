"""Release-facing P6 boundary checks: public source != installed qualification."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_track_metadata_does_not_claim_executed_or_clinically_valid_des() -> None:
    metadata = json.loads((ROOT / 'conductor/tracks/P6-kairos-capacity-validation/metadata.json').read_text())
    assert metadata['status'] == 'in_progress'
    assert metadata['native_execution'].startswith('not_executed')
    assert metadata['clinical_validation'] is False
    assert 'P6.3-installed-native-Kairos-producer-and-replay' in metadata['blocked_phases']
    assert 'P6.4-CHHHS-calibration' in metadata['blocked_phases']


def test_source_lock_is_immutable_but_does_not_fake_an_installed_binary() -> None:
    lock = json.loads((ROOT / 'model-inputs/p6/kairos-provider-lock.json').read_text())
    assert lock['source_commit'] == 'a1f6283575ad26918230adc122a99b5c08fc4da3'
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
    assert 'not been compiled' in policy or 'no native' in policy or 'unverified' in policy
