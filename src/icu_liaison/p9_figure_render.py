"""Deterministic accessible SVGs for the six priority synthetic figures."""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

import matplotlib as mpl
from matplotlib.colors import Normalize, TwoSlopeNorm
from matplotlib.figure import Figure
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter, PercentFormatter
import numpy as np

from .p9_figure_data import DAYS

INK = '#172b3b'
TEAL = '#196872'
RUST = '#9c4128'
PALE = '#dce9ec'


def _panel(title, subtitle, *, height=4.55, bottom=.18, left=.18, right=.94):
    fig = Figure(figsize=(5.7, height), facecolor='white')
    ax = fig.add_subplot()
    fig.subplots_adjust(left=left, right=right, bottom=bottom, top=.742)
    _heading(fig, title, subtitle)
    return fig, ax


def _heading(fig, title, subtitle):
    fig.text(.055, .954, title, va='top', fontsize=18, weight='bold')
    fig.text(.055, .865, subtitle, va='top', fontsize=11, linespacing=1.35)
    fig.text(.055, .035, 'FICTIONAL ILLUSTRATION', fontsize=10, color=INK, weight='bold')


def _money_label(value):
    return f'{value / 1000:+,.1f}'


def _resource_waterfall(rows, year, cohort):
    fig, ax = _panel('Incremental annual resources',
                     f'Liaison versus current care · {cohort:,} eligible discharges\n'
                     'Nominal inputs · service cost counted once',
                     left=.332, right=.82)
    labels = ['ICU delay\nresource value', '72-hour return\nresource value',
              'Liaison\nservice cost', 'Net resource\nbenefit']
    for idx, row in enumerate(rows):
        start, end = row['start_aud'] / 1000, row['end_aud'] / 1000
        colour = INK if idx == len(rows) - 1 else TEAL if end >= start else RUST
        bar, = ax.barh(idx, end - start, left=start, height=.56, color=colour)
        bar.set_gid(f'waterfall-bar-{idx}')
        value = ax.annotate(_money_label(row['value_aud']), (max(start, end), idx),
                            xytext=(5, 0), textcoords='offset points', va='center', weight='bold')
        value.set_gid(f'waterfall-value-{idx}')
        if idx < len(rows) - 2:
            ax.plot([end, end], [idx + .28, idx + .72], color=INK, linewidth=.8, linestyle='--')
    ax.axvline(0, color=INK, linewidth=.8, zorder=0).set_gid('resource-zero')
    ax.set_yticks(np.arange(len(rows)), labels)
    ax.invert_yaxis()
    ax.set_xlabel(f'Annual contribution (thousand AUD {year})')
    ax.grid(axis='x', alpha=.18)
    ax.set_axisbelow(True)
    return fig


