# Scientific figure design and recommended improvements

## Reporting and evidence architecture

1. **Evidence tiers:** `synthetic_implemented`, `external_exploratory_only`, `synthetic_design_pending`, `empirical_blocked`, and `provider_blocked`. These are independent of whether a conceptual figure seems attractive.
2. **Decision scope:** executive core set is F01/F02/F10/F11/F15/F20/F24; other figures serve methods, operations, clinical safety and supplementary reporting. Avoid a 24-chart executive slide deck.
3. **Perspective separation:** economic resources, cash budget changes, NWAU, staffed bed-days and patient safety are distinct measures. Do not monetise released capacity and also count the same delay in costs.
4. **Denominator authority:** all live ward/home discharges for ANZICS rates; first eligible adult ICU-to-ward discharge per hospitalisation for index outcomes; 72-hour return follow-up, competing deaths, transfers and missingness must be explicit.
5. **Scientific uncertainty:** paired Monte Carlo quantiles are not sampling confidence intervals; distinguish model structural assumptions and intervention uncertainty from stochastic parameter draws. Include a null-effect and possible harmful-effect scenario.
6. **Accessible graphics:** deterministic vector SVG with title/description, legible contrasts, colour-independent markers or labels, numerically referenced axes, missing-value disclosure and zero/reference lines where meaningful.

## Further improvements recommended

- **A metric/estimand registry**, machine-linking Clinical Director KPI definitions, T-IDs, F-IDs, numerators, denominators, time anchors, exclusions and 72-hour censoring. Add negative tests for denominator drift before data ingestion.
- **A directed provenance graph**, with source/digest, transformation version, scenario/seed, native provider provenance, renderer pin, approval authority and exact output checksum per F-ID.
- **A claim/approval compiler**, not a manual Boolean: prevent figures claiming local clinical effectiveness, funding change, workforce cost parity or noninferiority without the corresponding signed external evidence receipts.
- **A renderer visual acceptance matrix:** representative viewport sizes, accessible SVG metadata, print-friendly styles, independently checked chart mark values and controlled image regression (not pixel-identical cross-platform PNG hashes).
- **A decision-surface suite:** use F10 for a break-even contour and optional occupancy/clinical-safety constraint panels, with no implication that a financially favourable strategy is safe.
- **Empirical design pre-registration:** choose controls and event-study covariates before local analysis; report missingness, censoring, equity, change points and concurrent interventions.

## Promotion gates

Synthetic source acceptance requires fixture hashes, deterministic model seed, numeric oracle, accessible SVG and hosted CI. Native output requires source/binary qualification and independent method parity. Empirical results require authorised CHHHS custodian access and clinical/Finance/statistical/First Nations governance as relevant. Investment recommendations require further substantive independent review. Missing evidence is never treated as compliance.

## Measurement assurance architecture

P10 now defines common denominator IDs, metric identifiers and uncertainty classes. It also defines source-only provenance/visual review specifications and a fail-closed claim policy. P9 must not promote any P10 template to a verified external approval by editing a JSON Boolean; independently reviewed external evidence is required.
