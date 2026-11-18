"""Command-line entry for the standalone illustrative cohort PSA."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .model import simulate, summarise
from .schemas import Scenario


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scenario', type=Path, help='JSON scenario (synthetic inputs only)')
    args = parser.parse_args(argv)
    scenario = Scenario.model_validate_json(args.scenario.read_text(encoding='utf-8'))
    print(json.dumps(summarise(simulate(scenario)), sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
