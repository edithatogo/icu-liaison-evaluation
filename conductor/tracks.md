# Track registry — independent ICU liaison economic evaluation

The previous exploratory `careops-sim` R78–R81 tracks remain historical source
context, not execution authority in this independent project. Retain PR #215
until content is faithfully reconciled and a replacement is verified.

- [~] **P0 — Portable consolidation and Conductor handoff**
  ([index](tracks/P0-portable-consolidation/index.md),
   [spec](tracks/P0-portable-consolidation/spec.md),
   [plan](tracks/P0-portable-consolidation/plan.md)).
  Source, curated evidence, scenario and tested local adapters are preserved;
  the repository is now public with GitHub Secret Scanning + Push Protection
  enabled, hosted GitHub Actions CI passed on `main` (`1c7f640`, run
  `44444785989`), local CI/CD + `gitleaks` Git hooks (`pre-commit`,
  `pre-merge-commit`, `pre-push`) are active, static Conductor 0.4.1 parity is
  verified (`autoUpdate: true` caveat), isolated Python 3.15.2 native
  Dapane `0.1.0` / Voiage `3.1.0` numerical oracles passed, and the 19-file
  PR #215 comparison is recorded. P0.5 completed the CPython 3.15.2 migration
  with 342 tests passing in hosted CI and locally with Dapane installed.
  [Migration receipt](../verification/python-315-migration-2026-11-19.json)
  Independent wheel-provenance adjudication,
  live Gemini runtime command qualification, CHHHS data, and independent
  sign-off to retire CareOps Sim PR #215 remain pending.
