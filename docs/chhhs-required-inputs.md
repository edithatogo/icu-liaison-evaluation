# CHHHS inputs required to replace the illustrative scenario

| Input | Required local source and completeness check | Can a public ANZICS report replace it? |
| --- | --- | --- |
| Eligible live adult ICU-to-ward discharges | ICU/Hospital movement join, discharge destination, agreed service catchment, eligibility | No |
| Clinical readiness-to-departure delays | APD readiness and actual transfer timestamps, date rules and cause codes | Pooled >=12h rate only, not local hours |
| Addressable delay fraction and covered cases | Prospective review of ward bed, staffing, transport, discharge planning, clinical stability | No |
| Early unplanned returns within 72 hours | Link all ICU episodes through same hospital stay, destination, planned status, timing | CCR/APD rates use different denominators |
| Readmission-specific incremental costs | Patient-level costs net of ordinary care and index ICU delays | No |
| Marginal ICU delay-day cost | ICU resource consumption, staffing/capacity response and incremental ward costs; financial/economic perspective | Average annual bed expenditure is not usable |
| Liaison workforce and operational cost | Fully loaded proposed rosters versus current coverage including relief and training | No |
| Clinical safety, ward burden, implementation | Ward arrests, deaths, MET timing, escalation appropriateness, treatment limitations, staff/patient feedback | Only broad context |
| Demand when ICU capacity released | Occupancy by time, refused/late admissions, cancellations, critical care staffing and transfer constraints | No |

Local inputs require an approved private route. Keep local extracts, patient identifiers,
workforce names and organisation-specific rates outside the portable/public archive.
Retain linkage hashes, data cutoff, completeness, currency, price year, and
counterfactual decision in private implementation receipts.

## 18 November 2026 structured request upgrade

For a complete owner/field/denominator specification, use
[`model-inputs/chhhs-data-request.json`](../model-inputs/chhhs-data-request.json)
and its generated [`CHHHS-first-stage-data-request.md`](CHHHS-first-stage-data-request.md).
Render a 115-row CSV and detailed Markdown with
`PYTHONPATH=src python tools/export_chhhs_data_request.py --output-dir <empty-private-or-working-dir>`.
Do **not** use a public repository or chat upload for actual patient-level extracts.
