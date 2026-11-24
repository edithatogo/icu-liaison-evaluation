# P6 material risks and stopping rules

1. **False capacity claim:** freeing thirty occupied minutes does not create a
   staffed thirty-minute bed slot at an actual demand time without qualified
   event generation and resource/ward constraints.
2. **Paired inference:** two fixture traces with common requests are still not
   a causal intervention effect, nor a validation of staffing feasibility.
3. **Incomplete queue histories:** censored requests must not be counted as
   declined or silently removed from the denominator.
4. **Conservation:** interval overlap and changing staff availability must be
   tested at every event boundary; intervals are half-open.
5. **Privacy:** real patients/ward identifiers, cost quotations and source
   records must never enter synthetic-only public inputs or output receipts.
6. **Provider claims:** a neutral trace does not prove a Kairos run, approved
   dependency pin, clinical validation, or installed provider integration.
7. **Structural uncertainty:** readmission, escalation, ward flow, transport,
   rescue severity and goals of care are outside P6.1/P6.2.

Stop if any capacity, provenance, pairing or governance gate fails; do not
replace a refused case with assumed clinical effectiveness or cash value.

8. **Artifact scope:** independent attestation covers the reviewed
   `b60c422` macOS arm64 executable and runner. Other artifacts or runners
   need evidence for their own scope.
   [Build decision](handoff.md#independent-build-attestation-on-25-november-2026)
9. **Static single-bed model:** variable staffing, ward friction, clinical
   readmission and multi-bed competition are unsupported by the native source
   candidate and must never be inferred from neutral trace-validator features.
10. **Holdout selection:** synthetic admitted-only wait analyses omit censored
    patients and may be uninformative under high ICU strain; use reviewed
    patient-level censoring and case-mix methods for CHHHS.
