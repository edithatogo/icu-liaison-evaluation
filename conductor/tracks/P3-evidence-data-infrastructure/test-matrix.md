# P3 verification matrix

Run `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_p3_public_evidence.py tests/test_p3_data_adapter.py tests/test_p3_cli.py` then `PYTHONPATH=src .venv/bin/python -m pytest -q` from a fresh unpacked checkout.

Required tests cover: source ID/denominator/value/page integrity; absence of a public 72-hour rate; no unverified-document promotion; first eligible index denominator; repeated ICU admissions; exact 12-hour/72-hour endpoints (via inherited P2 classifier); unknown readiness/censoring; competing death; time zone; source-hash tampering; unique episode and ledger identities; overlapping episodes; unknown columns; approved mapping; missing followup; malformed cost basis; restricted operator acknowledgement and nonpublic output; row-free reports; Pydantic-generated schema.

Positive tests are synthetic and prove local source/contract behaviour only. External PDF content SHA, independent document review, actual CHHHS data, contributor/CORE unit comparability and completed P1 provider-native tests require separate receipts and remain blocked.
