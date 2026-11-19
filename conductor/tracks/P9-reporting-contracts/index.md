# P9 reporting contract

[Clinical Director request](../../../docs/clinical-director-data-request.md) | [Figure contract](../../../contracts/reporting/catalogue.json) | [Contract schema](../../../contracts/reporting/catalogue.schema.json) | [Granular tasks](figure-workplan.md) | [Design decisions](design.md) | [Plan](plan.md)

**Seven table contracts and 24 distinct figure contracts.** F01 is the single source-generated P5 synthetic SVG. F05-F09 refer to five earlier exploratory PNGs in a separate ZIP; they are **not** repository report artifacts. The next six synthetic figures are F02, F10, F11, F15, F20 and F24. Every ungenerated figure remains a null-artifact placeholder. No clinical, Finance, provider or observed CHHHS acceptance is inferred.

P9 consumes the shared [P10 measurement/evidence assurance](../P10-measurement-figure-assurance/index.md) contracts. P10 owns metric meanings and claims; P9 retains figure generation and P5 independent numerical review.
