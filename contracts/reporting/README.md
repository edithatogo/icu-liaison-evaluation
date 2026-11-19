# ICU liaison reporting contract

The [figure catalogue](catalogue.json) specifies seven tables and 24 figures. `schema_version=1` preserves the existing structural revision; `catalogue_revision` identifies this extended evidence-tier figure programme. The [JSON schema](catalogue.schema.json) denies unknown figure fields and enforces null artifacts for all unproduced outputs.

**F01** is the only source-generated optional P5 SVG. **F05-F09** are five earlier synthetic PNGs externally referenced by SHA-256, not checked into Git. All other F-IDs remain unproduced placeholders. The six priority synthetic designs, including the break-even contour, are tracked as granular tasks in the [Conductor workplan](../../conductor/tracks/P9-reporting-contracts/figure-workplan.md). Scientific [claim and promotion rules](../../conductor/tracks/P9-reporting-contracts/design.md) apply.

Every figure specifies a decision question, estimand, source table, units, denominator, evidence tier, missingness, paired semantics, source requirements, accessibility, renderer provenance and release gate. No approved CHHHS data, native provider qualification or clinical/Finance sign-off is implied.

## P10 scientific measurement contracts

[Metric registry](metrics.json) and [schema](metrics.schema.json): 30 canonical metrics and 13 denominators tied to the Clinical Director and CHHHS 11-dataset request. [Claim policy](claim-policy.json) and [schema](claim-policy.schema.json) deny external approval by public-source flags. [Figure provenance](provenance-record.schema.json) and [unproduced template](provenance-template.json) do not represent completed figures. [Visual review matrix](visual-review.json) is not executed; [uncertainty taxonomy](uncertainty-taxonomy.json) distinguishes PSA from empirical sampling uncertainty. Historical [v2 catalogue](history/catalogue-figure-programme-v2.json) and [v2 schema](history/catalogue-schema-figure-programme-v2.json) remain versioned. Current revision is P10-v3; P4/P5 numerical behaviour is unchanged.
