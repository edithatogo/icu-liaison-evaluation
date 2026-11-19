# P9.4: task-level figure implementation contracts

**Ownership:** P9 figure workers own only bounded reporting code, synthetic fixtures, P9 contracts and dedicated tests. The integrator alone merges. No modification to P4 clinical/cost assumptions, P5 numerical oracles, native provider locks, protected data or source authorisation.

For **each figure**, build the RED negative tests first, render from versioned source inputs, retain exact source SHA-256, scenario seed, renderer version, numeric calculations, accessible SVG description, units and alt text. Admit only after full test suite, independent accounting cross-check, source-inventory check and exact-head CI. An external ZIP is not a repository output.

## Independently claimable priority tasks

| Task | Inputs | Required executable | Negative acceptance |
|---|---|---|---|
| P9.4.01 F02 resource waterfall | P4/P5 nominal resource components | source-to-waterfall CSV and zero-reconciled SVG | double-counted bed-days, staffing prior duplication, cash/revenue substitution |
| P9.4.02 F10 break-even boundary | P4 bounded effectiveness and annual cost priors | deterministic 2D grid, zero contour and source CSV | out-of-range effects, false crossings, silent extrapolation |
| P9.4.03 F11 paired decision scatter | P4 draw-level net resources and released capacity | draw-ID joined CSV and accessible scatter | shuffled/unpaired draw IDs, duplicated resource valuation |
| P9.4.04 F15 patient journey | P3/P6 synthetic event stages | conserved half-open interval chart with explicit unknown states | reversed timestamps, stage overlap, unknown-as-zero |
| P9.4.05 F20 nursing coverage | hypothetical paid/productive shifts and synthetic readiness distribution | weekly shift-demand heatmap and hour table | double-covered shifts, impossible productive hours, invented QLD award costs |
| P9.4.06 F24 clinical-effect assumption sensitivity | P4 clinical-effect priors incl null and harm | paired grid and caution-labelled clinical/economic plot | harm suppressed, unsafe threshold inference, invalid probabilities |

## Secondary figure tasks

- P9.4.07: Rebuild F05-F09 from reviewed source/fixture with independent visual/numeric receipts; existing PNG sha256 references serve as historical provenance only.
- P9.4.08: Prototype F13 Sankey and F18 controlled event-study **only as synthetic methodological designs**; no measured clinical or causal effect.
- P9.4.09: For F03/F04/F14/F16/F17/F19/F21/F23, implement data-admission fixtures and source/gate tests, but do not generate unqualified CHHHS results.
- P9.4.10: For F12 and F22, require installed exact pinned Voiage and official MCHS parity, respectively; no custom VOI or NWAU substitute.
- P9.4.11: Index all accepted F-IDs by question/figure type/audience/claim status, register SVG/PNG exports and reproducibility metadata.

**Definition of done per unit:** independently checked data transformations, documented population and denominator, negative fixtures, exact output identity and source provenance, visual/accessibility checks, synthetic-only watermark, and CI. Never promote a placeholder without an actual committed reproducible renderer and results.
