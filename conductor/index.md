# ICU liaison health-economic evaluation — Conductor

This is the source project for [edithatogo/icu-liaison-evaluation](https://github.com/edithatogo/icu-liaison-evaluation).
Track ownership and phase status are explicit in [the registry](tracks.md).
Current scope is the initial P7/P8 source reconciliation and repository import;
native providers, CHHHS calibration and clinical/Finance acceptance stay separate.

- [Product](product.md) and [guidelines](product-guidelines.md)
- [Technical stack](tech-stack.md) and [workflow](workflow.md)
- [Python style](code_styleguides/python.md)
- [Repository import](../docs/repository-import.md)

- [Architecture](decisions/ADR-0001-consumer-first.md)
- [Public source register](evidence/source-register.json)
- [Migration provenance](evidence/migration-manifest.json)
- [External inputs](../model-inputs/illustrative.json)
- [Quality and verification](tracks/P0-portable-consolidation/test-matrix.md)

- [P2 clinical-economic protocol](tracks/P2-clinical-economic-protocol/index.md)
- [Draft protocol for review](../docs/protocol-p2.md)
- [CHHHS source requirements](../docs/data-requirements-p2.md)

- [P3 public source and controlled data intake](tracks/P3-evidence-data-infrastructure/index.md): synthetic-only source implementation, local and provider gates retained.

- [P4 probabilistic cost-consequence model](tracks/P4-economic-decision-model/index.md):
  P2/P3 admission, correlated uncertainty, clinical safety guardrails and
  scenario analysis; no local-CHHHS effect claim.
- [P5 reproducible reports and review](tracks/P5-reporting-independent-review/index.md):
  standalone JSON/CSV/Markdown/SVG reports, retained evidence fingerprints,
  independent accounting checks and unavailable-native-provider gates.

- [P6 time-aware capacity qualification](tracks/P6-kairos-capacity-validation/index.md): neutral synthetic trace auditor and optional future Kairos dependency; no DES activation.

- [P6 optional Kairos source and synthetic holdout](../docs/p6-native-qualification.md): pinned Rust source contract; no actual provider compilation or CHHHS calibration.

- [P8 MCHS, workforce and valuation boundary](tracks/P8-abf-workforce-interop/index.md):
  source contracts and proposed provider changes; **not native/local qualification**.

- [P1 provider reuse](tracks/P1-provider-reuse/index.md).
- [P7 technical and empirical qualification](tracks/P7-technical-empirical-qualification/index.md).
- [P7 placeholder workflow](tracks/P7-placeholder-assisted-qualification/index.md): companion track preserving the later portable branch.

- [P10 measurement and claim assurance](tracks/P10-measurement-figure-assurance/index.md): canonical metrics/denominators and fail-closed evidence gates for P7 and P9.
