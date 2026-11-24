# Migration Comparison: CareOps Sim PR #215 vs `icu-liaison-evaluation`

- **Source PR** [CareOps Sim #215](https://github.com/edithatogo/careops-sim/pull/215), branch `feat/icu-liaison-anzics-economic-psa-20261117`, inspected head `e6caa16c5b87cbfadd2b10588ed10b7c6d60b637`.
- **Target repository:** `https://github.com/edithatogo/icu-liaison-evaluation`.
- **Scope** Exact 19-file provenance mapping and central accounting parity verification.

## Central Fixed-Input Numerical & Scientific Parity

Comparing `model-inputs/icu-liaison/illustrative.json` (PR #215) with [`model-inputs/illustrative.json`](../model-inputs/illustrative.json):

- **Top-level parameters:** `schema_version = 1`, `scenario_id = "public-anzics-plus-explicit-illustrative-assumptions-2026-11"`, `data_class = "synthetic"`, `seed = 20261117`, `iterations = 5000`, `annual_eligible_discharges = 1000` match identically.
- **All 9 parameter point values, triangular bounds, and provenance statuses** match identically (`delayed_discharge_ge12h_rate = 0.204`, `delayed_cases_addressable_fraction = 0.45`, `addressable_cases_improved_fraction = 0.5`, `hours_released_per_improved_case = 4`, `unplanned_72h_readmission_risk = 0.03`, `relative_readmission_reduction = 0.15`, `additional_cost_per_readmission_aud = 15000`, `net_avoidable_cost_per_icu_day_aud = 1800`, `annual_incremental_service_cost_aud = 250000`). Target extends the JSON schema with `annual_eligible_discharges_source` and typed `unit` fields.
- **Central deterministic accounting identity** (bounds collapsed to point `value`, `iterations = 1`):
  - Index ICU bed-days released: `1000 * 0.204 * 0.45 * 0.5 * 4 / 24 = 7.65` days
  - Unplanned 72h returns avoided: `1000 * 0.03 * 0.15 = 4.5` returns
  - Gross resource benefit: `7.65 * 1800 + 4.5 * 15000 = 81270.00` AUD
  - Net resource benefit: `81270 - 250000 = -168730.00` AUD
- **Deliberate algorithmic difference:** Hand-coded Rust triangular inverse-CDF (`kairo_ecs_rng::DeterministicStream`) and nearest-rank rounding quantiles in `crates/careops-core/src/icu_liaison.rs` were deliberately replaced with maintained `scipy.stats.triang.rvs` and `numpy.quantile` in [`src/icu_liaison/model.py`](../src/icu_liaison/model.py) (per `ADR-0001-consumer-first.md`). Exact seeded Monte Carlo trajectories differ across PRNG/quantile implementations, while the central deterministic identity holds exactly.

## Complete 19-File Reconciliation Table

| # | PR #215 File | Change | Disposition | Target Location(s) & Notes |
| :---: | :--- | :---: | :--- | :--- |
| 1 | `.careops-security/inventory.json` | Modified (+15/-0) | `careops_sim_repo_specific_not_carried_over` | CareOps Sim repo inventory; replaced here by [`SOURCE_MANIFEST.json`](../SOURCE_MANIFEST.json) & [`tools/verify_source_manifest.py`](../tools/verify_source_manifest.py). |
| 2 | `GEMINI.md` | Added (+20/-0) | `migrated_and_expanded` | [`GEMINI.md`](../GEMINI.md) (expanded for P0–P8 standalone context and Conductor pin). |
| 3 | `conductor/execution/tasks.json` | Modified (+503/-115) | `careops_sim_repo_specific_not_carried_over` | CareOps Sim shared task ledger; replaced by standalone [`conductor/tracks.md`](../conductor/tracks.md) and per-track plans. |
| 4 | `conductor/tracks.md` | Modified (+14/-0) | `migrated_and_expanded` | [`conductor/tracks.md`](../conductor/tracks.md) (expanded to P0–P8 + P7 placeholder tracks). |
| 5 | `conductor/tracks/icu_liaison_economic_psa_20261117/agent-contract.md` | Added (+21/-0) | `migrated_and_expanded` | [`conductor/tracks/P0-portable-consolidation/agent-contract.md`](../conductor/tracks/P0-portable-consolidation/agent-contract.md). |
| 6 | `conductor/tracks/icu_liaison_economic_psa_20261117/handoff.md` | Added (+28/-0) | `migrated_and_expanded` | [`conductor/tracks/P0-portable-consolidation/handoff.md`](../conductor/tracks/P0-portable-consolidation/handoff.md). |
| 7 | `conductor/tracks/icu_liaison_economic_psa_20261117/index.md` | Added (+11/-0) | `migrated_and_expanded` | [`conductor/tracks/P0-portable-consolidation/index.md`](../conductor/tracks/P0-portable-consolidation/index.md). |
| 8 | `conductor/tracks/icu_liaison_economic_psa_20261117/metadata.json` | Added (+27/-0) | `migrated_and_expanded` | [`conductor/tracks/P0-portable-consolidation/metadata.json`](../conductor/tracks/P0-portable-consolidation/metadata.json). |
| 9 | `conductor/tracks/icu_liaison_economic_psa_20261117/plan.md` | Added (+44/-0) | `migrated_and_expanded` | [`conductor/tracks/P0-portable-consolidation/plan.md`](../conductor/tracks/P0-portable-consolidation/plan.md). |
| 10 | `conductor/tracks/icu_liaison_economic_psa_20261117/risk-register.md` | Added (+24/-0) | `migrated_and_expanded` | [`conductor/tracks/P0-portable-consolidation/risk-register.md`](../conductor/tracks/P0-portable-consolidation/risk-register.md). |
| 11 | `conductor/tracks/icu_liaison_economic_psa_20261117/spec.md` | Added (+43/-0) | `migrated_and_expanded` | [`conductor/tracks/P0-portable-consolidation/spec.md`](../conductor/tracks/P0-portable-consolidation/spec.md). |
| 12 | `conductor/tracks/icu_liaison_economic_psa_20261117/test-matrix.md` | Added (+23/-0) | `migrated_and_expanded` | [`conductor/tracks/P0-portable-consolidation/test-matrix.md`](../conductor/tracks/P0-portable-consolidation/test-matrix.md). |
| 13 | `crates/careops-core/examples/icu_liaison.rs` | Added (+55/-0) | `deliberately_replaced_with_scipy_numpy` | [`src/icu_liaison/cli.py`](../src/icu_liaison/cli.py) (`icu-liaison-evaluate` CLI). |
| 14 | `crates/careops-core/src/icu_liaison.rs` | Added (+309/-0) | `deliberately_replaced_with_scipy_numpy` | [`src/icu_liaison/model.py`](../src/icu_liaison/model.py), [`src/icu_liaison/schemas.py`](../src/icu_liaison/schemas.py), [`tests/test_model.py`](../tests/test_model.py); extended in `p4_model.py` and Dapane/Voiage adapters. |
| 15 | `crates/careops-core/src/lib.rs` | Modified (+1/-0) | `careops_sim_repo_specific_not_carried_over` | Exported `pub mod icu_liaison;` in CareOps Sim crate; standalone Python package lives in [`src/icu_liaison/`](../src/icu_liaison/__init__.py). |
| 16 | `docs/icu-liaison/evidence-and-decisions.md` | Added (+71/-0) | `migrated_and_expanded` | [`conductor/evidence/source-register.json`](../conductor/evidence/source-register.json), [`conductor/decisions/ADR-0001-consumer-first.md`](../conductor/decisions/ADR-0001-consumer-first.md), [`docs/anzics-source-reconciliation-2026-11-18.md`](anzics-source-reconciliation-2026-11-18.md), [`README.md`](../README.md). |
| 17 | `model-inputs/icu-liaison/README.md` | Added (+60/-0) | `migrated_and_expanded` | [`README.md`](../README.md) and [`docs/anzics-source-reconciliation-2026-11-18.md`](anzics-source-reconciliation-2026-11-18.md). |
| 18 | `model-inputs/icu-liaison/illustrative.json` | Added (+82/-0) | `migrated_and_expanded` | [`model-inputs/illustrative.json`](../model-inputs/illustrative.json) (all 9 values/bounds/seed preserved; units & cohort source note added). |
| 19 | `tools/install_gemini_conductor.sh` | Added (+18/-0) | `migrated_and_expanded` | [`tools/prepare_conductor_submodule.sh`](../tools/prepare_conductor_submodule.sh), [`.gitmodules`](../.gitmodules), and `extensions/conductor` submodule pinned at `7a5c560a4fdf5297be58594cc37527eb12790272`. |

## Source PR disposition

GitHub shows CareOps Sim PR #215 closed on 19 November 2026 at 14:04 AEST,
with its exploratory head preserved as an unmerged source revision. The
closure cites standalone PR #5, merge commit `1ff7ca460ac135a3cd545701d22ddf82d2d97d90`
and its passing hosted checks.
[CareOps Sim PR #215](https://github.com/edithatogo/careops-sim/pull/215) ·
[Standalone PR #5](https://github.com/edithatogo/icu-liaison-evaluation/pull/5) ·
[Hosted run](https://github.com/edithatogo/icu-liaison-evaluation/actions/runs/44455595345)

## Portable source release

The repository owner approved release of the tested standalone PR #5 migration
on 24 November 2026. The preserved PR #215 source revision remains the basis
for the comparison. P0.4, P1.5 and both P7 plans record the decision.
Provider acceptance remains tracked separately in P1.4 and P7.5.
