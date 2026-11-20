# P11 — Scenario workflows and versioned runs

## Objective

Make fictional scenario analyses repeatable and easy to compare as assumptions,
model code and reports evolve. Record which inputs, model, environment, seed
and output revision produced each result. Evaluate a thin Snakemake workflow
for repeated scenarios through observable rerun behaviour.

## Existing foundations

- P4 runs current_care and proposed strategies together using common baseline
  and resource draws. P5 exports paired differences, cost-consequence tables,
  sensitivities, a decision surface and a separately checked report.
- P10 exercises five fictional stress cases. They cover no intervention
  effect, harmful returns, zero addressable delay, zero usable capacity and
  zero cash realisability. Reuse their existing definitions and invariants.
- P5 already fingerprints the scenario, admitted evidence and output files.
  P10 supplies an F01 provenance reader. The six-figure P9 companion in
  [PR #26](https://github.com/edithatogo/icu-liaison-evaluation/pull/26)
  also records model, renderer and input hashes, subject to integration.
  Extend and consume these records where appropriate.
- Python and packages use the repository's pinned, qualified 3.15 runtime and
  constraints. Snakemake and its dependencies still require qualification in
  an isolated environment before adoption.

## Scenario comparisons

Provide a versioned synthetic scenario suite with a base scenario and the five
existing P10 stress cases. Each scenario records its stable name, description,
source scenario and changed assumptions. Use the validated P4 scenario schema
and existing model and reporting entry points.

A basic A/B analysis compares current care with ICU liaison within each model
run using P4's shared draws. Preserve the existing extended-cover arm when
included. Report each scenario's paired difference, uncertainty quantiles,
resource benefit, physical capacity and cash-budget measure with their units
and denominators. Retain null and adverse outcomes. These are fictional
parameter-sensitivity results with unmeasured clinical safety.

Scenario-to-scenario output must identify its scenario and seed. Only call a
cross-scenario difference paired when draw correspondence has been established
for the changed parameters and the method is documented. Reusing a seed alone
does not establish that correspondence.

## Inputs, model runs and output revisions

Create a versioned run record that is generated from the actual execution.
It must link the scenario definition and data snapshot identities, schema and
content digests, model source revision and executed code identity, Python and
relevant dependency identities, provider versions and execution status, seed,
draw count, output artefacts and their hashes, and the outcome of the
independent numerical and admission checks.

Define stable model-run identity from the effective model inputs, code and
runtime needed to reproduce the results. Preserve both the Git revision and
an accurate identity for executed source when the checkout is dirty, or refuse
a reproducibility claim if that identity cannot be captured. Store execution
attempts and timestamps separately from the model-run identity. Record
qualification status separately from file integrity.

A reporting or renderer change creates a distinct output revision linked to the
model run. Record each produced file's digest after production. Preserve
previous reports and human-reviewed or issued artefacts. Maintain atomic
publication and a retry/recovery path compatible with P5's refusal to
overwrite an existing report directory.

Keep restricted inputs, sensitive metadata and resulting artefacts in the
authorised private environment. The public portable workflow and its fixtures
remain synthetic. A checksum identifies bytes and does not establish their
authority or scientific validity.

## Snakemake pilot

Qualify a compatible Snakemake release and its complete dependency set on the
repository-local Python 3.15 patch in an isolated environment. Record actual
versions and resolve supported incompatibilities. Retain a concrete blocker if
qualification fails.

The pilot orchestrates existing scenario validation, P4/P5 execution,
independent numerical review, combined scenario summary and, when available,
the accepted P9 figure renderer. Declare the effective code, input,
configuration and environment dependencies that determine each result. Keep
the existing CLIs usable as direct entry points.

The pilot succeeds when the same completed target performs no analytical
rebuild on a second run, changing one scenario rebuilds only that scenario and
its downstream aggregate, and changing figure presentation reuses the existing
P5 model report while rebuilding affected figures. If P9 independently replays
model draws to validate figures, record that verification replay separately
from a P5 model-output rebuild. Preserve run records and prior outputs across
failures and retries.

Snakemake's documented rerun criteria include rule code, inputs, parameters
and software environments. Its optional shared between-workflow cache is
documented for public resources and is unsuitable for private data under the
documented sharing model. Use the existing qualified local environment and
private-data boundaries when designing execution.
[Snakemake execution documentation](https://snakemake.readthedocs.io/en/stable/executing/cli.html#cmdoption-rerun-triggers) ·
[Snakemake cache documentation](https://snakemake.readthedocs.io/en/stable/executing/caching.html)

## Acceptance and boundaries

Synthetic acceptance requires the scenario matrix, linked identities and
checksums, numerical parity with P4/P5, the three rerun experiments, recovery
and the repository's full local and hosted checks at the integrated revision.
Record evidence and unresolved issues in the track. This work does not itself
establish site data admission, causal effectiveness, clinical safety, funding
or investment approval. Those remain with their existing project owners.
