"""Audit an externally supplied *synthetic* ICU occupancy trace (not a DES runner)."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from .p6_capacity import TraceBundle, audit_trace_bundle


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path, help='versioned synthetic trace JSON')
    args = parser.parse_args(argv)
    try:
        data = args.trace.read_bytes()
        bundle = TraceBundle.model_validate_json(data)
        result = audit_trace_bundle(bundle)
        result['trace_sha256'] = hashlib.sha256(data).hexdigest()
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except (OSError, ValueError):
        print('P6 INVALID_OR_UNQUALIFIED_TRACE: rejected source or capacity trace', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
