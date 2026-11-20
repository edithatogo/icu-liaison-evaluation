"""Rasterise source-verified P9 SVGs at the four visual review sizes."""
from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

from PIL import Image, ImageOps, __version__ as pillow_version

ROOT = Path(__file__).resolve().parents[1]


def capture(bundle: Path, output: Path, f01: Path | None = None) -> dict:
    if output.exists() or output.is_symlink() or output.resolve().is_relative_to(bundle.resolve()):
        raise ValueError('choose a fresh capture directory outside the figure bundle')
    manifest_file = bundle / 'manifest.json'
    manifest_bytes = manifest_file.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get('data_class') != 'synthetic' or manifest.get('investment_ready') is not False:
        raise ValueError('expected a fictional P9 figure bundle')
    figures = []
    for record in manifest['figures']:
        key, filename = record['id'], record['svg']
        if not key.isascii() or len(key) != 3 or key[0] != 'F' or not key[1:].isdigit() or filename != f'{key.lower()}.svg':
            raise ValueError('unsafe figure identity')
        figures.append((key, bundle / filename, manifest['files_sha256'][filename]))
    if f01 is not None:
        from icu_liaison.p11_figure import verify_figure
        record = verify_figure(f01)
        model = f01.parent.parent / 'models' / record['model_run_id']
        summary = json.loads((model / 'p5-report/model-summary.json').read_bytes())
        if summary['input_digest_sha256'] != manifest['model_input_sha256']:
            raise ValueError('F01 and P9 describe different scenarios')
        filename = 'scenario-comparison.svg'
        figures.insert(0, ('F01', f01 / filename, record['files_sha256'][filename]))
    profiles = json.loads((ROOT / 'contracts/reporting/visual-review.json').read_text())['required_profiles']
    version = subprocess.check_output(['rsvg-convert', '--version'], text=True, timeout=10).splitlines()[0]
    entries = []
    output.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='.p9-capture-', dir=output.parent) as temporary:
        staging = Path(temporary) / 'captures'
        staging.mkdir()
        for key, svg, expected_hash in figures:
            if svg.is_symlink() or not svg.is_file():
                raise ValueError('missing or symlinked SVG')
            source_bytes = svg.read_bytes()
            source_sha256 = hashlib.sha256(source_bytes).hexdigest()
            if source_sha256 != expected_hash:
                raise ValueError('SVG changed since its bundle was reviewed')
            for profile in profiles:
                name = profile['id']
                width, height = profile['width_px'], profile['height_px']
                grayscale = name == 'print_a4'
                # Match the index width cap and padding at each screen width. The
                # A4 portrait capture also retains the 14 mm print gutter.
                pad = 53 if grayscale else 16 + max(10, min(20, round(width * .025)))
                raster = subprocess.run(
                    ['rsvg-convert', '--width', str(min(560, width - 2 * pad)),
                     '--height', str(height - 2 * pad), '--keep-aspect-ratio',
                     '--background-color', 'white'],
                    input=source_bytes, capture_output=True, check=True, timeout=30,
                )
                with Image.open(BytesIO(raster.stdout)) as rendered:
                    image = rendered.convert('RGB')
                page = Image.new('RGB', (width, height), 'white')
                page.paste(image, ((width - image.width) // 2, pad))
                if grayscale:
                    page = ImageOps.grayscale(page)
                target = staging / f'{key}-{name}.png'
                page.save(target)
                entries.append({
                    'figure': key, 'profile': name, 'width': width, 'height': height,
                    'grayscale': grayscale, 'file': target.name, 'svg_sha256': source_sha256,
                    'capture_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                })
        result = {
            'status': 'rasters_captured_for_visual_review',
            'bundle_manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(),
            'svg_renderer': version, 'pillow': pillow_version, 'captures': entries,
        }
        (staging / 'captures.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
        if output.exists() or output.is_symlink():
            raise FileExistsError('capture directory appeared during generation')
        staging.rename(output)
    return result


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('figures', type=Path)
    cli.add_argument('output', type=Path)
    cli.add_argument('--f01', type=Path, help='Matching P11 F01 revision directory')
    args = cli.parse_args()
    record = capture(args.figures, args.output, args.f01)
    print(json.dumps({'status': record['status'], 'captures': len(record['captures'])}))


if __name__ == '__main__':
    # The optional P11 reader also imports repository-owned workflow tools.
    sys.path.insert(0, str(ROOT))
    main()
