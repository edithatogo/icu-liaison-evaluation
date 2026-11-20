# P11 — Verification matrix

| Requirement | Acceptance evidence | Status |
| --- | --- | --- |
| Qualified workflow runtime | Isolated install and execution on the actual repo-local Python patch, with dependency versions and failure details retained | Planned |
| Synthetic scenario definitions | Base plus five existing P10 cases, schema validation and exact changed assumptions | Planned |
| Paired A/B model and report | P4 shared draws, P5 comparison and independent reader agree for every scenario | Planned |
| Null and adverse cases | Existing P10 invariants pass and clinically unmeasured status remains explicit | Planned |
| Run identity and provenance | Stable identity for identical effective inputs, code, runtime and seed, and changed relevant components change identity | Planned |
| Output revision and integrity | Linked report/figure revisions, file hashes, tamper and missing-file checks, and prior outputs retained | Planned |
| Scenario change | Only the changed scenario and its downstream aggregate rebuild | Planned |
| Figure-only change | P5 model report reused, affected figures rebuilt, and any numerical verification replay reported | Planned |
| No-op rerun | Unchanged completed targets perform no analytical rebuild | Planned |
| Failure and recovery | Interrupted and concurrent synthetic runs preserve committed output and recover without partial publication | Planned |
| Privacy and readiness | Public fixture and metadata remain synthetic, and restricted material remains in its approved environment | Planned |
| Integration | Full local suite and synthetic workflow plus hosted CI for the integrated source revision | Planned |
