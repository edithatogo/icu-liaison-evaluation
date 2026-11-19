# Acceptance controls

| Gate | Executed or pending control | Admission limit |
| --- | --- | --- |
| P3 quality | `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_qualification_independent.py` | Aggregate descriptive uncertainty only; unknown retained |
| P4 oracle | Independent Decimal accounting over selected stochastic draws | Numeric calculation only, not a causal or cost-source validation |
| CHHHS fields | `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_data_request_pack.py` | Request schema, not a processed clinical extract |
| Existing Python | All test modules, partitioned P0–P4/P5/P6 | No inference about native binaries |
| Dapane, Voiage | `tools/qualify_providers.py --provider ...` | True native tests require installed reviewed distribution |
| Kairos | `tools/qualify_p6_native.py` | Requires Rust, reviewed Cargo.lock and exact source pin |
| ANZICS 2024/25 | Retain and independently inspect publisher PDF and SHA | Unverified until actual document admission |
| CHHHS readiness | Approved local extraction, calibration, independent safety, Finance, clinical and equity review | No check-box alone constitutes approval |
| Dedicated Git | Target repo, pinned dependencies, hosted tests/reviews and explicit privacy boundaries | Not yet supplied |
