# P5 source completion and P6 capacity-trace handoff

18 November 2026 — self-contained portable source and synthetic validation
only; no new GitHub destination or native clinical deployment.

## P5 scope added

The inherited P4 numerical and statistical model is **unchanged**. P5 now has:

1. Opt-in Dapane evaluation of its existing current/proposed nominal resource
   ledgers, with the provider (not this project) performing exact quotation
   arithmetic. Independently calculated P4 point-input net resource results
   must agree within two cents, accounting for separate ledger rounding.
2. Explicit fail-closed `--dapane` CLI behaviour on missing provider, invalid
   report or mathematical disagreement. When not selected, no Dapane provider
   is imported or claimed to have executed.
3. An independent output reader: P5 sums/quantiles and paired comparisons are
   recalculated from the exported draw table. Simple SHA256 manifest rehashing
   cannot conceal mismatched published numbers. This does not authenticate
   provenance; the manifest is unsigned.
4. Retained separate decisions for capacity, resource cost and hypothetical
   cash budget; no clinical effectiveness or safety assertion.

Reproducible commands from package root:

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p5_cli model-inputs/p4/illustrative.json \
  --output-dir path/to/new/report --plots
PYTHONPATH=src .venv/bin/python -m icu_liaison.p5_review_cli path/to/new/report
PYTHONPATH=src .venv/bin/python -m icu_liaison.p5_cli model-inputs/p4/illustrative.json \
  --output-dir path/to/new/with-dapane --dapane  # requires actual installed native Dapane
```

P5 native Dapane and Voiage installed-wheel/binary qualification, external
clinical/Finance review, CHHHS empirical calibration and hosted CI in the
future private repository remain open. A locally injected contract stub is
not a native qualification. The previously transcribed ANZICS 20.4% source
remains separately unauthenticated against publisher document bytes.

## P6 implementation — phases P6.1/2 only

`icu_liaison.p6_capacity` accepts versioned, synthetic-only already-generated
ICU occupancy and admission request traces, with staffed capacity varying
within the horizon. Its NumPy boundary sweep independently checks half-open
interval conservation, overcapacity, admissions linked to occupied beds,
paired demand and separate censored/declined requests. Its CLI reports only
aggregate source-verification-safe totals.

**This does not simulate patient movements or execute Kairos.** It reports
on supplied fictional alternatives. The output is **not numerically combined**
with the annual P4 cohort results. P6.3 native Kairos adapter and P6.4 site
calibration / independent acceptance remain blocked pending verified upstream
provider APIs and authorised local timelines, staff/ward capacities and
clinical safety evidence. No parallel scheduler or cost kernel was built.

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p6_cli model-inputs/p6/synthetic-trace.json
PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_p6_capacity_trace.py
```

## Reproducibility and ownership

- Full local Python suite: 175 passed, under current user environment.
- P4 engine SHA-256 preserved from the previous package:
  `ce63accb416f4c40e02b87b3be086c52b1dd038f70e0374f2e8a7a1a75ffb63b`.
- No changes made to the previously drafted public careops-sim PR #215.
- Imported local and public source data remain governed separately; no private
  CHHHS extracts, credentials, patient identifiers or original report PDFs
  are included in this portable bundle.
- Continue by creating the dedicated project repository and pinning/qualifying
  provider installation; do not mark P6.3/4 complete without native/clinical
  evidence.
