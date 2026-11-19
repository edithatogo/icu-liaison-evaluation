# P1 portable implementation handoff — 18 November 2026

Existing P0 package recovered from the prior portable archive. The original
ANZICS Library workbook remains outside this archive; the original CareOps Sim
PR #215 remains unmerged and is not modified in this source-only increment.

Changes:
- Portable P1 source-reference lock for Dapane `0658d94...` and Voiage
  release `v3.1.0`/commit `d40af027...`, with binary hashes unset.
- Dapane nominal incremental counterfactual bridge, exact Decimal quantities,
  return increase accounting, real-provider call and report admission.
- Voiage financial-only EVPI consumer and native two-state reference oracle.
- Version-gated explicit `qualify_providers` with JSON statuses, installed
  extension SHA observations and no silent fallback.
- Regression tests and a reproducible provider-environment setup guide.

**Open gates:** native Dapane/Voiage distributions are not available in the
local container; full P1 release acceptance cannot be claimed. Exact wheel
source provenance, installed native execution, other supported platforms and
independent source review remain pending. P0.4 and P1.5 are blocked until a
user-provided dedicated repository can receive the portable implementation.

Source labels from previous conversation material remain curated, rather than
raw private chat exports. Hospital observations are not introduced. Downstream
P2 clinical/economic specification should not be inferred as completed by P1.
