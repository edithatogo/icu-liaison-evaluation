# P0 portable consolidation

[Specification](spec.md) · [Plan](plan.md) · [Metadata](metadata.json) ·
[Ownership](agent-contract.md) · [Tests](test-matrix.md) ·
[Risks](risk-register.md) · [Handoff](handoff.md)

P0 is **partially completed**, with portable sources and local tests prepared.
The user has provided the private destination repository and the reviewed
Conductor submodule is initialized at `7a5c560a4fdf5297be58594cc37527eb12790272`.
The [import record](../../../docs/repository-import.md) tracks source reconciliation
and checks. PR #1 is merged into `main` (`4644bb4`), local CI/CD + Git hooks are
active, and static Conductor 0.4.1 runtime parity is verified (`autoUpdate: true`
caveat noted). Hosted CI, Dapane/Voiage installed-provider qualification, live
Gemini runtime command acceptance, original PR closure and CHHHS calibration
remain pending.
