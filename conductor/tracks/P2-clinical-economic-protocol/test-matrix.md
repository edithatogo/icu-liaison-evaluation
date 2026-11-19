# P2 checks and independent oracles

1. `PYTHONPATH=src python -m pytest -q tests/test_p2_protocol.py tests/test_p2_cli.py`:
   real source negative tests for denominators, time clocks, exclusion,
   safety, cost segments, budget and reference encounter timing.
2. `PYTHONPATH=src python -m pytest -q`:
   ensure P0/P1 and P2 coexist without regression.
3. `PYTHONPATH=src python -m icu_liaison.protocol_cli model-inputs/clinical-economic-protocol.json model-inputs/illustrative.json --data-dictionary model-inputs/clinical-data-dictionary.json`:
   JSON admission success for illustrative-only source, no clinical/budget claim.
4. Same command with `--require-local-ready`: must exit 2 with UNVERIFIED,
   never a false positive site-approved investment decision.
5. `PYTHONPATH=src python -m icu_liaison.cli model-inputs/illustrative.json`:
   P1 model remains usable and its existing deterministic input/output oracles
   pass unchanged.
6. `PYTHONPATH=src python -m pytest -q tests/test_p2_governance_pack.py`:
   validates 32/32 coverage of `model-inputs/clinical-data-dictionary.json`
   against `model-inputs/chhhs-data-request.json` and fail-closed rejection of
   tampered SHA-256 hashes, missing gates, or unapproved site-ready claims in
   `model-inputs/p2-governance-signoff-TEMPLATE.json`.

Do not confuse protocol metadata validation with actual clinical adjudication,
patient-level measurement, installed provider checks or study validity.
