# P0 portable consolidation

[Specification](spec.md) · [Plan](plan.md) · [Metadata](metadata.json) ·
[Ownership](agent-contract.md) · [Tests](test-matrix.md) ·
[Risks](risk-register.md) · [Handoff](handoff.md)

P0 is **partially completed**, with portable sources, local CI/CD + `gitleaks`
hooks, public hosted CI (`44444785989`), isolated Python 3.15.2 native
Dapane/Voiage numerical oracle runs, and the 19-file PR #215 comparison
completed. The repository is now public with GitHub Secret Scanning and Push
Protection enabled, and the reviewed Conductor submodule is initialized at
`7a5c560a4fdf5297be58594cc37527eb12790272` (`autoUpdate: true` caveat noted).
The [import record](../../../docs/repository-import.md) and
[PR #215 comparison](../../../docs/pr215-migration-comparison.md) track
reconciliation and checks. Independent wheel-provenance adjudication, live
Gemini runtime command acceptance, original PR #215 closure and CHHHS
calibration remain pending.

P0.5 completed the CPython 3.15.2 migration for local development, isolated
builds, Git hooks and hosted synthetic CI. The
[migration receipt](../../../verification/python-315-migration-2026-11-19.json)
records the exact hosted run and the full suite and focused P5 results with
Dapane installed.
