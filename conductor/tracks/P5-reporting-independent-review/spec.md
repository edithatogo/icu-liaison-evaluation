# P5 specification — inspection-grade synthetic decision outputs

**Required report contract:** machine-readable P4 summary with all economic
and safety caveats; cost-consequence table (resource savings, hypothetical
budget costs and physical bed capacity separately); paired incremental draws
and probabilities; nominal break-even thresholds; one-way marginal prior
sensitivity; provider-compatible valuation requests; Voiage-compatible annual
programme net resource decision matrix; a non-proprietary Markdown decision
brief; optional Matplotlib SVG; source-admission and SHA256 content manifest.

**Independent checking:** cross-check each sampled strategy's accounting
identities, including net cash versus net resource and nonmonetised capacity.
Test against known nominal reference and tampered data. Report does not equal
external clinical/economic independent peer review; its output cannot approve a
business case.

**Provider policy:** `--voiage` must use the actual installed Voiage v3.1 API
and fail closed when absent; never compute EVPI by reimplementation. A
synthetic contract-test stub is labelled `injected_contract_test_only`. Dapane
resource use is exported as two nonnegative counterfactual requests, but
valuation status remains pending actual installed native execution.

**Publication:** new aggregate synthetic directory only; create in isolated
temporary staging, verify exact SHA256 file manifest and atomically rename.
Never overwrite an existing output; no patient-level identifiers or real data.
Actual CHHHS private data require an independently scoped governance and
processing contract, not this public portable package.

## P5 completion increment — 18 November 2026

Consumer now optionally executes Dapane exact-costing requests under an explicit
`--dapane` flag, reconciles modal resource benefit against the P4 independent
point-input reference to two-cent tolerance for separately rounded ledgers and
stops without publication on disagreement. The status
`native_provider_called_unqualified` **does not** certify installed binary,
release signatures or independent economic assumptions; injected tests report
`injected_contract_test_only`. Default valuation remains `not_executed`.

A second, separately callable P5 report reader loads the published `decision-
surface.csv`, recalculates all strategy means/quantiles and paired financial
resource comparisons, verifies the manifest and rejects false investment-ready
claims even after the manifest is rehashed. It checks computational consistency
of a self-contained synthetic artefact, not external clinical/causal validity.

## Standalone table checks

The reader recomputes resource statistics and paired differences from the
annual decision draws. It matches the cost-consequence rows and their units
and boundaries to the report summary. The paired cash rows must agree with
the summary for the zero incremental current-care comparator. The cash
cross-check uses the published summaries. Fully fixed scenarios publish the
registered sensitivity header and explain the absence of sensitivity rows.

## Bundle review

The version 1 bundle has eight required files. The comparison SVG and Dapane
valuation are optional. The manifest and each listed file must be regular
files in the bundle. The reader checks the digests and uses those same bytes
for its accounting checks. It validates one-way sensitivity row bounds and
swings, then compares the decision brief with the text rendered from the
published summary and tables. Verifying the sensitivity estimates themselves
requires the original priors and P4 model.

An empty pair of Dapane nominal ledgers has zero incremental resource use.
The report records that no provider call was needed, including when every
proposed strategy has empty ledgers.
