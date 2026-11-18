"""Source-only native consumer qualification; never a substitute for Rust execution."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'native/kairos-icu-liaison'


def test_native_manifest_reuses_one_pinned_kairos_provider_without_new_scheduler():
    content = (SRC / 'Cargo.toml').read_text()
    lock = json.loads((ROOT / 'model-inputs/p6/kairos-provider-lock.json').read_text())
    assert lock['source_commit'] in content
    assert 'kairo-ecs-des' in content
    assert 'kairo-ecs-types' in content
    assert '[patch.crates-io]' not in content


def test_native_domain_source_uses_staged_resource_leases():
    text = (SRC / 'src/main.rs').read_text()
    for needle in ('StagedResourceRuntime', 'StagedRequestState', '.submit(', '.release(',
                   '.run_for(', '.request('):
        assert needle in text
    assert 'struct Scheduler' not in text
    assert 'BinaryHeap' not in text
    assert 'VecDeque' not in text


def test_native_source_is_explicitly_unqualified_until_compiled():
    guide = (SRC / 'README.md').read_text()
    assert 'NOT EXECUTED' in guide
    assert 'cargo build --locked' in guide
    assert 'no CHHHS' in guide.lower() or 'CHHHS' in guide
