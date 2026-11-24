"""Command-line entry for the standalone illustrative cohort PSA."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from pydantic import ValidationError

from .model import simulate, summarise
from .schemas import Scenario


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scenario', type=Path, help='JSON scenario (synthetic inputs only)')
    args = parser.parse_args(argv)
    try:
        scenario = Scenario.model_validate_json(args.scenario.read_bytes())
    except OSError:
        parser.error('could not read the scenario file')
    except ValidationError as exc:
        parser.error(f'invalid synthetic scenario ({exc.error_count()} validation errors)')
    try:
        report = json.dumps(summarise(simulate(scenario)), sort_keys=True, indent=2, allow_nan=False)
    except ValueError:
        parser.error('scenario could not produce finite output')
    print(report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
