# P1 verification matrix

| Check | Implemented | Current evidence |
| --- | --- | --- |
| Exact source ref and distribution version lock | Yes | GitHub source/tag inspected; lock checked in tests |
| Dapane nonnegative exact counterfactual resource construction | Yes | Local synthetic P1 tests |
| Additional ICU returns charged on intervention side | Yes | Local synthetic P1 tests |
| Provider method/policy/output rejection | Yes | Injected boundary test; no native acceptance |
| Independent fixed-input cost identity | Yes | Decimal synthetic oracle; expected -168730.00 AUD |
| Voiage financial-only 2-strategy layout and EVPI call | Yes | Injected boundary test; no native acceptance |
| Voiage native 2-state EVPI equals AUD 5 | Yes (macOS arm64) | Passed `qualify_providers.py` (`5.0` & `887.91` AUD) in Python 3.15.2; provenance adjudication pending |
| Dapane native 2×50 and paired cost oracle | Yes (macOS arm64) | Passed `qualify_providers.py` (`100.00` & `-168730.00` AUD) and P5 `--dapane --voiage` |
| Exact wheel/native extension hashes | Observed (unadjudicated) | Recorded in `verification/p1-native-qualification-2026-11-19.json`; `providers.lock.json` `binary_sha256` kept `null` pending P7 review |
| Rebuilt Dapane wheel, pinned inputs and installed files | Verified locally (macOS arm64) | Source archive, locked SBOM, ZIP and `RECORD` checks passed. Installed files and retained Cargo output matched. The earlier wheel receipt records a different wheel digest and the same native extension digest. [P1.4 review](plan.md#rebuilt-dapane-wheel-evidence-review) |
| Rebuilt Dapane wheel admission | Sign-off withheld | The retained artifact used Homebrew Rust 1.100.0. Independent builds with the pinned Rust 1.99.1 differ. The binary hash remains null. [Technical P7.5 disposition](../P7-technical-empirical-qualification/plan.md#p75-independent-provider-review) |
| Supported platform, dependency, security, licence receipts | Partial (macOS arm64) | Dapane `54` core/`196` Py passed (`1` APFS `dapane-cli` non-UTF-8 fail, `RUSTSEC-2026-0543`); Voiage `13` core passed; Py 3.15 `pip-audit` 0 CVEs; Linux/Windows pending |
| Missing-native Dapane P5 branch tests on installed-provider hosts | Passed | Both corrected tests passed with Dapane 0.1.0 installed on macOS arm64 and CPython 3.15.2. The full suite passed 342 tests in that environment. [Migration receipt](../../../verification/python-315-migration-2026-11-19.json) |
| Hosted integration and independent review | Partial | Hosted CI green on `edithatogo/icu-liaison-evaluation`; external independent review remains open |

Execute local tests with `PYTHONPATH=src .venv/bin/python -m pytest -q`.
Run fail-closed native checks with
`PYTHONPATH=src private/venv-p1/bin/python tools/qualify_providers.py --provider all`.
An `UNVERIFIED` result (exit 2) is a failed *native gate*,
not a failing portable test. Record these statuses separately.
