# P10 test evidence matrix

| Obligation | Source test | Acceptance |
|---|---|---|
| Registry schema and 11 dataset links | Draft 2020-12 + P10 tests | Source-only |
| D02 all-live / D03 index / D04 readiness / D05 return | Wrong-denominator negative tests | Source-only |
| NWAU versus cash | M20 NWAU and M26 AUD test | Source-only |
| 24 figure and 7 table metric links | Cross-table overlap and unknown IDs | Source-only |
| Fake approvals and provider qualification | Fail-closed claim tests | Source-only |
| Claims on verified fictional artifacts | `tests/test_p10_claim_assurance.py` checks the exact run, CSV or SVG hash, metrics, denominators, replay and policy identity | Fictional illustration |
| Fake hashes and published SVGs | Provenance template and forged-output tests | Source-only |
| Responsive, print and contrast checks | Four profiles with 56 reviewed baseline captures | Synthetic baseline |
| Source-to-mark review | Figure reader replays numeric and mark checks against the recorded inputs | Synthetic computation |
| Independent visual acceptance and clinical review | Requires independent rendered and site evidence | Pending |
| Held-out CHHHS data / signed clinical decisions | Governed data and trusted verifier | **Blocked** |
| F01 report provenance | `tests/test_p10_figure_provenance.py` checks source, renderer, SVG and numeric hashes and P9 validation | Computational review |
| Rehashed SVG and changed scenario negatives | Fresh receipt computation after a change to the manifest or input | Source rejection |
