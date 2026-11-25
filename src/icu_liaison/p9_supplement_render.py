"""Supplementary fictional figures. Mark IDs identify the source series."""
from __future__ import annotations
from typing import Any

from matplotlib.figure import Figure
from matplotlib.patches import Patch, PathPatch
from matplotlib.path import Path
from matplotlib.ticker import MaxNLocator

from .p9_figure_render import INK, PALE, RUST, TEAL, _heading, _panel


def _arm(name: str) -> str:
    return name.replace('_service', '').replace('_', ' ').capitalize()


def resources(rows: list[dict[str, Any]], year: int, cohort: int) -> Figure:
    arms = list(dict.fromkeys(r['strategy'] for r in rows))
    fig, ax = _panel('Resources and cash budget',
                     f'Annual difference from current care · {cohort:,} discharges',
                     left=.17, bottom=.30)
    for i, row in enumerate(rows):
        cash = row['measure'] == 'net_budget_impact_aud'
        x = arms.index(row['strategy']) + (.19 if cash else -.19)
        bar, = ax.bar(x, row['mean_aud'] / 1000, width=.36, color=PALE if cash else TEAL,
                      edgecolor=INK, hatch='//' if cash else None)
        bar.set_gid(f'data-{i}')
    ax.axhline(0, color=INK, lw=.9)
    ax.set_xticks(range(len(arms)), [_arm(a) for a in arms])
    ax.set_ylabel(f'Mean difference (thousand AUD {year})')
    ax.legend([Patch(facecolor=TEAL), Patch(facecolor=PALE, hatch='//', edgecolor=INK)],
              ['Net resources', 'Hypothetical cash'], loc='upper center',
              bbox_to_anchor=(.5, -.19), ncols=2, frameon=False)
    return fig


def signs(rows: list[dict[str, Any]], year: int, cohort: int) -> Figure:
    arms = list(dict.fromkeys(r['strategy'] for r in rows))
    fig, ax = _panel('Sign of paired resource benefit',
                     f'Each strategy versus current care · {rows[0]["draws"]:,} draws',
                     left=.27, bottom=.27)
    offsets = dict.fromkeys(arms, 0.0)
    styles = {'positive': (TEAL, None), 'zero': ('white', '..'), 'negative': (PALE, '//')}
    for i, row in enumerate(rows):
        arm, sign = row['strategy'], row['sign']
        colour, hatch = styles[sign]
        bar, = ax.barh(arms.index(arm), 100 * row['fraction'], left=offsets[arm],
                       height=.45, facecolor=colour, edgecolor=INK, hatch=hatch)
        bar.set_gid(f'data-{i}')
        offsets[arm] += 100 * row['fraction']
    ax.set(ylim=(-.6, len(arms)-.4), xlim=(0, 100), xlabel='Share of all paired draws (%)')
    ax.set_yticks(range(len(arms)), [_arm(a) for a in arms])
    fig.legend([Patch(facecolor=c, hatch=h, edgecolor=INK) for c, h in styles.values()],
               ['Positive', 'Tied', 'Negative'], loc='lower center', bbox_to_anchor=(.5, .08),
               ncols=3, frameon=False)
    return fig


_PARAMETER_LABELS = {
    'coverage_fraction':'Service coverage', 'annual_incremental_cost_aud':'Service cost',
    'relative_return_effect':'Return effect', 'unplanned_72h_return_rate':'Baseline return risk',
    'incremental_return_cost_aud_per_return':'Cost per return', 'exit_block_rate':'Exit-block rate',
    'net_index_delay_cost_aud_per_day':'Cost per ICU day', 'delay_success_fraction':'Delay resolution',
    'addressable_delay_fraction':'Addressable delays', 'hours_released_per_improved_case':'Hours released',
}


