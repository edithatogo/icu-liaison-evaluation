# P8.4 separate funding, workforce and decision views

## Purpose

This project consumes the existing, separately owned MCHS annual acute,
Microcosting Health Workforce, Dapane and Voiage libraries. It must never
reproduce NWAU formulas, award/penalty interpretations, Rust valuation
arithmetic, or VOI solvers. The source-level composition exists solely to bind
an inspectable synthetic scenario to an explicit, unqualified provider trace.

## Three distinct financial perspectives

1. **P4 annual resource net benefit:** illustrative resource benefit minus an
   assumed total incremental service cost (including an unspecified workforce
   component). The model's 5,000 paired draws are not recalculated by P8.4.
2. **P4 cash-budget impact:** a different illustrative view using separately
   assumed cash-realisability fractions, not observed CHHHS funding.
3. **MCHS paired-episode activity shadow:** *one* synthetic hospitalisation's
   annual-price-year NWAU difference. Even an installed calculation cannot be
   called actual CHHHS incremental funding. The latter needs the actual funding
   mechanism, case-mix, provider-year parity and Finance approval.

Workforce/Dapane produces an **unvalued request** until installed Dapane and
source-qualified nursing quotations are available. The source-bound salary
rate would not by itself constitute a fully loaded incremental roster cost.

## Optional fictional comparison

Supply both `--funding-pricing-year` and `--assumed-aud-per-nwau` to calculate an
exact signed AUD sensitivity for one synthetic MCHS episode. The price year
must match the MCHS result. Actual hospital revenue and annual workforce cost
remain null. The other financial outputs retain their original price year and
scale.

Pass `--voiage-objective net_resource` or `--voiage-objective budget` to select
the P4 draws for current care and the named strategy only. Voiage returns EVPI
in the P4 price year's AUD per annual programme decision. The episode funding
sensitivity and workforce quotation amounts stay outside both sets of draws.
The default command needs no installed providers and preserves its prior output.

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p8_composition_cli \
  model-inputs/p4/illustrative.json --strategy liaison_service \
  --mchs-result /approved/fictional-mchs-result.json \
  --funding-pricing-year 2025 --assumed-aud-per-nwau 1000 \
  --voiage-objective net_resource
```

The provider receipt records both objectives for both proposed strategies, a
matched-year MCHS funding sensitivity and a separate dated workforce valuation.
[Fictional provider workflow](../verification/p8-provider-workflow-2026-11-24.json)

## Reconciliation before cash/funding integration

- Bind exact patient-group and episode IDs only within an approved private
  environment. A single NWAU change cannot be scaled to all discharges.
- Bind the MCHS pricing year/AR-DRG edition independently of the economic
  cost price year and service calendar. Preserve eligible ICU hours, bundled
  ICU exceptions, whole-stay LOS, patient status and adjustment provenance.
- Qualify actual service establishment, employment classifications, salary
  source editions, shift penalties, productive hours, replacement cover,
  allowances, leave relief, overhead components and no duplicate on-costs.
- Determine exactly which *components* of the existing synthetic P4 service-cost
  prior are being **replaced**. Never add the full roster cost on top of the
  same modelled service cost without a component-level reconciliation.
- Preserve three distinct Dapane valuation bases: economic resource cost,
  financial cash cost, and technical modelled funding, with separate source
  and rounding authority. Funding must not appear in the resource-cost ledger.
- Apply observed funding-allocation rules, if approved, after independently
  qualified MCHS calculation and Finance sign-off; do not equate NWAU × NEP
  with realised CHHHS revenue.
- Only select cost-only paired draw surfaces for Voiage when their units,
  run IDs, strategy order and economic perspective are explicitly aligned.
  Do not present conditional PSA assumptions as empirical probabilities.

## Local/source verification versus native acceptance

`tests/test_p8_composition.py` and `tests/test_p8_composition_cli.py` exercise
fail-closed source contracts. They do not execute MCHS, native Dapane or Voiage.
Run installed integration tests at qualified provider revisions with approved
source bundles and independent official reference oracles. The standalone
source-only package contains no wage, personal or patient data.

Upstream provider owners retain their contracts. The portfolio gates and scope
of the installed replays are tracked in the P8 plan.
[P8 plan](../conductor/tracks/P8-abf-workforce-interop/plan.md)
