# Artefact catalogue and editorial evidence

Use this contract for substantive reading and delivery editions of maintained
reports and documents. Take the saved file from the authoritative authoring route.
Record the SharePoint source and template versions when using structured document
generation. Keep calculations and governed admissions in their existing systems.

## Catalogue

Keep a versioned JSON catalogue with schema version 1. Give each artefact a unique
ID, role (source or output), stable location, saved path, label, document or data
kind, edition, provenance, and SHA-256 of the exact copy. Preserve older versions.
Record authored, issued, accessed and catalogued dates separately. Give each date
its basis. Use null with a specific reason where a date is uncertain. The
catalogued date is required. Use ISO calendar dates. If provider bytes cannot be
retained, record the exact local metadata or locator receipt as such. Name the
provider edition and unresolved questions in its provenance.

## Editorial evidence

The catalogue's checks map contains one local receipt reference for each of
CiteWeft, SourceRight, AuthenText and Textstat. Each reference has a path and the
SHA-256 of the receipt. Every receipt records its tool, version and a row for
each catalogue ID with the exact saved-file hash, outcome and scoped detail.
Checked or manually reconciled rows include the retained extract path and hash.

- **CiteWeft** extracts references and callouts. Reconcile each unsupported
  format or ambiguous result against the saved file and record the locations.
- **SourceRight** checks citation and source identity. Record whether each
  reported match reflects syntax, provider inspection or manual source readback.
  Retain the link from the claim to the dated passage, exact edition and result.
- **AuthenText** applies the maintained skill to contextual reasoning and prose.
  Preserve voice, meaning, uncertainty, citations and technical literals.
  Record material findings and their dispositions.
- **Textstat** measures explicitly selected prose with the repo-local runtime.
  Record the selector, language and scores. Scores guide editing and are not
  acceptance thresholds.

Record a specific reason for each inapplicable check. Resolve open material
issues before marking an edition verified. Refresh impacted evidence after prose,
references or source revisions. Keep protected records, extracts and tool output
in authorised storage. Verify document structure, visual acceptance, scientific
review and release authority through their existing procedures.

## Verify a saved edition

Run from the qualified repository environment. By default the verifier reads files
inside the catalogue directory. To verify a centrally managed saved copy, pass its
authorised folder explicitly. Extracts and editorial receipts remain with the
catalogue. The verifier also checks retained extract hashes. It does not fetch a
source or change release status.

```sh
.venv/bin/python tools/validate_reporting_contracts.py --edition ./catalogue.json
```

Public CI tests the contract with fictional artefacts and receipts.
