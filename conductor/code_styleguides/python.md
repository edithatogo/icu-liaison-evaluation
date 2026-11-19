# Python conventions

Follow the existing module layout and contract types. Add explicit types to
new public boundaries, validate inputs before calculating and keep I/O separate
from the numerical or contract functions. Use NumPy/SciPy and the nominated
providers rather than duplicating numerical, valuation or scheduling engines.

Errors must identify the unresolved input or qualification condition. Keep
missing, censored and ineligible outcomes distinct. Seed illustrative draws
explicitly and preserve source/version identifiers in exported artifacts.

Tests should establish observable behaviour, independent identities or evidence
rejection. Injected providers must be visibly synthetic and must not mark native
execution as accepted. Avoid tests that merely repeat the implementation.

Generated schemas and the source manifest are reviewed artifacts. Regenerate
them through their existing tools after a contract changes. Do not edit a
historical verification receipt to make it appear to cover a later source state.
