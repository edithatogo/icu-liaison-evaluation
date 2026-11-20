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
- [~] P10.10 Generate output-level provenance DAG and recompute actual source/model/renderer/SVG digests.
- [~] P10.11 Qualify visual regressions across mobile/tablet/desktop/A4: actual screenshots, contrast and independent data-mark audits.
- [~] P10.12 Implement factorial sensitivity decomposition with null/harm clinical effects and structural alternatives, without causal claims.
- [ ] P10.13 Reconcile P7 governed data with M-IDs and register external clinical/Finance review receipts.
- [ ] P10.14 Implement approval validity, protocol freeze and staleness notifications before site reports.

**Lower-capability task rule:** Each task owns a non-overlapping file set, has a failing negative fixture before behaviour changes, one deterministic acceptance oracle, explicit prohibited P4/P5/provider-core paths, source manifest update, exact-head CI and a reviewer handoff. One integrator merges.

- [x] **P10.10a:** independently recompute P4 canonical scenario digest, P5 model identity/manifest, F01 SVG hash and P5/P9 reviews; emit a reproducible directed source→table→figure graph outside the P5 bundle. This certifies **computational consistency only**.
- [x] **P10.10b:** negative fixtures for changed input seed, missing SVG and rehashed tampering; verify stored receipts against fresh source hashes. No editable receipt grants an external authority.
- [x] **P10.10c:** add actual independent SVG mark/visual receipts before any `accepted_synthetic` status or human visual acceptance.

- [x] **P10.15a:** register all six mandatory P2 safety outcomes as unmeasured with null noninferiority margins and no invented local source.
- [x] **P10.15b:** reject positive synthetic net resource benefit as clinical investment authorisation; test unknowns, fake margins/signoffs, endpoint omissions, nonfinite economics and incorrectly substituted endpoints.
- [ ] **P10.15c:** clinically determine margin/effect/threshold per endpoint and verify external authority before site decision.

- [x] **P10.14a:** source-level version, effective-date, exclusive expiry, price year and revocation contract with four explicit unverified source categories.
- [x] **P10.14b:** validate date intervals, linked M/F identifiers and pricing-year compatibility; deterministic expiry and revocation negative tests.
- [ ] **P10.14c:** trusted authority verification, subscription to real revocation feeds and removal of previously accepted site results, under approved governance.

- [x] **P10.12a:** execute five adversarial, paired, seeded P4 synthetic scenarios: null effect, harmful returns, no addressable delay, no usable capacity and no cash realisability; preserve P4/P5 kernel authority.
- [x] **P10.12b:** assert independent accounting/capacity invariants and fail-closed P10 safety policy for each proposed strategy in CI.
- [x] P10.12 synthetic factorial analysis in F24. Each paired grid cell reports the joint null, delay contrast, return contrast and interaction in annual AUD.
- [ ] **P10.12c:** add separately qualified structural-model and observed-data uncertainty decomposition after actual CHHHS/clinical evidence and methods review.

- [x] **P10.16a:** source-only draft study preregistration and intervention-fidelity contract; distinguish roster eligibility from realised liaison contacts and avoid adjustment for post-treatment exposure as baseline confounding.
- [x] **P10.16b:** prespecified comparison/design, mandatory clinical safety outcomes, negative controls and draft-case mix requirements; reject fake registration, site approval and missing outcomes.
- [x] **P10.16c:** define the D03 index-specific valid-ready discharge-delay metric separately from M05/D04 all-live descriptive reporting, before a site primary outcome or statistical analysis can be frozen.
- [ ] **P10.16d:** clinically approve pre-registration, current-care comparator, roster/contact definitions, intervention start, safety margins, data governance and independent analysis lock.
