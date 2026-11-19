# ADR-0006 — MCHS and nursing workforce as optional providers

Status: **Proposed for dedicated project; contract/source admission only**.
Date: 18 November 2026. Supersedes no existing ADR or provider track.

Decision: The ICU liaison programme owns the clinical estimand, counterfactual
scenarios, output joining and three separate financial views. MCHS remains the
source of weighted-activity and annual ABF formula logic. The workforce library
remains the source of wage, conditions and roster interpretation. Dapane prices
exact economic resource use (not general NWAU or payroll policy). Voiage owns
uncertainty/VOI analysis. Kairos remains optional for time-aware use events.

Views and units:

1. Resource/economic cost: AUD per explicitly identified resource exposure,
   measured or modelled using an exact-year quotation; marginal and fully
   allocated cost separately declared.
2. Workforce service cost: AUD of incremental paid employment and replacement
   cover, with explicit award, pay point, oncost composition and hours basis.
3. Funding shadow: NWAU and, if year-qualified, separately technically modelled
   AUD from IHACPA annual pricing rules; actual allocated CHHHS revenue remains
   unknown unless independent local Finance evidence establishes it.
4. Operational capacity: staffed-bed hours and queued waits, not automatically
   cash or incremental funding.
5. Decision uncertainty: explicitly selected annual net-benefit/perspective
   draws; no universal addition of resource cost and funding shadow.

Evidence sequence: source/semantic admission → official calculator and employment
fixture parity → installed provider receipts → local episode and staffing
reconciliation → actual funding applicability → independent clinical, economic
and Finance review. The included null-value schema intentionally prevents an
unobserved amount from being silently represented as zero.

Alternative rejected: duplicating the official SAS/Excel formula in the ICU
consumer, treating MCHS activity as Dapane resource use, or applying an HP3 wage
rate to a nursing role without classification evidence.
