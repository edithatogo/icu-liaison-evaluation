# Agent ownership and safety map

This public repository owns the portable ICU liaison evaluation source.
Deployment and local evaluation require separate approvals. Preserve the
original sources, the separate workbook and the historical migration evidence
for [CareOps Sim PR #215](docs/pr215-migration-comparison.md#source-pr-disposition).

Use `conductor/index.md` then `conductor/tracks.md`; do not take over CareOps
Sim, Dapane, Voiage, Kairos, Searchright or CareOps Finance tasks. No private
patient episodes, hospital staff information, internal costing, credentials or
verbatim conversations enter public Git. Clinical intervention effects remain
uncertain assumptions until approved local evidence supports replacement.
Keep candidate data from parallel repositories, SharePoint or OneDrive in
their approved private storage. This applies to derived results, source links
and access receipts. Public Git and hosted CI use the fictional fixtures and
admitted public references.

Set up and verify the repository-local Python in [README](README.md#tested-basic-workflow).
Run `.venv/bin/python -m pytest -q` and
`.venv/bin/python -m icu_liaison.cli model-inputs/illustrative.json`. Retain
the Python version, seed and SHA-256. Static tests
on provider *adapters* do not prove installed-provider success. Work in scoped
branches for subsequent changes; avoid multi-owner path conflicts.

P1 adapter qualification: inspect `providers.lock.json` and
`conductor/tracks/P1-provider-reuse/` before changing provider code. Execute
`PYTHONPATH=src .venv/bin/python -m pytest -q`. This checks local contracts, not native
provider acceptance. Native checks are performed only with trusted, reviewed
provider installations from the [P1 guide](docs/providers-p1.md) using
`PYTHONPATH=src private/venv-p1/bin/python tools/qualify_providers.py --provider all`,
which must fail closed when either is unavailable. Do not
store protected CHHHS data in portable regression fixtures.

P3 source admission: `conductor/tracks/P3-evidence-data-infrastructure/index.md`. Preserve public versus local denominators and patient confidentiality. Run the P3 synthetic tests; no automatic real-data ingestion, source web fetch, provider native installation or deployment.


### ICU liaison P4/P5 follow-through

Treat `conductor/tracks/P4-economic-decision-model/` and
`conductor/tracks/P5-reporting-independent-review/` as source-only local
acceptance. Run full Python tests and a synthetic P5 CLI report. Do not
promote a previously transcribed ANZICS figure into a document-verified rate,
run model data on real patients in the public portable package, mark Dapane or
Voiage native qualification based on injected stubs, or infer clinical safety
from the monetary result. Authorised local-data sources and empirical
acceptance remain missing.

## P6 native and clinical boundary

The optional Rust consumer in `native/kairos-icu-liaison` has a checked local
one-bed replay. Record independent build attestation for the exact reviewed
artifact and runner. Keep site acceptance subject to its own evidence. Run
`tools/qualify_p6_native.py` only with an approved toolchain, reviewed lock
and exact upstream source. No direct patient records in public Git.

## P8 provider and funding separation

Use [P8 Conductor](conductor/tracks/P8-abf-workforce-interop/index.md) before
working on MCHS, nursing workforce, Dapane, Voiage or Kairos integration. The
portable source crosswalk is planning-only and tests forbid fabricated amounts;
never promote it to local evidence. Preserve exact upstream ownership and source
revisions. Nursing rates require actual nursing classification and HR/source
admission, not a health-practitioner HP3 example. MCHS NWAU calculations require
complete pricing-year/parity and episode inputs; modelled ABF is not realised
hospital funding.

## P7 placeholder-assisted development


Use `conductor/tracks/P7-placeholder-assisted-qualification/` and
`docs/placeholder-qualification.md`. The public registry intentionally keeps
33 unresolved evidence obligations. You may run P3–P6 synthetic dry runs but
must never close a site data, ANZICS document, native provider, Finance,
clinical safety, cultural-governance or repository release gate through a
self-declared status or a matching hash. Candidate evidence stays private and
requires independent adjudication. Keep P4's economic source unchanged.
