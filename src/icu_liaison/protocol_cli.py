"""Validate P2 protocol against synthetic P1 input and private-data requirements."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from .protocol import EvaluationProtocol, admit_protocol, load_data_dictionary
from .schemas import Scenario


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('protocol', type=Path)
    parser.add_argument('scenario', type=Path)
    parser.add_argument('--data-dictionary', type=Path, default=None,
                        help='Validate local data field requirements, not local data itself')
    parser.add_argument('--require-local-ready', action='store_true',
                        help='Exit 2 while only illustrative inputs have been admitted')
    args = parser.parse_args(argv)
    try:
        protocol = EvaluationProtocol.model_validate_json(args.protocol.read_text(encoding='utf-8'))
        scenario = Scenario.model_validate_json(args.scenario.read_text(encoding='utf-8'))
        report = admit_protocol(protocol, scenario)
        if args.data_dictionary is not None:
            dictionary_bytes = args.data_dictionary.read_bytes()
            d = load_data_dictionary(args.data_dictionary)
            report['data_dictionary'] = {
                'status': d['status'], 'field_count': len(d['fields']),
                'sha256': hashlib.sha256(dictionary_bytes).hexdigest(),
            }
    except (OSError, ValueError, TypeError) as exc:
        print(f'P2 protocol validation failed: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.require_local_ready and not report['ready_for_local_claims']:
        print('UNVERIFIED: CHHHS observed inputs, causal effects, safety and budget qualification required', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
