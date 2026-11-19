# P6.3 source-level native consumer and P6.4 holdout checklist

## Native provider

`native/kairos-icu-liaison` consumes the immutable Kairos
`kairo-ecs-des::StagedResourceRuntime` API; **it has NOT been compiled** in this
portable execution environment. No clinical/Finance data are included. The
provider's exact commit, API and inspected Git blob SHAs are in
`model-inputs/p6/kairos-provider-lock.json`.

After the dedicated repository is supplied, use a separately authorised Rust
runner with the source lock and an independently reviewed Cargo.lock:

```sh
cd native/kairos-icu-liaison
cargo generate-lockfile            # one-time reviewed dependency resolution
cd ../..
PYTHONPATH=src .venv/bin/python tools/qualify_p6_native.py
```

The script executes actual Cargo format, Clippy, tests and build, performs
replay and source-pin checks, and compares the binary's output to an independent
one-bed fixture. A compiler-free test does **not** satisfy those gates. The
separate `icu-liaison-p6-native` CLI requires the actual binary and its
expected SHA-256; it never invents patient-flow events or silently substitutes
Python calculations when Rust is unavailable.

### Limits of the native scenario

The first consumer models a single staffed ICU bed, one existing patient, fixed
candidate discharge times, exogenous same-timestamp patient requests and
fixed subsequent lengths of occupancy. Cancellation, preemption, change of
staffed capacity, multiple wards, clinical readmission, nursing skill mix,
post-ICU deterioration, goals of care and economic costing are outside that
source-level proof. The `seed` is a declared stream identity only in the
fixed-input demonstration, not a claim of stochastic sampling.

The normalised NumPy audit independently checks exact half-open occupancy
and paired demand time. All comparisons remain `synthetic` and unpriced.

## P6.4 synthetic holdout diagnostics

`icu_liaison.p6_holdout` uses existing SciPy `wasserstein_distance` and
`ks_2samp` to quantify error on an independently identified synthetic holdout
cohort, with paired mean absolute and signed error. The toy fixture evaluates
**admitted** request waits only. Censoring, declined admissions, shift capacity,
acuity and sequential dependence need explicit alternative methods before any
clinical prediction claim. `gate_readiness` enumerates outstanding evidence;
self-declared Boolean values never grant independent approval.

## CHHHS inputs and governance outstanding

| Source | Required observed field | Key verification |
| --- | --- | --- |
| ICU/APD local export | Index episode, discharge-ready and physical departure times; 48/72h returns | Source version, completeness, episode-linkage and censoring |
| Patient flow/bed manager | Every request and acceptance timestamp, ward availability | Common demand counterfactual and plausible transfer constraint |
| ICU nursing | Staffed beds by minute/shift, changed roster and skill mix | Capacity reductions, staffing backfill and safety |
| Hospital data warehouse | Ward/ICU moves, MET, cardiac arrest, discharge/death | Avoid falsely labelling rescue as prevention |
| Clinical costing/Finance | Incremental resource components, avoidable cash components, price year | No readmission/index-bed double counting |
| Aboriginal and Torres Strait Islander governance | Appropriate permissions and care-context/equity review | Access, data sovereignty and acceptable reporting |
| Clinical & research governance | Protocol/SSA/quality-improvement classification and review | Clinical safety, rights and causality safeguards |

Hold out complete hospitalisations or time periods (not overlapping episodes)
when validating. Use appropriate count/censored-data metrics in addition to
Wasserstein/KS for time spent waiting. Compare current-care simulation with
observed occupancy/demand before inferring effect from any simulated liaison
change. P4 annual decision and P6 capacity outputs must remain separate unless
joint event conservation and cohort alignment are independently established.

## Public-source status

The previously curated ANZICS 2024/25 exit-block rate (20.4%) has **not been
reverified against authenticated publisher PDF bytes** in this P6 increment.
Earlier ANZICS 2023/24 CCR reporting confirms the 12-hour measure definition
but not the 2024/25 value. This study's base-case annual parameters remain
illustrative, not observed Cairns activity. Site data and ANZICS registry
secondary use require the appropriate approvals. See
https://www.anzics.org/advocacy/core-icu-registries/registry-impact/data-requests-and-research/
