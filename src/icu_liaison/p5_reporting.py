"""P5 inspectable economic and clinical-safety reporting of admitted P4 draws.

This module *reports* existing P4 results: it does not provide a new economic,
statistical, valuation, or value-of-information engine. Only synthetic P4 inputs
are admitted, and missing Voiage/Dapane qualifications remain explicit.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from decimal import Decimal, ROUND_HALF_EVEN
import tempfile
from typing import Callable, Literal

import numpy as np

from .adapters.p4_dapane import make_p4_nominal_requests, evaluate_p4_nominal_valuation
from .p4_admission import admit_p4
from .p4_model import (
    EconomicScenario, P4Run, evaluate_scenarios, financial_decision_surface,
    make_p4_voiage_analysis, nominal_counterfactual, one_way_sensitivity, summarise_p4,
)

ROOT = Path(__file__).resolve().parents[2]

# Explicitly different outcome types must not be aggregated into a single
# artificial 'value of all ICU capacity' measure.
MEASURES = (
    ('icu_bed_days_released', 'icu_bed_days', 'capacity_not_cash'),
    ('usable_bed_days', 'icu_bed_days', 'capacity_not_monetised'),
    ('readmissions_avoided', 'expected_unplanned_returns', 'clinical_utilisation_not_safety'),
    ('gross_resource_benefit_aud', 'AUD', 'resource_not_cash'),
    ('net_resource_benefit_aud', 'AUD', 'net_resource_cost_consequence'),
    ('net_budget_impact_aud', 'AUD', 'hypothetical_cash_realisability_only'),
)
SERVICE_COST = ('incremental_service_cost_aud', 'AUD', 'incremental_programme_cost_only')
PAIRED_MEASURES = ('net_resource_benefit_aud', 'net_budget_impact_aud')
PAIRED_DEFINITION = 'paired_draw_incremental_comparison_not_clinical_superiority'
SUMMARY_FIELDS = ('mean', 'p05', 'p50', 'p95')
SENSITIVITY_COLUMNS = (
    'strategy_id', 'parameter', 'lower_prior_quantile', 'upper_prior_quantile',
    'low_net_resource_aud', 'high_net_resource_aud', 'absolute_net_resource_swing_aud',
    'interpretation',
)
REQUIRED_REPORT_FILES = {
    'model-summary.json', 'evidence-admission.json', 'dapane-nominal-requests.json',
    'report.md', 'cost-consequence.csv', 'paired-comparisons.csv',
    'one-way-sensitivity.csv', 'decision-surface.csv',
}
OPTIONAL_REPORT_FILES = {'dapane-nominal-valuation.json', 'scenario-comparison.svg'}


def _stats(a: np.ndarray) -> dict[str, float]:
    z = np.asarray(a, dtype=np.float64)
    if z.ndim != 1 or z.size == 0 or not np.isfinite(z).all():
        raise ValueError('nonfinite/empty P4 report array')
    q05, q50, q95 = np.quantile(z, [0.05, 0.5, 0.95])
    return {'mean': float(np.mean(z)), 'p05': float(q05),
            'p50': float(q50), 'p95': float(q95)}


def audit_p4_accounting(run: P4Run) -> dict:
    """Reconcile independent component identities across every sampled draw.

    This is an accounting/conservation audit, not a second causal estimator or
    clinical external validation. It must reject modified strategy arrays.
    """
    r = run.sampled_inputs
    checks = 0
    for s in run.scenario.strategies:
        x = run.strategies[s.id]
        service = r[f'strategy.{s.id}.annual_incremental_cost_aud']
        index = x.icu_bed_days_released * r['resource.net_index_delay_cost_aud_per_day']
        returns = x.readmissions_avoided * r['resource.incremental_return_cost_aud_per_return']
        identities = (
            (x.usable_bed_days, x.icu_bed_days_released * r['resource.usable_released_capacity_fraction']),
            (x.gross_resource_benefit_aud, index + returns),
            (x.net_resource_benefit_aud, x.gross_resource_benefit_aud - service),
            (x.net_budget_impact_aud,
             index * r['resource.index_cash_realisability_fraction']
             + returns * r['resource.return_cash_realisability_fraction'] - service),
        )
        for observed, reference in identities:
            if observed.shape != reference.shape or not np.allclose(
                observed, reference, rtol=1e-12, atol=1e-7
            ):
                raise ValueError(f'P4 accounting identity mismatch for {s.id}')
            checks += 1
    return {'passed': True, 'checked_strategies': len(run.scenario.strategies),
            'checked_annual_draw_identities': checks * run.scenario.iterations,
            'scope': 'internal_accounting_only_not_independent_clinical_or_empirical_validation'}


def _admission(scenario: EconomicScenario, *, protocol: Path, catalogue: Path,
               register: Path) -> dict:
    p = json.loads(protocol.read_text(encoding='utf-8'))
    c = json.loads(catalogue.read_text(encoding='utf-8'))
    r = json.loads(register.read_text(encoding='utf-8'))
    return admit_p4(scenario, p, c, r)


def _evpi(run: P4Run, *, mode: Literal['skip', 'provider'],
          value_array_factory: Callable | None = None,
          analysis_factory: Callable | None = None) -> dict:
    if mode == 'skip':
        return {
            'status': 'not_executed',
            'provider': 'voiage_v3_1',
            'reason': 'opt_in_only; no custom or surrogate EVPI calculation',
            'money_unit': f'AUD_{run.scenario.price_year}_per_one_annual_programme_decision',
            'clinical_utility_evaluated': False,
        }
    if mode != 'provider':
        raise ValueError('Unsupported Voiage mode')
    analysis = make_p4_voiage_analysis(
        run, value_array_factory=value_array_factory,
        analysis_factory=analysis_factory,
    )
    if not callable(getattr(analysis, 'evpi', None)):
        raise ValueError('invalid Voiage EVPI interface: evpi method unavailable')
    evpi = float(analysis.evpi())  # exclusively owned by the Voiage provider
    if not np.isfinite(evpi) or evpi < -1e-9:
        raise ValueError('invalid Voiage EVPI: expected finite nonnegative value')
    injected = value_array_factory is not None or analysis_factory is not None
    return {
        'status': 'injected_contract_test_only' if injected else 'native_provider_called_unqualified',
        'provider': 'voiage_v3_1', 'value_aud': max(0.0, evpi),
        'money_unit': f'AUD_{run.scenario.price_year}_per_one_annual_programme_decision',
        'population_scaled': False,
        'clinical_utility_evaluated': False,
        'qualification_note': 'A provider call alone does not qualify installed binaries or model assumptions',
    }


def _dapane_nominal(
    scenario: EconomicScenario, requests: dict[str, dict[str, dict | None]], *,
    mode: Literal['skip', 'provider'], provider: Callable | None,
) -> tuple[dict, dict[str, dict] | None]:
    """Optional Dapane exact valuation, never an alternate valuation engine.

    The independent point-input identity bounds cent-rounding differences but
    does not certify the external provider binary or the underlying cost model.
    """
    if mode == 'skip':
        if provider is not None:
            raise ValueError('Dapane injection requires provider mode')
        return ({'status': 'not_executed', 'reason': 'opt_in_only',
                 'installed_provider_qualified': False}, None)
    if mode != 'provider':
        raise ValueError('unsupported Dapane mode')
    point = nominal_counterfactual(scenario)
    outputs: dict[str, dict] = {}
    no_call = 'no_provider_call_no_resource_use'
    status = no_call
    for arm, request in requests.items():
        evaluated = evaluate_p4_nominal_valuation(request, provider=provider)
        if any(ledger is not None for ledger in request.values()):
            status = 'injected_contract_test_only' if provider is not None else 'native_provider_called_unqualified'
        else:
            evaluated['provider_evidence'] = no_call
        observed = Decimal(evaluated['incremental_resource_benefit_aud'])
        expected = Decimal(str(point[arm]['net_resource_benefit_aud'])).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_EVEN
        )
        # Separately rounded ledgers (current and proposed) can differ from
        # rounding the single unrounded incremental value by at most two cents.
        if abs(observed - expected) > Decimal('0.02'):
            raise ValueError(f'Dapane nominal resource reconciliation failed for {arm}')
        outputs[arm] = {
            **evaluated,
            'independent_float_reference_aud': format(expected, '.2f'),
            'difference_from_float_reference_aud': format(observed - expected, '.2f'),
            'reconciliation_scope': 'nominal_accounting_not_full_provider_or_clinical_qualification',
        }
    return ({'status': status,
             'all_strategies_reconciled': True,
             'installed_provider_qualified': False,
             'method': 'dapane-exact-v0.1.0'}, outputs)


def _rows(run: P4Run) -> tuple[list[dict], list[dict], list[dict]]:
    consequences: list[dict] = []
    for arm in run.scenario.strategies:
        result = run.strategies[arm.id]
        for measure, unit, boundary in MEASURES:
            consequences.append({
                'strategy_id': arm.id, 'measure': measure, 'unit': f'{unit}_{run.scenario.price_year}' if unit == 'AUD' else unit,
                'boundary': boundary, **_stats(getattr(result, measure)),
            })
        service_measure, _, service_boundary = SERVICE_COST
        consequences.append({
            'strategy_id': arm.id, 'measure': service_measure,
            'unit': f'AUD_{run.scenario.price_year}',
            'boundary': service_boundary,
            **_stats(run.sampled_inputs[f'strategy.{arm.id}.annual_incremental_cost_aud']),
        })
    base = run.strategies['current_care']
    pairs = []
    for arm in run.scenario.strategies[1:]:
        alt = run.strategies[arm.id]
        for measure in PAIRED_MEASURES:
            difference = getattr(alt, measure) - getattr(base, measure)
            pairs.append({
                'strategy_id': arm.id, 'reference_strategy': 'current_care',
                'measure': measure, 'unit': f'AUD_{run.scenario.price_year}',
                **_stats(difference),
                'probability_strictly_better': float(np.mean(difference > 0)),
                'probability_equal': float(np.mean(difference == 0)),
                'definition': PAIRED_DEFINITION,
            })
    sensitivity = []
    for arm in run.scenario.strategies[1:]:
        sensitivity += [{'strategy_id': arm.id, **row}
                        for row in one_way_sensitivity(run.scenario, arm.id)]
    return consequences, pairs, sensitivity


def _markdown(model: dict, pairs: list[dict], sensitivity: list[dict], admission: dict) -> str:
    lines = [
        '# Illustrative ICU liaison economic evaluation — decision brief',
        '',
        '**Unapproved synthetic scenario — not a CHHHS forecast, investment recommendation or clinical safety finding.**',
        '',
        f"Scenario: `{model['scenario_id']}` · Price year: AUD {model['price_year']} · "
        f"Horizon: {model['horizon_months']} months · Draws: {model['draws']}",
        '',
        '## Cost-consequence comparison',
        '',
        '| Strategy | Released ICU bed-days (mean) | Unplanned returns avoided (mean) | Net resource benefit (AUD) | Net cash-budget impact (AUD) |',
        '|---|---:|---:|---:|---:|',
    ]
    for arm, outcome in model['strategies'].items():
        lines.append(
            f"| `{arm}` | {outcome['icu_bed_days_released']['mean']:,.1f} | "
            f"{outcome['readmissions_avoided']['mean']:,.1f} | "
            f"{outcome['net_resource_benefit_aud']['mean']:,.0f} | "
            f"{outcome['net_budget_impact_aud']['mean']:,.0f} |"
        )
    lines += [
        '',
        'These results are conditional on independently assumed input distributions and a Gaussian copula; the intervals in the machine-readable output are *uncertainty sensitivity intervals*, not confidence intervals.',
        'ICU capacity is reported separately and is not monetised again.',
        '',
        '## Paired comparisons and threshold interpretation',
        '',
        '| Proposed strategy | Mean incremental resource benefit (AUD) | Probability resource benefit > 0 |',
        '|---|---:|---:|',
    ]
    for p in pairs:
        if p['measure'] == 'net_resource_benefit_aud':
            lines.append(
                f"| `{p['strategy_id']}` | {float(p['mean']):,.0f} | "
                f"{float(p['probability_strictly_better']):.1%} |"
            )
    lines += [
        '',
        '### Break-even thresholds at nominal inputs',
        '',
        '| Proposed strategy | Maximum annual service cost consistent with net resource break-even (AUD) | Required coverage | Coverage feasible at nominal inputs? |',
        '|---|---:|---:|---|',
    ]
    for name, outcome in model['strategies'].items():
        if name == 'current_care':
            continue
        necessary = outcome['break_even_coverage_fraction']
        display = 'Not identified (nonpositive savings at full coverage)' if necessary is None else f'{necessary:.1%}'
        lines.append(
            f"| `{name}` | {outcome['threshold_annual_service_cost_aud']:,.0f} | {display} | "
            f"{outcome['break_even_coverage_feasible_at_point_inputs']} |"
        )
    lines += [
        '',
        'These thresholds refer to modelled *resource* costs, not verified budget savings or clinical acceptability.',
        '',
        '### One-way sensitivity — illustrative prior 5th/95th quantiles',
        '',
    ]
    if sensitivity:
        lines += [
            '| Proposed strategy | Largest illustrative driver | Change in net resource benefit between marginal quantiles (AUD) |',
            '|---|---|---:|',
        ]
        for name in model['strategies']:
            leading = max(
                (row for row in sensitivity if row['strategy_id'] == name),
                key=lambda row: float(row['absolute_net_resource_swing_aud']),
                default=None,
            )
            if leading:
                lines.append(
                    f"| `{name}` | `{leading['parameter']}` | "
                    f"{float(leading['absolute_net_resource_swing_aud']):,.0f} |"
                )
        lines += [
            '',
            'This diagnostic varies one marginal prior while fixing the others at their nominal inputs; it is not a correlated posterior sensitivity analysis.',
        ]
    else:
        lines.append('All model priors are fixed in this scenario.')
    lines += [
        '',
        'Probability is a descriptive property of the illustrative input draws; it is **not** the probability that CHHHS will realise a saving.',
        '',
        '## Clinical safety and implementation',
        '',
        '**Clinical safety: unmeasured.** The model contains no observed ward deaths, cardiac arrests, delayed escalation, return severity, goals-of-care reconciliation or ward workload.',
        'No favourable financial result authorises implementation without clinical, nursing, Finance and governance review.',
        '',
        '## Evidence and provider status',
        '',
        f"- Public ANZICS benchmark: {admission['benchmark_rate']:.1%} ≥12-hour exit-block among pooled live ward/home discharges. **Not a local adult CHHHS rate.**",
        f"- Publisher document status: `{admission['source_status']}`; direct PDF authenticity review is outstanding.",
        '- Voiage EVPI: ' + str(model['voiage_evpi']['status']) + '; clinical QALYs have not been calculated.',
        '- Dapane: ' + model['dapane_valuation']['status'] + '; modal costs only, installed-provider qualification remains unverified.',
        '- Source/input digests are in the evidence-admission and manifest files.',
        '',
        '## Unresolved evidence and decision gates',
        '',
        '- Verify eligible discharges, delay hours and discharge causes at CHHHS.',
        '- Verify existing/proposed liaison rosters, incremental FTE and displaced work.',
        '- Obtain linked unplanned 72-hour returns, survival, rescue appropriateness and ward balancing outcomes.',
        '- Obtain local patient-level costing and a separately approved estimate of cash-realisable expenditure.',
        '- Independently review risk adjustment, confounding, censoring and applicability of proposed effectiveness assumptions.',
        '- Qualify installed Dapane/Voiage artefacts and complete external validation before an investment claim.',
        '',
        'Source: [ANZICS 2024/25 CCR public report](https://www.anzics.org/public/311/files/PDFs/CORE/2024_2025-CCR-Activity-Report.pdf), pending independent documentary re-verification.',
        '',
    ]
    return '\n'.join(lines)


def _csv(path: Path, rows: list[dict], *, columns: tuple[str, ...] | None = None) -> None:
    if columns is None and not rows:
        raise ValueError('empty decision report table')
    fields = columns if columns is not None else tuple(rows[0])
    with path.open('w', newline='', encoding='utf-8') as fp:
        writer = csv.DictWriter(fp, fieldnames=fields, extrasaction='raise', lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def _draw_surface(path: Path, run: P4Run) -> None:
    array, labels = financial_decision_surface(run)
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(labels)
        writer.writerows(array.tolist())


def _plot(path: Path, model: dict) -> None:
    # Matplotlib is a maintained optional reporting dependency; no custom SVG
    # geometry or charting runtime is introduced. It is not needed for core P5.
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError('matplotlib reporting extra not installed') from exc
    names = list(model['strategies'])
    means = [model['strategies'][name]['net_resource_benefit_aud']['mean'] for name in names]
    low = [model['strategies'][name]['net_resource_benefit_aud']['p05'] for name in names]
    high = [model['strategies'][name]['net_resource_benefit_aud']['p95'] for name in names]
    fig, ax = plt.subplots(figsize=(8, 4.4))
    ax.bar(names, means)
    for name, m, l, h in zip(names, means, low, high):
        ax.plot([name, name], [l, h], linewidth=1.8, color='black')
    ax.axhline(0, linewidth=1, color='black')
    ax.set_ylabel('Annual net resource benefit (illustrative AUD)')
    ax.set_title('Synthetic ICU liaison scenarios — not CHHHS predictions')
    ax.tick_params(axis='x', rotation=15)
    fig.tight_layout()
    plt.rcParams['svg.hashsalt'] = 'icu-liaison-p5'
    fig.savefig(path, format='svg', metadata={
        'Date': None,
        'Title': 'Synthetic ICU liaison scenarios - not CHHHS predictions',
        'Description': 'Synthetic net resource benefit by strategy with fifth to ninety-fifth percentile ranges, not CHHHS outcomes',
    })
    plt.close(fig)


def _read_verified_bundle(directory: Path) -> tuple[dict, dict[str, bytes]]:
    directory = Path(directory)
    manifest_file = directory / 'manifest.json'
    if manifest_file.is_symlink() or not manifest_file.is_file():
        raise ValueError('report manifest must be a regular bundle file')
    manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
    if (not isinstance(manifest, dict) or manifest.get('schema_version') != 1
            or manifest.get('data_class') != 'synthetic'):
        raise ValueError('invalid report manifest profile')
    files = manifest.get('files_sha256')
    if (not isinstance(files, dict)
            or not REQUIRED_REPORT_FILES <= files.keys() <= REQUIRED_REPORT_FILES | OPTIONAL_REPORT_FILES
            or files.keys() != {p.name for p in directory.iterdir() if p.name != 'manifest.json'}):
        raise ValueError('report manifest file-set mismatch')
    verified = {}
    for name, expected in files.items():
        file = directory / name
        if file.is_symlink() or not file.is_file():
            raise ValueError(f'report manifest entry must be a regular file: {name}')
        data = file.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'report manifest hash mismatch: {name}')
        verified[name] = data
    return manifest, verified


def verify_manifest(directory: Path) -> bool:
    _read_verified_bundle(directory)
    return True


def _report_rows(data: bytes, table: str, expected: set[tuple[str, str]]) -> dict[tuple[str, str], dict[str, str]]:
    rows = {}
    with io.StringIO(data.decode('utf-8'), newline='') as stream:
        for row in csv.DictReader(stream):
            key = (row['strategy_id'], row['measure'])
            if key not in expected or key in rows:
                raise ValueError(f'unexpected or duplicate P5 {table} row')
            rows[key] = row
    if set(rows) != expected:
        raise ValueError(f'missing P5 {table} rows')
    return rows


def _match_report_value(actual: str | float, expected: float, label: str) -> None:
    value = float(actual)
    if not np.isfinite(value) or not np.isclose(value, float(expected), rtol=1e-11, atol=1e-7):
        raise ValueError(f'P5 {label} summary differs from report evidence')


def _match_report_summary(actual: dict, expected: dict, label: str) -> None:
    for stat in SUMMARY_FIELDS:
        _match_report_value(actual[stat], expected[stat], label)


def _review_cost_consequences(data: bytes, model: dict) -> None:
    outcomes = model['strategies']
    measures = {name: (unit, boundary) for name, unit, boundary in (*MEASURES, SERVICE_COST)}
    expected = {(arm, measure) for arm in outcomes for measure in measures}
    for (arm, measure), row in _report_rows(data, 'cost-consequence', expected).items():
        unit, boundary = measures[measure]
        declared_unit = f"AUD_{model['price_year']}" if unit == 'AUD' else unit
        if row['unit'] != declared_unit or row['boundary'] != boundary:
            raise ValueError('wrong unit or boundary for P5 cost-consequence row')
        if measure != SERVICE_COST[0]:
            _match_report_summary(row, outcomes[arm][measure], 'cost-consequence')
            continue
        mean, p05, p50, p95 = (float(row[stat]) for stat in SUMMARY_FIELDS)
        gross = outcomes[arm]['gross_resource_benefit_aud']['mean']
        net = outcomes[arm]['net_resource_benefit_aud']['mean']
        tolerance = 1e-7 + 1e-11 * max(abs(gross), abs(net), mean)
        if (not np.isfinite([mean, p05, p50, p95]).all() or mean < 0
                or not 0 <= p05 <= p50 <= p95 or abs(gross - net - mean) > tolerance):
            raise ValueError('P5 cost-consequence service cost is inconsistent')


def _review_paired_comparisons(data: bytes, model: dict, draws: dict[str, np.ndarray]) -> list[dict[str, str]]:
    outcomes = model['strategies']
    reference = 'current_care'
    budget_measure = 'net_budget_impact_aud'
    if any(outcomes[reference][budget_measure][stat] != 0 for stat in SUMMARY_FIELDS):
        raise ValueError('P5 paired budget comparison requires a zero current-care baseline')
    expected = {(arm, measure) for arm in draws if arm != reference for measure in PAIRED_MEASURES}
    pairs = _report_rows(data, 'paired-comparisons', expected)
    for (arm, measure), row in pairs.items():
        if (row['reference_strategy'] != reference or row['unit'] != f"AUD_{model['price_year']}"
                or row['definition'] != PAIRED_DEFINITION):
            raise ValueError('invalid P5 paired comparison metadata')
        if measure == budget_measure:
            # For a zero incremental comparator, paired cash summaries equal the strategy's.
            _match_report_summary(row, outcomes[arm][measure], 'paired budget')
            better, equal = (float(row[name]) for name in ('probability_strictly_better', 'probability_equal'))
            if not (0 <= better <= 1 and 0 <= equal <= 1 and better + equal <= 1 + 1e-12):
                raise ValueError('invalid P5 paired budget probabilities')
            _match_report_value(better + equal, outcomes[arm]['p_net_budget_impact_nonnegative'], 'paired budget')
        else:
            difference = draws[arm] - draws[reference]
            _match_report_summary(row, _stats(difference), 'paired resource')
            _match_report_value(row['probability_strictly_better'], np.mean(difference > 0), 'paired resource')
            _match_report_value(row['probability_equal'], np.mean(difference == 0), 'paired resource')
    return list(pairs.values())


def _review_sensitivity(data: bytes, strategies: set[str]) -> list[dict[str, str]]:
    seen = set()
    with io.StringIO(data.decode('utf-8'), newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(SENSITIVITY_COLUMNS):
            raise ValueError('invalid P5 sensitivity header')
        rows = list(reader)
    for row in rows:
        key = (row['strategy_id'], row['parameter'])
        if (None in row or None in row.values() or key in seen or key[0] not in strategies
                or not key[1].strip()
                or row['interpretation'] != 'one_at_a_time_prior_quantile_not_joint_posterior'):
            raise ValueError('unexpected or duplicate P5 sensitivity row')
        seen.add(key)
        lower, upper, low, high = (float(row[column]) for column in SENSITIVITY_COLUMNS[2:6])
        if not np.isfinite([lower, upper, low, high]).all() or lower > upper or low > high:
            raise ValueError('invalid P5 sensitivity bounds')
        _match_report_value(row['absolute_net_resource_swing_aud'], high - low, 'sensitivity swing')
    return rows


def review_report(directory: Path) -> dict:
    """Review draw-based resource results and cross-check the other published tables."""
    manifest, bundle = _read_verified_bundle(directory)
    model = json.loads(bundle['model-summary.json'])
    admission = json.loads(bundle['evidence-admission.json'])
    if model.get('investment_ready') is not False or model.get('clinical_safety') != 'unmeasured':
        raise ValueError('investment readiness or clinical safety is unsupported')
    if model.get('schema_version') != 1 or model.get('decision_class') != (
        'illustrative_probabilistic_cost_consequence_not_CHHHS_impact_estimate'
    ):
        raise ValueError('unsupported P5 model summary profile')
    if (manifest.get('scenario_id') != model.get('scenario_id') or
            manifest.get('source_model_input_digest_sha256') != model.get('input_digest_sha256') or
            manifest.get('evidence_digest_sha256') != admission.get('evidence_digest_sha256') or
            model.get('P4_source_admission') != admission):
        raise ValueError('evidence/manifest/model identity mismatch')
    if (manifest.get('publication_status') != 'illustrative_only'
            or manifest.get('installed_provider_qualification') is not False
            or admission.get('admission') != 'illustrative_only'
            or any(admission.get(field) is not False for field in (
                'document_verified', 'local_CHHHS_inputs_verified',
                'clinical_safety_approved', 'economic_investment_ready',
            ))):
        raise ValueError('unsupported P5 evidence admission')
    strategies = set(model['strategies'])
    if 'current_care' not in strategies or len(strategies) < 2:
        raise ValueError('reference strategy missing from P5 summary')
    with io.StringIO(bundle['decision-surface.csv'].decode('utf-8'), newline='') as stream:
        reader = csv.reader(stream)
        labels = next(reader, [])
        if len(labels) != len(strategies) or set(labels) != strategies or labels[0] != 'current_care':
            raise ValueError('decision surface strategy columns mismatch summary')
        rows = list(reader)
    if len(rows) != model['draws'] or not 2 <= len(rows) <= 100_000:
        raise ValueError('P5 decision surface draw-count mismatch')
    if any(len(r) != len(labels) for r in rows):
        raise ValueError('ragged P5 draw surface')
    try:
        data = np.asarray(rows, dtype=np.float64)
    except ValueError as exc:
        raise ValueError('non-numeric P5 decision surface') from exc
    if not np.isfinite(data).all():
        raise ValueError('nonfinite P5 decision surface')
    draws = dict(zip(labels, data.T, strict=True))
    if np.any(draws['current_care'] != 0):
        raise ValueError('P5 current-care resource comparator must be zero')
    for strategy, values in draws.items():
        reported = model['strategies'][strategy]
        _match_report_summary(reported['net_resource_benefit_aud'], _stats(values), 'strategy')
        _match_report_value(reported['p_net_resource_benefit_nonnegative'], np.mean(values >= 0), 'strategy')
    _review_cost_consequences(bundle['cost-consequence.csv'], model)
    pairs = _review_paired_comparisons(bundle['paired-comparisons.csv'], model, draws)
    sensitivity = _review_sensitivity(bundle['one-way-sensitivity.csv'], strategies - {'current_care'})
    # The JSON keys are sorted. The surface retains the publication order.
    model['strategies'] = {name: model['strategies'][name] for name in labels}
    brief = bundle['report.md'].decode('utf-8').replace('\r\n', '\n')
    if brief != _markdown(model, pairs, sensitivity, admission):
        raise ValueError('P5 decision brief differs from the published report evidence')
    return {
        'status': 'self_consistency_verified_not_empirically_accepted',
        'independent_accounting_check': 'P4_draws_recomputed_from_published_decision_surface',
        'strategies_checked': len(labels),
        'draws_checked': int(data.shape[0]),
        'provider_qualification': False,
        'clinical_safety_approved': False,
        'document_authenticity_verified': False,
        'scope': 'independent_report_consumer_not_independent_study_or_source_validation',
    }


def build_report(
    scenario: EconomicScenario, output_dir: Path, *,
    protocol: Path | None = None, catalogue: Path | None = None,
    source_register: Path | None = None,
    voiage_mode: Literal['skip','provider'] = 'skip',
    dapane_mode: Literal['skip','provider'] = 'skip',
    dapane_provider: Callable | None = None,
    value_array_factory: Callable | None = None,
    analysis_factory: Callable | None = None,
    plots: bool = False,
) -> dict:
    """Publish a whole synthetic report directory atomically, without overwrite.

    The public mode does not accept real clinical records. Exact mathematical
    provider qualification is separate from the successful file publication.
    """
    s = EconomicScenario.model_validate(scenario.model_dump(mode='json'))
    target = Path(output_dir)
    if target.exists() or target.is_symlink():
        raise FileExistsError('refusing to overwrite an existing report directory')
    protocol = Path(protocol) if protocol is not None else ROOT/'model-inputs/clinical-economic-protocol.json'
    catalogue = Path(catalogue) if catalogue is not None else ROOT/'model-inputs/anzics-benchmarks.json'
    source_register = Path(source_register) if source_register is not None else ROOT/'conductor/evidence/source-register.json'
    admission = _admission(s, protocol=protocol, catalogue=catalogue, register=source_register)
    run = evaluate_scenarios(s)
    audit = audit_p4_accounting(run)
    model = summarise_p4(run)
    model['P4_source_admission'] = admission
    model['p5_accounting_audit'] = audit
    model['voiage_evpi'] = _evpi(run,mode=voiage_mode,
        value_array_factory=value_array_factory,analysis_factory=analysis_factory)
    model['investment_ready'] = False
    consequences, pairs, sensitivity = _rows(run)
    nominal = {arm.id: make_p4_nominal_requests(s,arm.id)
               for arm in s.strategies if arm.id != 'current_care'}
    valuation_summary, valuation_outputs = _dapane_nominal(
        s, nominal, mode=dapane_mode, provider=dapane_provider
    )
    model['dapane_valuation'] = valuation_summary
    report = _markdown(model, pairs, sensitivity, admission)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.icu-liaison-p5-',dir=target.parent) as scratch:
        staging = Path(scratch)/'report'
        staging.mkdir()
        (staging/'model-summary.json').write_text(json.dumps(model,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
        (staging/'evidence-admission.json').write_text(json.dumps(admission,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        (staging/'dapane-nominal-requests.json').write_text(json.dumps(nominal,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
        if valuation_outputs is not None:
            (staging/'dapane-nominal-valuation.json').write_text(
                json.dumps(valuation_outputs, indent=2, sort_keys=True, allow_nan=False)+'\n',encoding='utf-8'
            )
        (staging/'report.md').write_text(report,encoding='utf-8')
        _csv(staging/'cost-consequence.csv', consequences)
        _csv(staging/'paired-comparisons.csv', pairs)
        _csv(staging/'one-way-sensitivity.csv', sensitivity, columns=SENSITIVITY_COLUMNS)
        _draw_surface(staging/'decision-surface.csv',run)
        if plots:
            _plot(staging/'scenario-comparison.svg',model)
        manifest = {
            'schema_version':1,'data_class':'synthetic','publication_status':'illustrative_only',
            'scenario_id':s.scenario_id,'source_model_input_digest_sha256':run.input_digest_sha256,
            'evidence_digest_sha256':admission['evidence_digest_sha256'],
            'installed_provider_qualification':False,
            'files_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in sorted(staging.iterdir())},
        }
        (staging/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        review_report(staging)
        if target.exists() or target.is_symlink():
            raise FileExistsError('report appeared during publication; no overwrite')
        staging.rename(target)
    return {'status':'illustrative_report_built','output_directory':str(target),
            'input_digest_sha256':run.input_digest_sha256,'manifest_verified':verify_manifest(target),
            'investment_ready':False}
