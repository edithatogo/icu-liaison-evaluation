"""Independently inspect a published P5 bundle without rerunning P4."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .p5_reporting import review_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report_dir', type=Path)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(review_report(args.report_dir), indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError):
        print('P5 REVIEW_UNVERIFIED: bundle integrity or semantics rejected', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
