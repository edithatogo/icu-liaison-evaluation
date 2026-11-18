# P0: Consolidate existing ICU liaison work into a portable independent project

Goal: preserve the information and decisions already developed without adding
another generic simulator, forcing a repository before its user-provided address,
or copying confidential data or copyrighted reports into public version control.

Inputs: exploratory CareOps Sim PR #215 (draft/unmerged), ANZICS publisher links,
Library workbook identified in `conductor/evidence/migration-manifest.json`,
user decisions in this conversation (curated non-verbatim), and inspected
Dapane/Voiage/Kairos/Power BI implementation contracts.

Outputs: source register, numerical JSON fixture with typed units/status,
consumer-first ADR, working local cohort PSA using maintained SciPy/NumPy,
strict optional provider interfaces, owner-scoped Conductor tasks, seed/hash and
independent local test evidence. Original material stays untouched.

Acceptance: source is reconciled into the user-selected private repository,
with a pinned Conductor gitlink and source/synthetic CI evidence. Installed
provider and Gemini runtime qualification retain their separate acceptance
requirements. Avoid unsupported financial, clinical or occupancy
claims and fail closed on invalid data or providers.
