"""P5 inspectable economic and clinical-safety reporting of admitted P4 draws.

This module *reports* existing P4 results: it does not provide a new economic,
statistical, valuation, or value-of-information engine. Only synthetic P4 inputs
are admitted, and missing Voiage/Dapane qualifications remain explicit.
"""
from __future__ import annotations

import csv
import hashlib
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
    for arm, request in requests.items():
        evaluated = evaluate_p4_nominal_valuation(request, provider=provider)
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
    return ({'status': ('injected_contract_test_only' if provider is not None
                        else 'native_provider_called_unqualified'),
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
        consequences.append({
            'strategy_id': arm.id, 'measure': 'incremental_service_cost_aud',
            'unit': f'AUD_{run.scenario.price_year}',
            'boundary': 'incremental_programme_cost_only',
            **_stats(run.sampled_inputs[f'strategy.{arm.id}.annual_incremental_cost_aud']),
        })
    base = run.strategies['current_care']
    pairs = []
    for arm in run.scenario.strategies[1:]:
        alt = run.strategies[arm.id]
        for measure in ('net_resource_benefit_aud','net_budget_impact_aud'):
            difference = getattr(alt, measure) - getattr(base, measure)
            pairs.append({
                'strategy_id': arm.id, 'reference_strategy': 'current_care',
                'measure': measure, 'unit': f'AUD_{run.scenario.price_year}',
                **_stats(difference),
                'probability_strictly_better': float(np.mean(difference > 0)),
                'probability_equal': float(np.mean(difference == 0)),
                'definition': 'paired_draw_incremental_comparison_not_clinical_superiority',
            })
    sensitivity = []
    for arm in run.scenario.strategies[1:]:
        sensitivity += [{'strategy_id': arm.id, **row}
                        for row in one_way_sensitivity(run.scenario, arm.id)]
    return consequences, pairs, sensitivity


def _markdown(model: dict, consequences: list[dict], pairs: list[dict],
              sensitivity: list[dict], admission: dict) -> str:
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
            lines.append(f"| `{p['strategy_id']}` | {p['mean']:,.0f} | {p['probability_strictly_better']:.1%} |")
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
        '| Proposed strategy | Largest illustrative driver | Change in net resource benefit between marginal quantiles (AUD) |',
        '|---|---|---:|',
    ]
    for name in model['strategies']:
        if name == 'current_care':
            continue
        leading = next((row for row in sensitivity if row['strategy_id'] == name), None)
        if leading:
            lines.append(f"| `{name}` | `{leading['parameter']}` | {leading['absolute_net_resource_swing_aud']:,.0f} |")
    lines += [
        '',
        'This diagnostic varies one marginal prior while fixing the others at their nominal inputs; it is not a correlated posterior sensitivity analysis.',
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


def _csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError('empty decision report table')
    with path.open('w', newline='', encoding='utf-8') as fp:
        writer = csv.DictWriter(fp, fieldnames=list(rows[0]), extrasaction='raise', lineterminator='\n')
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
    fig.savefig(path, format='svg', metadata={'Date': None})
    plt.close(fig)


def verify_manifest(directory: Path) -> bool:
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    if manifest['schema_version'] != 1 or manifest['data_class'] != 'synthetic':
        raise ValueError('invalid report manifest profile')
    files = manifest['files_sha256']
    if not files or set(files) != {p.name for p in directory.iterdir() if p.name != 'manifest.json'}:
        raise ValueError('report manifest file-set mismatch')
    if any(not isinstance(name, str) or Path(name).name != name for name in files):
        raise ValueError('report manifest path escape')
    for name, expected in files.items():
        file = directory/name
        if not file.is_file() or file.is_symlink() or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            raise ValueError(f'report manifest hash mismatch: {name}')
    return True


def review_report(directory: Path) -> dict:
    """Independently consume a P5 output and compare its published draw surface.

    File hashes alone are not a scientific check: a modified file and modified
    manifest would still agree. This routine recomputes strategy summaries and
    paired resource comparisons from the exported annual decision draws, with
    no P4 model execution or reliance on a live provider. It does *not* verify
    clinical effectiveness, a value-of-information solver or source authenticity.
    """
    import csv

    folder = Path(directory)
    verify_manifest(folder)
    model = json.loads((folder / 'model-summary.json').read_text(encoding='utf-8'))
    admission = json.loads((folder / 'evidence-admission.json').read_text(encoding='utf-8'))
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
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
    labels = list(model['strategies'])
    if not labels or labels[0] != 'current_care':
        raise ValueError('reference strategy missing from P5 summary')
    with (folder / 'decision-surface.csv').open(newline='', encoding='utf-8') as stream:
        reader = csv.reader(stream)
        names = next(reader)
        if len(names) != len(labels) or set(names) != set(labels) or names[0] != 'current_care':
            raise ValueError('decision surface strategy columns mismatch summary')
        labels = names  # JSON serialisation sorts summary keys; CSV retains decision order.
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

    def match(actual, expected, label):
        if not np.isfinite(float(actual)) or not np.isclose(
            float(actual), float(expected), rtol=1e-11, atol=1e-7
        ):
            raise ValueError(f'P5 {label} summary differs from independently read draws')

    for col, strategy in enumerate(labels):
        expected = _stats(data[:, col])
        reported = model['strategies'][strategy]['net_resource_benefit_aud']
        for stat in ('mean', 'p05', 'p50', 'p95'):
            match(reported[stat], expected[stat], 'strategy')
    with (folder / 'cost-consequence.csv').open(newline='', encoding='utf-8') as stream:
        costs = list(csv.DictReader(stream))
    expected_costs = {(name, 'net_resource_benefit_aud') for name in labels}
    matched_costs = set()
    for row in costs:
        key = (row['strategy_id'], row['measure'])
        if key in expected_costs:
            if key in matched_costs or row['unit'] != f"AUD_{model['price_year']}":
                raise ValueError('duplicate/wrong-unit P5 cost summary')
            matched_costs.add(key)
            for stat in ('mean','p05','p50','p95'):
                match(row[stat], model['strategies'][key[0]]['net_resource_benefit_aud'][stat], 'cost')
    if matched_costs != expected_costs:
        raise ValueError('missing P5 cost-consequence resource summary')

    with (folder / 'paired-comparisons.csv').open(newline='', encoding='utf-8') as stream:
        comparisons = list(csv.DictReader(stream))
    checked = set()
    for row in comparisons:
        if row['measure'] != 'net_resource_benefit_aud':
            continue
        name = row['strategy_id']
        if (name not in labels[1:] or name in checked or
                row['reference_strategy'] != 'current_care'):
            raise ValueError('invalid P5 paired comparison strategy')
        checked.add(name)
        difference = data[:, labels.index(name)] - data[:, 0]
        for stat, expected in _stats(difference).items():
            match(row[stat], expected, 'paired')
        match(row['probability_strictly_better'], np.mean(difference > 0), 'paired')
        match(row['probability_equal'], np.mean(difference == 0), 'paired')
    if checked != set(labels[1:]):
        raise ValueError('missing P5 paired comparison')
    return {
        'status': 'self_consistency_verified_not_empirically_accepted',
        'independent_accounting_check': 'P4_draws_recomputed_from_published_decision_surface',
        'strategies_checked': len(labels),
        'draws_checked': int(data.shape[0]),
        'provider_qualification': False,
        'clinical_safety_approved': False,
        'document_authenticity_verified': bool(admission.get('document_verified', False)),
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
    report = _markdown(model, consequences, pairs, sensitivity, admission)
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
        _csv(staging/'one-way-sensitivity.csv', sensitivity)
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
        verify_manifest(staging)
        review_report(staging)
        if target.exists() or target.is_symlink():
            raise FileExistsError('report appeared during publication; no overwrite')
        staging.rename(target)
    return {'status':'illustrative_report_built','output_directory':str(target),
            'input_digest_sha256':run.input_digest_sha256,'manifest_verified':verify_manifest(target),
            'investment_ready':False}