def _break_even_grid(rows, year, cohort):
    x = sorted({row['delay_success'] for row in rows})
    y = sorted({row['annual_cost_aud'] / 1000 for row in rows})
    z = np.array([row['net_resource_aud'] / 1000 for row in rows]).reshape(len(y), len(x))
    low, high = float(z.min()), float(z.max())
    crossing = low < 0 < high
    message = ('Zero contour inside the tested bounds' if crossing else
               'Break-even touches the tested grid' if low <= 0 <= high else
               'No break-even within the tested bounds')
    fixed_x, fixed_y = len(x) == 1, len(y) == 1
    fixed = ('Both assumptions fixed' if fixed_x and fixed_y else
             f'Delay resolution fixed at {x[0]:.0%}' if fixed_x else
             f'Annual service cost fixed at {y[0]:,.1f} thousand AUD' if fixed_y else None)
    subtitle = (f'{fixed}\n{message}\nLiaison · {cohort:,} eligible discharges · other inputs nominal'
                if fixed else f'{message}\nLiaison · {cohort:,} eligible discharges · other inputs nominal')
    title = 'Resource break-even: fixed input' if fixed else 'Two-way resource break-even'
    fig, ax = _panel(title, subtitle,
                     left=.17, right=.97)
    ax.patch.set_gid('breakeven-background')
    padding = max(.1, abs(low) * .01) if low == high else 0.
    norm = Normalize(vmin=low - padding, vmax=high + padding)
    if fixed:
        fig.subplots_adjust(top=.69)
        mesh = ax.scatter([row['delay_success'] for row in rows],
                          [row['annual_cost_aud'] / 1000 for row in rows],
                          c=z.ravel(), marker='s', s=46, cmap='cividis',
                          norm=norm)
    else:
        mesh = ax.pcolormesh(x, y, z, shading='nearest', cmap='cividis',
                             norm=norm)
    mesh.set_gid('breakeven-grid')
    if crossing:
        if fixed:
            values, axis = (z[:, 0], y) if fixed_x else (z[0, :], x)
            idx = next(i for i in range(len(values) - 1) if values[i] * values[i + 1] <= 0)
            fraction = -values[idx] / (values[idx + 1] - values[idx])
            position = axis[idx] + fraction * (axis[idx + 1] - axis[idx])
            marker = ax.axhline(position, color='white', linewidth=2) if fixed_x else ax.axvline(
                position, color='white', linewidth=2)
            marker.set_gid('breakeven-zero')
        else:
            contour = ax.contour(x, y, z, levels=[0], colors=['white'], linewidths=2)
            contour.set_gid('breakeven-zero')
            ax.clabel(contour, fmt={0: 'Zero'}, fontsize=9)
    elif low <= 0 <= high:
        y_idx, x_idx = np.where(z == 0)
        ax.scatter(np.asarray(x)[x_idx], np.asarray(y)[y_idx], marker='x', color='white',
                   linewidths=1.5).set_gid('breakeven-touch')
    if fixed_x:
        ax.set_xlim(x[0] - .05, x[0] + .05)
        ax.set_xticks([x[0]])
    else:
        margin = (x[-1] - x[0]) * .04 if fixed else 0
        ax.set_xlim(x[0] - margin, x[-1] + margin)
    if fixed_y:
        margin = max(1., abs(y[0]) * .05)
        ax.set_ylim(y[0] - margin, y[0] + margin)
        ax.set_yticks([y[0]])
    else:
        margin = (y[-1] - y[0]) * .04 if fixed else 0
        ax.set_ylim(y[0] - margin, y[-1] + margin)
    ax.set_xlabel('Addressable delays resolved (%)')
    ax.set_ylabel(f'Annual service cost\n(thousand AUD {year})')
    ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    scale = fig.colorbar(mesh, ax=ax, pad=.035, shrink=.93)
    scale.set_label(f'Net resources (thousand AUD {year})', fontsize=9.5)
    return fig


def _paired_scatter(rows, year, cohort):
    fig, ax = _panel('Resources and released capacity',
                     f'Liaison versus current care · {len(rows):,} paired draws\n'
                     f'{cohort:,} eligible discharges per year',
                     left=.19)
    dots = ax.scatter([row['released_icu_bed_days'] for row in rows],
                      [row['net_resource_aud'] / 1000 for row in rows],
                      s=7, color=TEAL, edgecolors='none', alpha=.30)
    dots.set_gid('paired-scatter')
    ax.axhline(0, color=INK, linestyle='--', linewidth=1).set_gid('resource-zero')
    ax.set_xlim(left=0)
    low, high = ax.get_ylim()
    ax.set_ylim(min(0, low), max(0, high))
    ax.set_xlabel('Additional ICU bed-days released per year')
    ax.set_ylabel(f'Net resource benefit\n(thousand AUD {year})')
    ax.grid(alpha=.17)
    ax.set_axisbelow(True)
    return fig


JOURNEY_STYLES = {
    'ready_to_referral': ('Readiness to referral', PALE, ''),
    'referral_to_bed': ('Referral to ward bed', TEAL, ''),
    'bed_to_departure': ('Ward bed to departure', '#e2a68d', ''),
    'unresolved_stage': ('Unresolved stage', '#eeeeee', '///'),
}


