# P2 — Clinical and economic model specification

[Specification](spec.md) | [Implementation plan](plan.md) |
[Metadata](metadata.json) | [Ownership](agent-contract.md) |
[Risk register](risk-register.md) | [Test matrix](test-matrix.md) |
[Handoff](handoff.md)

The machine-readable [draft protocol](../../../model-inputs/clinical-economic-protocol.json),
[32-field data dictionary](../../../model-inputs/clinical-data-dictionary.json),
[P2-to-CHHHS field crosswalk](../../../model-inputs/p2-chhhs-field-crosswalk.json),
and [fail-closed P2.5 sign-off template](../../../model-inputs/p2-governance-signoff-TEMPLATE.json)
are supported by the [clinical/economic methods brief](../../../docs/protocol-p2.md),
[P2.5 stakeholder review pack](../../../docs/p2-stakeholder-review-pack.md),
and the [P2 admissions CLI](../../../src/icu_liaison/protocol_cli.py).

P2.1–P2.4 source contracts and the P2.5 stakeholder review pack / crosswalk
validators are verified (`verification/p2-governance-crosswalk-2026-11-19.json`);
site-specific clinical/Finance/HREC/First Nations approval and local CHHHS data
remain blocked in P2.5.
