# ADR-0004 — Keep P4 economic and P5 reporting logic in the independent consumer

**Accepted for portable source only, 18 November 2026.**

The standalone ICU liaison project owns only population/comparator contracts,
non-overlapping physical resource assumptions, safety requirements, cost-
consequence scenarios and portable audit reports. P4 reuses SciPy/NumPy and
Pydantic, P3 for source identity, Dapane for exact monetary provider valuation
and Voiage for financial VOI. P5 only presents model outputs and checks
identities. The optional Kairos temporal bed-flow module remains separate.

No new Dapane or Voiage kernel is implemented. Installed-provider evidence and
clinical/economic validation stay unverified until real receipts are reviewed.
