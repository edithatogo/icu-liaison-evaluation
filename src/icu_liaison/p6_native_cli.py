"""Run a hash-checked candidate native Kairos consumer, never silently emulate one."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .p6_native import invoke_native_binary

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scenario', type=Path)
    parser.add_argument('--binary', type=Path, help='locally built native executable')
    parser.add_argument('--expected-binary-sha256', type=str)
    parser.add_argument('--provider-lock', type=Path,
                        default=ROOT / 'model-inputs/p6/kairos-provider-lock.json')
    args = parser.parse_args(argv)
    if not args.binary or not args.expected_binary_sha256:
        print('P6 UNVERIFIED: native executable and approved byte digest are required',
              file=sys.stderr)
        return 2
    try:
        lock = json.loads(args.provider_lock.read_text(encoding='utf-8'))
        report = invoke_native_binary(args.binary, args.scenario,
                                      expected_sha256=args.expected_binary_sha256,
                                      provider_lock=lock)
        print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except (OSError, ValueError, RuntimeError):
        print('P6 UNVERIFIED: native execution or output validation failed', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
