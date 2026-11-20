# P9 reporting contract

[Clinical Director request](../../../docs/clinical-director-data-request.md) | [Figure contract](../../../contracts/reporting/catalogue.json) | [Contract schema](../../../contracts/reporting/catalogue.schema.json) | [Granular tasks](figure-workplan.md) | [Design decisions](design.md) | [Plan](plan.md)

**Seven table contracts and 24 figure contracts.** F01 is the optional P5
synthetic SVG. The P9 companion renderer generates F02, F10, F11, F15, F20
and F24 with matching CSVs, hashes and an accessible index. F05–F09 retain
their external exploratory references. Site-validated figures still require
admitted data and independent review.

P9 consumes the shared [P10 measurement/evidence assurance](../P10-measurement-figure-assurance/index.md) contracts. P10 owns metric meanings and claims; P9 retains figure generation and P5 independent numerical review.
