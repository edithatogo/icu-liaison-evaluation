# P4 specification — decision-analytic cost-consequence simulation

**Decision:** compare an incremental adult ICU liaison programme with actual
current care; report resource and potential budget consequences, access/capacity
and required safety outcomes without approving clinical effectiveness.

**Inputs:** versioned `EconomicScenario` in `model-inputs/p4/illustrative.json`;
annual eligible discharges, public external exit-block rate, *separate* synthetic
unplanned 72h return probability, delay mechanism/effect, incremental costs,
shift-independent usability/cash fractions, strategy coverage, safety status and
selected Gaussian-copula correlations. Parameter types/provenance validated by
Pydantic; inverse CDF and numerical operations owned by SciPy/NumPy.

**Admit P2/P3 before modelling:** preserve the 12-month programme horizon,
AUD price year, primary `current_care` and `liaison_service` comparators and
all six mandatory balancing outcomes. Reconcile public proxy identity, value,
source URL, reporting period, cohort and denominator against the P3 register.
Fictional P4 runs and P5 reports reject priors labelled as local aggregates.
Additional synthetic variants retain their proposed-strategy status.

**Outputs:** annual index ICU days released; physically usable days not
monetised; early unplanned returns avoided (including negative); gross and net
*resource* benefits; distinct *hypothetical* cash-budget impact; paired strategy
and threshold reports; structured Voiage surface. Index delay and subsequent
readmission segments do not overlap. Dapane owns *actual* quotation arithmetic;
P4 exports exact nominal nonnegative counterfactual requests for later
installed-provider qualification. Value-of-information method is Voiage-owned.

**Stop conditions:** no observed CHHHS input, no validated causal treatment
mechanism, safety margins unapproved, rights/clinical review and local costing
unavailable, hosted/native providers not qualified. No publication-ready ICER,
QALY, commercial investment case, complete capacity DES or mortality estimate.
