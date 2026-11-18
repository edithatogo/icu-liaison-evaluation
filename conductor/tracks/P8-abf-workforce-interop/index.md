# P8 — MCHS ABF and Workforce costing interoperability

[Specification](spec.md) | [Plan](plan.md) | [Metadata](metadata.json) |
[Risk register](risk-register.md) | [Acceptance matrix](test-matrix.md) |
[Handoff](handoff.md)

Consumer-led implementation track for the dedicated ICU liaison project. Reuses
MCHS, Microcosting Health Workforce, Dapane, Voiage and optional Kairos. An
inspectable provider-capability register, a strict **planning-only** source
crosswalk, **synthetic annual MCHS paired-input and nursing quote consumers**,
and focused negative tests are implemented. Provider binaries, local
pricing, roster entitlement, NWAU episode parity, Finance approval and the
receiving GitHub repository remain *unverified*. This track does not take over
active work in any provider repository.

[Capability register](../../../model-inputs/p8/provider-capabilities.json) |
[Null-valued source-only contract](../../../model-inputs/p8/synthetic-null-shadow.json) |
[Library change proposals](../../../docs/P8-library-improvements-and-handoffs.md)

[Implemented P8.2/P8.3 source consumer contract](../../../docs/P8-implemented-consumer-contracts.md) | [MCHS fixture](../../../model-inputs/p8/synthetic-mchs-pair.json) | [Nursing fixture](../../../model-inputs/p8/synthetic-nursing-roster.json)
