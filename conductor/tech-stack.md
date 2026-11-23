# Technical stack

The project uses the CPython 3.15.2 pin in `.python-version` for repository-local
development, builds, hooks and hosted CI. The package supports Python
`>=3.15.2,<3.16` and uses a `src/icu_liaison` layout. Pydantic
validates contracts. NumPy and SciPy provide numerical operations. Pytest and
JSON Schema support contract checks. Matplotlib is optional for report plots.
`pyproject.toml` defines supported ranges. `requirements-ci.txt` pins
source, test, report and isolated build dependencies.

The optional Rust consumer under `native/kairos-icu-liaison` remains uncompiled
and unqualified in this import. The dedicated provider environments and exact
source/binary provenance requirements remain in their locks and tracks. The
base Python CI must not silently install or substitute these native providers.

Project records live in `conductor/`. The upstream Conductor agent plugin is
versioned by the Git link at `extensions/conductor`. The [workspace setup](../GEMINI.md#conductor-agent-plugin)
checks its pinned source with Antigravity.

Inputs and reports use versioned JSON/JSON Schema, CSV and Markdown. Public
source metadata and synthetic fixtures are tracked. Permissioned clinical or
financial data require a separate approved private processing location.

No hosted clinical service or deployment is configured. GitHub Actions runs
source integrity, unit/contract checks and synthetic CLI acceptance only.
