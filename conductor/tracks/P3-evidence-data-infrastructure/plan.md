# P3 executable implementation and gates

## P3.1 — Public benchmarks and provenance
- [x] Record versioned ANZICS values, page, period, denominators and source-specific verification status without treating historical transcription as a newly reverified report.
- [x] Implement metadata/source-register integrity checks, incompatible denominators and no public 72-hour unplanned-return assumption.
- [ ] Admit actual publisher document digest with licensing/reviewer evidence; verify historical 2024/25 20.4% rate against independently accessible report bytes.

## P3.2 — Local source profiles and safe loading
- [x] Create canonical CSV and Pydantic-JSON-Schema contracts with editable source column mapping, extraction freshness and SHA-256-pinned feed manifests.
- [x] Implement fail-closed restricted processing gate with private aggregate output; synthetic fixtures are the only committed data.
- [ ] Verify actual CHHHS/ANZICS feed structure and privacy/ethics/cultural governance with custodians in an approved environment.

## P3.3 — Episode linkage and data quality
- [x] Select first eligible adult ward transfer per hospitalisation while retaining later ICU episodes, censor/competing-risk statuses and readiness missingness.
- [x] Reject duplicate/overlapping episodes, invalid/naive times, orphaned contacts/cost lines, incompatible resource segments and repeated use components.
- [x] Provide 32-field dictionary completeness/availability and non-overlapping local-vs-public denominators.
- [ ] Reconcile observed CHHHS data quality, case-mix, risk adjustment, full incident/outreach/workforce/cost feeds, temporal stability and source-level minimum completeness thresholds.

## P3.4 — Reproducibility and handoff
- [x] Write failing negative tests before implementation and test synthetic output, provenance, flags, privacy and source-schema publication.
- [x] Package the portable consumer and append-only Conductor source/migration receipt without overwriting earlier P0/P1/P2 evidence.
- [ ] Run installed native Dapane/Voiage and repository-hosted CI in the future dedicated repo; preserve unverified gates.

This source handoff does not authorise reading real CHHHS data or label any clinical or financial result empirically validated.
