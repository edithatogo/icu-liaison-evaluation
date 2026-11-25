# P6.3 native consumer and P6.4 holdout checklist

On 26 November 2026, the scheduled update to Kairos `ddd0f4b` passed a fresh locked native build and both fictional reference replays. The earlier independent decision continues to identify its original artifact. [Current build and scope](../conductor/tracks/P6-kairos-capacity-validation/handoff.md#scheduled-kairos-update-ddd0f4b)

## Native provider

`native/kairos-icu-liaison` consumes the immutable Kairos
`kairo-ecs-des::StagedResourceRuntime` API. The provider's exact commit, API
and inspected Git blob SHAs are in
`model-inputs/p6/kairos-provider-lock.json`.

On 25 November 2026, Rust 1.100.0 built and tested the consumer at Kairos
`b60c422`. Repeated executions of both one-bed scenarios returned identical
bytes and matched their simultaneous-demand and queue references. The
committed Cargo.lock fixes all 30 packages, including five Kairos crates
at that exact revision, and retains the 24 reviewed registry checksums.
[Dependency check](../conductor/tracks/P6-kairos-capacity-validation/handoff.md#scheduled-kairos-update-b60c422)

To repeat the check, use a supported Rust toolchain and the committed lock.

```sh
cargo fetch --locked --manifest-path native/kairos-icu-liaison/Cargo.toml
PYTHONPATH=src .venv/bin/python tools/qualify_p6_native.py
```

The script checks the exact Git source for every resolved Kairos crate and the
Git blob IDs of three inspected files before running Cargo format, Clippy,
tests and build. It runs two fictional inputs twice each and compares their
actual output with the corresponding hand-authored reference. The receipt
binds the compiler, binary and lock hashes to the input, reference and output
digests. Set Cargo's `CARGO_TARGET_DIR` to an isolated absolute directory to
keep the build in a private workspace. The `icu-liaison-p6-native` CLI runs a
temporary copy of the binary it checks against the supplied SHA-256, using the
same input bytes it validated. It requires the integer fields used by the Rust
consumer and reports invalid locks or timed-out replay as unverified.
The independent build attestation applies to the exact retained
`b60c422` macOS arm64 executable and runner. CHHHS calibration and
clinical and Finance review remain open.
[Build decision](../conductor/tracks/P6-kairos-capacity-validation/handoff.md#independent-build-attestation-on-25-november-2026)

In the contention case, the earlier discharge frees the bed in time to admit
one more of the same three requests. Both alternatives still use 240 staffed
bed-minutes. The wait for the common admission falls from 60 to 30 minutes.
The report gives that paired wait difference separately from the disposition
counts.

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
`ks_2samp` to describe distances between the observed and predicted wait
distributions, alongside paired mean absolute and signed error. The KS
p-value field is `null` because the waits are paired by request and the
two-sample test assumes independent samples.
[SciPy KS documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ks_2samp.html)

The toy fixture evaluates **admitted** request waits only. Censoring, declined
admissions, shift capacity,
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