- [~] **P1 — Runtime provider reuse qualification**
  ([index](tracks/P1-provider-reuse/index.md),
   [spec](tracks/P1-provider-reuse/spec.md),
   [plan](tracks/P1-provider-reuse/plan.md)).
  Source lock, Dapane incremental cost bridge, Voiage financial decision
  consumer, offline conformance tests, and macOS arm64 / Python 3.15.2
  native oracle, vendor-test, PEP 740 / PGP attestation, advisory, cross-env
  parity, and P5 reconciliation runs are implemented
  (`verification/p1-native-qualification-2026-11-19.json`). **Voiage
  adjudication and broader release review remain open** (`dapane-cli`
  APFS non-UTF-8 test and `RUSTSEC-2026-0543` unmaintained `chrono` documented).
  The two corrected P5 regressions passed with the locked Dapane source build,
  and P0.5 raised the setuptools pin to 84.2.1.
  The corrected Rust 1.99.1 Dapane wheel passed P1/P5. The independent reviewer
  approved the wheels, binary pins and native counterfactual pricing and
  component conservation receipts for the tested macOS arm64, Ubuntu
  x86-64 and Windows Server x86-64 hosts. The Windows rebuild passed
  all 215 vendor tests directly from the upstream fixture fix.
  [P1.4 Windows rebuild](tracks/P1-provider-reuse/plan.md#windows-rebuild-after-the-upstream-fixture-fix)
- [~] **P2 — Clinical/economic model and CHHHS data specification**
  ([index](tracks/P2-clinical-economic-protocol/index.md),
   [spec](tracks/P2-clinical-economic-protocol/spec.md),
   [plan](tracks/P2-clinical-economic-protocol/plan.md)).
  P2.1–P2.4 clinical/cohort/economic contracts, synthetic outcome tests, and
  P2.5 preparation deliverables (`docs/p2-stakeholder-review-pack.md`, 32↔115
  CHHHS field crosswalk, fail-closed 7-gate sign-off template, and
  `verification/p2-governance-crosswalk-2026-11-19.json`) are implemented;
  **P2.5 site clinical/Nursing/Finance/HREC/First Nations approvals, real
  CHHHS data, safety thresholds, and P1/P7 provider provenance adjudication
  remain open**.
- [~] **P3 — Public evidence provenance and controlled data admission**
  ([index](tracks/P3-evidence-data-infrastructure/index.md),
   [spec](tracks/P3-evidence-data-infrastructure/spec.md),
   [plan](tracks/P3-evidence-data-infrastructure/plan.md)).
  Implemented portable source-value/denominator crosswalk, versioned synthetic
  feed manifests, SHA-256 and Pydantic schema admission, hospitalisation/ICU
  linkage, explicit missingness/censoring and aggregate report checks. Actual
  2024/25 PDF document re-verification, Searchright run, CHHHS local data and
  clinical/governance/Finance approval remain **blocked**. Source tests do not
  certify deployed or native-provider operation.
- [~] **P4 — Reconciled probabilistic cost-consequence model**
  ([index](tracks/P4-economic-decision-model/index.md),
   [spec](tracks/P4-economic-decision-model/spec.md),
   [plan](tracks/P4-economic-decision-model/plan.md)).
  Multi-strategy, correlated-uncertainty model, threshold and one-way
  analyses, resource/budget/capacity separation and P2/P3 source admission
  have source-level local tests. **Clinical validation, CHHHS data, exact
  publisher document admission and native Dapane/Voiage qualification remain
  blocked**. No experimental clinical or financial effect is admitted.
- [~] **P5 — Reproducible reporting and independent checks**
  ([index](tracks/P5-reporting-independent-review/index.md),
   [spec](tracks/P5-reporting-independent-review/spec.md),
   [plan](tracks/P5-reporting-independent-review/plan.md)).
  Deterministic cost-consequence, paired comparisons, sensitivity tables,
  Dapane nominal requests, Voiage-compatible draw surface, opt-in Voiage EVPI,
  report and SHA-256 file manifest have local source verification. The
  synthetic P5 report smoke test passed in hosted CPython 3.15.2 CI.
  **Independent clinical/economic review, provider artifact qualification
  and observed CHHHS validation remain open.**
- [~] **P6 — Optional Kairos time-aware capacity modelling**
  ([index](tracks/P6-kairos-capacity-validation/index.md),
   [spec](tracks/P6-kairos-capacity-validation/spec.md),
   [plan](tracks/P6-kairos-capacity-validation/plan.md)).
  P6.1/2 synthetic neutral event-trace, time-varying staffed-capacity
  conservation, paired-demand and CLI gates are implemented with NumPy/Pydantic.
  **P6.3 native Kairos consumer source and P6.4 synthetic holdout diagnostics
  added**; exact upstream API inspected and pinned. Rust binary/lock/hosted CI
  and approved CHHHS data, clinical/Finance governance remain **unverified**. No financial
  or empirical effect is inferred from synthetic trace differences.

- [~] **P7 — Technical, primary-source and empirical qualification closeout**
  ([index](tracks/P7-technical-empirical-qualification/index.md),
  [plan](tracks/P7-technical-empirical-qualification/plan.md)).
  Adds independent P3/P4 oracles, structured CHHHS data request and publisher
  2023/24 review. P7.5 records scoped approval of the Dapane artifacts and
  native execution receipts on three tested hosts. Broader Dapane
  qualification and release review, Voiage admission, the 2024/25 PDF,
  CHHHS empirical calibration and approvals remain open.
  Hosted integration evidence is tracked in the repository import record.
  [P7.5 Windows upstream rebuild decision](tracks/P7-technical-empirical-qualification/plan.md#windows-upstream-rebuild-decision)

- [~] **P8 — MCHS ABF, nursing workforce and valuation interoperability**
  ([index](tracks/P8-abf-workforce-interop/index.md),
  [plan](tracks/P8-abf-workforce-interop/plan.md)).
  Source-pinned provider capability register, funding/workforce/resource
  separation contract, ADR, negative tests, bounded synthetic MCHS paired-episode
  and workforce-to-Dapane quotation consumers are **source-level complete**.
  Official MCHS annual parity, nursing pay/roster qualification,
  native Dapane/Voiage, actual hospital revenue and CHHHS clinical/Finance
  approval are pending. Existing provider track ownership is retained.

- [~] **P7 companion: placeholder-assisted progress and evidence closure**
  ([index](tracks/P7-placeholder-assisted-qualification/index.md),
   [plan](tracks/P7-placeholder-assisted-qualification/plan.md)).
  The independent placeholder branch is preserved alongside the technical P7
  track. The 33-entry register, candidate checks and synthetic P3–P6 dry run
  are implemented. Knowing the repository address does not satisfy the
  separate release-review, native-provider or site-acceptance gates.

Status legend: `[~]` is in progress; `[x]` requires acceptance evidence;
`[!]` is blocked on a stated dependency. Both P7 directories retain their
historical phase identifiers; use the full track directory in handoffs.

- [~] **P9 - Clinical Director request and reporting contracts** ([index](tracks/P9-reporting-contracts/index.md), [plan](tracks/P9-reporting-contracts/plan.md)). Two request tables and source-level catalogues implemented; site-validated figures and independent review remain pending.

- [~] **P10 — Measurement, provenance, claim and visual assurance** ([index](tracks/P10-measurement-figure-assurance/index.md), [requirements](tracks/P10-measurement-figure-assurance/requirements.md), [plan](tracks/P10-measurement-figure-assurance/plan.md)). Source-only M01–M30/D01–D13 contracts, T/F links, uncertainty, visual and claim-admission checks; no site/governance or real visual validation.

- [x] **P11 — Scenario workflows and versioned runs** ([index](tracks/P11-scenario-workflows/index.md), [spec](tracks/P11-scenario-workflows/spec.md), [plan](tracks/P11-scenario-workflows/plan.md)). Synthetic A/B and stress scenarios, input/model/output identities and P9 figures passed local and integrated hosted checks; clinical and provider gates remain separate.
