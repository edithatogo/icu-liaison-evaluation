# P10 test evidence matrix

| Obligation | Source test | Acceptance |
|---|---|---|
| Registry schema and 11 dataset links | Draft 2020-12 + P10 tests | Source-only |
| D02 all-live / D03 index / D04 readiness / D05 return | Wrong-denominator negative tests | Source-only |
| NWAU versus cash | M20 NWAU and M26 AUD test | Source-only |
| 24 figure and 7 table metric links | Cross-table overlap and unknown IDs | Source-only |
| Fake approvals and provider qualification | Fail-closed claim tests | Source-only |
| Fake hashes and published SVGs | Provenance template and forged-output tests | Source-only |
| Responsive/print/contrast checks | Four profiles in visual matrix | **Not executed** |
| Actual source-to-mark visual and clinical review | Requires independent rendered and site artefacts | **Not executed** |
| Held-out CHHHS data / signed clinical decisions | Governed data and trusted verifier | **Blocked** |

| F01 real report provenance | `tests/test_p10_figure_provenance.py`; source/input/renderer/SVG/numeric SHA-256 + P9 validation | Implemented as **rendered_unqualified**; not a visual or clinical acceptance |
| Rehashed SVG and changed scenario negatives | Fresh receipt recomputation under tampered manifest / modified input | Implemented; independent visual/marks review remains open |
