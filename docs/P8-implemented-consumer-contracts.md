# P8.2/P8.3 consumer increments — source acceptance and executable boundaries

Date: 2026-11-18. **Portable source candidate only**, not a native-provider or
clinical-financial acceptance receipt. Neither the shared P4/P5 numerical engine
nor any upstream domain library was modified.

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
by NEP. Its reference SHA is a **caller-declared identity**, not proof that the
actual installed reference directory matches the SHA.

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

It selects an externally pinned **workforce-dapane-quotes/1 artifact SHA**,
not the unverified original wage source digest. The owning workforce library
handles source/quote applicability and builds the exact Dapane financial-cost
request. P8 checks the request's basis, currency, year, IDs, dates and cost
component preservation. **Dapane execution and monetary totals remain separate**;
no local payroll formula or substitute valuation calculation is implemented.
The bundled roster is an intentionally incomplete, synthetic test fixture with
no actual nursing award rates.

## Runnable checks

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p8_cli inspect-mchs model-inputs/p8/synthetic-mchs-pair.json
PYTHONPATH=src .venv/bin/python -m icu_liaison.p8_cli inspect-roster model-inputs/p8/synthetic-nursing-roster.json
PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_p8_*.py
```

Installed-provider calls, **only** in isolated compatible environments:

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p8_cli run-mchs \
  model-inputs/p8/synthetic-mchs-pair.json --ref-dir /approved/MCHS/year-2025-reference
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
5. **Repository**: the intended `edithatogo/icu-liaison-evaluation` repository is
   a **suggested name, not an existing or created remote**. The owner has not
   provided an established destination. Neither source nor tests have been
   pushed and no hosted CI/PR has been run.
