"""Validate the draft P2 protocol, illustrative inputs and stakeholder review pack."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from pydantic import ValidationError

from .p2_governance import audit_governance_signoff, validate_p2_chhhs_crosswalk
from .protocol import EvaluationProtocol, admit_protocol, load_data_dictionary
from .schemas import Scenario


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('protocol', type=Path)
    parser.add_argument('scenario', type=Path)
    parser.add_argument('--data-dictionary', type=Path, default=None,
                        help='Validate local data field requirements, not local data itself')
    parser.add_argument('--field-crosswalk', type=Path,
                        help='Check the mapping from the P2 dictionary to the CHHHS request')
    parser.add_argument('--chhhs-request', type=Path,
                        help='CHHHS data request catalogue used by the field crosswalk')
    parser.add_argument('--governance-signoff', type=Path,
                        help='Audit the sign-off form and its protocol and dictionary fingerprints')
    parser.add_argument('--require-local-ready', action='store_true',
                        help='Exit 2 while only illustrative inputs have been admitted')
    args = parser.parse_args(argv)
    if (args.field_crosswalk is None) != (args.chhhs_request is None):
        parser.error('--field-crosswalk and --chhhs-request must be supplied together')
    if args.data_dictionary is None and (args.field_crosswalk or args.governance_signoff):
        parser.error('--data-dictionary is required with review-pack inputs')
    try:
        protocol_bytes = args.protocol.read_bytes()
        protocol = EvaluationProtocol.model_validate_json(protocol_bytes)
        scenario = Scenario.model_validate_json(args.scenario.read_text(encoding='utf-8'))
        report = admit_protocol(protocol, scenario)
        if args.data_dictionary is not None:
            dictionary_bytes = args.data_dictionary.read_bytes()
            d = load_data_dictionary(json.loads(dictionary_bytes))
            dictionary_sha256 = hashlib.sha256(dictionary_bytes).hexdigest()
            report['data_dictionary'] = {
                'status': d['status'], 'field_count': len(d['fields']),
                'sha256': dictionary_sha256,
            }
            if args.field_crosswalk:
                crosswalk = validate_p2_chhhs_crosswalk(
                    args.field_crosswalk, args.data_dictionary, args.chhhs_request,
                )
                if crosswalk['dictionary_sha256'] != dictionary_sha256:
                    raise ValueError('data dictionary changed during the crosswalk audit')
                report['field_crosswalk'] = crosswalk
            if args.governance_signoff:
                signoff = audit_governance_signoff(
                    args.governance_signoff, args.protocol, args.data_dictionary,
                )
                if (signoff['dictionary_sha256'] != dictionary_sha256
                    or signoff['protocol_sha256'] != hashlib.sha256(protocol_bytes).hexdigest()):
                    raise ValueError('protocol or data dictionary changed during the sign-off audit')
                report['governance_signoff'] = signoff
    except ValidationError as exc:
        error = exc.errors(include_url=False, include_context=False, include_input=False)[0]
        location = '.'.join(map(str, error['loc'])) or 'document'
        print(f'P2 protocol validation failed in {exc.title} at {location} ({error["type"]})', file=sys.stderr)
        return 2
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
