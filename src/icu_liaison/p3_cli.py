"""P3 public-metadata checks and controlled local data-source audit.

No network access, no implicit source fetch, no rows output. A local approval
acknowledgement records an operator assertion, not authority granted by software.
"""
from __future__ import annotations
from typing import Any

import argparse
import json
from pathlib import Path
import subprocess
import sys

from .local_data import LocalDatasetError, load_and_audit
from .public_evidence import Catalogue, audit_publisher_receipt, reconcile_catalogue


def _write_report(report: dict[str, Any], output: Path | None) -> None:
    data=json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)+'\n'
    if output is None:
        print(data, end='')
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() or output.is_symlink():
        raise ValueError('output path must be new and nonsymlinked')
    # Refuse pre-existing overwrite or accidental world-readable file creation.
    with open(output, 'x', encoding='utf-8', opener=_private_opener) as file:
        file.write(data)


def _private_opener(path: str, flags: int) -> int:
    import os
    return os.open(path, flags, 0o600)


def _restricted_output_allowed(output: Path, project_root: Path) -> bool:
    # An installed entry point may live outside the destination checkout.
    target = output.resolve()
    checkout = next((parent for parent in target.parents if (parent / '.git').exists()), None)
    if checkout is not None:
        relative = target.relative_to(checkout)
        if relative.parts[0] not in {'.local', 'private'}:
            return False
        ignored = subprocess.run(
            ['git', '-C', str(checkout), 'check-ignore', '--quiet', '--', str(relative)],
            capture_output=True, check=False,
        )
        return ignored.returncode == 0
    try:
        sub = target.relative_to(project_root.resolve())
    except ValueError:
        return True
    return bool(sub.parts and sub.parts[0] in {'.local', 'private'})


def _require_private_output(output: Path | None) -> None:
    if (
        output is None or output.is_symlink() or output.exists()
        or not _restricted_output_allowed(output, Path(__file__).resolve().parents[2])
    ):
        raise LocalDatasetError('restricted aggregate report requires a new private output destination')


def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command', required=True)
    sources=sub.add_parser('sources', help='Check source metadata and optionally a saved publisher receipt')
    sources.add_argument('--catalogue', type=Path, required=True)
    sources.add_argument('--source-register', type=Path, required=True)
    sources.add_argument('--publisher-receipt', type=Path, help='Recorded ANZICS 2024/25 publisher check')
    sources.add_argument('--publisher-document', type=Path, help='Saved PDF to match to the recorded digest')
    sub.add_parser('schema', help='Emit canonical JSON Schema for source manifest and CSV feed rows')
    audit=sub.add_parser('audit', help='Audit a strictly pseudonymised, hashed and governance-scoped feed')
    audit.add_argument('--manifest', type=Path, required=True)
    audit.add_argument('--dictionary', type=Path, required=True)
    audit.add_argument('--acknowledge-approved-processing', action='store_true')
    audit.add_argument('--private-output', type=Path)
    args=parser.parse_args(argv)
    if args.command == 'sources' and args.publisher_document and not args.publisher_receipt:
        sources.error('--publisher-document requires --publisher-receipt')
    try:
        if args.command == 'schema':
            from .local_data import DatasetManifest, FEED_MODELS
            _write_report({
                'schema_version':1,
                'schemas':{
                    'manifest':DatasetManifest.model_json_schema(),
                    **{key:model.model_json_schema() for key,model in FEED_MODELS.items()},
                },
            },None)
            return 0
        if args.command=='sources':
            registry = json.loads(args.source_register.read_bytes())
            c = reconcile_catalogue(Catalogue.model_validate_json(args.catalogue.read_bytes()), registry)
            report={
                'schema_version':1,'status':'CATALOGUE_METADATA_ADMITTED_NOT_DOCUMENT_VERIFIED',
                'external_only':True,'metrics':len(c['metrics']),
                'unverified_document_count':sum(m['verification_status']!='document_hash_attested_and_substantively_reviewed' for m in c['metrics']),
                'source_ids':sorted(set(m['source_id'] for m in c['metrics'])),
                'eligible_local_72h_readmission_rate_available':False,
            }
            if args.publisher_receipt is not None:
                report['publisher_check'] = audit_publisher_receipt(
                    args.publisher_receipt, registry, document_path=args.publisher_document,
                )
            _write_report(report,None)
            return 0
        report = load_and_audit(
            args.manifest,
            restricted_acknowledged=args.acknowledge_approved_processing,
            data_dictionary_path=args.dictionary,
            before_restricted_read=lambda: _require_private_output(args.private_output),
        )
        if report['data_class'] == 'restricted':
            _require_private_output(args.private_output)
        _write_report(report, args.private_output)
        if report['data_class'] == 'restricted':
            print('RESTRICTED_SOURCE_AUDITED: aggregate report written to private destination; clinical approval remains unverified')
        return 0
    except (KeyError, TypeError, ValueError, OSError) as error:
        # Fail closed without patient rows, source fields or Pydantic values.
        kind = 'UNVERIFIED' if args.command=='audit' else 'INVALID_SOURCE'
        print(f'{kind}: source or governance admission failed ({type(error).__name__})',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
