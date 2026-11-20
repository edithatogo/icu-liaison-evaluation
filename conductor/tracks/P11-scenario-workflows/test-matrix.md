# P11 — Verification matrix

| Requirement | Acceptance evidence | Status |
| --- | --- | --- |
| Qualified workflow runtime | Isolated install and execution on the actual repo-local Python patch, with dependency versions and failure details retained | Local pass |
| Synthetic scenario definitions | Base plus five existing P10 cases, schema validation and exact changed assumptions | Local pass |
| Paired A/B model and report | P4 shared draws, P5 comparison and independent reader agree for every scenario | Local pass |
| Null and adverse cases | Existing P10 invariants pass and clinically unmeasured status remains explicit | Local pass |
| Run identity and provenance | Stable identity for identical effective inputs, code, runtime and seed, and changed relevant components change identity | Local pass |
| Output revision and integrity | Linked report/figure revisions, file hashes, tamper and missing-file checks, and prior outputs retained | Local pass |
| Scenario change | Only the changed scenario and its downstream aggregate rebuild | Local pass |
| Figure-only change | P5 model report reused, affected figures rebuilt, and any numerical verification replay reported | Local pass, renderer and style |
| P9 companion | Six independently reviewed figures per scenario; fixed-prior F10 does not invent a range | Local 36-figure run and recovery tests passed |
| No-op rerun | Unchanged completed targets perform no analytical rebuild | Local pass |
| Failure and recovery | Interrupted and concurrent synthetic runs preserve committed output and recover without partial publication | Local pass |
| Privacy and readiness | Public fixture and metadata remain synthetic, and restricted material remains in its approved environment | Local synthetic checks pass; external gates remain open |
| Integration | Full local suite and synthetic workflow plus hosted CI for the integrated source revision | Passed locally and on integrated main commit 4398a03 |
