# P5 acceptance

- `.venv/bin/python -m pytest -q tests/test_p5_reporting.py`
- `.venv/bin/python -m pytest -q`
- `.venv/bin/python -m icu_liaison.p5_cli model-inputs/p4/illustrative.json --output-dir <new-output> --plots`
- Independent cross-check: P4 component algebra per draw; CSV resource/budget
  units; false readiness rejection; negative/censored clinical endpoints remain
  unmeasured; provider-failure no partial publication; no overwrite; altered
  digest failure; identical seeded outputs under the same exact environment.

These commands verify local source behaviour. P1 records the admitted
provider artifacts and environments. P5.4 records the outstanding
independent review and site evidence.

## Additional acceptance gates

- `tests/test_p5_provider_execution.py`: exact-decimal Dapane contract stub,
  real-provider-unavailable fail-closed, provider arithmetic disagreement,
  no implicit execution, CLI error without output.
- `tests/test_p5_semantic_review.py`: repeatable independent report reader;
  SHA-rehashed mean/probability tampering and false clinical readiness rejected.
- End-to-end command: `.venv/bin/python -m icu_liaison.p5_review_cli OUTPUT_DIR` must
  pass after the P5 report has been built. No provider or authenticity claim.

## Standalone report verification on 24 November 2026

Seven regression cases failed before implementation and passed within the
136 focused tests on CPython 3.15.2. The cases cover fully fixed priors,
strategy order, conflicting cash and capacity rows and false source
admission. The standalone CLI rejected a rehashed conflicting cash table
with exit status 2. The fixed scenario's sensitivity CSV retained its header.

At seed `20261118`, two reports with `--plots` reproduced the previous
report byte for byte. The reader checked 5,000 decision draws across three
strategies. The rendered SVG had readable labels and complete marks.
The report manifest SHA-256 is
`e6a0d373cc7a2c7bd2455db68a18e3b68bb0dada69e0d2ca027d7257034a3066`.

## P5 review fixes on 24 November 2026

Six cases failed before the fixes and passed in the 142 focused tests on
CPython 3.15.2. The reader rejects a symlinked manifest. It also rejects
an unregistered attachment, a contradictory decision brief and an incorrect
sensitivity swing after their hashes are recomputed. The two Dapane cases
cover empty nominal ledgers with and without an injected provider.

The standard bundle with its SVG and the fully fixed bundle both reproduced
byte for byte. The standalone reader checked 5,000 draws across three
strategies. The P1 illustrative CLI output also matched the previous run.
