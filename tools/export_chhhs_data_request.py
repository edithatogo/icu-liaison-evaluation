"""Render the approved-for-request (not approved-to-extract) CHHHS specification."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from icu_liaison.data_request import DataRequestCatalogue, render_request_csv, render_request_markdown

ROOT = Path(__file__).resolve().parents[1]


def export_request(request: DataRequestCatalogue, destination: Path) -> None:
    """Write the paired renderings and roll back files created by a failed export."""
    if destination.is_symlink() or destination.resolve() in {ROOT.resolve(), Path('/').resolve()}:
        raise ValueError('choose an isolated output directory')
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise FileExistsError('destination must be a new or empty directory')
    renderings = (
        ('CHHHS_ICU_Liaison_Data_Extraction_Request.md', render_request_markdown(request)),
        ('CHHHS_ICU_Liaison_Fields.csv', render_request_csv(request)),
    )
    destination.mkdir(parents=True, exist_ok=True)
    created: list[tuple[Path, os.stat_result]] = []
    try:
        for name, content in renderings:
            path = destination / name
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                created.append((path, os.fstat(stream.fileno())))
                stream.write(content)
    except BaseException:
        for path, previous in reversed(created):
            try:
                if os.path.samestat(path.lstat(), previous):
                    path.unlink()
            except FileNotFoundError:
                continue
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--source', type=Path, default=ROOT / 'model-inputs/chhhs-data-request.json')
    args = parser.parse_args()
    try:
        request = DataRequestCatalogue.model_validate_json(args.source.read_bytes())
        export_request(request, args.output_dir)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    print(f'Data request exported: {len(request.datasets)} datasets; no observed hospital records')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
