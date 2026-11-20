"""Exercise public synthetic CLI paths without installing native providers."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def run(module: str, *args: str | Path, expected: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, '-m', module, *map(str, args)],
        cwd=ROOT,
        env={**os.environ, 'PYTHONPATH': str(ROOT/'src')},
        capture_output=True, text=True, check=False, timeout=90,
    )
    if result.returncode != expected:
        raise RuntimeError(f'{module} returned {result.returncode}; expected {expected}: {result.stderr}')
    return result


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    audit = json.loads(run('icu_liaison.placeholders_cli', 'audit').stdout)
    require(audit['investment_ready'] is False and audit['unresolved_count'] > 0,
            'placeholder audit must preserve unresolved evidence gates')
    blocked = run('icu_liaison.placeholders_cli', 'audit', '--require-site-ready', expected=2)
    require('UNVERIFIED' in blocked.stderr, 'site admission must reject unqualified placeholders')
    with tempfile.TemporaryDirectory(prefix='icu-liaison-ci-') as temp:
        bundle = Path(temp)/'synthetic-progress'
        output = json.loads(run('icu_liaison.placeholders_cli', 'dry-run', '--output-dir', bundle).stdout)
        require(output['manifest_verified'] is True and output['investment_ready'] is False,
                'synthetic report must verify without granting site admission')
        report = bundle/'p5-report'
        reviewed = json.loads(run('icu_liaison.p5_review_cli', report).stdout)
        require(reviewed['status'] == 'self_consistency_verified_not_empirically_accepted'
                and reviewed['provider_qualification'] is False,
                'independent review must preserve source-only qualification')
        figures = json.loads(run(
            'icu_liaison.p9_figures', ROOT/'model-inputs/p4/illustrative.json',
            '--p5-report', report, '--output-dir', Path(temp)/'priority-figures',
        ).stdout)
        require(figures['figures_checked'] == ['F02', 'F10', 'F11', 'F15', 'F20', 'F24']
                and figures['p5_draws_reconciled'] == reviewed['draws_checked'] and figures['investment_ready'] is False,
                'all six P9 figures must match their fictional source rows and SVG marks')
        # Rehashing a fabricated readiness label must not evade semantic review.
        summary = report/'model-summary.json'
        model = json.loads(summary.read_text(encoding='utf-8'))
        model['investment_ready'] = True
        summary.write_text(json.dumps(model), encoding='utf-8')
        manifest = report/'manifest.json'
        hashes = json.loads(manifest.read_text(encoding='utf-8'))
        hashes['files_sha256']['model-summary.json'] = hashlib.sha256(summary.read_bytes()).hexdigest()
        manifest.write_text(json.dumps(hashes), encoding='utf-8')
        rejected = run('icu_liaison.p5_review_cli', report, expected=2)
        require('REVIEW_UNVERIFIED' in rejected.stderr, 'tampered readiness must fail semantic review')

    composition_args = (
        ROOT/'model-inputs/p4/illustrative.json', '--strategy', 'liaison_service',
        '--mchs-result', ROOT/'model-inputs/p8/synthetic-mchs-provider-output.json',
        '--workforce-result', ROOT/'model-inputs/p8/synthetic-workforce-provider-output.json',
        '--roster-scenario-id', 'synthetic-nurse-roster',
    )
    composed = json.loads(run('icu_liaison.p8_composition_cli', *composition_args).stdout)
    require(composed['admission'] == 'planning_only'
            and composed['actual_hospital_revenue_change_aud'] is None
            and composed['workforce']['annual_labour_cost_aud'] is None
            and composed['extra_workforce_cost_applied_to_p4'] is False,
            'P8 source projection must not fabricate funding or workforce value')
    rejected = run('icu_liaison.p8_composition_cli', *composition_args, '--require-qualified', expected=2)
    require('UNVERIFIED' in rejected.stderr and not rejected.stdout,
            'P8 qualification must reject missing native and site evidence')
    print(json.dumps({'status': 'synthetic_cli_smoke_passed', 'investment_ready': False,
                      'native_providers_executed': False}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
