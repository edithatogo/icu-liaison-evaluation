# P2 checks and independent oracles

1. `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_p2_protocol.py tests/test_p2_cli.py`:
   real source negative tests for denominators, time clocks, exclusion,
   safety, cost segments, budget and reference encounter timing.
2. `PYTHONPATH=src .venv/bin/python -m pytest -q`:
   ensure P0/P1 and P2 coexist without regression.
3. [Run the P2 review-pack audit](../../../docs/p2-stakeholder-review-pack.md#5-verify-the-review-pack):
   JSON admission for illustrative inputs, checked field coverage and
   seven pending decisions bound to the draft protocol and dictionary.
4. Same command with `--require-local-ready`: must exit 2 with UNVERIFIED,
   never a false positive site-approved investment decision.
5. `PYTHONPATH=src .venv/bin/python -m icu_liaison.cli model-inputs/illustrative.json`:
   P1 model remains usable and its existing deterministic input/output oracles
   pass unchanged.
6. `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_p2_governance_pack.py`:
   validates 32/32 coverage of `model-inputs/clinical-data-dictionary.json`
   against `model-inputs/chhhs-data-request.json` and fail-closed rejection of
   tampered hashes and missing gates. A fully populated fictional form with
   matching hashes still leaves site authority unverified.
7. Run `.venv/bin/python tools/validate_preregistration.py` and
   `.venv/bin/python tools/evaluate_safety_decision.py` to verify the draft
   analysis and the six safety outcomes against P2.

Do not confuse protocol metadata validation with actual clinical adjudication,
patient-level measurement, installed provider checks or study validity.
