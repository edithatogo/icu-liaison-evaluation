# P7 specification

## Goal

Keep P3–P6 development, testing, reporting and evidence acquisition executable
without observed local data or a native Kairos/Dapane/Voiage environment.
Centralise the 33 unresolved evidence and integration dependencies into a
machine-checkable, fail-closed register with a named prospective source and
human-review acceptance criteria for each.

## Invariants

- Only synthetic and curated unverified public context in this portable source.
- No source-field, benchmark or native-provider promotion by a JSON status flag.
- P3 synthetic data are **not** fit or calibrated to P4 placeholder inputs.
- Never infer financing, clinical benefit or deployed capacity from a trace.
- Real evidence path is private; candidate SHA-256 confirms byte identity only.
- P5 report uses existing calculation and independent reader, not custom VOI.
- P6 capacity trace does not replace the Kairos scheduler.
- Never modify other active repository owners or exploratory PR #215.

## Explicit outputs

`model-inputs/placeholders/{registry.json,unresolved.json,p3-synthetic/}`;
`src/icu_liaison/placeholders.py` and CLI; source/candidate JSON Schemas;
`docs/placeholder-qualification.md` and ADR-0007; synthetic progress report
with full SHA-256 manifest, P5 report, P3 QA, P6 trace/holdout and a replacement
checklist; verified negative and replay tests.

## Non-goals

Installed native provider receipt, CHHHS patient-level ingestion, live ward or
ICU calibration, independent clinical approval, publishing a new repository,
claiming external validity, or merging PR #215.
