# Gemini project context (extension runtime not yet qualified)

Upstream Gemini Conductor extension: `gemini-cli-extensions/conductor`,
reviewed commit `7a5c560a4fdf5297be58594cc37527eb12790272`, release 0.4.1.
It is registered as a pinned Git submodule at `extensions/conductor`.
Use `git submodule update --init -- extensions/conductor` to retrieve the
reviewed source, then verify `git submodule status`.
After reviewing the extension scripts/permissions in that checkout, a user may
explicitly install it into Gemini CLI with `gemini extensions install
./extensions/conductor`.

Read `AGENTS.md`, `conductor/index.md`, `conductor/tracks.md` and the active
track before changes. The repository includes P0–P8 source and synthetic
qualification work; local CHHHS calibration remains blocked on permissioned data.
The original CareOps Sim PR and existing third-party repos retain their owners.

## P3 source provenance and restricted-data boundary

Follow `conductor/tracks/P3-evidence-data-infrastructure/` before any data-file processing. Only the synthetic fixture is included. Do not import clinical/financial records without separately approved source governance; never write restricted reports to tracked directories. A source register entry or permission flag does not establish ANZICS document verification or CHHHS authority.


### ICU liaison P4/P5 follow-through

Treat `conductor/tracks/P4-economic-decision-model/` and
`conductor/tracks/P5-reporting-independent-review/` as source-only local
acceptance. Run full Python tests and a synthetic P5 CLI report. Do not
promote a previously transcribed ANZICS figure into a document-verified rate,
run model data on real patients in the public portable package, mark Dapane or
Voiage native qualification based on injected stubs, or infer clinical safety
from the monetary result. Authorised local-data sources and empirical acceptance remain missing. Preserve the exploratory careops-sim PR #215 pending
an exact reconciled migration.

## P6 native and clinical boundary

Reconcile P6 under its own Conductor track; preserve Kairos upstream
ownership and immutable source pin. Source-only tests and self-declared
binary hashes are not independent native or CHHHS clinical acceptance.

## P7 placeholder-assisted progress


Read `conductor/tracks/P7-placeholder-assisted-qualification/` and
`docs/placeholder-qualification.md`. P7.1–P7.3 are synthetic-source milestones;
P7.4 remains blocked on true source, native and site qualification. Do not
interpret 33 placeholder entries, candidate hash matching or P3 synthetic
fixtures as any authority to use observed data or conclude clinical/economic
benefit. Keep this work outside the exploratory CareOps Sim PR #215.
