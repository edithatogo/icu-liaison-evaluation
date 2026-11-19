"""Synthetic-only ICU evaluation P8 provider-consumer CLI (no hidden fallback)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from pydantic import ValidationError
from .adapters.p8_mchs import MchsPair, run_mchs_pair
from .adapters.p8_workforce import RosterScenario, prepare_workforce_dapane_request


def _no_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate input key")
        result[key] = value
    return result


def _load(path: Path) -> dict:
    if path.stat().st_size > 2_000_000:
        raise ValueError("P8 synthetic input is too large")
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)
    if not isinstance(data, dict):
        raise ValueError("P8 input must be an object")
    return data


def _emit(message: dict) -> None:
    print(json.dumps(message, sort_keys=True, allow_nan=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bounded, synthetic-only MCHS and workforce consumer")
    parser.add_argument("action", choices=("inspect-mchs", "inspect-roster", "run-mchs", "build-roster"))
    parser.add_argument("input", type=Path)
    parser.add_argument("--ref-dir", default=None,
                        help="Explicit installed MCHS annual calculator reference directory")
    args = parser.parse_args(argv)
    try:
        data = _load(args.input)
        if args.action.endswith("mchs"):
            case = MchsPair.model_validate(data)
            if args.action == "inspect-mchs":
                _emit({"status": "VALIDATED_SYNTHETIC_INPUT", "episode_id": case.episode_id,
                       "pricing_year": case.pricing_year, "drg_edition": case.drg_edition,
                       "installed_provider_executed": False, "cash_or_revenue_verified": False})
                return 0
            output = run_mchs_pair(case, ref_dir=args.ref_dir)
            _emit({"status": "PROVIDER_SOURCE_ONLY_UNQUALIFIED",
                   "installed_provider_executed": True, "cash_or_revenue_verified": False,
                   "result": output})
            return 0
        roster = RosterScenario.model_validate(data)
        if args.action == "inspect-roster":
            _emit({"status": "VALIDATED_SYNTHETIC_INPUT", "scenario_id": roster.scenario_id,
                   "segments": len(roster.exposures), "completeness": roster.completeness_status,
                   "installed_provider_executed": False, "cash_or_revenue_verified": False})
            return 0
        output = prepare_workforce_dapane_request(roster)
        _emit({"status": "PROVIDER_SOURCE_ONLY_UNQUALIFIED", "installed_provider_executed": True,
               "cash_or_revenue_verified": False, "result": output})
        return 0
    except (ImportError, RuntimeError) as exc:
        _emit({"status": "UNVERIFIED", "installed_provider_executed": False,
               "reason": type(exc).__name__, "cash_or_revenue_verified": False})
        return 2
    except (ValidationError, ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
        # Do not echo rejected payload values in a CLI diagnostic.
        _emit({"status": "INVALID", "reason": type(exc).__name__})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
