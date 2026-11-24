# P8 source-only planning handoff — 18 November 2026

Reconciled with existing P0–P7 source, no numerical model changes or provider
repository mutations. Frozen source observations are in
`model-inputs/p8/provider-capabilities.json`, with no installed acceptance.
The user intends to provide a dedicated repository later.

The highest-value domain-library improvements are registered in
`docs/P8-library-improvements-and-handoffs.md`. They are *candidate requests*,
not permissions to override active provider owners or change their published
APIs. P8.0–P8.1 source/contract design may be accepted after local tests;
P8.2–P8.5 native, clinical, finance and repository tasks remain pending.

No new nursing rate, annual MCHS weighting, funding allocation, cohort volume,
actual clinical benefit or native provider release is inferred.

## Consumer increment — 18 November 2026

Implemented source-only P8.2.0/P8.3.0 with strict synthetic typed contracts, two
MCHS annual calls, roster quote/usage transport to existing workforce/Dapane,
reproducible schemas and CLI. No provider formulae, rates or quantitative funding
logic copied. Native binaries and workforce source fixtures unavailable; tests
are **injected contract checks**, not installed provider qualification.

The portable source remains unpushed. No named dedicated GitHub repository is
present in the accessible `edithatogo` repositories; PR #215 in CareOps Sim is
preserved, not a receiving repository.

## P8.4 consumer composition increment

The new `icu_liaison.p8_composition` module creates an audit sidecar from an
existing P4 run. An annual MCHS output remains **one synthetic episode's NWAU
change**, with unverified annual formula parity, not an annual financial
consequence. The workforce result remains a **not-valued Dapane request**:
no staff rate or annual cost is invented. The P4 assumed total service-cost
prior is not overwritten, double counted or silently reconciled with a salary
amount. A replacement/full roster comparison requires the original P4 prior
component to be identified first.

The CLI is a safe source-only JSON-output projection; native runs, Voiage VOI,
CHHHS income, clinical validation and private repository creation remain
unqualified. Reuse only the existing provider owners' contracts. No original
provider source, payroll formula, patient extract, hospital revenue or private
quote is packaged here.

### Native fictional valuation on 24 November 2026

Chat 01a1f64b-ef56-75f3-a2dc-bafc0180b28e owns the bounded P8.4 valuation and
Conductor reconciliation on `codex/icu-review-readiness` in
`/Users/doughnut/.codex/worktrees/icu-remaining-schedule.ZuYzD4/conductor`.
The runtime scope is the approved Dapane 0.1.0 wheel and CPython 3.15.2 on
the recorded macOS arm64 host. The next operation is exact-head source and
privacy checks.

For the fictional MCHS pair, Dapane valued resource use and cash costs in
separate requests. Both views included the salary and on-cost components once
for the same paid shift. A repeated salary component failed with
`component_overlap`. The NWAU change was multiplied by a fictional price
and recorded as an episode funding sensitivity. Actual revenue stays null.
[Valuation receipt](../../../verification/p8-native-synthetic-valuation-2026-11-24.json)

Repeat with the reviewed wheel installed into an isolated directory for the
verified repository interpreter.

```sh
PYTHONPATH="src:$icu_dapane_overlay" .venv/bin/python \
  tools/qualify_p8_synthetic_valuation.py --wheel "$icu_dapane_wheel"
```

## Reference, quote and decision replay on 24 November 2026

The consumer now checks reference directory hashes and exact dated workforce
quantities. The pinned workforce provider's fictional test rates passed
Dapane valuation. The fixture was exported with the provider's synthetic
source type and unvalidated evidence labels. The HP3 artifact was rejected
for the fictional roster's different classification.

The composed report can show a price-year-matched case funding sensitivity
beside an explicitly selected Voiage comparison. The annual P4 cost prior
still needs component-level reconciliation before a site staffing estimate
can replace it. Actual CHHHS funding remains unknown.
[Native workflow receipt](../../../verification/p8-provider-workflow-2026-11-24.json) ·
[Rerun instructions](../../../docs/P8-composition-and-reconciliation.md#optional-fictional-comparison)
