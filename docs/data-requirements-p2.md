# P2 source contract and local-data acquisition checklist

The machine-readable schema is [`clinical-data-dictionary.json`](../model-inputs/clinical-data-dictionary.json): 32 field requirements, each with grain, source class,
missingness policy and use. **There are no observations, local prices, names,
MRNs, or private data in the portable bundle.** Presence in the list does not
prove a hospital system exports it.

## Proposed owner and join contracts

| Candidate custodian | Link and grain | Key quality and access checks |
| --- | --- | --- |
| ICU APD/clinical registry manager | ICU admission episode, index discharge, clinical readiness, physical departure, case mix | Versioned extract, timestamp timezone, completeness trends, unique episode, accepted readiness definitions and local coding differences |
| Patient administration/ward movements | Same continuous hospital stay across ICU episodes and receiving wards | Stable pseudonymised hospitalisation ID, ordered admissions/returns, in-network/out-of-network transfers, separation/death follow-up and 72-hour eligibility |
| Clinical incident/MET and ward systems | Ward deterioration, escalation, arrest, documented severity and goals of care | Local event availability, incident under-reporting, ward denominator and appropriateness of coding |
| Liaison service manager | Rosters and per-contact activity | Distinguish current vs incremental hours, duplicate contacts, coverage by shift/site, types of support, cancellations, staff education and causal overlap |
| ICU and ward nursing/workforce | Staffed capacity, ward work and overtime | Shift-level time alignment, productive vs funded hours, award/on-costs, agency, backfill and changeable staffing |
| Costing and Finance | Resources and quotations for index delay, subsequent returns and new service | Price year, direct/marginal vs average allocations, economic vs cash basis, Dapane use/component identity, ward offsets and fixed-cost sensitivity |
| Consumer and patient experience | Approved follow-up experience measure and context | Validated instrument, timing, consent/quality permissions and sufficient subgroup reporting protections |

**Do not join at patient identity alone.** Link a pseudonymous hospitalisation,
ICU episode(s), movements, returns and events; the index denominator counts
a first eligible live ward discharge per continuous hospitalisation. Allow
subsequent ICU returns and full inpatient costs without counting them as
new independent index discharges for the primary clinical estimand.

## Data quality and negative controls

- Preserve missing readiness time as missing—not zero delay—and report the
  numerator/denominator with availability by period and ward.
- A transfer or death within 72 hours can truncate observed return surveillance;
  classify separately, with chosen competing-risk/censoring methods in a later
  statistical analysis rather than counting it as no unplanned return.
- Planned readmission is not an unplanned return, and *unknown planned status*
  is not a confirmed unplanned-free stay.
- Check readiness earlier than departure, monotonic time order across episodes,
  actual local timezone, repeated admission/ward-movement duplication,
  consistent diagnosis/severity risk adjustment and year changes in coding.
- Separately tag site access, cultural governance, incomplete remote follow-up
  and loss to observation; do not publish small-cell rural/Indigenous counts.
- Match finance lines to resource segments using unique use/component IDs;
  reject duplicated index-readmission pricing or double counting of opportunity
  costs with financial savings.
- A suitable *minimum completeness threshold* must be agreed and documented;
  this draft deliberately does not invent one.

## Required approval path

Local extract ownership, secure de-identification, data stewardship, ethics or
quality-improvement determination, Indigenous governance where applicable,
and Finance concurrence must be established separately. The P2 admission tool
contains **no** patient-file reader and cannot make private data public.
P3 will implement approved source adapters against this dictionary and report
actual field-level provenance and missingness. No dataset is promoted by a
successful synthetic-only test.
