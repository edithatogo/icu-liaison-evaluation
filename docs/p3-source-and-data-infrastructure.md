# P3: Evidence provenance and protected ICU data-interface design

**Status:** portable source implementation, tested against synthetic fixtures only. There are **no approved CHHHS patient-level extracts**, no implemented live ANZICS CORE Portal adapter, no native Searchright run and no completed clinical, cost, privacy, Indigenous-governance or ethics approval in this portable source. A successful synthetic audit is not an approval to access or publish data.

## Public reference data and source status

- The retained 2024/25 ANZICS CCR report matched the recorded publisher
  digest and six page locators. The mixed-age binational reference values
  include **20.4%** of ward/home discharges delayed ≥12 hours, **18.4%**
  after hours and **4.5%** ICU/HDU return admission episodes. Independent
  admission for the intended use remains pending.
  [ANZICS 2024/25 report](https://www.anzics.org/public/311/files/PDFs/CORE/2024_2025-CCR-Activity-Report.pdf) ·
  [Publisher check](../verification/p7-anzics-2024-25-publisher-2026-11-24.json)
- The ANZICS 2023/24 text and rendered pages record **19.8% exit block**
  across 154 contributing ICUs on p. 17 and **18.8% after-hours discharge**
  across 164 ICUs on p. 16. The period and contributing sites differ from
  2024/25. The 2023/24 check has page evidence only.
  [ANZICS 2023/24 report](https://www.anzics.org/wp-content/uploads/2025/05/2023_24-CCR-Activity-Report-1.pdf) ·
  [Source register](../conductor/evidence/source-register.json)
- [ANZICS CORE 2024 Report](https://www.anzics.org/public/311/files/PDFs/CORE/2024-CORE-Report.pdf): the P2 adult patient readmission rate **4.0%**, covering 2023/24, is retained as a previously transcribed external observation. It is not a 72-hour unplanned return risk and is not interchangeable with the CCR 4.5% *episode* rate.
- [ANZICS APD](https://www.anzics.org/advocacy/core-icu-registries/registry-datasets/adult-patient-database/) publishes variable definitions and descriptions of the CORE Portal; **individual-unit data are returned to authorised contributors**, not as an unrestricted public patient-level download.

`conductor/evidence/source-register.json` is the source register.
`model-inputs/anzics-benchmarks.json` is the offline benchmark crosswalk.
The P3 validator checks the report edition and reporting period as well as
amounts, units, page locations and contributor counts. Source IDs must be
unique. The catalogue status tracks independent
document admission. The publisher check reports the receipt and saved
document separately.

To reconcile the recorded publisher check with the current source register,
run from the repository root:

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.p3_cli sources \
  --catalogue model-inputs/anzics-benchmarks.json \
  --source-register conductor/evidence/source-register.json \
  --publisher-receipt verification/p7-anzics-2024-25-publisher-2026-11-24.json
```

For an already retained local copy, add
`--publisher-document /secure/evidence/ANZICS-CCR-2024-25.pdf` to check
its size and SHA-256. The command runs offline, checks the receipt's own
SHA-256 against the source register and reconciles the recorded locators.
The original page checks are documented
in the receipt. Independent source admission still requires reviewer and
licensing evidence for the intended use. Keep publisher files in their
approved private location.

## Existing providers: avoid duplicate components

- Use **Searchright** to acquire/deduplicate/screen scientific literature and export its native CSL-JSON/receipt formats. This project stores only a source-register *consumer* contract; it does **not** reimplement Searchright or claim a search run happened. When available, register a Searchright run ID, exact source commit, exported artefact hash, dates, search protocol, inclusion decisions and reviewer receipts in a separate approved ingest track.
- Use **Dapane** for exact resource valuation and **Voiage** for decision
  uncertainty within their recorded platform scopes. The P3 audit checks
  cost-line identity, currency, price year and segment.
  [P1 provider evidence](../conductor/tracks/P1-provider-reuse/index.md)
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

The manifest is JSON with `schema_version=1`, `data_class=synthetic|restricted`, an offset-aware `extracted_at` timestamp, source reference, governance attestation, and a SHA-256 plus optional original-to-canonical `column_map` for every feed. The extraction time must cover the latest observed ICU departure, follow-up and recorded hospital separation. The audit reports elapsed days since the latest ICU departure. The column map permits adaptation to approved local extract headers. Feeds must match the expected canonical columns after mapping.

The audit reads the manifest once and uses those bytes for validation,
privacy checks and the reported manifest SHA-256. The CLI requires a new
private output path before opening restricted feeds.

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

The CLI writes the aggregate report with mode 0600 on platforms that support
it. Standard output contains a status message. For a destination inside a Git
checkout, use `.local/` or `private/` and confirm that Git ignores the
report path. The destination check also applies to the installed command.
The approved private runtime and disclosure controls remain the custodian's
responsibility.

## Public repository boundary

Keep source files from parallel repositories, SharePoint and OneDrive in their
approved private environments. Keep extracts, links, evidence receipts,
derived aggregate results and site-calibrated outputs there as well. The public
workflow uses fictional fixtures and admitted public references.

The commit and push checks read Git objects. They reject private working
directories, common export formats, restricted JSON, raw SharePoint exports
and tenant links. The CSV checks bind the existing fictional fixtures to their
exact bytes. The push check also inspects intermediate commits whose files
were subsequently removed. Hosted CI checks the public checkout with
path-redacted diagnostics. Keep these protections enabled and review any
fixture change for accidental disclosure before pushing.

## Outcome and denominator integrity

A continuous hospitalisation may contain multiple ICU stays. P3 sorts every episode, rejects missing/duplicate keys and overlaps, and chooses the **first eligible live adult ward discharge per continuous hospitalisation** as the index. Additional ICU admissions remain in the same hospitalisation for readmission ascertainment, not as independent clinical index records.

- Exit block is **≥12 hours** from documented readiness to physical ICU departure. Missing readiness remains unknown and is excluded from the observed-readiness rate; report numerator, observed denominator and total eligible denominator separately.
- After-hours transfer is **18:00–05:59 Australia/Brisbane time** based on physical departure.
- Early return is an **unplanned return in [departure, departure+72h)**. Planned returns alone are not unplanned; unknown planned status or incomplete observation does not become a negative outcome. Death before an observed return is a competing event, not proof of no readmission.
- `first eligible index ward discharge` and `all live ward/home discharges` are **different denominators**, and APD adult *patients* vs CCR ICU/HDU *episodes* are **different measures**. P3 never labels a local index rate as an ANZICS CCR indicator.
- Cost lines may be checked for identity/segment conflicts, but their presence does not qualify provider prices, ward offsets, cash flow, staffing changes or capital opportunity costs. FTE and clinical safety outcomes are not present in the synthetic sample.

## Quality and research readiness

The output includes all 32 P2 dictionary fields. Hospitalisation identifier
completeness comes from the hospital follow-up feed. ICU episode identifier
completeness comes from the episode feed. Unsupported fields are labelled
`not_supplied_or_not_mapped`. The local 72-hour outcome reports confirmed
unplanned returns, observed no return and unknown separately. Local
completeness, case mix, admission severity, ward outcomes and causal
attribution require source agreement and the controlled P4 design.

The explicit remaining gates are:

1. Independent admission of the retained 2024/25 report for the intended use, with reviewer and licensing evidence.
2. Approval of CHHHS extract ownership and source mapping, privacy/ethics/QI permissions, and local governance including relevant First Nations data-governance requirements.
3. Linkage/field completeness in actual APD and hospital systems, reconciliation to unit-level CORE Portal returns and local counts, and agreement on minimum quality thresholds and censoring methods.
4. New incident/MET, capacity, roster, ward workload, patient experience and costing feeds for the remaining P2 fields; clinical/Finance sign-off and independent validation.
5. Provider qualification for the intended runtime (P1), full model revision (P4) and disclosure-reviewed reporting (P5) before any investment recommendation.
