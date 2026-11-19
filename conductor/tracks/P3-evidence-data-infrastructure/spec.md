# P3 — Evidence provenance and local data infrastructure

Authorised portable phase; user requested implementation on 18 November 2026. The dedicated GitHub repository has not yet been provided. P3 must NOT create or mutate a different project repository or merge CareOps Sim PR #215.

## Contract

1. Maintain separate machine-readable ANZICS metrics with source ID, denominator, age/region cohort, period, contributors, page, verification status and document-hash boundary. Do not infer a 72-hour unplanned return rate from public CCR/APD readmissions.
2. Reconcile source-register changes with the cited publisher material; an inaccessible newer report remains `previous_transcription_not_independently_reverified`, not new independent evidence. Re-use Searchright for future scientific search; no duplicate review engine.
3. Accept pseudonymous, fully timestamped local hospitalisation/ICU episode, follow-up, optional liaison and cost feeds via a source-mapped, SHA-256-pinned manifest with a timezone-aware extraction timestamp. Use Pydantic and Python standard CSV, not a new homegrown dataframe library.
4. Enforce unique identities, no overlaps, consistent timestamps, completeness with missingness preserved, 12h discharge delay, 72h unplanned readmission with censoring, and separate cost segments. Count one eligible index discharge per continuous hospitalisation.
5. Emit only aggregate counts/availability/status with provenance. Restricted input requires a separately approved governance reference, operator acknowledgement and a private output; source code alone establishes no patient consent, secure deployment, QI/HREC or Finance approval.
6. Keep all source/clinical/economic gates explicit in Conductor and verification receipts; no automatically approved local investment decision.

## Owners and scope

This track owns `public_evidence.py`, `local_data.py`, `p3_cli.py`, versioned P3 inputs and fixtures, corresponding tests, documentation, P3 track records and an append-only P3 migration/registry section. It does not own `careops-sim` runtime, Kairos, Dapane/Voiage provider internals, current CHHHS hospital systems, ANZICS databases, authentication or clinical care decisions.

## Evidence and limitations

Read [the P3 guide](../../../docs/p3-source-and-data-infrastructure.md) and the existing P2 protocol. Tests qualify source-code behaviour on invented records only. Native provider qualification, direct publisher PDF binary verification, data steward governance and deployed workflows remain outside this phase.
