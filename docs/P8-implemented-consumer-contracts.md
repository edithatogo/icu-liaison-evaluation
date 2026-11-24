# P8.2/P8.3 consumer increments — source acceptance and executable boundaries

The portable source was first implemented on 18 November 2026. The P8 plan
records the scoped provider replays and the evidence required for annual,
clinical and Finance acceptance.
[P8 plan](../conductor/tracks/P8-abf-workforce-interop/plan.md)

## MCHS annual paired-episode consumer

`src/icu_liaison/adapters/p8_mchs.py` validates one explicitly **synthetic**
2024/25 or 2025/26 acute-episode pair. It preserves the hospitalisation's
DRG, v11.0 coding edition, whole-stay LOS, ICU-other hours, same-day/private
flags and supported case-mix context. **Only `ICU_HOURS` can differ** between
the two annual-calculator calls. Each call invokes the existing
`nwau_py.calculators.acute.calculate_acute` with explicit year, `AcuteParams` and
reference directory. The facade requires the year-specific `NWAU24`/`NWAU25`
column, one returned episode and successful `Error_Code`. It never executes the
Excel economic/monetary calculator, copies a funding formula or multiplies NWAU
by NEP. The installed route checks the fixture's SHA-256 against the selected
directory's named, regular SAS tables before and after both calls. The output
retains the `source_bundle_sha256_declared` field for existing callers.

Output remains **unqualified**, even after installed execution, until the annual
MCHS price-weight and SAS/Excel parity evidence, precise bundle identity and
clinical input eligibility are independently checked. The 2026/27 equation
alone is insufficient to support its full annual calculator and is rejected.
Actual CHHHS hospital revenue remains `null` regardless of this output.

## Queensland nursing roster — workforce/Dapane consumer

`src/icu_liaison/adapters/p8_workforce.py` accepts explicit, timezone-aware
Queensland +10:00 roster segments. Each segment declares a named shift, source
quote ID, nonnegative decimal quantity, component, valuation date and evidence
type. The consumer rejects duplicate identities, same-component overlapping
segments, non-finite quantities and false completeness declarations. It does
**not** calculate paid hours, interpret enterprise agreements, choose staff
classification, stack allowances or annualise an example shift.

The optional installed route uses:

- `microcosting_healthworkforce.unit_quotes.QuoteQuantity`, and
- `microcosting_healthworkforce.dapane_adapter.build_dapane_request`.

It selects the pinned `workforce-dapane-quotes/1` artifact. The workforce library
checks source and quote applicability and builds the Dapane financial-cost
request. P8 matches the release jurisdiction and classification to the roster
and verifies the basis, currency, year, dates, units, exact quantities, cost
components and synthetic evidence labels. Dapane supplies any separate
valuation. The consumer transports analyst-specified quantities and leaves
annual costs open. The bundled roster contains an incomplete fictional example.

## Runnable checks

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p8_cli inspect-mchs model-inputs/p8/synthetic-mchs-pair.json
PYTHONPATH=src .venv/bin/python -m icu_liaison.p8_cli inspect-roster model-inputs/p8/synthetic-nursing-roster.json
PYTHONPATH=src .venv/bin/python -m icu_liaison.p8_cli reference-mchs /approved/MCHS/year-2025-reference
PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_p8_*.py
```

Record the reference command's digest in `source_bundle_sha256` in a copy of
the synthetic input bound to the reviewed tables. Use a qualified isolated
runtime for the installed-provider commands.

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p8_cli run-mchs \
  /approved/synthetic-episode-with-reference-sha.json --ref-dir /approved/MCHS/year-2025-reference
PYTHONPATH=src .venv/bin/python -m icu_liaison.p8_cli build-roster \
  /approved/synthetic-quote-bound-roster.json
```

The synthetic examples deliberately use placeholder source hashes, so they are
for **inspection** and injected tests; installed-provider work requires replacing
placeholders with independently source-qualified reference bundles and quotation
artifacts. Both installed commands return `UNVERIFIED` without their providers.
No patient records, credentials, personnel names, salary inputs or private
CHHHS evidence should be committed to any public source repository.

## Planned owner work and material blockers

1. **MCHS**: official-year SAS/Excel golden results for varied ICU hour thresholds,
   modelled age/eligibility and DRG exceptions; exact wheel/weight bundle hashes;
   a stable general paired-row interface if multiple consumers demonstrate demand.
2. **Workforce**: qualify Queensland nursing award/agreement and position/pay point,
   roster conditions, public holidays, cross-midnight rates and all oncosts;
   construct the complete source-pinned full-year quote artifact through the
   existing provider, then compare against authorised payroll/HR costing.
3. **Dapane**: independently installed-wheel execution and cost-component
   conservation, separate economic, financial and funding policy runs.
4. **CHHHS**: approved case-mix/DRG edition, admission/ICU hours/LOS, shift roster,
   staff classification, productive time, funding mechanism and external review.
5. **Repository**. The portable source and synthetic tests are hosted in this
   repository. Dated provider run receipts accompany the source checks.
   [P8 verification](../conductor/tracks/P8-abf-workforce-interop/test-matrix.md)
