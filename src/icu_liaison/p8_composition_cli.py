"""P8.4 auditable source-only composition; never a CHHHS investment admission."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from pydantic import ValidationError

from .p4_model import EconomicScenario, evaluate_scenarios
from .p8_composition import FictionalFundingPrice, compose_p8_shadow


def _unique(pairs: list[tuple[str, object]]) -> dict:
    out={}
    for k,v in pairs:
        if k in out:
            raise ValueError('duplicate JSON key')
        out[k]=v
    return out


def _load(path: Path) -> dict:
    if path.stat().st_size > 2_000_000:
        raise ValueError('oversized scenario or provider output')
    content=json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=_unique,
                       parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    if not isinstance(content,dict):
        raise ValueError('scenario must be a JSON object')
    return content


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description='Strict synthetic ABF/workforce/P4 source-only crosswalk')
    parser.add_argument('scenario', type=Path)
    parser.add_argument('--strategy',required=True)
    parser.add_argument('--mchs-result',type=Path)
    parser.add_argument('--workforce-result',type=Path)
    parser.add_argument('--roster-scenario-id')
    parser.add_argument('--funding-pricing-year', type=int, choices=(2024, 2025))
    parser.add_argument('--assumed-aud-per-nwau', help='Fictional episode sensitivity price in AUD per NWAU')
    parser.add_argument('--voiage-objective', choices=('net_resource', 'budget'),
                        help='Run Voiage on the selected pair and financial perspective')
    parser.add_argument('--require-qualified',action='store_true')
    args=parser.parse_args(argv)
    if args.require_qualified:
        print('UNVERIFIED: installed providers, local CHHHS evidence and approval are absent',file=sys.stderr)
        return 2
    try:
        price = None
        if args.funding_pricing_year is not None or args.assumed_aud_per_nwau is not None:
            price = FictionalFundingPrice.model_validate({
                'pricing_year': args.funding_pricing_year, 'aud_per_nwau': args.assumed_aud_per_nwau,
            })
        scenario=EconomicScenario.model_validate(_load(args.scenario))
        run=evaluate_scenarios(scenario)
        result=compose_p8_shadow(run,strategy_id=args.strategy,
                                 mchs_result=_load(args.mchs_result) if args.mchs_result else None,
                                 workforce_result=_load(args.workforce_result) if args.workforce_result else None,
                                 expected_roster_scenario_id=args.roster_scenario_id,
                                 fictional_funding_price=price, voiage_objective=args.voiage_objective)
    except (OSError,ValueError,TypeError,ValidationError,RuntimeError,OverflowError) as exc:
        # Keep raw hospital identifiers and local amounts out of errors.
        print(f'P8.4 INVALID_OR_UNVERIFIED: {type(exc).__name__}',file=sys.stderr)
        return 2
    print(json.dumps(result,sort_keys=True,allow_nan=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
