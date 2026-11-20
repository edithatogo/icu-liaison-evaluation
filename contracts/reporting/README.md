# ICU liaison reporting contract

The [figure catalogue](catalogue.json) specifies seven tables and 24 figures. `schema_version=1` preserves the existing structural revision; `catalogue_revision` identifies this extended evidence-tier figure programme. The [JSON schema](catalogue.schema.json) denies unknown figure fields and enforces null artifacts for all unproduced outputs.

F01 belongs to the P5 report. F02, F10, F11, F15, F20 and F24 are executable
synthetic outputs in the P9 companion bundle. F05–F09 retain their historical
references by SHA-256. The remaining designs await their registered inputs
and reviews. The [Conductor workplan](../../conductor/tracks/P9-reporting-contracts/figure-workplan.md)
describes each figure's source and numerical checks.

Every figure specifies a decision question, estimand, source table, units, denominator, evidence tier, missingness, paired semantics, source requirements, accessibility, renderer provenance and release gate. No approved CHHHS data, native provider qualification or clinical/Finance sign-off is implied.

## P10 scientific measurement contracts

[Metric registry](metrics.json) and [schema](metrics.schema.json): 30 canonical metrics and 13 denominators tied to the Clinical Director and CHHHS 11-dataset request. [Claim policy](claim-policy.json) and [schema](claim-policy.schema.json) deny external approval by public-source flags. [Figure provenance](provenance-record.schema.json) and [unproduced template](provenance-template.json) do not represent completed figures. [Visual review matrix](visual-review.json) specifies the display profiles; [uncertainty taxonomy](uncertainty-taxonomy.json) distinguishes PSA from empirical sampling uncertainty. Historical [v2 catalogue](history/catalogue-figure-programme-v2.json) and [v2 schema](history/catalogue-schema-figure-programme-v2.json) remain versioned. The current catalogue revision is P9-v4.

## Visual review

Generate the figures using the [repository workflow](../../README.md#p9-priority-synthetic-figures).
The report reader checks source values and visible SVG data marks independently
of the plot-writing step. Its receipt is scoped to synthetic computation and
rendered marks. Use the optional local capture command to inspect mobile, tablet,
desktop and A4 portrait grayscale renders.

```sh
.venv/bin/python tools/capture_p9_visuals.py outputs/p9-figures outputs/p9-captures
```

The capture uses locally installed `rsvg-convert` and records the renderer
version, SVG and raster hashes and exact dimensions. A capture requires an
actual visual check for typography, clipping, tonal contrast and interpretation.
