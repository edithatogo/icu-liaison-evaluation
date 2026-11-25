"""Check supplementary SVG positions against source values and the visible axes."""
import numpy as np
from collections.abc import Callable
from typing import Any
from numpy.typing import ArrayLike, NDArray
from xml.etree import ElementTree as ET

from .p9_figure_review import SVG, _points


def _axis(ax: ET.Element, dimension: str) -> Callable[[ArrayLike], NDArray[np.float64]]:
    """Recover data-to-page coordinates from labelled major tick marks."""
    ticks = []
    for group in ax.iter(f'{SVG}g'):
        if not group.get('id', '').startswith(f'{dimension}tick_'):
            continue
        mark = group.find(f'.//{SVG}use')
        label = group.find(f'.//{SVG}text')
        if mark is None or label is None:
            continue
        try:
            value = float(''.join(label.itertext()).replace('−', '-').replace(',', ''))
        except ValueError:
            continue
        ticks.append((value, float(mark.attrib[dimension])))
    if len(ticks) < 2 or ticks[0][0] == ticks[-1][0]:
        raise ValueError('SVG mark axis lacks numeric references')
    a, b = ticks[0], ticks[-1]
    slope = (b[1] - a[1]) / (b[0] - a[0])
    return lambda values: a[1] + slope * (np.asarray(values) - a[0])


def _check(actual: ArrayLike, expected: ArrayLike) -> None:
    if np.shape(actual) != np.shape(expected) or not np.allclose(actual, expected, atol=.015, rtol=0):
        raise ValueError('SVG mark differs from source and labelled axis')


def check_supplement(nodes: dict[str, ET.Element], key: str, rows: list[dict[str, Any]]) -> None:
    arms = list(dict.fromkeys(r['strategy'] for r in rows if 'strategy' in r))
    count = {'F07': min(5, len(rows)), 'F09': 3 * len(arms), 'F18': 1}.get(key, len(rows))
    if {k for k in nodes if k.startswith('data-')} != {f'data-{i}' for i in range(count)}:
        raise ValueError('unexpected or missing supplementary data mark')
    points = []
    for i in range(count):
        group = nodes[f'data-{i}']
        path = group.find(f'.//{SVG}path')
        if path is None or not path.get('d') or 'opacity: 0;' in path.get('style', ''):
            raise ValueError('missing or invisible SVG mark')
        points.append(_points(group))
    ax = nodes['axes_1']
    if key == 'F05':
        y = _axis(ax, 'y')
        for row, pts in zip(rows, points, strict=True):
            _check(pts[:, 1], y([0, 0, row['mean_aud']/1000, row['mean_aud']/1000]))
    elif key == 'F06':
        x = _axis(ax, 'x')
        running = dict.fromkeys(arms, 0.)
        for row, pts in zip(rows, points, strict=True):
            start = running[row['strategy']]
            end = start + 100 * row['count'] / row['draws']
            _check(pts[:, 0], x([start, end, end, start]))
            running[row['strategy']] = end
    elif key == 'F07':
        x = _axis(ax, 'x')
        for row, pts in zip(rows[:5], points, strict=True):
            _check(pts[:, 0], x([row['lower_aud']/1000, row['upper_aud']/1000]))
        pivot = _points(nodes['nominal-pivot'])
        _check(pivot[:, 0], x([rows[0]['pivot_aud']/1000]*2))
    elif key == 'F08':
        x, y = _axis(ax, 'x'), _axis(ax, 'y')
        for row, pts in zip(rows, points, strict=True):
            lo, hi = row['lower_aud']/1000, row['upper_aud']/1000
            _check(pts[:, 0], x([lo, hi, hi, lo]))
            _check(pts[:, 1], y([0, 0, row['count'], row['count']]))
    elif key == 'F09':
        x = _axis(nodes[f'axes_{len(arms)}'], 'x')  # shared elapsed-time axis
        for i, arm in enumerate(arms):
            intervals = [r for r in rows if r['strategy'] == arm]
            y = _axis(nodes[f'axes_{i+1}'], 'y')
            for j, field in enumerate(('staffed_beds', 'occupied_beds', 'known_waiting')):
                pts = points[3*i+j]
                _check(pts[:, 0], x([v for r in intervals for v in (r['start_minute'], r['end_minute'])]))
                _check(pts[:, 1], y([r[field] for r in intervals for _ in range(2)]))
    elif key == 'F13':
        # Ribbon edge 0/7 is the origin. Vertices 3/4 are the receiving flow.
        origin = np.array([p[0, 1] - p[7, 1] for p in points])
        receiving = np.array([p[3, 1] - p[4, 1] for p in points])
        counts = np.array([r['count'] for r in rows])
        if (origin < 0).any() or (counts.sum() and origin.sum() <= 0):
            raise ValueError('SVG flow mark has reversed or absent width')
        _check(receiving, origin)
        _check(origin, counts / max(1, counts.sum()) * origin.sum())
    elif key == 'F18':
        _check(points[0][:, 0], _axis(ax, 'x')([r['week'] for r in rows]))
        _check(points[0][:, 1], _axis(ax, 'y')([r['gap_change_hours'] for r in rows]))