def tornado(rows: list[dict[str, Any]], year: int, cohort: int) -> Figure:
    displayed = rows[:5]
    pivot = rows[0]['pivot_aud'] / 1000
    fig, ax = _panel('One-way sensitivity',
                     'Liaison service · largest nominal resource swings\n'
                     'One prior varies from its 5th to 95th percentile.',
                     left=.34, bottom=.25)
    for i, row in enumerate(displayed):
        lo, hi = row['lower_aud']/1000, row['upper_aud']/1000
        line, = ax.plot([lo, hi], [i, i], color=TEAL, lw=7, solid_capstyle='butt')
        line.set_gid(f'data-{i}')
        ax.plot([lo, hi], [i, i], '|', color=INK, ms=9)
    ax.axvline(pivot, color=RUST, linestyle='--', lw=1.5).set_gid('nominal-pivot')
    names = [r['parameter'].split('.')[-1] for r in displayed]
    ax.set_yticks(range(len(displayed)), [_PARAMETER_LABELS.get(n, n.replace('_', ' ')) for n in names],
                  fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel(f'Net resources (thousand AUD {year})')
    fig.text(.34, .09, 'Dashed line = nominal result', fontsize=9)
    return fig


def histogram(rows: list[dict[str, Any]], year: int, cohort: int) -> Figure:
    fig, ax = _panel('Distribution of paired differences',
                     'Liaison minus current care · annual net resources')
    for i, row in enumerate(rows):
        lo, hi = row['lower_aud']/1000, row['upper_aud']/1000
        bar, = ax.bar(lo, row['count'], width=hi-lo, align='edge', facecolor=TEAL,
                      edgecolor='white', linewidth=.6)
        bar.set_gid(f'data-{i}')
    ax.axvline(0, color=RUST, linestyle='--', lw=1)
    ax.set(xlabel=f'Difference (thousand AUD {year})', ylabel='Paired draws per bin')
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    return fig


def trace(rows: list[dict[str, Any]], year: int, cohort: int) -> Figure:
    arms = list(dict.fromkeys(r['strategy'] for r in rows))
    fig = Figure(figsize=(5.7, 2.05*len(arms)+1.9), facecolor='white')
    _heading(fig, 'Occupancy and waiting requests',
             'Fictional event trace · counts between events\nWaiting counts requests with a known admission time.')
    axes = fig.subplots(len(arms), 1, sharex=True, squeeze=False)[:, 0]
    fig.subplots_adjust(left=.14, right=.94, bottom=.22, top=.73, hspace=.62)
    for j, (arm, ax) in enumerate(zip(arms, axes, strict=True)):
        arm_rows = [r for r in rows if r['strategy'] == arm]
        for k, (field, colour, style) in enumerate([('staffed_beds', INK, ':'),
                                                    ('occupied_beds', TEAL, '-'), ('known_waiting', RUST, '--')]):
            x = [t for r in arm_rows for t in (r['start_minute'], r['end_minute'])]
            y = [r[field] for r in arm_rows for _ in range(2)]
            ax.plot(x, y, color=colour, linestyle=style, lw=[3.5, 1.7, 1.6][k])[0].set_gid(f'data-{j*3+k}')
        ax.set_title(_arm(arm), loc='left', fontsize=10)
        ax.set_ylabel('Count')
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    axes[-1].set_xlabel('Minutes from fixture start')
    fig.legend(axes[0].lines, ['Staffed beds', 'Occupied beds', 'Waiting requests'],
               loc='lower center', bbox_to_anchor=(.5, .076), ncols=3, fontsize=8.6, frameon=False)
    return fig


def flow(rows: list[dict[str, Any]], year: int, cohort: int) -> Figure:
    total = rows[0]['eligible_indices']
    fig, ax = _panel('Flow after an index discharge',
                     f'{total} fictional first ward discharges · 72-hour follow-up',
                     left=.08, right=.98, bottom=.13)
    ax.set(xlim=(-.03, 1), ylim=(0, 1))
    ax.axis('off')
    start = .10
    for i, row in enumerate(rows):
        thickness = .49 * row['count'] / max(1, total)
        end = start + i * .075
        lo, hi = start, start + thickness
        verts = [(.06, lo), (.32, lo), (.40, end), (.64, end), (.64, end+thickness),
                 (.40, end+thickness), (.32, hi), (.06, hi), (.06, lo)]
        patch = PathPatch(Path(verts, [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
                                      Path.LINETO, Path.CURVE4, Path.CURVE4, Path.CURVE4, Path.CLOSEPOLY]),
                          facecolor=[TEAL, PALE, '#b8916b', 'white'][i], edgecolor=INK,
                          linewidth=.6 if thickness else 0)
        patch.set_gid(f'data-{i}')
        ax.add_patch(patch)
        ax.text(.66, end+thickness/2, f'{row["outcome"]}\n{row["count"]}', va='center', fontsize=9)
        start = hi
    return fig


def event_study(rows: list[dict[str, Any]], year: int, cohort: int) -> Figure:
    fig, ax = _panel('Controlled event-study design',
                     'Fictional ward means · rollout ward minus comparison ward\n'
                     'Difference from week −1, the reference week.', left=.16, bottom=.20)
    x = [r['week'] for r in rows]
    y = [r['gap_change_hours'] for r in rows]
    ax.axhline(0, color=INK, lw=.8)
    ax.axvline(0, color=RUST, lw=1.1, linestyle='--')
    line, = ax.plot(x, y, marker='o', color=TEAL, lw=1.7)
    line.set_gid('data-0')
    ax.set(xlabel='Weeks from fictional rollout', ylabel='Change in ward gap (hours)')
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    return fig


RENDERERS = {'F05': resources, 'F06': signs, 'F07': tornado, 'F08': histogram,
             'F09': trace, 'F13': flow, 'F18': event_study}
