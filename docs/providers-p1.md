# P1: installed-provider qualification and dependency reuse

**Source candidate only — the executing environment used for this package was
Python 3.13.5, with no Rust toolchain or network access. Native Dapane and Voiage
could not be installed, so no native acceptance is claimed.**

## Provider identity

`providers.lock.json` holds the reviewed public source references:

- **Dapane 0.1.0**: Git commit
  `0658d94ad772023a0185a000b5254f9c2f4a63a9`;
  JSON contract `0.1` and method `dapane-exact-v0.1.0`.
  Dapane is unpublished; build its native wheel from the exact reviewed revision.
  A source commit is not a native wheel checksum.
- **Voiage 3.1.0**: annotated tag `v3.1.0` points to release commit
  `d40af0276019a7d63657349b53dad96845e2b4c1`.
  This release requires Python `>=3.15.2,<3.16` for its published package.

The lock does not pretend to freeze all transitive dependencies. Qualifying
operators must record exact wheel hashes, native extension hashes, distribution
RECORDs, dependency versions and platform/ABI on the selected supported host.
The current null `binary_sha256` values explicitly represent *missing* evidence.

## Source-dependent runtime setup (on a network-enabled authorised workstation)

Create a separate project environment, retaining existing provider environments:

```sh
uv python install 3.15.2
uv venv --python 3.15.2 .venv-icu-providers
PROVIDER_PYTHON="$PWD/.venv-icu-providers/bin/python"
uv pip install --python "$PROVIDER_PYTHON" -e '.[test,voiage]' 'maturin==1.16.0'
```

Keep the absolute `PROVIDER_PYTHON` path when leaving the evaluation project
directory. Do not silently change to an older interpreter or Voiage version.

Build Dapane in an **independent inspected clone** checked out at the lock's
full source SHA, using its own `docs/quickstart.md` and `Cargo.lock`:

```sh
git clone https://github.com/edithatogo/dapane.git ../dapane-p1-provider
cd ../dapane-p1-provider
git checkout --detach 0658d94ad772023a0185a000b5254f9c2f4a63a9
# Verify git rev-parse HEAD and the source manifests before running the build.
# Use Rust 1.99.1 and maturin 1.16.0 with the selected CPython 3.15.2.
"$PROVIDER_PYTHON" -m maturin build --locked --release \
  --interpreter "$PROVIDER_PYTHON" --out dist
```

Paths above are illustrative: invoke the actual trusted interpreter and
maturin installation from your controlled environment. Install the resulting
reviewed Dapane wheel with
`uv pip install --python "$PROVIDER_PYTHON" --no-deps <reviewed-wheel.whl>`.
Record the wheel SHA-256 **before installation** and compare its installed
native module digest with the build receipt. Do not insert an unverified binary
hash into the source lock or accept a mutable branch HEAD as the provider pin.

Then run from the portable evaluation project:

```sh
"$PROVIDER_PYTHON" -m pytest -q
"$PROVIDER_PYTHON" tools/qualify_providers.py --provider all
```

A native smoke that passes returns `NATIVE_ORACLES_PASSED_ARTIFACT_PROVENANCE_PENDING`
with observed interpreter/distribution and extension digest evidence. This is
**not final release admission**; a separate signed/immutable artifact build,
source trace, license/dependency scan and independent review remain mandatory.

## Exactly what the two adapters do

### Dapane counterfactual pair

`make_nominal_cost_bridge(scenario)` produces two Dapane `0.1` requests:
`current_care` contains the *addressable slice* of index ICU delay and returns
that liaison is assumed to avoid. `liaison_service` contains the incremental
annual staffing cost and any *additional* early returns arising from better
surveillance. Both requests are nonnegative and share one economic basis,
currency, price year and perspective. The cost difference is:

    net resource benefit = valued avoidable current-care slice - valued added liaison slice

These are **not full health service costs** and do not establish that any ICU
resources would be cash-releasable. When local evidence becomes available,
construct complete, mutually exclusive resource ledgers instead. Dapane accepts
explicit quantities/quotes; it does not infer clinical use or treatment effect.

`compare_valued_scenarios` calls the genuine installed Dapane provider by
default and rejects a mismatched output envelope. Injected providers in unit
tests are clearly marked `injected_contract_test_only` and do not qualify
Dapane. Price-year and basis sensitivity remain under the project policy.

### Voiage decision surface

`evaluate_financial_information(draws)` hands the existing 2-column financial
array to Voiage `DecisionAnalysis` for EVPI. Rows are parameter-uncertainty
samples; one row describes an annual CHHHS-scale programme decision under the
illustrative cohort assumptions. The source library, not this project, owns
the EVPI calculation. This is **not a patient-level, health-utility, or
population-scaled value of information**. Full EVSI/ENBS requires an explicit
study design and is reserved for P4.

## Real provider oracles

The native qualifier executes: Dapane `2 staff minutes × A$50 = A$100`,
then the fixed nominal two-ledger resource difference `−A$168,730`;
Voiage two equally likely states, net benefit alternative `+A$10` or `−A$10`,
with current care zero in both, must yield EVPI `A$5`.

These are *synthetic independent numerical references*, not effect estimates.
The script exits with code **2 / `UNVERIFIED`** for missing, incompatible,
failed oracles or missing runtime. The executing host must record its actual
result as a separate immutable verification receipt; never re-label an
injected-provider test as installed acceptance.

## Initial macOS arm64 / Python 3.15.2 qualification checkpoint (19 November 2026)

On `macOS-27.2.1-arm64` with CPython `3.15.2` in an external isolated
environment, `tools/qualify_providers.py --provider all` returned
`NATIVE_ORACLES_PASSED_ARTIFACT_PROVENANCE_PENDING` for source-built
`dapane==0.1.0` (`0658d94ad772023a0185a000b5254f9c2f4a63a9`) and PyPI
`voiage==3.1.0` (`v3.1.0`). Observed wheel/extension/RECORD digests, vendor
tests, PyPI PEP 740 + GitHub PGP attestations, `cargo deny`/`pip-audit`
findings, cross-environment `3.13.18` vs `3.15.2` CLI byte-parity, and P5
`--dapane --voiage` reconciliation are recorded in
`verification/p1-native-qualification-2026-11-19.json` and
`verification/p0-py315-native-lock-2026-11-19.txt`. Independent P7 adjudication
of `providers.lock.json` (`binary_sha256` kept `null`) and Linux/Windows
platform qualification remain open.

## Provider-presence-independent P5 negative tests

The historical 19 November Python 3.15 receipt documented two failing P5 tests
because they implicitly assumed Dapane was not installed. The tests now simulate
unavailability explicitly in their own process/subprocess, so CI can exercise
the fail-closed refusal both with and without a provider on the host. This
source-level test repair does not modify the P5 production valuation adapter or
change the historical receipt. Re-run the complete Python 3.15 native matrix
before qualifying that platform as fully accepted.
