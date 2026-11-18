# P6 — Temporal ICU capacity: what the pilot can and cannot establish

The public ANZICS 2024/25 20.4% delayed-discharge figure is an aggregate pooled
**proxy** previously transcribed from a publisher report; the original PDF has
not been independently authenticated in this portable package. It is not a
Cairns-specific rate, delay-duration distribution, or patient event trace.

## Why a discrete-event analysis is optional

A one-day reduction in aggregate ICU occupancy need not correspond to a
continuously staffed bed available for another patient. A temporal analysis
requires admissions and readiness/departure times, staffed capacity by shift,
ward bed availability, transport/acceptance constraints and concurrent demand.
Clinical outcomes and readmissions need separate modelling and validation.

## Implemented P6.1/2: neutral synthetic trace audit

The input contract is `model-inputs/p6/synthetic-trace.json`. All IDs start
with `syn-`, all times are integer minutes from a fixed synthetic horizon, and
occupied intervals are half-open `[start, end)`. Staffed capacity must fully
cover the horizon; changes in available staffed beds are integrated at their
actual boundaries. Admission requests link to observed occupancy starts, and
same requests and arrival times are compared across strategies. A request can
be admitted, declined, or censored; an unknown outcome is not automatically
coded as no admission.

Run from the package root:

```sh
PYTHONPATH=src python -m icu_liaison.p6_cli model-inputs/p6/synthetic-trace.json
PYTHONPATH=src python -m pytest -q tests/test_p6_capacity_trace.py
```

The synthetic four-hour one-bed example produces 180 vs 150 occupied bed-
minutes and 60 vs 30 minutes of waiting for the same admitted request.
It **does not simulate the discharge change**: both alternative traces are
supplied by the fixture. The computed 30-minute occupancy difference is neither
a CHHHS throughput estimate nor a cash saving; the two arm traces are not an
annual P4 simulation, and no P4 bed-days should be scaled from them.

## P6.3/4 native and empirical entry gates

Before any temporal simulation claim, the independent owner must establish:

- Precisely pinned and tested Kairos native provider and real event export,
  including queue state, occupancy, handovers, scheduling order, preemption,
  stale event handling, deterministic seeds, and source/binary hashes.
- Approved CHHHS extract with consistent ICU episode grain, timestamps,
  actual staffed beds, ward acceptance constraints and patient-event linkage.
- Explicit intervention effects and clinical safety outcomes. Discharge
  delay is not automatically preventable, and early readmission can represent
  improved rescue rather than harm.
- Synthetic conservation/negative traces, observed holdout calibration,
  independently replayed native outputs, plus clinical/Finance research review.
- Demonstrated incremental decision value above the current P4 cohort model;
  do not build a duplicate scheduler merely to produce more elaborate plots.

These are presently **unverified**. The source contract permits inspection of a
future native producer output only after a separately reviewed adapter defines
its real upstream field mappings. The portable synthetic CLI does not accept
private operational data or pretend to run Kairos.
