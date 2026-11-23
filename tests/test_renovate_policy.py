"""The shared Renovate preset must not bypass project dependency review."""
import json
from pathlib import Path


def test_project_policy_disables_automatic_dependency_promotion():
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / 'renovate.json').read_text())
    assert config['extends'] == [
        'local>edithatogo/renovate-config#19c8297137dd58de7dbc83ba9de187bf7dc67e5f'
    ]
    assert config['automerge'] is False and config['platformAutomerge'] is False
    rule, *groups = config['packageRules']
    assert rule['automerge'] is False and rule['platformAutomerge'] is False
    assert set(rule['matchUpdateTypes']) == {
        'major', 'minor', 'patch', 'pin', 'pinDigest', 'digest',
        'lockFileMaintenance', 'lockfileUpdate', 'rollback', 'bump', 'replacement',
    }
    python_group, kairos_group = groups
    assert all(not group.get('automerge') and not group.get('platformAutomerge') for group in groups)
    assert python_group['matchUpdateTypes'] == ['minor', 'patch']
    assert {'pydantic', 'pydantic-core'} <= set(python_group['matchPackageNames'])
    assert kairos_group['matchUpdateTypes'] == ['digest']
    assert set(kairos_group['matchDepNames']) == {'kairo-ecs-des', 'kairo-ecs-types'}
    assert 'matchPackageNames' not in kairos_group
