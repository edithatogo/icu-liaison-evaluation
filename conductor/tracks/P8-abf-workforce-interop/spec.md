# P8 specification — workforce resource cost, ABF shadow and decision value

## Decision and definitions

Estimate whether an additional ICU liaison nurse service is worthwhile using
three **separate** perspectives: (1) physical/economic resource consumption
and opportunity cost, (2) workforce and cash-budget implications, (3) episode
weighted activity and a modelled ABF shadow. A change in NWAU or IHACPA
technical-price output does **not** establish actual CHHHS revenue, cash saving,
or a funded extra bed. Voiage receives explicit paired draws with decision and
perspective tags; Kairos supplies physical resource usage only if native qualified.

## Existing owner interfaces to reuse

- MCHS `nwau_py.calculators.acute` owns annual DRG/LOS/ICU-eligible-hour
  activity formulae and the official IHACPA reference bundles; 2026–27 NEP
  equation is **not** full annual calculator parity. Keep case-mix edition,
  pricing year, ICU eligibility, bundled ICU adjustment and hospitalisation
  linkage explicit. No local formula copy.
- Microcosting Health Workforce owns dated award/enterprise-agreement sources,
  employee classification, pay-point, penalty and leave/rostering interpretation,
  immutable `UnitQuoteRelease` and Dapane quote exports. An existing HP3 public
  wage example does not qualify Queensland nursing classifications or a fully
  loaded clinical-nurse liaison roster.
- Dapane v0.1 owns exact dated resource valuation and cost-component
  conservation; it separates `economic_cost`, `financial_cost`, `funding` and
  `charge` bases. Its existing MCHS source-adapter track owns any general
  MCHS-to-valuation integration. Do not duplicate it here.
- Voiage v3.1.0 owns VOI/decision uncertainty; P4/P5 own ICU clinical effects,
  cost-consequence perspectives and the study's uncertainty draws.
- Kairos owns DES queues and physical events; event/resource-use export is
  subject to its own independent source and native qualification.

## Deliverables

- Source-pinned current capability register with no installed-admission claim.
- Structural crosswalk that requires NWAU (not AUD) for activity; a nursing
  classification and accepted rate/roster before workforce totals; separate
  Dapane resource-cost and cash-realisation views; no fake hospital revenue.
- Synthetic positive and fail-closed negative tests for schema, provenance and
  provider boundaries, and explicit P8 plans for installed and clinical gates.
- One bounded project adapter per adopted provider, not an invented calculator,
  duplicate roster engine, valuation kernel, VOI solver or event scheduler.

## Excluded claims

No historical or current CHHHS patient data, true local hospital staffing, actual
payment/allocation, annual funding change, change to contract classifications,
clinical safety or implementation effectiveness can be inferred from this
source-only configuration. No repository remote, PR merge, provider release,
patient data extraction or deployment authority is implied.

## P8.4 optional composition contract (added)

The source-only crosswalk is generated using `icu_liaison.p8_composition`.
It accepts the exact P4 strategy identity and input SHA, plus optional bounded
MCHS NWAU and workforce/Dapane provider results. It rejects any claimed actual
revenue, premature installed/clinical/annual parity, mismatched valuation basis,
changed price year, duplicate use, or fabricated financial total. It never
updates the P4 decision-surface arrays. Future fully valued staffing exposure
must reconcile against and **replace**, not duplicate, the relevant existing
P4 service-cost prior component.
