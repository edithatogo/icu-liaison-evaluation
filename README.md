# ICU liaison evaluation

Private project repository: [edithatogo/icu-liaison-evaluation](https://github.com/edithatogo/icu-liaison-evaluation).

This project brings together the P0–P8 evaluation source and the P7 placeholder
workflow from the dated portable checkpoints. It contains the draft clinical
and economic protocol, data contracts, synthetic economic/capacity examples,
reporting and optional provider adapters. **Local CHHHS data, intervention
effects, native-provider qualification and clinical/Finance approvals remain
unresolved. The supplied model results are illustrative only.**

Missing information remains in the [placeholder register](model-inputs/placeholders/registry.json)
and [unresolved inputs](model-inputs/placeholders/unresolved.json), with source
requirements and replacement responsibilities. Unknown local amounts and
approvals stay null; existing numerical fixtures are explicitly synthetic.
The P8 funding/workforce contracts likewise retain their unqualified status.

Start with [Conductor](conductor/index.md), the [replacement workflow](docs/placeholder-qualification.md)
and the [repository import record](docs/repository-import.md). Historical
verification receipts retain their original date and scope. The exploratory
CareOps Sim PR #215 remains a separate migration/reconciliation obligation.

## Purpose and source boundaries

Reconcile the public ANZICS resources and the earlier decision-analytic work;
replace handwritten generic distributions and quantiles with SciPy and NumPy;
provide external, source-tagged inputs and validated outputs; establish strict
interfaces to the existing Dapane and Voiage libraries. Design further work so
no clinical facts, confidential CHHHS data, or source artifacts are silently
copied into public version control.

The inherited **2024/25 ANZICS CCR** transcription records **20.4% of live
ward/home discharges delayed >=12 hours** (162 contributing ICUs). Its source
document remains **independently unverified**; it is an external pooled proxy,
not a local adult Cairns estimate. See the [source reconciliation](docs/anzics-source-reconciliation-2026-11-18.md). An
illustrative 1,000-discharge annual cohort and all intervention effects and
costs are explicitly synthetic. ANZICS readmission endpoints are not used as
72-hour unplanned readmission rates. Source and denominator distinctions are
preserved in `conductor/evidence/source-register.json`.

## Tested basic workflow

Create a repository-local environment with the CPython release in
`.python-version`. If the existing `.venv` uses a different release, move it
aside once its processes have finished.

```sh
uv venv --python "$(cat .python-version)" .venv
.venv/bin/python --version
test "$(.venv/bin/python --version)" = "Python $(cat .python-version)"
uv pip install --python .venv/bin/python -c requirements-ci.txt \
  --build-constraints requirements-ci.txt '.[test,report]'
.venv/bin/python -m pytest -q
mkdir -p outputs
.venv/bin/python -m icu_liaison.cli model-inputs/illustrative.json > outputs/illustrative.json
```

The tested source and model results are reproducible for the same Python and
NumPy/SciPy versions and random seed; cross-version byte-identical trajectories
are not guaranteed. The model uses SciPy `triang.rvs` and NumPy `quantile` rather
than project-specific distribution/quantile algorithms. All adjustable
quantities and their assumed uncertainty live in the JSON file, including
status, source, units and ranges. The output includes source-hash, seed,
intervals and `P(net resource benefit >= 0)`.

The P1 adapter now calls Voiage for financial-only EVPI, with an independent
native two-state reference and a strict source lock. Install **Voiage v3.1**
as an optional dependency in the separate P1 provider environment.
`adapters.voiage.make_voiage_analysis()` uses the
published `ValueArray.from_numpy` / `DecisionAnalysis` boundary in a separately
qualified environment. It is a **financial-only** net-benefit decision surface,
not a QALY or cost-effectiveness result. **Do not claim VOI results until the
installed provider has executed and passed the integration tests.**

P1 now also builds two nonnegative, exact-decimal **incremental
counterfactual resource ledgers** and can execute them through the real Dapane
provider. The local synthetic regression tests prove the request/response
boundary but not provider-runtime execution. See [P1 provider guide](docs/providers-p1.md).

**Dapane v0.1 is not a published pip dependency.**
`adapters.dapane.make_request()` assembles its published exact resource quotation
contract. It does **not** calculate costs itself; Dapane must be independently
installed and qualified to execute `.evaluate()`. Use separately generated
nonnegative current and proposed-care resource ledgers, then compare their
valued totals. Do not use a negative or duplicated resource use as a cost-saving
shortcut. Dapane provider integration and underlying case mix need local evidence.

## What the pilot actually computes

For each independent parameter-uncertainty draw:

- released index ICU bed-days = eligible discharges × exit-block fraction ×
  addressable fraction × improved fraction × hours released per improved case / 24;
- unplanned 72-hour returns avoided = eligible discharges × change in early
  return probability, which can be negative;
- gross potential resource benefit = released days × hypothetical net
  avoidable index ICU-day cost + returns avoided × hypothetical incremental
  readmission cost;
- net resource benefit = gross benefit − added service cost.

**It does not establish cash savings, QALYs, reduced mortality, released staffed
beds, causality, costs of all downstream ward care or improved clinical safety.**
Independent triangular inputs are judgemental; the 5th and 95th percentiles
are sensitivity intervals, not confidence or prediction intervals. Readmission
benefit excludes the index discharge-delay cost segment to limit double counting.

## Reuse plan and ownership

| Component | Owner/provider | Implemented in this bundle |
| --- | --- | --- |
| Public studies and ANZICS observations | ANZICS and study authors | Source register and non-verbatim curated synthesis |
| Input validation and editable provenance | Pydantic | Schema and synthetic JSON fixture |
| Uncertainty draws, distributions, quantiles | NumPy and SciPy | Tested basic economic scenario |
| Exact resource cost, allocation and quotation | Dapane | Contract-producing adapter; **native execution not qualified** |
| Value of information and decision analysis | Voiage | Financial draw adapter; **native execution not qualified** |
| Evidence search and PRISMA | Searchright | Future qualified consumer; no duplicate review engine |
| Bed occupancy, timed transfer and resource queues | Kairos | Synthetic trace audit and pinned native consumer source; **native execution unqualified** |
| BI and semantic reporting | CareOps Finance | Optional downstream consumer; not mandatory |
| Strategic games | Paignia | Not needed for this decision problem |

The Conductor dependency is pinned as a Git submodule at its reviewed SHA.
Initial source import and synthetic CI do not establish native or local-data
acceptance. Before admitting provider outputs or retiring PR #215, complete
the corresponding provenance, runtime and independent review obligations. See
`conductor/tracks/P0-portable-consolidation/plan.md`.

## What is *not* embedded

The original Library workbook
`ANZICS_CHHHS_ICU_liaison_starting_model.xlsx` is preserved in its current
Library location. Its filename, library reference and SHA-256 are in the
migration manifest; its binary is deliberately **not** in this source archive.
Raw ChatGPT conversation transcripts, confidential CHHHS records, unpublished
costing and original publisher PDFs are not copied. The source register links
the public publisher documents and the original exploratory GitHub branch.

## P1 source implementation status

The package contains `providers.lock.json`, validated Dapane and Voiage
consumer APIs, a fail-closed installed-provider qualifier, P1 Conductor
track, reference tests and a setup guide. The additional test suite explicitly
uses injected boundary providers and marks them as such. For real native
qualification, use [the execution guide](docs/providers-p1.md):

```sh
PYTHONPATH=src private/venv-p1/bin/python tools/qualify_providers.py --provider all
```

In a host without the required native environments this command must exit 2
with `UNVERIFIED`. This is an expected native-qualification blocker. The
source repository and its synthetic checks do not satisfy that separate gate.

## P2 clinical and economic model contract (draft, not approved)

P2 adds a **separate structured protocol**, field-grain data dictionary, and
synthetic-only timing oracle. It does **not** infer actual CHHHS FTE, costs,
activity or service effectiveness from public ANZICS comparisons.

- [Clinical/economic methods and explicit estimands](docs/protocol-p2.md)
- [CHHHS source and missingness requirements](docs/data-requirements-p2.md)
- [CHEERS reporting crosswalk and omissions](docs/reporting-checklist-p2.md)
- [Conductor P2 implementation and independent checks](conductor/tracks/P2-clinical-economic-protocol/index.md)
- [P2 protocol JSON](model-inputs/clinical-economic-protocol.json) and
  [32-field source dictionary](model-inputs/clinical-data-dictionary.json)

Validate the *illustrative-only* economic model against the protocol:

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.protocol_cli \
  model-inputs/clinical-economic-protocol.json \
  model-inputs/illustrative.json \
  --data-dictionary model-inputs/clinical-data-dictionary.json
```

With `--require-local-ready`, the same admission command deliberately exits
**2 (UNVERIFIED)**. That is the correct result until approved local input,
clinical-safety evaluation and financial validation are available. The P1
probabilistic model and optional provider interfaces are unchanged; P2 does
not license a new clinical claim or native runtime status.

## P3: public source and authorised-local-data intake

P3 adds a [versioned ANZICS benchmark catalogue](model-inputs/anzics-benchmarks.json),
[source and data governance guide](docs/p3-source-and-data-infrastructure.md),
[synthetic episode/follow-up/contact/cost fixtures](tests/fixtures/p3_episodes/manifest.json)
and [Conductor track](conductor/tracks/P3-evidence-data-infrastructure/index.md).
It verifies local source-file SHA-256, Pydantic-generated schemas, column mappings,
clinical/financial episode linkage, readiness completeness, early ICU return
censoring and aggregate report privacy. It **does not** automatically acquire
ANZICS Portal data, read real CHHHS records, or perform a Searchright review.

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p3_cli sources \
  --catalogue model-inputs/anzics-benchmarks.json \
  --source-register conductor/evidence/source-register.json
PYTHONPATH=src .venv/bin/python -m icu_liaison.p3_cli audit \
  --manifest tests/fixtures/p3_episodes/manifest.json \
  --dictionary model-inputs/clinical-data-dictionary.json
PYTHONPATH=src .venv/bin/python -m icu_liaison.p3_cli schema
```

The inherited 2024/25 exit-block percentage is **previously transcribed but
not independently reverified** during P3 because the referenced PDF was not
accessible. The 2023/24 publisher text has been checked for its own 19.8%
exit-block reference, but no reviewed PDF hash has been admitted. Every
benchmark remains external and cannot be substituted for a CHHHS rate. P3 tests
use synthetic records only and never confer local clinical/economic acceptance.

## P4: multi-strategy illustrative economic model

P4 preserves a separate clinical/economic specification, and now explicitly
reconciles the scenario to P2 and P3 at the CLI boundary before any result can
be admitted. The public ANZICS exit-block rate remains a **previously
transcribed, unverified external proxy**; none of the modelled interventions
has an observed CHHHS effect. All cost values are synthetic in AUD 2026.

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p4_cli model-inputs/p4/illustrative.json \
  --one-way-strategy liaison_service
```

The source checks, Gaussian-copula sensitivity, independent identities,
threshold/negative-effect cases and blocked external acceptance are in
[the P4 track](conductor/tracks/P4-economic-decision-model/index.md).

## P5: reporting, decision-analysis transfer and audit

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p5_cli \
  model-inputs/p4/illustrative.json --output-dir outputs/p5-synthetic --plots
```

The output directory must not exist. It contains `model-summary.json`,
`evidence-admission.json`, `cost-consequence.csv`, `paired-comparisons.csv`,
`one-way-sensitivity.csv`, `decision-surface.csv` for Voiage, Dapane nominal
request JSON, `report.md`, a SHA-256 file manifest and optional Matplotlib SVG.
The report writer uses atomic staging and refuses overwrite or partial
publication. The matching manifest-check function is in
`icu_liaison.p5_reporting.verify_manifest`.

`--voiage` opts into the **actual Voiage** EVPI provider and fails if the
installed provider is unavailable; there is no replacement EVPI algorithm.
Without that flag the report states `EVPI not executed`, not zero. Actual native
Dapane valuation and Voiage installation remain unqualified, even when a
contract-test fake is used. `--require-investment-ready` returns a blocked
status until separate empirical, safety and governance evidence exists.

This decision surface is **financial resource cost only** and must not be
represented as a cost-per-QALY or clinical benefit analysis. It is one annual
programme choice, not a patient-level scaled decision. The P5 method, audit
and remaining review obligations are in
[the P5 track](conductor/tracks/P5-reporting-independent-review/index.md).

## P5 source completion and P6 entry (18 November 2026)

The prior P5 reporting engine now supports explicit `--dapane` opt-in, which
calls the installed Dapane provider (no fallback) for each nominal incremental
strategy ledger. Outputs are reconciled against point-input P4 accounting to
within two cents, labelled `native_provider_called_unqualified` until exact
installed artefacts are admitted. Without the flag valuation is `not_executed`.
No binary or wheel was qualified in this environment.

A separate `icu-liaison-p5-review` command independently loads a published P5
bundle, checks its file manifest, and recomputes strategy/paired resource
summaries from the *exported draw table* without running the P4 engine. It
refuses a tampered mean, paired probability or investment-readiness label even
if the attacker recalculates the unsigned manifest. This still does not provide
authenticated source evidence or independent clinical/financial peer review.

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p5_cli model-inputs/p4/illustrative.json \
  --output-dir outputs/new-p5 --plots
PYTHONPATH=src .venv/bin/python -m icu_liaison.p5_review_cli outputs/new-p5
```

[P6 trace audit](docs/p6-temporal-capacity.md) analyses **supplied synthetic**
ICU occupancy and admission-request trajectories against time-varying staffed
bed counts, with common-demand and no-overbooking checks:

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p6_cli model-inputs/p6/synthetic-trace.json
```

This is not a DES runner. Actual Kairos source bindings, installed native
qualification, CHHHS timing/calibration and clinical/economic acceptance remain
future gates under the independent Conductor P6 track.

## P6.3 / P6.4 source-only continuation

The [optional native Kairos consumer](native/kairos-icu-liaison/README.md)
now uses the inspected, immutable upstream `StagedResourceRuntime` API for
a fixed single-bed, synthetic demand and discharge fixture. The Python
`icu_liaison.p6_native` adapter independently audits exported occupancy and
refuses a false native-execution claim. `tools/qualify_p6_native.py` will
qualify actual installed provider builds and fixture replay once a Rust
toolchain, reviewed Cargo.lock, and fetched dependencies are available. The
current source **has not been compiled**.

`icu_liaison.p6_holdout` now computes synthetic train/holdout diagnostics
with SciPy Wasserstein and KS without introducing an additional queue engine
or clinical causal estimator. See [P6 acceptance checklist](docs/p6-native-qualification.md).
No CHHHS clinical records or real approval have been added.

## P7 source/qualification handoff (18 November 2026)

- [Independent source and numerical audit](src/icu_liaison/qualification_independent.py) independently recomputes selected P4 draws with Decimal and validates P3 aggregate denominator/missingness boundaries; **not** clinical or causal evidence.
- [Current CHHHS data request](model-inputs/chhhs-data-request.json) is an 11-dataset, 115-field versioned request, with editable schema and [source request document](docs/causal-and-safety-validation-plan.md). Generate MD/CSV using `PYTHONPATH=src .venv/bin/python tools/export_chhhs_data_request.py --output-dir /tmp/chhhs-request`.
- [Publisher verification note](docs/anzics-source-reconciliation-2026-11-18.md) directly verifies 2023/24 pages; 2024/25 inherited values remain unverified.
- [P7 track](conductor/tracks/P7-technical-empirical-qualification/index.md) records native, empirical, governance and hosted CI gates. No external approvals claimed.

## P8: Optional MCHS and nursing workforce valuation sources

[P8's Conductor track](conductor/tracks/P8-abf-workforce-interop/index.md)
adds a source-qualified capability/owner matrix, versioned null-value
funding/workforce/resource separation schema and a concrete library improvement
handoff. It does **not** claim installed MCHS/Wage/Dapane/Voiage consumers or
local CHHHS applicability. In particular, NWAU is an activity measure; neither
the technical NWAU difference nor a published nursing wage rate establishes
actual local hospital revenue or fully loaded workforce costs. Run its focused
checks with `PYTHONPATH=src .venv/bin/python -m pytest -q
tests/test_p8_provider_roadmap.py`.

- [P8 provider matrix](model-inputs/p8/provider-capabilities.json)
- [P8 synthetic contract](model-inputs/p8/synthetic-null-shadow.json)
- [Library improvement proposals](docs/P8-library-improvements-and-handoffs.md)

This remains **planning/source-only** until installed-provider, local-data
and governance receipts are available. Repository hosting does not close
those evidence obligations.

## P8.2/P8.3 — source-level ABF and nursing roster consumers (18 November 2026)

MCHS and Microcosting Health Workforce are now **explicit optional providers**.
The P8 consumer admits only synthetic scenarios with independently pinned
source identities; it calls MCHS's existing annual acute calculator twice,
or transports declared nursing roster quantities into the existing workforce
quote -> Dapane request builder. It has **no calculator or payroll formulas**.
The tests are source-only and injected, not native provider acceptance.

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p8_cli inspect-mchs model-inputs/p8/synthetic-mchs-pair.json
PYTHONPATH=src .venv/bin/python -m icu_liaison.p8_cli inspect-roster model-inputs/p8/synthetic-nursing-roster.json
PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_p8_*.py
```

See [P8 source implementation and unresolved provider gates](docs/P8-implemented-consumer-contracts.md).
The original portable checkpoint predates this repository. Its provider
qualification limits remain in force after source import; current hosting
status is recorded in [the import record](docs/repository-import.md).

## P8.4 bounded source composition (portable; not native-qualified)

The ICU evaluation can now attach unqualified case-level MCHS NWAU and
source-only workforce/Dapane quote requests to one named P4 strategy **without
changing its resource or budget result**. This is a typed audit projection,
not additional economic value, an allocation change or a clinical recommendation.

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p8_composition_cli \
  model-inputs/p4/illustrative.json --strategy liaison_service

# Optional synthetic source-only MCHS and workforce fixtures (no native execution):
PYTHONPATH=src .venv/bin/python -m icu_liaison.p8_composition_cli \
  model-inputs/p4/illustrative.json --strategy liaison_service \
  --mchs-result model-inputs/p8/synthetic-mchs-provider-output.json \
  --workforce-result model-inputs/p8/synthetic-workforce-provider-output.json \
  --roster-scenario-id synthetic-nurse-roster
```

`--require-qualified` must fail until native, CHHHS and Finance acceptance
receipts exist. The JSON Schema is
`model-inputs/p8/p8-composition.schema.json`, regenerated with
`PYTHONPATH=src .venv/bin/python tools/export_p8_schemas.py`. The only computed
numerical outputs are *unchanged* means from the synthetic P4 economic model.
MCHS case NWAU is **not** monetised, and the workforce source request is
**not** valued. Any fully source-verified workforce cost will later need to
**replace or reconcile** the model's incremental-service cost prior rather
than being subtracted again. See `docs/P8-composition-and-reconciliation.md`.

## P7 placeholder workflow


P7 adds a **machine-checkable, 33-item replacement register** for the remaining
public-source, CHHHS-data, clinical-approvals, native-provider and repository
release-review gates. The repository URL is known; evidence and approval
placeholders remain unresolved until their separate admission review. Its synthetic
cross-track development run executes existing P3 aggregate intake, P4/P5
probabilistic reporting, P6 occupancy trace and holdout validation without
creating another numerical, valuation, VOI or DES engine.

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.placeholders_cli audit
PYTHONPATH=src .venv/bin/python -m icu_liaison.placeholders_cli dry-run --output-dir ./outputs/new-synthetic-run
PYTHONPATH=src .venv/bin/python -m icu_liaison.placeholders_cli audit --require-site-ready # exit 2
```

The fresh output contains a hash-checked `p5-report/`, `progress.json`,
`replacement-checklist.csv` and `manifest.json`; it must not be interpreted as
observed Cairns hospital performance, clinical safety or financial saving.
Private replacements, candidate byte checks, evidence responsibilities and
sign-off boundaries are documented in [P7 qualification](docs/placeholder-qualification.md)
and the [P7 Conductor plan](conductor/tracks/P7-placeholder-assisted-qualification/plan.md).
