# P10 execution plan — bounded testable increments

## Source-level (implemented; requires hosted acceptance)
- [x] P10.01 Version denominator D01–D13 and metric M01–M30 definitions with explicit censoring.
- [x] P10.02 Link all T01–T07 and F01–F24 to metric IDs; reject unknown/disjoint references.
- [x] P10.03 Preserve methodological denominator pins and source dataset IDs with regression tests.
- [x] P10.04 Version six uncertainty classes and interval semantics; separate source-quality from model uncertainty.
- [x] P10.05 Define a figure provenance record schema and unproduced template; fake output hashes do not grant qualification.
- [x] P10.06 Define a claim-policy schema and fail-closed source validator for clinical, Finance, NWAU, provider and investment gates.
- [x] P10.07 Define responsive/print visual acceptance matrix with clear **unexecuted** status.
- [x] P10.08 Integrate with P9 catalogue validation and full CI; retain original v2 catalogue/schema for migration audit.

## Evidence-dependent implementation tasks (unaccepted)
- [ ] P10.09 Implement independent verifier for CHHHS custodian and external provider signatures, including revocation/expiry, with no public signing material.
- [ ] P10.10 Generate output-level provenance DAG and recompute actual source/model/renderer/SVG digests.
- [ ] P10.11 Qualify visual regressions across mobile/tablet/desktop/A4: actual screenshots, contrast and independent data-mark audits.
- [ ] P10.12 Implement factorial sensitivity decomposition with null/harm clinical effects and structural alternatives, without causal claims.
- [ ] P10.13 Reconcile P7 governed data with M-IDs and register external clinical/Finance review receipts.
- [ ] P10.14 Implement approval validity, protocol freeze and staleness notifications before site reports.

**Lower-capability task rule:** Each task owns a non-overlapping file set, has a failing negative fixture before behaviour changes, one deterministic acceptance oracle, explicit prohibited P4/P5/provider-core paths, source manifest update, exact-head CI and a reviewer handoff. One integrator merges.
