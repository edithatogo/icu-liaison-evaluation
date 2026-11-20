# P11 — Implementation plan

The P9 companion, local workflow and recovery checks, and hosted checks for the
integrated synthetic source revision have passed. Separate empirical and native
qualification gates remain in their existing tracks.

## P11.1 — Reuse and qualification

- [x] P11.01 Map the existing P4 paired A/B calculation, P5 bundles and
      independent reader, P10 stress cases and available P9 figure workflow.
      Identify the authoritative inputs and every output dependency.
- [x] P11.02 Qualify the chosen Snakemake release and dependency set with the
      repository-local Python 3.15 patch in an isolated environment. Record
      the exact versions and any compatibility blockers.
- [x] P11.03 Establish focused synthetic regression checks for the scenario
      matrix, run records and invalidation behaviour before changing execution.

## P11.2 — Scenario suite

- [x] P11.04 Define a versioned, discoverable set containing the base case and
      the five existing P10 stress cases. Record each changed assumption, the
      source scenario and its data classification.
- [x] P11.05 Run current care and ICU liaison together through P4 for each
      scenario. Preserve the extended-cover arm where present and keep the
      existing common-draw and P5 numerical-review semantics.
- [x] P11.06 Produce a scenario comparison with paired within-run differences,
      uncertainty quantiles, resource values, capacity and cash-budget
      measures. Carry seed, units, denominators and synthetic safety status.
- [x] P11.07 Verify no-effect, harmful-return, no-addressable-delay,
      no-usable-capacity and no-cash-realisability outcomes against the
      existing P10 invariants and P5 paired-draw calculations. Reject an
      unsupported claim of cross-scenario pairing.

## P11.3 — Versioned inputs, model and outputs

- [x] P11.08 Extend the existing provenance records with stable model-run
      identity derived from effective input snapshots, code and runtime,
      provider status, configuration, seed and draw count. Record source
      revisions and accurately account for dirty source.
- [x] P11.09 Link each generated report and figure revision to the model run,
      its renderer or reporting source and the actual output file hashes.
      Keep attempt timestamps and review status separate from run identity.
- [x] P11.10 Test identity stability, changed-input and changed-code
      invalidation, missing or modified artefacts, and rejection of
      unauthorised or invented qualification claims. Preserve previously
      generated files and support safe retries after interrupted publication.

## P11.4 — Snakemake pilot

- [x] P11.11 Wrap the existing synthetic validation, model, reporting,
      independent review and scenario-summary entry points with declared
      dependencies. Include figure rendering when the P9 companion is
      integrated. Preserve direct CLI use and the existing P5 output contract.
- [x] P11.12 Verify an unchanged second run does no analytical rebuild.
      Change one scenario and verify only its model/report and downstream
      aggregate rebuild. Change only the figure renderer and verify the P5
      bundle is reused and affected figures rebuild.
- [x] P11.13 Exercise serial and parallel synthetic execution and a
      deliberately interrupted run. Show that retries and concurrent targets
      preserve atomic publication, existing outputs and complete run records.

## P11.5 — Handoff

- [x] P11.14 Run the relevant focused checks, full Python suite, synthetic
      workflow and exact-revision hosted CI. Record commands, versions, seeds,
      hashes, comparison outputs and failure/recovery evidence.
- [x] P11.15 Document how to define and rerun a scenario, inspect A/B results,
      find input/model/output identities and interpret synthetic limitations.
      Record the Snakemake pilot decision and hand off unresolved gates.
