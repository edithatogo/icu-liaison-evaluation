"""P4 synthetic economic evaluation CLI.

Multi-strategy P4 profile; existing P1 model remains independently executable.
Refuse all investment-readiness claims. No patient records enter.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

from numpy import ndarray


def _write_surface(path: Path, names: list[str], matrix: ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='.p4-surface-', dir=path.parent) as scratch:
        staged = Path(scratch) / 'decision.csv'
        with staged.open('x', newline='', encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(names)
            writer.writerows(matrix.tolist())
        # A complete file becomes visible at the destination without overwriting it.
        path.hardlink_to(staged)


ROOT = Path(__file__).resolve().parents[2]

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scenario', type=Path)
    parser.add_argument('--protocol', type=Path, default=ROOT/'model-inputs/clinical-economic-protocol.json')
    parser.add_argument('--catalogue', type=Path, default=ROOT/'model-inputs/anzics-benchmarks.json')
    parser.add_argument('--source-register', type=Path, default=ROOT/'conductor/evidence/source-register.json')
    parser.add_argument('--decision-surface', type=Path,
                        help='Export SYNTHETIC annual programme decision draws for Voiage (CSV)')
    parser.add_argument('--one-way-strategy', type=str,
                        help='Add one-at-a-time 5th/95th prior-quantile sensitivity for a proposed strategy')
    parser.add_argument('--require-local-ready', action='store_true')
    parser.add_argument('--require-investment-ready', action='store_true')
    args = parser.parse_args(argv)
    try:
        from .p4_model import (EconomicScenario, evaluate_scenarios,
                               financial_decision_surface, summarise_p4)
        scenario = EconomicScenario.model_validate_json(args.scenario.read_text(encoding='utf-8'))
        from .p4_admission import admit_p4
        evidence = admit_p4(
            scenario,
            json.loads(args.protocol.read_text(encoding='utf-8')),
            json.loads(args.catalogue.read_text(encoding='utf-8')),
            json.loads(args.source_register.read_text(encoding='utf-8')),
        )
        run = evaluate_scenarios(scenario)
        report = summarise_p4(run)
        report['P4_source_admission'] = evidence
        if args.one_way_strategy is not None:
            from .p4_model import one_way_sensitivity
            report['one_way_sensitivity'] = {
                'strategy_id': args.one_way_strategy,
                'status': 'illustrative_prior_diagnostic_not_joint_posterior',
                'drivers': one_way_sensitivity(scenario, args.one_way_strategy),
            }
        payload = json.dumps(report, indent=2, sort_keys=True, allow_nan=False)
        if args.require_local_ready or args.require_investment_ready:
            print(payload)
            print('UNVERIFIED: approved local data, clinical safety and native Dapane/Voiage gates remain open',
                  file=sys.stderr)
            return 2
        if args.decision_surface is not None:
            matrix, names = financial_decision_surface(run)
            _write_surface(args.decision_surface, names, matrix)
        print(payload)
        return 0
    except (OSError, ValueError, TypeError) as error:
        print(f'P4 INVALID_OR_UNVERIFIED: {type(error).__name__}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
