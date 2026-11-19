# P5 acceptance

- `.venv/bin/python -m pytest -q tests/test_p5_reporting.py`
- `.venv/bin/python -m pytest -q`
- `.venv/bin/python -m icu_liaison.p5_cli model-inputs/p4/illustrative.json --output-dir <new-output> --plots`
- Independent cross-check: P4 component algebra per draw; CSV resource/budget
  units; false readiness rejection; negative/censored clinical endpoints remain
  unmeasured; provider-failure no partial publication; no overwrite; altered
  digest failure; identical seeded outputs under the same exact environment.

These are *local source* checks. Independent clinical review, Dapane/Voiage
installed artifacts, real data/causal validation and hosted CI are open.

## Additional acceptance gates

- `tests/test_p5_provider_execution.py`: exact-decimal Dapane contract stub,
  real-provider-unavailable fail-closed, provider arithmetic disagreement,
  no implicit execution, CLI error without output.
- `tests/test_p5_semantic_review.py`: repeatable independent report reader;
  SHA-rehashed mean/probability tampering and false clinical readiness rejected.
- End-to-end command: `.venv/bin/python -m icu_liaison.p5_review_cli OUTPUT_DIR` must
  pass after the P5 report has been built. No provider or authenticity claim.
