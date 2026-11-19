# Evidence lifecycle and revocation contract

[evidence-lifecycle.json](evidence-lifecycle.json) lists national activity weights, Queensland nursing terms, ANZICS benchmarks and site governance as **unverified**. Missing dates or source digests remain null, not current or approved.

Run `python tools/evidence_lifecycle.py --as-of 2026-11-19 --price-year 2026` for a deterministic source-date assessment. Declared validity uses inclusive `valid_from` and *exclusive* `valid_until_exclusive`; revocation takes precedence. A missing MCHS pricing year is not assumed compatible.

Even a source whose metadata appears current remains `evidence_admitted=false`: the trusted independent verifier and revocation feed are future work. Do not place patient records or authenticating secrets in this public repository.
