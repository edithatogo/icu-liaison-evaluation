"""Read the F01 mean bars and percentile whiskers against the labelled SVG axes."""
from __future__ import annotations

import re
from pathlib import Path
from numpy.typing import ArrayLike, NDArray
from typing import Any
from xml.etree import ElementTree as ET

import numpy as np

SVG = '{http://www.w3.org/2000/svg}'
UNSIGNED = r'(?:\d*\.\d+|\d+\.?)(?:[eE][+-]?\d+)?'
NUMBER = rf'[+-]?{UNSIGNED}'


def _label(group: ET.Element) -> str:
    # Matplotlib stores original accessible text as an XML comment when it
    # embeds glyph outlines. Text-mode SVGs retain ordinary text nodes.
    for node in group.iter():
        tag: object = node.tag  # Comment-preserving XML parsers also emit callable sentinel tags.
        if tag in (ET.Comment, f'{SVG}text'):
            label = node.text if tag is ET.Comment else ''.join(node.itertext())
            return (label or '').strip().replace('−', '-')
    return ''


def _axis_ticks(axis: ET.Element, direction: str) -> dict[str, float]:
    ticks = {}
    for group in axis.findall(f'{SVG}g'):
        if group.get('id', '').startswith(f'{direction}tick_'):
            mark = group.find(f'.//{SVG}use')
            label = _label(group)
            if not label or label in ticks or mark is None:
                raise ValueError('F01 mark axis lacks a unique labelled tick')
            ticks[label] = float(mark.attrib[direction])
    return ticks


def _vertices(path: ET.Element) -> NDArray[np.float64]:
    commands = path.get('d', '').strip()
    if not re.fullmatch(rf'(?:[ML]\s*{NUMBER}\s+{NUMBER}\s*)+[zZ]?', commands):
        raise ValueError('F01 mark has unexpected geometry')
    return np.array([float(n) for n in re.findall(NUMBER, commands)]).reshape(-1, 2)


def _matches(actual: ArrayLike, expected: ArrayLike) -> None:
    if np.shape(actual) != np.shape(expected) or not np.allclose(actual, expected, atol=.015, rtol=0):
        raise ValueError('F01 mark differs from its labelled strategy or model summary')


def review_f01(path: Path, model: dict[str, Any]) -> dict[str, int]:
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    root = ET.parse(path, parser=parser).getroot()
    axes = root.find(f'.//{SVG}g[@id="axes_1"]')
    if axes is None:
        raise ValueError('F01 mark axes missing')
    horizontal, vertical = (axes.find(f'{SVG}g[@id="matplotlib.axis_{i}"]') for i in (1, 2))
    if horizontal is None or vertical is None:
        raise ValueError('F01 mark axis missing')
    categories = _axis_ticks(horizontal, 'x')
    ticks = _axis_ticks(vertical, 'y')
    # ScalarFormatter can express a shared multiplier and additive offset
    # above the axis. The reference line at zero remains an independent check.
    multiplier, offset = 1., 0.
    for group in vertical.findall(f'{SVG}g'):
        if group.get('id', '').startswith('text_'):
            label = _label(group)
            parts = re.fullmatch(rf'(1e[+-]?\d+)?([+-]{UNSIGNED})?', label)
            if parts and label:
                multiplier = float(parts[1] or 1.)
                offset = float(parts[2] or 0.)
    values = np.array([float(k) * multiplier + offset for k in ticks])
    positions = np.array(list(ticks.values()))
    if len(ticks) < 2 or values[0] == values[-1] or set(categories) != set(model['strategies']):
        raise ValueError('F01 mark axis differs from model categories or numeric scale')
    slope = (positions[-1] - positions[0]) / (values[-1] - values[0])
    if slope >= 0:
        raise ValueError('F01 mark has a reversed axis')

    def ordinate(value: ArrayLike) -> NDArray[np.float64]:
        return np.asarray(positions[0] + (np.asarray(value) - values[0]) * slope, dtype=np.float64)

    _matches(positions, ordinate(values))
    bars, lines = [], []
    for group in axes.findall(f'{SVG}g'):
        mark = group.find(f'{SVG}path')
        if mark is None or not mark.get('clip-path'):
            continue
        label = group.get('id', '')
        if label.startswith('patch_'):
            bars.append(_vertices(mark))
        elif label.startswith('line2d_'):
            lines.append(_vertices(mark))
    if len(bars) != len(categories) or len(lines) != len(categories) + 1:
        raise ValueError('F01 mark count differs from model strategies')
    for (name, x), bar, whisker in zip(categories.items(), bars, lines[:-1], strict=True):
        stats = model['strategies'][name]['net_resource_benefit_aud']
        if len(bar) != 4 or bar[0, 0] >= bar[1, 0]:
            raise ValueError('F01 mark is not a mean bar')
        _matches(bar[:, 0], [bar[0, 0], bar[1, 0], bar[1, 0], bar[0, 0]])
        _matches((bar[0, 0] + bar[1, 0]) / 2, x)
        _matches(bar[:, 1], ordinate([0., 0., stats['mean'], stats['mean']]))
        _matches(whisker[:, 0], [x, x])
        _matches(whisker[:, 1], ordinate([stats['p05'], stats['p95']]))
    _matches(lines[-1][:, 1], ordinate([0., 0.]))
    return {'mean_bars': len(bars), 'percentile_intervals': len(bars), 'zero_reference': True}
