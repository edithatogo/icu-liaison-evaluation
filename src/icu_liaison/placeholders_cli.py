"""Audit unresolved evidence placeholders or run all existing tracks synthetically."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .placeholders import (
    audit_placeholders, build_synthetic_progress_bundle,
    inspect_replacement_candidates, load_registry,
)

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    audit = sub.add_parser('audit',help='Validate all placeholder bindings and show the open gates')
    audit.add_argument('--registry',type=Path,default=ROOT/'model-inputs/placeholders/registry.json')
    audit.add_argument('--require-site-ready',action='store_true')
    review = sub.add_parser('review-candidates',help='Hash-check private evidence candidates without claiming approval')
    review.add_argument('--registry',type=Path,default=ROOT/'model-inputs/placeholders/registry.json')
    review.add_argument('--submission',type=Path,required=True)
    dry = sub.add_parser('dry-run',help='Run P3–P6 against public synthetic placeholders')
    dry.add_argument('--registry',type=Path,default=ROOT/'model-inputs/placeholders/registry.json')
    dry.add_argument('--output-dir',type=Path,required=True)
    args = parser.parse_args(argv)
    try:
        if args.command=='audit':
            report=audit_placeholders(load_registry(args.registry),root=ROOT)
            print(json.dumps(report,indent=2,sort_keys=True))
            if args.require_site_ready:
                print('UNVERIFIED: placeholder profile cannot qualify a site investment decision',file=sys.stderr)
                return 2
            return 0
        if args.command=='review-candidates':
            report=inspect_replacement_candidates(
                json.loads(args.submission.read_text(encoding='utf-8')),
                load_registry(args.registry), project_root=ROOT)
            print(json.dumps(report,indent=2,sort_keys=True))
            return 0
        output=build_synthetic_progress_bundle(root=ROOT,registry_path=args.registry,
                                               output_dir=args.output_dir)
        print(json.dumps(output,indent=2,sort_keys=True))
        return 0
    except (ValueError,OSError,TypeError) as exc:
        # Never print user-file contents, pseudonyms, or evidence paths.
        print(f'UNVERIFIED_PLACEHOLDER: {type(exc).__name__}',file=sys.stderr)
        return 2


if __name__=='__main__':
    raise SystemExit(main())