def _journey(rows, _year, _cohort):
    fig, ax = _panel('Time from readiness to departure',
                     'Selected fictional ICU-to-ward journeys\n'
                     'Addressable time requires separate evidence',
                     height=4.85, bottom=.285, left=.208)
    labels = list(dict.fromkeys(row['episode'] for row in rows))
    for idx, row in enumerate(rows):
        at = labels.index(row['episode'])
        if row['stage'] == 'readiness_unknown':
            ax.text(.018, at, 'Readiness unknown', va='center', transform=ax.get_yaxis_transform(),
                    style='italic').set_gid(f'journey-unknown-{idx}')
            continue
        _, colour, hatch = JOURNEY_STYLES[row['stage']]
        bar, = ax.barh(at, row['duration_minutes'], left=row['start_minute'], height=.62,
                       facecolor=colour, edgecolor=INK, linewidth=.6, hatch=hatch)
        bar.set_gid(f'journey-bar-{idx}')
    ax.set_yticks(range(len(labels)), [f'Journey {label}' for label in labels])
    ax.set_ylim(len(labels) - .45, -.55)
    ax.set_xlim(left=0)
    ax.set_xlabel('Elapsed minutes from documented readiness')
    ax.grid(axis='x', alpha=.17)
    ax.set_axisbelow(True)
    fig.legend([Patch(facecolor=colour, edgecolor=INK, hatch=hatch)
                for _, colour, hatch in JOURNEY_STYLES.values()],
               [label for label, _, _ in JOURNEY_STYLES.values()],
               loc='lower center', bbox_to_anchor=(.52, .076), ncols=2,
               frameon=False, fontsize=10.2)
    return fig


def _coverage(rows, _year, _cohort):
    fig = Figure(figsize=(5.7, 6.3), facecolor='white')
    paid, productive, demand = (sum(row[key] for row in rows) for key in
                                ('paid_staff_hours', 'productive_staff_hours',
                                 'eligible_readiness_cases'))
    _heading(fig, 'Nursing coverage and readiness',
             f'One liaison post · {paid} paid h · {productive} productive h · {demand} cases\n'
             'Fictional week · hours and readiness counts shown separately')
    coverage, cases = fig.subplots(2, 1)
    coverage.patch.set_gid('coverage-grid-background')
    cases.patch.set_gid('demand-grid-background')
    fig.subplots_adjust(left=.13, right=.96, bottom=.18, top=.735, hspace=.45)
    coverage.set_title('Roster hours per hour of day', loc='left', fontsize=12, weight='bold')
    cases.set_title('Eligible readiness cases per hour of day', loc='left', fontsize=12, weight='bold')
    for ax in (coverage, cases):
        ax.set(xlim=(0, 24), ylim=(7, 0))
        ax.set_yticks(np.arange(7) + .5, DAYS)
        ax.set_xticks([0, 6, 12, 18, 24], ['00:00', '06:00', '12:00', '18:00', '24:00'])
        ax.set_xticks(range(25), minor=True)
        ax.set_yticks(range(8), minor=True)
        ax.tick_params(which='both', length=0)
        ax.grid(which='minor', color='#abb9c1', linewidth=.35)
        ax.grid(axis='x', which='major', color='#abb9c1', linewidth=.6)
        ax.set_axisbelow(True)
    for row in rows:
        day, hour = row['day'], row['hour']
        if row['paid_staff_hours']:
            working = row['productive_staff_hours'] == 1
            box = Rectangle((hour, day), 1, 1, facecolor=TEAL if working else PALE,
                            hatch='' if working else '//', edgecolor=INK, linewidth=.45)
            box.set_gid(f'coverage-{day}-{hour}')
            coverage.add_patch(box)
        count = row['eligible_readiness_cases']
        if count:
            box = Rectangle((hour, day), 1, 1, facecolor=PALE, edgecolor=INK, linewidth=.45)
            box.set_gid(f'demand-cell-{day}-{hour}')
            cases.add_patch(box)
            cases.text(hour + .5, day + .5, str(count), ha='center', va='center',
                       fontsize=10.2, weight='bold').set_gid(f'demand-{day}-{hour}')
    fig.legend([Patch(facecolor=TEAL, edgecolor=INK),
                Patch(facecolor=PALE, edgecolor=INK, hatch='//')],
               ['Productive', 'Paid only'], loc='lower left', bbox_to_anchor=(.09, .086),
               frameon=False, ncols=2, fontsize=9.7)
    fig.text(.58, .114, 'Blank cells = 0', fontsize=9.7)
    return fig


