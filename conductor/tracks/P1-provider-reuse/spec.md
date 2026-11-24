# Specification — P1 provider reuse

## Purpose

Eliminate unnecessary custom cost valuation and VOI computation in the ICU
liaison economic study by consuming the existing maintained first-party Dapane
and Voiage providers. Preserve scenario-specific clinical resource equations
and independent synthetic oracles. Require installed native evidence before
claiming a provider integration complete.

## Implemented interfaces

1. Source reference lock: Dapane source at an immutable commit, unpublished
   0.1.0 valuation interface; Voiage released v3.1.0 tagged commit, Python
   3.15.2+ requirement. No wheel digest is falsely inferred from Git source.
2. Dapane: construct two counterfactual *incremental* resource ledgers with
   nonnegative exact decimal use/quotation values, consistent AUD price year,
   perspective and cost basis; value each using Dapane. Divide index ICU
   discharge-delay time from subsequent return episodes to avoid double
   charging. A negative avoided-return outcome becomes an additional-return
   cost in the intervention ledger, never negative usage. Reject incomplete,
   incompatible or malformed provider reports.
3. Voiage: provide an annual programme financial net-resource-benefit array,
   with two named alternatives and one state-of-uncertainty per row. Delegate
   EVPI to the released DecisionAnalysis method rather than implementing an
   alternative solver. Label output as economic resource-only (not QALY/ICER).
4. Installed qualification CLI: require exact provider versions, execute
   numerical reference oracles against the actual providers and report observed
   interpreter/distribution/native-extension metadata. Require the imported
   package and loaded extension to match the installed distribution. The
   reviewed-extension check requires the locked file and digest for the
   selected platform and Python patch. Unavailable or incompatible
   environments must fail closed with UNVERIFIED and nonzero exit.
   Source/runtime artifact attestation and true CHHHS validity are separate gates.

## Out of scope

No access to CHHHS local files or private case-level observations; no wheel
publication, provider source edits, new Rust numerical engine, new agent,
macroeconomic benefit, mortality/QALY inference, automatic annual funding, or
Kairos event simulation. The nominal Dapane bridge is a *difference ledger*;
it is not a hospital episode cost model or a drop-in replacement for the
NumPy/SciPy exploratory sensitivity analysis. Dapane cannot infer resource
use from epidemiological rates; the consumer supplies that use explicitly.
