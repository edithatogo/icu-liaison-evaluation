"""Export an independently auditable, synthetic P4 cost-consequence report."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

from .p4_model import EconomicScenario
from .p5_reporting import build_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scenario',type=Path)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--protocol',type=Path)
    parser.add_argument('--catalogue',type=Path)
    parser.add_argument('--source-register',type=Path)
    parser.add_argument('--voiage',action='store_true',help='Require actual Voiage provider; fail if unavailable')
    parser.add_argument('--dapane',action='store_true',help='Require actual Dapane valuation; fail if unavailable')
    parser.add_argument('--plots',action='store_true',help='Create optional matplotlib SVG scenario chart')
    parser.add_argument('--require-investment-ready',action='store_true')
    args=parser.parse_args(argv)
    if args.require_investment_ready:
        print('UNVERIFIED: CHHHS clinical safety, causality, financing and provider qualification missing',file=sys.stderr)
        return 2
    try:
        scenario=EconomicScenario.model_validate_json(args.scenario.read_text(encoding='utf-8'))
        result=build_report(scenario,args.output_dir,protocol=args.protocol,catalogue=args.catalogue,
                            source_register=args.source_register,
                            voiage_mode='provider' if args.voiage else 'skip',
                            dapane_mode='provider' if args.dapane else 'skip', plots=args.plots)
    except (ValueError,TypeError,OSError,RuntimeError) as exc:
        # Deliberately do not echo user-provided source contents or raw extracts.
        print(f'P5 INVALID_OR_UNVERIFIED: {type(exc).__name__}',file=sys.stderr)
        return 2
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
