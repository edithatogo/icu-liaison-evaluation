"""Check each SVG's actual data marks against the independently loaded source rows."""
from pathlib import Path
import re
from xml.etree import ElementTree as ET

import matplotlib as mpl
from matplotlib.colors import Normalize, to_hex
import numpy as np

SVG = '{http://www.w3.org/2000/svg}'
DC = '{http://purl.org/dc/elements/1.1/}'
NUMBER = re.compile(r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?')


def _points(node):
    path = node.find(f'.//{SVG}path')
    if path is None or not path.get('d'):
        raise ValueError('SVG mark has no vector path')
    return np.array([float(value) for value in NUMBER.findall(path.get('d'))]).reshape(-1, 2)


def _affine(values, positions, direction):
    """A linear chart axis may change across renderers; positions must follow it."""
    data = np.asarray(values, dtype=float)
    pixels = np.asarray(positions, dtype=float)
    if data.size == 0 or data.shape != pixels.shape or not np.isfinite(pixels).all():
        raise ValueError('SVG mark count or coordinate is invalid')
    first, last = int(data.argmin()), int(data.argmax())
    if data[first] == data[last]:
        if not np.allclose(pixels, pixels[0], atol=.01, rtol=0):
            raise ValueError('SVG mark positions differ for equal source values')
        return None
    scale = (pixels[last] - pixels[first]) / (data[last] - data[first])
    origin = pixels[first] - data[first] * scale
    if scale * direction <= 0 or not np.allclose(pixels, origin + data * scale, atol=.01, rtol=0):
        raise ValueError('SVG mark positions differ from ordered source values')
    return origin


def _text(nodes, gid, expected):
    node = nodes.get(gid)
    visible = node.find(f'.//{SVG}text') if node is not None else None
    if visible is None or ''.join(visible.itertext()) != expected:
        raise ValueError(f'SVG mark label differs from source: {gid}')
    return float(visible.get('x')), float(visible.get('y'))


def _bars(nodes, rows, prefix, x0, x1):
    values, positions = [], []
    for idx, row in enumerate(rows):
        if row[x0] is None:
            continue
        node = nodes.get(f'{prefix}-{idx}')
        if node is None:
            raise ValueError('SVG mark is missing a source interval')
        points = _points(node)
        values.extend(sorted((row[x0], row[x1])))
        positions.extend((points[:, 0].min(), points[:, 0].max()))
    return _affine(values, positions, 1) if values else None


def _zero(nodes, origin, dimension):
    node = nodes.get('resource-zero')
    if node is None:
        raise ValueError('SVG mark is missing its resource zero reference')
    if origin is not None and not np.allclose(_points(node)[:, dimension], origin, atol=.01, rtol=0):
        raise ValueError('SVG resource zero mark differs from the data axis')


def _rectangle(node):
    if node is None:
        raise ValueError('SVG coverage mark is missing its rectangle')
    points = _points(node)
    if points.shape != (4, 2) or not np.isfinite(points).all():
        raise ValueError('SVG coverage mark has invalid rectangle geometry')
    x0, x1 = points[:, 0].min(), points[:, 0].max()
    y0, y1 = points[:, 1].min(), points[:, 1].max()
    corners = {(round(float(x), 3), round(float(y), 3)) for x, y in points}
    expected = {(round(float(x), 3), round(float(y), 3)) for x in (x0, x1) for y in (y0, y1)}
    if x0 >= x1 or y0 >= y1 or corners != expected:
        raise ValueError('SVG coverage mark is not a rectangle')
    return np.array([x0, x1, y0, y1])


def _cell_bounds(bounds, day, hour):
    x0, x1, y0, y1 = bounds
    dx, dy = (x1 - x0) / 24, (y1 - y0) / 7
    return np.array([x0 + hour * dx, x0 + (hour + 1) * dx,
                     y0 + day * dy, y0 + (day + 1) * dy])


def read_accessible_svg(path: Path, figure: dict) -> ET.Element:
    """Verify the SVG title and description against the figure's catalogue entry."""
    try:
        svg = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ValueError('invalid SVG markup') from exc
    if svg.tag != f'{SVG}svg' or svg.get('role') != 'img' or svg.get('aria-labelledby') != 'figure-title figure-desc':
        raise ValueError('SVG accessibility role or label is missing')
    title, desc = svg.find(f'{SVG}title'), svg.find(f'{SVG}desc')
    description = svg.find(f'.//{DC}description')
    if (title is None or title.get('id') != 'figure-title' or title.text != figure['title']
            or desc is None or desc.get('id') != 'figure-desc' or desc.text != figure['alt_text']
            or description is None or description.text != figure['alt_text']):
        raise ValueError('SVG accessibility title or description differs from the catalogue')
    return svg


def review_svg(path, figure, rows):
    svg = read_accessible_svg(path, figure)
    nodes = {node.get('id'): node for node in svg.iter() if node.get('id')}
    marks = [node.get('id') for node in svg.iter() if node.get('id', '').startswith('data-')]
    if len(set(marks)) != len(marks):
        raise ValueError('duplicate SVG data mark')
    figure_id = figure['id']
    if figure_id == 'F02':
        _zero(nodes, _bars(nodes, rows, 'waterfall-bar', 'start_aud', 'end_aud'), 0)
        for idx, row in enumerate(rows):
            _text(nodes, f'waterfall-value-{idx}', f"{row['value_aud'] / 1000:+,.1f}")
    elif figure_id == 'F10':
        grid = nodes.get('breakeven-grid')
        uses = list(grid.iter(f'{SVG}use')) if grid is not None else []
        marks = uses or (list(grid.iter(f'{SVG}path')) if grid is not None else [])
        if len(marks) != len(rows):
            raise ValueError('SVG mark count differs from break-even grid')
        x_centres, y_centres = [], []
        net = np.array([row['net_resource_aud'] / 1000 for row in rows])
        low, high = net.min(), net.max()
        padding = max(.1, abs(low) * .01) if low == high else 0.
        norm = Normalize(vmin=low - padding, vmax=high + padding)
        fills = [to_hex(value) for value in mpl.colormaps['cividis'](norm(net))]
        for mark, fill in zip(marks, fills, strict=True):
            if f'fill: {fill}' not in mark.get('style', ''):
                raise ValueError('SVG heatmap mark differs from its source value')
            if uses:
                reference = mark.get('{http://www.w3.org/1999/xlink}href', '')
                shape = nodes.get(reference.removeprefix('#')) if reference.startswith('#') else None
                if shape is None or shape.tag != f'{SVG}path' or not shape.get('d'):
                    raise ValueError('SVG fixed-prior mark has no visible shape')
                xpos, ypos = float(mark.get('x')), float(mark.get('y'))
                vertices = np.array([float(v) for v in NUMBER.findall(shape.get('d'))]).reshape(-1, 2)
                bounds = _rectangle(nodes.get('breakeven-background'))
                if (vertices.shape != (4, 2)
                        or not bounds[0] <= xpos + vertices[:, 0].min() < xpos + vertices[:, 0].max() <= bounds[1]
                        or not bounds[2] <= ypos + vertices[:, 1].min() < ypos + vertices[:, 1].max() <= bounds[3]):
                    raise ValueError('SVG fixed-prior mark is clipped by its chart')
                view = [float(value) for value in svg.get('viewBox', '').split()]
                if (len(view) != 4 or not view[0] <= xpos <= view[0] + view[2]
                        or not view[1] <= ypos <= view[1] + view[3]):
                    raise ValueError('SVG fixed-prior mark is outside the view')
                x_centres.append(xpos)
                y_centres.append(ypos)
            else:
                points = np.array([float(v) for v in NUMBER.findall(mark.get('d', ''))]).reshape(-1, 2)
                x_centres.append((points[:, 0].min() + points[:, 0].max()) / 2)
                y_centres.append((points[:, 1].min() + points[:, 1].max()) / 2)
        _affine([row['delay_success'] for row in rows], x_centres, 1)
        _affine([row['annual_cost_aud'] for row in rows], y_centres, -1)
        crossing, touching = net.min() < 0 < net.max(), net.min() == 0 or net.max() == 0
        if ('breakeven-zero' in nodes) != crossing or ('breakeven-touch' in nodes) != touching:
            raise ValueError('SVG break-even mark does not match the feasible grid')
    elif figure_id == 'F11':
        scatter = nodes.get('paired-scatter')
        dots = list(scatter.iter(f'{SVG}use')) if scatter is not None else []
        _affine([row['released_icu_bed_days'] for row in rows], [dot.get('x') for dot in dots], 1)
        _zero(nodes, _affine([row['net_resource_aud'] for row in rows],
                             [dot.get('y') for dot in dots], -1), 1)
    elif figure_id == 'F15':
        _bars(nodes, rows, 'journey-bar', 'start_minute', 'end_minute')
        for idx, row in enumerate(rows):
            if row['start_minute'] is None:
                _text(nodes, f'journey-unknown-{idx}', 'Readiness unknown')
                if f'journey-bar-{idx}' in nodes:
                    raise ValueError('SVG mark replaces unknown readiness with a numeric bar')
    elif figure_id == 'F20':
        coverage_grid = _rectangle(nodes.get('coverage-grid-background'))
        demand_grid = _rectangle(nodes.get('demand-grid-background'))
        view = np.asarray([float(v) for v in svg.get('viewBox', '').split()])
        if (view.shape != (4,) or not np.isfinite(view).all()
                or view[2] <= 0 or view[3] <= 0):
            raise ValueError('SVG coverage chart has invalid view bounds')
        for x0, x1, y0, y1 in (coverage_grid, demand_grid):
            if x0 < view[0] or x1 > view[0] + view[2] or y0 < view[1] or y1 > view[1] + view[3]:
                raise ValueError('SVG coverage chart grid is outside the view')
        for row in rows:
            suffix = f"{row['day']}-{row['hour']}"
            paid = nodes.get(f'coverage-{suffix}')
            if (paid is not None) != bool(row['paid_staff_hours']):
                raise ValueError('SVG paid coverage mark differs from fixture')
            if paid is not None:
                if not np.allclose(_rectangle(paid), _cell_bounds(coverage_grid, row['day'], row['hour']),
                                   atol=.01, rtol=0):
                    raise ValueError('SVG paid coverage geometry differs from its source hour')
                mark = paid.find(f'.//{SVG}path')
                style = mark.get('style', '')
                hatched = 'fill: url(' in style
                if hatched == bool(row['productive_staff_hours']):
                    raise ValueError('SVG productive coverage hatch differs from fixture')
                if (row['productive_staff_hours'] and 'fill: #196872' not in style
                        or 'opacity: 0' in style or 'display: none' in style):
                    raise ValueError('SVG paid coverage mark is not visible')
            count = row['eligible_readiness_cases']
            cell = nodes.get(f'demand-cell-{suffix}')
            if count:
                bounds = _cell_bounds(demand_grid, row['day'], row['hour'])
                if not np.allclose(_rectangle(cell), bounds, atol=.01, rtol=0):
                    raise ValueError('SVG demand cell geometry differs from its source hour')
                if 'fill: #dce9ec' not in cell.find(f'.//{SVG}path').get('style', ''):
                    raise ValueError('SVG demand mark is not visible')
                x, y = _text(nodes, f'demand-{suffix}', str(count))
                if not np.isclose(x, (bounds[0] + bounds[1]) / 2, atol=.01, rtol=0) or not bounds[2] <= y <= bounds[3]:
                    raise ValueError('SVG demand mark lies outside its source hour')
            elif f'demand-{suffix}' in nodes or cell is not None:
                raise ValueError('SVG mark invents demand for a known empty hour')
    elif figure_id == 'F24':
        for panel, field, divisor in (('money', 'mean_net_resource_aud', 1000),
                                      ('returns', 'mean_returns_avoided', 1)):
            positions = [_text(nodes, f'{panel}-{idx}', f'{row[field] / divisor:+.1f}')
                         for idx, row in enumerate(rows)]
            cols, lines = zip(*positions, strict=True)
            # Each tested effect is a category, including unevenly spaced priors.
            effects = sorted({row['relative_return_reduction'] for row in rows})
            delays = sorted({row['delay_success'] for row in rows})
            _affine([effects.index(row['relative_return_reduction']) for row in rows], cols, 1)
            _affine([delays.index(row['delay_success']) for row in rows], lines, -1)
            if f'null-{panel}' not in nodes:
                raise ValueError('SVG mark for the joint null is missing')
    else:
        from .p9_supplement_data import SUPPLEMENT_IDS
        from .p9_supplement_review import check_supplement
        if figure_id not in SUPPLEMENT_IDS:
            raise ValueError('unregistered synthetic figure')
        check_supplement(nodes, figure_id, rows)
