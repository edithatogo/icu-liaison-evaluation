# Track registry — independent ICU liaison economic evaluation

The exploratory `careops-sim` R78–R81 tracks are historical source context.
PR #215 was closed after the standalone migration. The exact exploratory head
is retained in the [migration comparison](../docs/pr215-migration-comparison.md).

The portable implementation and review fixes through P10 are integrated.
P11 has completed fictional acceptance. The track plans identify the
outstanding evidence and approvals.
[Repository reconciliation](tracks/P0-portable-consolidation/handoff.md#repository-reconciliation-on-25-november-2026)

- [~] **Track: P0 — Portable consolidation and Conductor handoff**
  ([index](tracks/P0-portable-consolidation/index.md),
   [spec](tracks/P0-portable-consolidation/spec.md),
   [plan](tracks/P0-portable-consolidation/plan.md)).
  Source, curated evidence, scenario and tested local adapters are preserved;
  the repository is now public with GitHub Secret Scanning + Push Protection
  enabled, hosted GitHub Actions CI passed on `main` (`1c7f640`, run
  `44444785989`), local CI/CD + `gitleaks` Git hooks (`pre-commit`,
  `pre-merge-commit`, `pre-push`) are active, the pinned Antigravity Conductor
  plugin exposes six workspace commands and passed an interactive read-only
  status check in Antigravity, isolated Python 3.15.2 native
  Dapane `0.1.0` / Voiage `3.1.0` numerical oracles passed, and the 19-file
  PR #215 comparison is recorded. P0.5 completed the CPython 3.15.2 migration
  with 342 tests passing in hosted CI and locally with Dapane installed.
  [Migration receipt](../verification/python-315-migration-2026-11-19.json)
  The repository owner approved the verified portable migration release on
  24 November 2026. Voiage's macOS artifact is admitted. Broader Dapane
  release review and CHHHS calibration remain open.
  [Portable source release](../docs/pr215-migration-comparison.md#portable-source-release)
- [~] **Track: P1 — Runtime provider reuse qualification**
  ([index](tracks/P1-provider-reuse/index.md),
   [spec](tracks/P1-provider-reuse/spec.md),
   [plan](tracks/P1-provider-reuse/plan.md)).
  Source lock, Dapane incremental cost bridge, Voiage financial decision
  consumer, offline conformance tests, and macOS arm64 / Python 3.15.2
  native oracle, vendor-test, PEP 740 / PGP attestation, advisory, cross-env
  parity, and P5 reconciliation runs are implemented
  (`verification/p1-native-qualification-2026-11-19.json`). The Voiage
  macOS arm64 wheel is admitted after signature and native checks.
  [P1.4 qualification](tracks/P1-provider-reuse/plan.md#voiage-macos-artifact-admission)
  The two corrected P5 regressions passed with the locked Dapane source build,
  and P0.5 raised the setuptools pin to 84.2.1.
  The corrected Rust 1.99.1 Dapane wheel passed P1/P5. The independent reviewer
  approved the wheels, binary pins and native counterfactual pricing and
  component conservation receipts for the tested macOS arm64, Ubuntu
  x86-64 and Windows Server x86-64 hosts. The Windows rebuild passed
  all 215 vendor tests directly from the upstream fixture fix.
  The separate Dapane release-assurance successor passed the APFS case and a
  clean locked dependency audit and awaits independent admission.
  [P1.4 Windows rebuild](tracks/P1-provider-reuse/plan.md#windows-rebuild-after-the-upstream-fixture-fix)
- [~] **Track: P2 — Clinical/economic model and CHHHS data specification**
  ([index](tracks/P2-clinical-economic-protocol/index.md),
   [spec](tracks/P2-clinical-economic-protocol/spec.md),
   [plan](tracks/P2-clinical-economic-protocol/plan.md)).
  P2.1–P2.4 clinical, cohort and economic source contracts are implemented.
  The P2.5 CLI audits the 32-field crosswalk and seven-role sign-off form
  against the draft. P2.6 safety and P2.7 preregistration contracts are
  implemented as drafts. **Site approvals, linked CHHHS data, safety
  adjudication and an approved analysis plan remain open.**
  [P2 stakeholder review pack](../docs/p2-stakeholder-review-pack.md)
- [~] **Track: P3 — Public evidence provenance and controlled data admission**
  ([index](tracks/P3-evidence-data-infrastructure/index.md),
   [spec](tracks/P3-evidence-data-infrastructure/spec.md),
   [plan](tracks/P3-evidence-data-infrastructure/plan.md)).
  Implemented portable source-value/denominator crosswalk, versioned synthetic
  feed manifests, SHA-256 and Pydantic schema admission, hospitalisation/ICU
  linkage, explicit missingness/censoring and aggregate report checks. The
  saved 2024/25 PDF and six page locators match the publisher receipt.
  The intake audit uses one manifest for privacy and provenance. Independent
  source admission, Searchright, CHHHS data and clinical, governance and
  Finance approval remain open.
- [~] **Track: P4 — Reconciled probabilistic cost-consequence model**
  ([index](tracks/P4-economic-decision-model/index.md),
   [spec](tracks/P4-economic-decision-model/spec.md),
   [plan](tracks/P4-economic-decision-model/plan.md)).
  Multi-strategy, correlated-uncertainty model, threshold and one-way
  analyses, resource/budget/capacity separation and P2/P3 source admission
  have source-level local tests. P4 and P5 reject mismatched benchmark periods
  and labelled local aggregates in fictional runs. Clinical validation,
  CHHHS data, independent publisher-source admission and broader provider
  qualification remain open.
  P1 records the admitted artifacts and their supported environments.
- [~] **Track: P5 — Reproducible reporting and independent checks**
  ([index](tracks/P5-reporting-independent-review/index.md),
   [spec](tracks/P5-reporting-independent-review/spec.md),
   [plan](tracks/P5-reporting-independent-review/plan.md)).
  Deterministic cost-consequence, paired comparisons, sensitivity tables,
  Dapane nominal requests, Voiage-compatible draw surface, opt-in Voiage EVPI,
  report and SHA-256 file manifest have local source verification. The
  standalone reader checks cost, paired and evidence records. Fully fixed
  scenarios produce a complete report with an empty sensitivity table. The
  synthetic P5 report smoke test passed in hosted CPython 3.15.2 CI.
  **Independent clinical/economic review, provider artifact qualification
  and observed CHHHS validation remain open.**
- [~] **Track: P6 — Optional Kairos time-aware capacity modelling**
  ([index](tracks/P6-kairos-capacity-validation/index.md),
   [spec](tracks/P6-kairos-capacity-validation/spec.md),
   [plan](tracks/P6-kairos-capacity-validation/plan.md)).
  P6.1/2 synthetic neutral event-trace, time-varying staffed-capacity
  conservation, paired-demand and CLI gates are implemented with NumPy/Pydantic.
  P6.3 passed the pinned local Rust build and two one-bed replays, including
  FIFO contention and horizon censoring. P6.4 includes synthetic holdout
  diagnostics. Independent build attestation, CHHHS
  calibration and clinical and Finance governance remain open.

- [~] **Track: P7 — Technical, primary-source and empirical qualification closeout**
  ([index](tracks/P7-technical-empirical-qualification/index.md),
  [plan](tracks/P7-technical-empirical-qualification/plan.md)).
  Adds independent P3/P4 oracles, structured CHHHS data request and publisher
  2023/24 review. The portable receipt verifies the 2024/25 document record,
  request pack and synthetic audit inputs. P7.5 records scoped approval of the
  Dapane artifacts and native execution receipts on three tested hosts and the
  exact Voiage macOS arm64 admission. Kairos build attestation, broader Dapane
  release review, independent admission of the retrieved 2024/25 PDF, CHHHS
  calibration and approvals remain open.
  Hosted integration evidence is tracked in the repository import record.
  [P7.5 Windows upstream rebuild decision](tracks/P7-technical-empirical-qualification/plan.md#windows-upstream-rebuild-decision)

- [~] **Track: P8 — MCHS ABF, nursing workforce and valuation interoperability**
  ([index](tracks/P8-abf-workforce-interop/index.md),
  [plan](tracks/P8-abf-workforce-interop/plan.md)).
  The fictional workflow verifies annual MCHS reference fingerprints, exact
  workforce quantities and Dapane valuation, and selected Voiage comparisons.
  Episode funding sensitivities stay separate from annual resource and budget
  draws. Full annual parity, nursing pay and roster admission, cost-prior
  reconciliation, actual hospital funding and CHHHS approval remain open.
  [P8 workflow receipt](../verification/p8-provider-workflow-2026-11-24.json)

- [~] **Track: P7 companion: placeholder-assisted progress and evidence closure**
  ([index](tracks/P7-placeholder-assisted-qualification/index.md),
   [plan](tracks/P7-placeholder-assisted-qualification/plan.md)).
  The independent placeholder branch is preserved alongside the technical P7
  track. The 33-entry register, private candidate checks and synthetic P3–P6
  dry run with complete bundle verification are implemented. The P7.4 plan
  records the publisher check, scoped provider decisions and hosted migration
  evidence. Independent admission, receiving review and site acceptance remain open.

Status legend: `[~]` is in progress; `[x]` requires acceptance evidence;
`[!]` is blocked on a stated dependency. Both P7 directories retain their
historical phase identifiers; use the full track directory in handoffs.

- [~] **Track: P9 - Clinical Director request and reporting contracts**
  ([index](tracks/P9-reporting-contracts/index.md), [plan](tracks/P9-reporting-contracts/plan.md)).
  Per-run coverage verifies four tables and 14 figures for each current
  synthetic scenario. Three tables and ten figures require admitted site or
  provider evidence.

- [~] **Track: P10 — Measurement, provenance, claim and visual assurance**
  ([index](tracks/P10-measurement-figure-assurance/index.md), [requirements](tracks/P10-measurement-figure-assurance/requirements.md), [plan](tracks/P10-measurement-figure-assurance/plan.md)).
  M01–M31 and D01–D14, verified fictional claim decisions by artifact, and
  source-linked figures with synthetic mark and visual checks. Trusted
  external evidence and independent acceptance remain open.

- [x] **Track: P11 — Scenario workflows and versioned runs** ([index](tracks/P11-scenario-workflows/index.md), [spec](tracks/P11-scenario-workflows/spec.md), [plan](tracks/P11-scenario-workflows/plan.md)). Synthetic A/B and stress scenarios, input/model/output identities and P9 figures passed local and integrated hosted checks; clinical and provider gates remain separate.
