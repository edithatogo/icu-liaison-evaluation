# Material risks and stop rules

- Wrong ICU denominator: CCR episode 4.5% and APD patient 4.0% do not supply a
  72-hour unplanned return risk; neither may be substituted by the model.
- Pooled rate used as local effect: external 20.4% delay rate cannot be a CHHHS
  estimate, regardless of model precision.
- Cost/risk overlap: early returns and index ICU delays must not be priced twice.
- Capacity versus expenditure: released bed-days are not necessarily cash or
  usable staffed capacity; neither Dapane nor Voiage solves causal identification.
- Input uncertainty: independent triangular ranges are illustrative, not fitted
  posterior distributions or predictive intervals.
- Provider acceptance: import/interface tests with fakes do not validate an
  installed Dapane wheel or Voiage native Rust package.
- Source privacy: the workbook and conversations remain separate; reviewed
  migration need not imply publishing material.
- Incomplete migration comparison: closing PR #215 before comparing the
  imported source and independent acceptance risks losing source history.
