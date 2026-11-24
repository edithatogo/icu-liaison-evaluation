# P2.5 CHHHS Stakeholder Review & Governance Sign-Off Pack

**Status:** Draft for CHHHS stakeholder review (`ready_for_local_claims: false`; zero real CHHHS records, staff identifiers, or site approvals exist in this repository).

This pack coordinates the external P2.5 clinical, workforce, Finance, ethics/data stewardship, and First Nations / consumer governance reviews required before local CHHHS extracts or empirical model claims can proceed.

## 1. Linked Source & Specification Artifacts

- Clinical/economic draft protocol: [`docs/protocol-p2.md`](protocol-p2.md) and [`model-inputs/clinical-economic-protocol.json`](../model-inputs/clinical-economic-protocol.json)
- Local data acquisition checklist & 32-field dictionary: [`docs/data-requirements-p2.md`](data-requirements-p2.md) and [`model-inputs/clinical-data-dictionary.json`](../model-inputs/clinical-data-dictionary.json)
- Authoritative 115-field CHHHS data request: [`docs/clinical-director-data-request.md`](clinical-director-data-request.md) and [`model-inputs/chhhs-data-request.json`](../model-inputs/chhhs-data-request.json)
- Machine-checked 32↔115 field crosswalk: [`model-inputs/p2-chhhs-field-crosswalk.json`](../model-inputs/p2-chhhs-field-crosswalk.json)
- Fail-closed governance sign-off template: [`model-inputs/p2-governance-signoff-TEMPLATE.json`](../model-inputs/p2-governance-signoff-TEMPLATE.json) (validated by [`src/icu_liaison/p2_governance.py`](../src/icu_liaison/p2_governance.py))
- [Draft causal preregistration and service fidelity](../contracts/clinical/preregistration.json) and [six-outcome safety decision contract](../contracts/clinical/safety-decision.json)

## 2. Seven-Role Governance Sign-Off Matrix (All Pending)

| Gate ID | Owner Role | Review & Decision Scope | Status |
| :--- | :--- | :--- | :---: |
| `icu_medical_clinical_director` | ICU Medical / Clinical Director | First-index live adult (`>=16y`) ward discharge denominator, clinical readiness definition, exclusion rules, and study design | `pending` |
| `icu_nursing_liaison_lead` | ICU Nursing / Liaison Service Lead | Observed baseline comparator, incremental liaison FTE, weekly coverage hours, roster model, and displaced work | `pending` |
| `ward_nursing_operations` | Receiving Ward Nursing & Patient Flow Operations | Receiving-ward bed/staffing constraints, handover workflow, ward workload metric, and deterioration escalation | `pending` |
| `finance_and_clinical_costing` | CHHHS Finance & Clinical Costing | 2026 price year, marginal ICU vs ward offset cost, nonoverlapping segments, workforce on-costs, and budget vs economic separation | `pending` |
| `clinical_governance_patient_safety` | Clinical Governance & Patient Safety Committee | Six mandatory balancing safety endpoints, prespecified noninferiority margins/stopping criteria, and minimum completeness threshold | `pending` |
| `hrec_and_data_stewardship` | HREC / Quality Activity & CHHHS Data Stewardship | Ethics vs QI pathway determination, pseudonymisation key custody, secure CHHHS environment boundary, and extract approval | `pending` |
| `first_nations_and_consumer_governance` | Aboriginal and Torres Strait Islander Health & Consumer Governance | First Nations data sovereignty, small-cell suppression rules, rural/remote equity stratification, and approved transition-experience reporting | `pending` |

## 3. Six Unresolved Protocol Parameters Requiring Formal Sign-Off

1. **`current_care_funded_fte`** (`strategies[0].funded_fte`): Actual funded and realised baseline ICU liaison/outreach FTE (must not be assumed zero).
2. **`liaison_service_funded_fte`** (`strategies[1].funded_fte`): Proposed incremental service establishment net of displaced existing work.
3. **`hours_of_coverage_per_week`** (`strategies[0..1].hours_of_coverage_per_week`): Verified baseline and proposed shift/weekend coverage hours.
4. **`approved_noninferiority_margins`** (`safety.approved_noninferiority_margins`): Prespecified clinical safety thresholds across `post_icu_death`, `ward_cardiac_arrest`, `delayed_escalation`, `return_severity_and_appropriateness`, `ward_workload`, and `treatment_limitations`.
5. **`minimum_data_completeness_approved`** (`design.minimum_data_completeness_approved`): Minimum readiness-timestamp and 72-hour follow-up completeness required before empirical calibration.
6. **`ethics_or_qi_pathway`** (`design.governance_status`): Formal HREC or approved quality-improvement determination and CHHHS data-stewardship authorisation.

## 4. Field-Alignment Cautions Surfaced by the 32↔115 Crosswalk

Reviewing [`model-inputs/p2-chhhs-field-crosswalk.json`](../model-inputs/p2-chhhs-field-crosswalk.json) across all 32 dictionary fields (9 exact matches, 23 renamed/derived/filtered/governed mappings) surfaced four critical local-definition checks for CHHHS custodians:

- **Receiving-ward staffed vs open beds (`ward_staffed_bed_count` -> `bed_capacity.ward_open_beds`):** Confirm with Patient Flow and Ward Workforce whether `ward_open_beds` reflects physically open beds or actively staffed beds by shift.
- **Ward workload units (`ward_workload_minutes` -> `clinical_safety.ward_workload_metric`):** Confirm whether local incident/nursing systems record workload in nursing minutes or a categorical acuity score.
- **Deterioration recognition vs escalation request (`deterioration_recognised_at` -> `clinical_safety.escalation_request_at`):** Verify whether `escalation_request_at` captures initial clinical recognition or only formal MET activation time.
- **Treatment limitation capture (`treatment_goals_at_discharge` -> `clinical_safety.treatment_limitation_status`):** Confirm treatment goals are captured at index ICU departure (`icu_episodes`) rather than only for patients who later trigger a safety event.

## 5. Verify the review pack

```sh
PYTHONPATH=src .venv/bin/python -m icu_liaison.protocol_cli \
  model-inputs/clinical-economic-protocol.json model-inputs/illustrative.json \
  --data-dictionary model-inputs/clinical-data-dictionary.json \
  --field-crosswalk model-inputs/p2-chhhs-field-crosswalk.json \
  --chhhs-request model-inputs/chhhs-data-request.json \
  --governance-signoff model-inputs/p2-governance-signoff-TEMPLATE.json
```

The audit checks all 32 dictionary mappings and binds the form to the exact
protocol and dictionary files. Numeric staffing, completeness and safety
values supplied in a form must be finite. The gate counts describe decisions
recorded in the form. A completed form that declares approval is reported as
`site_approval_declared_unverified`. The audit leaves
`site_authority_verified` and `ready_for_local_claims` false. Add
`--require-local-ready` to enforce this boundary with exit code 2.

The site decision requires verification of the signatories' authority and
approval scope, plus the approved linked data, staffing and costing inputs
and safety and analysis decisions. The P10 draft and safety checks can run
before these decisions are available.

## 6. Privacy & Repository Boundary

All patient-level extracts, direct identifiers, site rosters/payroll, and signed local governance records stay inside approved CHHHS infrastructure. Public repository files contain schemas, crosswalks, synthetic tests, and unapproved templates only.
