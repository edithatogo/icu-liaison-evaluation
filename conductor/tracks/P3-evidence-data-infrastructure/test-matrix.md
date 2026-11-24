# P3 verification matrix

Run `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_p3_public_evidence.py tests/test_p3_data_adapter.py tests/test_p3_cli.py` then `PYTHONPATH=src .venv/bin/python -m pytest -q` from a fresh unpacked checkout.

Required tests cover: source ID/denominator/value/page integrity; absence of a public 72-hour rate; no unverified-document promotion; first eligible index denominator; repeated ICU admissions; exact 12-hour/72-hour endpoints (via inherited P2 classifier); unknown readiness/censoring; competing death; time zone; source-hash tampering; unique episode and ledger identities; overlapping episodes; unknown columns; approved mapping; missing followup; malformed cost basis; restricted operator acknowledgement and nonpublic output; row-free reports; Pydantic-generated schema.

Check the tracked receipt with `p3_cli sources --publisher-receipt` and add
`--publisher-document` for the retained PDF. The tests cover mismatched
locators, incomplete coverage, an inconsistent document digest and a
self-declared admission. The local-intake tests also check that replacing
the manifest during an audit cannot change its data class or provenance.
Independent documentary review, actual CHHHS data and local comparability
require separate evidence.
