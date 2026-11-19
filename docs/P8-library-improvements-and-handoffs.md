# P8 library improvement recommendations and dependency handoffs

Source observations: 18 November 2026 (exact source SHAs in the capability
register). This is a **proposal and owner handoff**, not modified upstream code,
installed validation or organisational approval. Propose improvements only when
consumer-level adapters are demonstrably insufficient; avoid expanding core
libraries for a one-off ICU study.

## MCHS — funding activity, not cost or cash (highest ABF priority)

Existing: Annual NWAU acute calculator with `DRG`, `LOS`, `ICU_HOURS`, and ICU/
private patient flags, 2024/25 and 2025/26 calculation work, an opt-in Rust acute
2025 slice and separate NEP26 equation qualification. Full current-year annual
calculator parity must **not** be inferred from a verified isolated equation.

**Improvements to consider** (use MCHS's existing annual support/parity tracks):

- Priority 1: versioned **paired-episode** consumer façade that accepts the same
  hospital episode with current-care and intervention ICU hours, records
  DRG/coding edition, pricing year, source/weight release, hospital LOS and ICU
  hour eligibility. It should call existing annual engines twice; no duplicated
  formula and no implicit shift in classification or LOS.
- Priority 1: official SAS/Excel comparison fixtures for thresholds where ICU
  hours move across rounding/eligibility/LOS category boundaries; record
  no-benefit, positive/negative hour shifts, age/bundled ICU flags, private
  patient, HAC/AHR and unsupported 2026–27 cases.
- Priority 2: machine-readable annual **capability manifest** for calculator
  stream/year, coding edition, source bundle, ICU hourly applicability,
  parity level and certified API/binary hash. Reject unknown year/edition rather
  than silently falling back to 2025 parameters.
- Priority 2 (only when multiple consumers need it): a generic output
  `NWAU` vs `technical_modelled_AUD` DTO; do **not** add actual cash-flow
  estimates to MCHS or claim the IHACPA formula is a hospital's revenue model.

Stop: until official current-year parity and local activity/coding inputs exist,
use an explicit unqualified shadow. Do not interpret a saved ICU hour as an
independently funded amount.

## Microcosting Health Workforce — nursing and shifts

Existing: source- and date-scoped `UnitQuoteRelease`, explicit quantity/price
matching and reusable `DapaneQuoteBinding`, plus work on static/dynamic
conditions, retroactive rules and QLD salary-source coverage. The current
illustrative qualified published HP3.1 reference is **health practitioner**
base pay, *not* a Queensland clinical nurse award or fully loaded staff cost.

**Improvements to consider** (join existing source-coverage and conditions v2
tracks; do not fork a second workforce engine):

- Priority 1: admit relevant **Queensland nursing** grade/band/paypoint,
  enterprise-agreement/award version and effective pay period with original
  primary source and independent HR eligibility review; explicit confidence
  and unqualified status if source rights/grade are unsettled.
- Priority 1: an immutable `RosterCostRequest` concept mapping proposed paid
  shift boundaries, productive clinical hours, employment fraction, grade, night/
  weekend/public holiday, supervision/training, vacancy/leave relief and
  backfill. Use existing interval/conditions and quote APIs; no new generic
  arithmetic or duplicate calendar.
- Priority 1: component-conservation and stacking guards for salary,
  superannuation, leave loading, overtime, allowances, agency premium, backfill
  and other oncosts; explicitly define what an already-loaded quote includes.
- Priority 2: return both a source-bound **financial roster cost** and an
  separately labelled **economic opportunity cost**, with distinct basis and
  assumptions when hours are redeployed rather than newly funded.
- Priority 2: negative fixtures for shifts crossing pay adjustments, public
  holidays, overlapping entitlements, grade substitution and retrospective
  salary corrections. Retain expected source, payroll and Dapane proof separately.

Stop: workforce FTE and salary may be estimated until a position is chosen,
but never present a hypothetical grade as CHHHS personnel cost.

## Dapane — value exact quantities; do not reimplement payroll or NWAU

Existing: exact dated quotations, component-disjoint pricing and allocation,
financial/economic/funding basis separation, source provenance, and optional
workforce Dapane consumer. Existing **MCHS source adapter track** already covers
future classified-activity and funding quotation integration.

- Priority 1: complete the existing MCHS track's source/weight edition checks
  and parallel funding/economic-cost views with explicit activity vs consumption
  identity; no new Dapane core calculator for NWAU.
- Priority 1: support consuming existing workforce quote envelopes in a
  paired-run use case, with exact quantity and component identity preserved.
- Priority 2: add a neutral, versioned ICU **interval-usage export consumer**
  only after Kairos implements committed admission/release events; open leases
  censored, no queue waiting billed as occupied use. Reuse planned process
  integration rather than adding a generic scheduler to Dapane.
- Priority 2: preserve source currency, fiscal price year and basis separately
  and offer explicit missing-cost/unknown status rather than a fabricated zero.

## Voiage and Kairos — avoid unnecessary platform changes

Voiage already supports EVPI, EVPPI, selected EVSI/ENBS, paired decisions and
financial/cost-effectiveness views. The ICU project should first supply typed,
properly aligned draw labels and per-perspective choices. Only request a general
provider change if multiple consumers demonstrate the same deficiency.

Kairos already owns deterministic staged-resource capacity scheduling. Its
neutral **quantitative usage export** under the established domain-contract
track is the relevant improvement; an ICU-specific parallel event engine is
not warranted. Native proof must precede claims about efficiency or throughput.

## Consumer acceptance matrix

| Consumer scenario | Reused provider | Independent acceptance |
| --- | --- | --- |
| Same episode, changing eligible ICU hours, unchanged DRG | MCHS | Official year-matched SAS/Excel NWAU difference; change in revenue not claimed |
| Unsupported year/DRG edition or bundled ICU | MCHS | Reject with explicit unsupported reason |
| One extra nurse shift with leave and penalties | Workforce + Dapane | Full roster/payroll reference comparison, component conservation and exact Dapane result |
| Saved ICU hours and changed readmission risk | P4/P5 + Dapane | No index/return-cost overlap; capacity not double monetised |
| Resource cost and ABF shadow from same patient episodes | MCHS + Dapane | Separate units, source years and ledger projections, no automatic sum |
| Uncertain cost-effectiveness and further research | Voiage | Same-draw alignment, appropriate perspective, independent EVPI reference |
| Shift-sensitive usable ICU capacity | Kairos | Native replay, accepted resource-use events, observed-data calibration pending |

## Data still required to activate provider paths

From ICU and coding: eligible first live adult ICU-to-ward discharges,
whole-hospitalisation episodes, ICU admission/discharge/readiness times,
DRG and **DRG edition**, in-scope ICU hours and eligibility, whole stay LOS,
cohort safety and data completeness. From Nursing Workforce and HR: selected
nursing classification/paypoint and agreement, shift/leave/backfill rosters,
paid/productive hours, actual components. From Clinical Costing: net avoidable
ICU cost, ward displacement, ICU return cost and costing year. From Finance:
pricing year, applicable funding policy, whether a shadow NWAU change can alter
an actual CHHHS allocation, and accounting treatment of non-cash capacity.
Keep actual records within authorised CHHHS systems, not in public Git.

## Consumer-first implementation update — 18 November 2026

The dedicated-project **source** now includes the narrow P8.2/P8.3 consumers
(`adapters/p8_mchs.py`, `adapters/p8_workforce.py`) and explicit runtime admission.
This satisfies the source-contract prerequisites, not upstream library improvements
or provider acceptance. The installed annual MCHS reference/parity gate and
clinical nursing quotation/conditions gate remain **unqualified**.
Do not duplicate the paired-row consumer in MCHS unless other downstream projects
need a stable general interface. The upstream handoffs above remain candidates.
