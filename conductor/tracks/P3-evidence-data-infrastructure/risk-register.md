# P3 material risks

- **Source drift/freshness:** newer 2024/25 CCR PDF was inaccessible in this session; inherited numbers are not independently admitted. 2023/24 searchable publisher text is not the same as verified binary/hash.
- **Denominator error:** CCR admission-episode, APD surviving-adult-patient and locally eligible first ward-discharge denominators are distinct. Unplanned 72h risk cannot be inferred from published all-return rates.
- **Hidden missingness and censoring:** readiness, treatment-goal status, return planning and hospital separation require source confirmation; planned returns, death and transfers must not be reclassified as zeros.
- **Patient confidentiality:** pseudonym-shaped IDs do not prove de-identification; filename and schema checks do not establish secure deployment, privacy approval or Indigenous data governance.
- **Data linkage and completeness:** local hospital episodes or wards may not share a unique continuous hospitalisation; cross-site transfers and overlapping episodes may require manual adjudication.
- **Cost duplication:** readmission resource use may overlap index discharge delay; average bed cost cannot be substituted for marginal cost; source snapshots need cost perspective/year.
- **Small cells and bias:** aggregate reporting may still disclose information if tiny clinical subgroups are exported. Use only approved private destinations and disclosure review; public reporting blocked until P5.
- **Upstream API status:** Searchright import and Dapane/Voiage providers remain independent consumers with required installed evidence; no automatic integration is implied.
