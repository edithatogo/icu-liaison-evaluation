# ICU liaison reporting contract

The [figure catalogue](catalogue.json) specifies seven tables and 24 figures. `schema_version=1` preserves the existing structural revision; `catalogue_revision` identifies this extended evidence-tier figure programme. The [JSON schema](catalogue.schema.json) denies unknown figure fields and enforces null artifacts for all unproduced outputs.

F01 belongs to the P5 report and has its own immutable P11 figure revision.
The P9 companion has six priority figures and seven supplementary figures.
F05–F09 are rebuilt from versioned sources. Historical PNG hashes identify the
original references. F13 and F18 demonstrate methods on fictional data. Ten
additional figures require admitted site or provider evidence. The
[Conductor workplan](../../conductor/tracks/P9-reporting-contracts/figure-workplan.md) lists their inputs.

Every figure specifies a decision question, estimand, source table, units, denominator, evidence tier, missingness, paired semantics, source requirements, accessibility, renderer provenance and release gate. No approved CHHHS data, native provider qualification or clinical/Finance sign-off is implied.

## P10 scientific measurement contracts

[Metric registry](metrics.json) and [schema](metrics.schema.json): 31 canonical metrics and 14 denominators tied to the Clinical Director and CHHHS 11-dataset request. [Claim policy](claim-policy.json) and [schema](claim-policy.schema.json) deny external approval by public-source flags. [Figure provenance](provenance-record.schema.json) and [unproduced template](provenance-template.json) do not represent completed figures. [Visual review matrix](visual-review.json) specifies the display profiles; [uncertainty taxonomy](uncertainty-taxonomy.json) distinguishes PSA from empirical sampling uncertainty. Historical [v2 catalogue](history/catalogue-figure-programme-v2.json) and [v2 schema](history/catalogue-schema-figure-programme-v2.json) remain versioned. The current catalogue revision is P9-v5.

## Visual review

Generate the figures using the [repository workflow](../../README.md#p9-priority-synthetic-figures).
The report reader checks source values and visible SVG data marks independently
of the plot-writing step. Its receipt is scoped to synthetic computation and
rendered marks. Each gallery preview links to a full-size SVG for dense charts
on narrow screens. Use the optional local capture command to inspect mobile,
tablet, desktop and A4 portrait grayscale renders.

```sh
.venv/bin/python tools/capture_p9_visuals.py outputs/p9-figures outputs/p9-captures
```

Supply `--f01 outputs/p11/figures/<revision>` to include the matching F01.
The capture uses locally installed `rsvg-convert` and records the renderer
version, SVG and raster hashes and exact dimensions. A capture requires an
actual visual check for typography, clipping, tonal contrast and interpretation.

## Figure inventory

Use the read-only inventory to see both contracts together. It lists each
figure's stable ID, contract, evidence tier, production route and related
P9 IDs. The status describes the contract and renderer. Check a run manifest
to verify actual artifacts.

```sh
PYTHONPATH=src .venv/bin/python tools/validate_reporting_contracts.py --inventory
```

P11 versions the P9 catalogue as a workflow input. The presentation profile
has its own inputs and output manifest, so edits to it leave the P11 figure
fingerprint intact. The inventory check validates cross-references between
the two contracts without changing either renderer's evidence rules.

## Check a run

After running the [P11 suite](../../docs/p11-scenario-workflows.md), check
which P9 outputs its current scenarios produced.

```sh
PYTHONPATH=src private/venv-p11/bin/python tools/validate_reporting_contracts.py --run outputs/p11
```

The check runs the existing P11 verifier before listing artifacts. It checks
the four contracted table headers and lists each scenario's
verified table and SVG paths and SHA-256 hashes, figure source and review
links, and frozen catalogue hash. Paths are relative to the run directory.
Matching source and runtime allow numerical and SVG mark replay. Archived
runs retain their original scope, so newer figures appear in `not_in_run`.
Tables and figures awaiting evidence appear in `blocked`. The private
presentation continues to use its own manifest.

## Private evaluation presentation

The [evaluation-deck profile](evaluation-deck.json) requires three additional
figures for a presentation based on verified aggregate inputs.

| ID | Figure | Relation to the P9 catalogue |
| --- | --- | --- |
| E01 | Monthly ICU admissions and funded-bed occupancy | Complements F03 and F09. Missing observations are visible gaps. |
| E02 | ED screening and modelled ICU reuse | Complements F13 and F15. Observed counts and modelled changes are separate panels. |
| E03 | Cash sensitivity to QWAU payment and care costs | Complements F07 and F10. The scenario lines hold physical reuse at 100%. |

The profile also records the editable one-FTE funding comparison in the deck.
The new profile does not change the 24 P9 figure IDs or promote any empirical
or provider placeholder. P11 still runs F01 and the 13 synthetic P9 figures.
Use the existing figure bundle for portable fiction. Run the deck renderer
separately for a local presentation.

The renderer accepts a JSON object with `input_class`, `period_months`,
`activity`, `pathways` and `funding`. Activity rows contain `month` (YYYY-MM),
`admissions`, `icu1_pct` and `icu2_pct` (0–100 or null).
The pathway fields are `screen_months`, `adult_icu_destinations`, `labelled`,
`chart_review`, `avoided`, `reused_hours` and `added`. The four funding rows
are named `reference`, `longer_stays`, `longer_flat_weight` and
`higher_care_cost`. Each has `full_net_payment` and `incremental_spending` in
Australian dollars for the full period.

```sh
.venv/bin/python tools/render_evaluation_figures.py \
  --inputs /absolute/private/path/aggregates.json \
  --output /absolute/private/path/new-figure-directory
```

Declare actual inputs `private_aggregate` and use an owner-only directory outside
Git. The renderer rejects private inputs and outputs in Git worktrees. Fictional
examples use `synthetic_only` and display a visible label. The output has PNGs
for slide inclusion, SVGs for review and an input, contract, renderer and
artifact hash manifest.
