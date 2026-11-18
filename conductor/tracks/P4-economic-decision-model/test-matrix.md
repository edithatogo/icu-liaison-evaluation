# P4 acceptance tests

- `python -m pytest -q tests/test_p4_economic_model.py tests/test_p4_cli.py tests/test_p4_dapane_bridge.py tests/test_p4_admission.py`
- `python -m icu_liaison.p4_cli model-inputs/p4/illustrative.json --one-way-strategy liaison_service`
- `python -m pytest -q` — all inherited P0–P3 + P4 tests.

Require reference accounting identities; multi-run same-seed parity; no effect;
negative effects; source-benchmark and protocol crosswalk; bounds, copula and
finite-result guards; distinct Voiage/Dapane semantics; no clinical or investment
claim. Installed providers and CHHHS empirical outcomes are distinct unrun gates.
