# P3: Evidence provenance and protected ICU data-interface design

**Status:** portable source implementation, tested against synthetic fixtures only. There are **no approved CHHHS patient-level extracts**, no implemented live ANZICS CORE Portal adapter, no native Searchright run and no completed clinical, cost, privacy, Indigenous-governance or ethics approval in this portable source. A successful synthetic audit is not an approval to access or publish data.

## Public reference data and source status

- [ANZICS 2024/25 CCR report](https://www.anzics.org/public/311/files/PDFs/CORE/2024_2025-CCR-Activity-Report.pdf): the inherited P2 transcription gives **20.4%** of ward/home discharges delayed ≥12 hours, **18.4%** after hours and **4.5%** ICU/HDU return admission episodes. This publisher PDF could **not be independently accessed in the P3 18-Nov-2026 check**. `model-inputs/anzics-benchmarks.json` explicitly labels these results `previous_transcription_not_independently_reverified` and makes no new document-hash claim. They remain external, mixed-age and binational reference values, not Cairns estimates.
- [ANZICS 2023/24 CCR report](https://www.anzics.org/wp-content/uploads/2025/05/2023_24-CCR-Activity-Report-1.pdf): official publisher-hosted searchable text was independently checked for **19.8% exit block**, 154 contributing ICUs (printed p.17), and **18.8% after-hours discharge**, 164 ICUs (printed p.16). PDF-image screenshot retrieval failed, and no source-file SHA-256 has been admitted. This is a *publisher-text* check only, not binary/document review. The historical period and contributor sets differ from 2024/25.
- [ANZICS CORE 2024 Report](https://www.anzics.org/public/311/files/PDFs/CORE/2024-CORE-Report.pdf): the P2 adult patient readmission rate **4.0%**, covering 2023/24, is retained as a previously transcribed external observation. It is not a 72-hour unplanned return risk and is not interchangeable with the CCR 4.5% *episode* rate.
- [ANZICS APD](https://www.anzics.org/advocacy/core-icu-registries/registry-datasets/adult-patient-database/) publishes variable definitions and descriptions of the CORE Portal; **individual-unit data are returned to authorised contributors**, not as an unrestricted public patient-level download.

`conductor/evidence/source-register.json` is the human-readable source register; `model-inputs/anzics-benchmarks.json` is the machine-readable, offline benchmark crosswalk. The P3 validator requires matching reference IDs, amounts, units, page locations and numbers of contributors across both files. It never silently changes published rates into local parameters, accepts a 72-hour rate from CCR, or upgrades a transcription to verified publisher bytes.

A future document-level verification requires independently obtained copyright-compliant report bytes, a SHA-256 receipt, a substantive reviewer record, and explicit claims about what was read. **The source metadata alone never proves this.** Do not store unlicensed PDFs in a public repo.

## Existing providers: avoid duplicate components

- Use **Searchright** to acquire/deduplicate/screen scientific literature and export its native CSL-JSON/receipt formats. This project stores only a source-register *consumer* contract; it does **not** reimplement Searchright or claim a search run happened. When available, register a Searchright run ID, exact source commit, exported artefact hash, dates, search protocol, inclusion decisions and reviewer receipts in a separate approved ingest track.
- Use **Dapane** for exact resource valuation (unverified installed provider under P1). P3 checks cost-line identity, price year, currency and segment only; it does not value expenditures or call a provider in this phase.
- Use **Voiage** for decision uncertainty/VOI once economic inputs and installed provider are qualified; P3 imports do not directly trigger numerical model calibration.
- Use **Kairos** only for the later, optional temporal DES. A time-stamped ICU extract here does not establish a simulator or capacity benefit.
- Reuse **Pydantic** for structured validation, **Python's CSV and SHA-256 implementations** for bounded local parsing/integrity. No new data-processing, distribution, citation or numerical dependency was added.

## Controlled local-data import

The P3 intake is a *source gate*: it accepts a manifest referring to four CSV feeds. For the initial demonstration, only synthetic records appear under `tests/fixtures/p3_episodes/`. No direct patient identifiers, MRNs or names are accepted as headers. Pseudonym-looking tokens **cannot prove** a dataset is adequately de-identified; a verified local clinical data custodian must perform the actual pseudonymisation and governance assessment before creating a restricted manifest.

| Feed | Row grain | Canonical key fields | Scope |
| --- | --- | --- | --- |
| `episodes.csv` | ICU admission episode | `hospitalisation_pseudonym`, `index_icu_episode_id` | Admission/readiness/departure times, destination, adult age and planned-return status; all timestamps timezone-aware |
| `followup.csv` | Continuous hospitalisation | `hospitalisation_pseudonym` | Hospital separation/death/transfer, observed-until timestamp, censor reason |
| `liaison_contacts.csv` (optional) | Contact event | Hospitalisation plus ICU episode | Contact time and typed intervention; only identity/timing validation in P3 |
| `cost_lines.csv` (optional) | Distinct resource component/usage | Hospitalisation, ICU episode, ledger entry, use and component ID | Nonnegative quantities; mutually exclusive index vs return segments; AUD, price year and economic or financial basis |

The manifest is JSON with `schema_version=1`, `data_class=synthetic|restricted`, an offset-aware `extracted_at` timestamp, source reference, governance attestation, and a SHA-256 plus optional original-to-canonical `column_map` for every feed. A manifest cannot be dated before its latest observed ICU departure. The audit reports elapsed days since that episode without applying an invented freshness threshold. The column map permits adaptation to approved local extract headers **without hard-coding the source system into the model**. A feed must match exactly the expected canonical columns after mapping; unexpected patient-name fields fail rather than being silently retained.

The JSON Schema for the manifest and feed rows is generated directly from the Pydantic contracts (`p3_cli schema`), avoiding a separately maintained schema fork. This is a candidate interchange contract, not a promise that CHHHS' current systems export all necessary values.

### Synthetic commands

Run from the project root in an environment with the P0/P1 dependencies:

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p3_cli schema > /tmp/icu_p3_input_schemas.json
PYTHONPATH=src .venv/bin/python -m icu_liaison.p3_cli sources \
  --catalogue model-inputs/anzics-benchmarks.json \
  --source-register conductor/evidence/source-register.json
PYTHONPATH=src .venv/bin/python -m icu_liaison.p3_cli audit \
  --manifest tests/fixtures/p3_episodes/manifest.json \
  --dictionary model-inputs/clinical-data-dictionary.json
.venv/bin/python -m pytest -q
```

The synthetic result includes **aggregate** counts, per-field availability, censor categories, SHA-256 feed hashes and an explicit `investment_ready=false`. It does not emit pseudonyms, individual episodes, dates of patient events, line-item costs or individual clinical records. No estimate of local liaison treatment effect is generated.

### Restricted local execution (only after actual governance approval)

**Do not run this on patient data solely because the software supports it.** A designated CHHHS custodian must determine the approved purpose, privacy, secure runtime, audit trail, patient pseudonymisation, system access, cultural data governance and release requirements. `--acknowledge-approved-processing` is a local *attestation*, not a substitute for an approved decision. Keep the real manifest and CSVs in private controlled storage—not this repo.

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p3_cli audit \
  --manifest /secure/approved-input/manifest.json \
  --dictionary model-inputs/clinical-data-dictionary.json \
  --acknowledge-approved-processing \
  --private-output /secure/approved-output/qa-summary.json
```

The CLI requires a separate private output location, creates an aggregate output with mode 0600 (on platforms supporting it), does not print restricted counts, and refuses writing into source-controlled directories except explicitly ignored `.local/` or `private/`. This is a **defence in depth**, not a certified secure environment. No interactive upload, Git commit, third-party API call, automated extraction or publication is performed.

## Outcome and denominator integrity

A continuous hospitalisation may contain multiple ICU stays. P3 sorts every episode, rejects missing/duplicate keys and overlaps, and chooses the **first eligible live adult ward discharge per continuous hospitalisation** as the index. Additional ICU admissions remain in the same hospitalisation for readmission ascertainment, not as independent clinical index records.

- Exit block is **≥12 hours** from documented readiness to physical ICU departure. Missing readiness remains unknown and is excluded from the observed-readiness rate; report numerator, observed denominator and total eligible denominator separately.
- After-hours transfer is **18:00–05:59 Australia/Brisbane time** based on physical departure.
- Early return is an **unplanned return in [departure, departure+72h)**. Planned returns alone are not unplanned; unknown planned status or incomplete observation does not become a negative outcome. Death before an observed return is a competing event, not proof of no readmission.
- `first eligible index ward discharge` and `all live ward/home discharges` are **different denominators**, and APD adult *patients* vs CCR ICU/HDU *episodes* are **different measures**. P3 never labels a local index rate as an ANZICS CCR indicator.
- Cost lines may be checked for identity/segment conflicts, but their presence does not qualify provider prices, ward offsets, cash flow, staffing changes or capital opportunity costs. FTE and clinical safety outcomes are not present in the synthetic sample.

## Quality and research readiness

The 32-field P2 dictionary is carried into the output. It includes candidate operational, incident, staffing, costing and experience fields, some of which are not supported by the current four-feed pilot and remain explicitly not supplied. If a field is not in the P3 feed profile, it is explicitly `not_supplied_or_not_mapped`—never zero. The local 72-hour outcome is reported with true, observed-no-return and unknown categories; monthly completeness/case-mix/admission-severity/ward outcome completeness and prospective causal attribution require the controlled P4 design and source agreement.

The explicit remaining gates are:

1. External verification of the 2024/25 report (PDF/document bytes and, if licensing permits, evidence digest), plus source-backed revisions to benchmark values if necessary.
2. Approval of CHHHS extract ownership and source mapping, privacy/ethics/QI permissions, and local governance including relevant First Nations data-governance requirements.
3. Linkage/field completeness in actual APD and hospital systems, reconciliation to unit-level CORE Portal returns and local counts, and agreement on minimum quality thresholds and censoring methods.
4. New incident/MET, capacity, roster, ward workload, patient experience and costing feeds for the remaining P2 fields; clinical/Finance sign-off and independent validation.
5. Installed Dapane/Voiage provider gates (P1), full model revision (P4) and non-disclosive business-case publication (P5) before any investment recommendation.
