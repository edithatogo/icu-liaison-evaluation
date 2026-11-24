"""Render the approved-for-request (not approved-to-extract) CHHHS specification."""
from __future__ import annotations

import argparse
from pathlib import Path
from icu_liaison.data_request import DataRequestCatalogue, render_request_csv, render_request_markdown

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--source', type=Path, default=ROOT/'model-inputs/chhhs-data-request.json')
    args=p.parse_args()
    data=DataRequestCatalogue.model_validate_json(args.source.read_text(encoding='utf-8'))
    if args.output_dir.resolve() in [ROOT.resolve(),Path('/').resolve()]:
        p.error('choose an isolated output directory')
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        p.error('destination must be new or empty')
    args.output_dir.mkdir(parents=True,exist_ok=True)
    (args.output_dir / 'CHHHS_ICU_Liaison_Data_Extraction_Request.md').write_text(
        render_request_markdown(data), encoding='utf-8', newline='\n',
    )
    (args.output_dir / 'CHHHS_ICU_Liaison_Fields.csv').write_text(
        render_request_csv(data), encoding='utf-8', newline='\n',
    )
    print(f'Data request exported: {len(data.datasets)} datasets; no observed hospital records')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
