# P7 plan

- [x] P7.1 Source and denominator reconciliation: ANZICS 2023/24 publisher text/page images; 2024/25 remains unverified.
- [x] P7.2 Independent P4 draw accounting and P3 aggregate QA/unknowns; focused tests.
- [x] P7.3 Typed CHHHS 11-dataset request pack and clinical/causal validation protocol; no observed data imported.
- [ ] P7.4 Run qualified Kairos native consumer against pinned source and reviewed Cargo.lock; currently missing Rust toolchain and lock.
- [~] P7.5 Execute and independently qualify Dapane and Voiage installed binaries and wheels. The independent Dapane reviewer withheld binary-pin sign-off after finding a toolchain mismatch. Voiage admission remains open.
- [ ] P7.6 Authenticate 2024/25 ANZICS publisher PDF bytes, exact source hash and pages.
- [ ] P7.7 Receive authorised CHHHS activity, capacity, staffing and costing extracts; calibrate and validate prospectively with clinical/Finance/equity governance.
- [ ] P7.8 Supply the selected dedicated GitHub repository, transplant sources, run hosted CI, independent review, and close exploratory careops-sim PR #215 after reconciliation.

No missing item may be checked merely because synthetic source tests pass.

## P7.5 independent provider review

The [P1.4 review](../P1-provider-reuse/plan.md#rebuilt-dapane-wheel-evidence-review)
was performed by the build owner. It ties the rebuilt Dapane wheel in the
[migration receipt](../../../verification/python-315-migration-2026-11-19.json)
to pinned source, a locked Rust dependency set, retained Cargo outputs, and
the CPython 3.15.2 macOS arm64 installation tested by P1 and P5.

On 19 November 2026 AEST, the separate Codex technical reviewer
`dapane_reviewer` verified the exact retained wheel and installed extension.
The binary and its compiler metadata identify Homebrew Rust 1.100.0. The
approved recipe specifies Rust 1.99.1. Controlled builds using the pinned
toolchain produced different archives and native extensions. The reviewer
withheld sign-off for the retained wheel and its extension. The private
verdict and build comparison are retained for the next adjudication.
[Independent P1.4 findings](../P1-provider-reuse/plan.md#independent-dapane-technical-review)

Independent sign-off still requires an authorised reviewer outside that build
to verify source-to-wheel provenance for the exact archive and native extension
digests against an immutable build record or independently controlled build.
The earlier and rebuilt wheels have different archive digests. The earlier
receipt records the same native extension digest. An explanation of the archive
difference requires the earlier wheel bytes or comparable build evidence.

The review reproduced the pinned crate and Rust 1.99.1 notice inventory.
The offline macOS arm64 crate graph passed bans, source and crate licence
checks. The advisory check still flagged `RUSTSEC-2026-0543`
(`chrono 0.4.45`). Effective Rust 1.100.0 notices, the Dapane CLI APFS
filename failure and Linux and Windows qualification remain open. Only the
macOS arm64 CPython 3.15.2 candidate was checked here. Both
`providers.lock.json` binary digests remain null pending independent
adjudication. Voiage's artifact evidence remains a separate decision.