def _cell_text_color(rgb):
    srgb = np.asarray(rgb[:3])
    linear = np.where(srgb <= .04045, srgb / 12.92, ((srgb + .055) / 1.055) ** 2.4)
    luminance = linear @ np.array([.2126, .7152, .0722])
    return 'white' if luminance < .179 else 'black'


def _effect_sensitivity(rows, year, cohort):
    fig = Figure(figsize=(5.7, 6.8), facecolor='white')
    _heading(fig, 'Sensitivity to assumed clinical effects',
             f'Liaison · shared draws for {cohort:,} eligible discharges per year\n'
             'Negative effects allow more returns. Clinical safety is unmeasured.')
    axes = fig.subplots(2, 1)
    fig.subplots_adjust(left=.18, right=.945, bottom=.195, top=.738, hspace=.48)
    x = sorted({row['relative_return_reduction'] for row in rows})
    y = sorted({row['delay_success'] for row in rows})
    panels = (
        ('mean_net_resource_aud', 'money', 1000, f'Annual net resources (thousand AUD {year})'),
        ('mean_returns_avoided', 'returns', 1, 'Expected 72-hour ICU returns avoided'),
    )
    for ax, (key, prefix, scale, title) in zip(axes, panels, strict=True):
        values = np.array([row[key] / scale for row in rows]).reshape(len(y), len(x))
        extent = max(.1, float(np.abs(values).max()))
        norm = TwoSlopeNorm(vmin=-extent, vcenter=0., vmax=extent)
        ax.pcolormesh(values, cmap='RdBu', norm=norm, edgecolor='white', linewidth=1.1)
        for idx, row in enumerate(rows):
            iy, ix = divmod(idx, len(x))
            value = values[iy, ix]
            colour = _cell_text_color(mpl.colormaps['RdBu'](norm(value)))
            ax.text(ix + .5, iy + .5, f'{value:+.1f}', va='center', ha='center',
                    color=colour, fontsize=10.5, weight='bold').set_gid(f'{prefix}-{idx}')
            if row['effect_class'] == 'joint_null':
                outline = Rectangle((ix + .03, iy + .03), .94, .94, facecolor='none',
                                    edgecolor=colour, linewidth=1.4, linestyle='--')
                outline.set_gid(f'null-{prefix}')
                ax.add_patch(outline)
        ax.set_title(title, loc='left', fontsize=11.5, weight='bold')
        ax.set_yticks(np.arange(len(y)) + .5, [f'{value:.0%}' for value in y])
        ax.set_xticks(np.arange(len(x)) + .5, [f'{value:+.0%}' if value else '0%' for value in x])
        ax.set_ylabel('Delays resolved', fontsize=10.5)
    axes[-1].set_xlabel('Assumed relative reduction in returns (%)')
    fig.text(.18, .087, 'Dashed outline = both effects set to zero', fontsize=9.6)
    return fig


_RENDERERS = {
    'F02': _resource_waterfall, 'F10': _break_even_grid, 'F11': _paired_scatter,
    'F15': _journey, 'F20': _coverage, 'F24': _effect_sensitivity,
}


def render_svg(path: Path, figure: dict, rows: list[dict], price_year: int, cohort: int) -> None:
    rc = {
        'font.family': 'DejaVu Sans', 'font.size': 11, 'text.color': INK,
        'axes.labelcolor': INK, 'axes.edgecolor': INK,
        'axes.spines.top': False, 'axes.spines.right': False,
        'xtick.color': INK, 'ytick.color': INK, 'svg.fonttype': 'none',
        'svg.hashsalt': 'icu-liaison-p9-v1', 'path.simplify': False,
    }
    with mpl.rc_context(rc):
        canvas = _RENDERERS[figure['id']](rows, price_year, cohort)
        canvas.savefig(path, format='svg', metadata={
            'Date': None, 'Title': figure['title'], 'Description': figure['alt_text'],
        })
    svg = path.read_text(encoding='utf-8')
    svg = svg.replace('<svg ', '<svg role="img" aria-labelledby="figure-title figure-desc" ', 1)
    svg = svg.replace('<title>', '<title id="figure-title">', 1)
    description = escape(figure['alt_text'])
    svg = svg.replace('</title>', f'</title>\n <desc id="figure-desc">{description}</desc>', 1)
    path.write_text(svg, encoding='utf-8')
