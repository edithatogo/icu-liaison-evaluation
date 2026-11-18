# P1 verification matrix

| Check | Implemented | Current evidence |
| --- | --- | --- |
| Exact source ref and distribution version lock | Yes | GitHub source/tag inspected; lock checked in tests |
| Dapane nonnegative exact counterfactual resource construction | Yes | Local synthetic P1 tests |
| Additional ICU returns charged on intervention side | Yes | Local synthetic P1 tests |
| Provider method/policy/output rejection | Yes | Injected boundary test; no native acceptance |
| Independent fixed-input cost identity | Yes | Decimal synthetic oracle; expected -168730.00 AUD |
| Voiage financial-only 2-strategy layout and EVPI call | Yes | Injected boundary test; no native acceptance |
| Voiage native 2-state EVPI equals AUD 5 | Implemented | Cannot execute: provider/Python unavailable |
| Dapane native 2×50 and paired cost oracle | Implemented | Cannot execute: unpublished wheel unavailable |
| Exact wheel/native extension hashes | Pending | Lock marks as null; no artifact admission |
| Supported platform, dependency, security, licence receipts | Pending | Requires isolated installed-provider environment |
| Hosted integration and independent review | Pending | No dedicated repository supplied |

Execute local tests: `PYTHONPATH=src python -m pytest -q`.
Run fail-closed native checks: `PYTHONPATH=src python tools/qualify_providers.py
--provider all`. An `UNVERIFIED` result (exit 2) is a failed *native gate*,
not a failing portable test. Record these statuses separately.
