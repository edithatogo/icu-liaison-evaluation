# P7 plan

- [x] P7.1 Review the ANZICS 2023/24 publisher text and page images. P7.6 covers the 2024/25 edition.
- [x] P7.2 Independent P4 draw accounting and P3 aggregate QA/unknowns; focused tests.
- [x] P7.3 Typed CHHHS 11-dataset request pack and clinical/causal validation protocol; no observed data imported.
- [x] P7.4 Run the pinned Kairos consumer with a reviewed Cargo.lock and check
  byte-identical replay against the one-bed oracle. [P6 evidence](../../../docs/p6-native-qualification.md)
- [ ] Independently attest the P7.4 build artifact and runner.
- [~] P7.5 Execute and independently qualify Dapane and Voiage installed binaries and wheels. Dapane's pinned macOS arm64, Ubuntu x86-64 and Windows Server x86-64 artifacts and native pricing receipts have scoped independent approval. Broader Dapane provider qualification and Voiage admission remain open.
- [x] P7.6 Retrieve the 2024/25 PDF directly from ANZICS and check the six
  benchmark values and their page locators. [Publisher receipt](../../../verification/p7-anzics-2024-25-publisher-2026-11-24.json)
- [ ] Independently review the 2024/25 source for admission and intended use.
- [ ] P7.7 Receive authorised CHHHS activity, capacity, staffing and costing extracts; calibrate and validate prospectively with clinical/Finance/equity governance.
- [x] P7.8 Integrate the portable source into the dedicated repository and
  verify the hosted synthetic and privacy workflows. [Import record](../../../docs/repository-import.md)
- [x] Verify the disposition of CareOps Sim PR #215. GitHub records it as
  closed, with the exploratory head preserved.
  [Migration comparison](../../../docs/pr215-migration-comparison.md)
- [ ] Independently accept the migration evidence for release.

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

For that candidate, independent sign-off required an authorised reviewer
outside the build to verify the exact archive and native extension against
an immutable build record or independently controlled build.
The earlier and rebuilt wheels have different archive digests. The earlier
receipt records the same native extension digest. An explanation of the archive
difference requires the earlier wheel bytes or comparable build evidence.

The review reproduced the pinned crate and Rust 1.99.1 notice inventory.
The offline macOS arm64 crate graph passed bans, source and crate licence
checks. The advisory check still flagged `RUSTSEC-2026-0543`
(`chrono 0.4.45`). Effective Rust 1.100.0 notices, the Dapane CLI APFS
filename failure and Linux and Windows qualification remain open. The
review left both provider digests unset at that checkpoint.

### Corrected Dapane artifact decision

On 19 November 2026 AEST, separate Codex reviewer `dapane_reviewer`
approved the exact corrected Dapane 0.1.0 wheel and binary pin for the
macOS arm64 installation tested on CPython 3.15.2. The pinned Rust 1.99.1
build trace and compiler evidence matched the installed extension.
Independent reconstruction produced both exact candidate digests after
accounting for the linker UUID and its derived page hash, the SBOM paths
and wheel packaging. The dated verdict and full verification evidence are
retained privately.

The provider lock records the reviewed extension as Dapane `binary_sha256`
and pairs it with the exact wheel digest. The P1/P5 reruns passed for that
installed artifact. [Provider lock](../../../providers.lock.json) ·
[P1/P5 reruns](../P1-provider-reuse/plan.md#corrected-rust-1991-candidate)

### Dapane native execution decision

On 19 November 2026 AEST, separate Codex reviewer `dapane_reviewer` approved
the exact native execution receipt for the pinned Dapane 0.1.0 wheel and
extension on macOS 27.2.1 arm64 with CPython 3.15.2. The review verified
counterfactual pricing through P1 for both beneficial and adverse return
effects, plus exact and rounded component conservation across three
synthetic ledger pairs. Duplicate same-use component pricing failed closed.
[P1.4 findings](../P1-provider-reuse/plan.md#native-counterfactual-pricing-and-component-conservation)

The lock records the reviewed receipt's SHA-256 in
`native_execution_receipt_sha256`. The receipt identifies the executed
consumer commit and the pre-insertion lock digest. The dated verdict and
supporting evidence are retained privately.
[Provider lock](../../../providers.lock.json)

### Linux and Windows Dapane decisions

On 19 November 2026 AEST, separate Codex reviewer `dapane_reviewer`
approved the exact Dapane 0.1.0 wheels, loaded extensions and native replay
receipts for Ubuntu 24.04.5 LTS x86-64 with glibc 2.39 and Windows Server
2025 Datacenter x86-64 build 26100 on CPython 3.15.2. The compiler trace
showed Rust 1.99.1. The reviewer audited source and wheel provenance,
the archived build evidence, wheel records, and the exact native output
of independently authored pricing and component-conservation checks in
a fresh environment on each build runner. [P1.4 platform findings](../P1-provider-reuse/plan.md#linux-and-windows-x86-64-qualification)

The unmodified Windows vendor suite exposed 30 schema lookups that used
inconsistent path separators. The reviewer verified the two test-only
edits in a disposable checkout and all 196 passing tests against the
follow-up wheel. The dated verdicts and sealed evidence for those runs
are retained privately.
[Windows rerun](https://github.com/edithatogo/icu-liaison-evaluation/actions/runs/44508599306/job/135506594520)

### Windows upstream rebuild decision

On 19 November 2026 AEST, separate Codex reviewer `dapane_reviewer`
approved the exact Dapane 0.1.0 wheel, loaded extension and replay receipt
rebuilt from landed source `33941aa22616629a26b58220f7e05ae615855072`
with Rust 1.99.1 and CPython 3.15.2 on Windows Server 2025 Datacenter
x86-64 build 26100. The upstream fixture fix normalized schema path keys
in three test modules. The reviewer matched all 215 passing vendor cases
to the independently collected test IDs, covering all 196 original cases
and 19 later QLD NBS cases. The sealed packet binds the compiler trace,
installed wheel and all six pricing and conservation replays.
[Upstream fixture fix](https://github.com/edithatogo/dapane/pull/32) ·
[P1.4 Windows rebuild](../P1-provider-reuse/plan.md#windows-rebuild-after-the-upstream-fixture-fix)

The Windows lock entry records the landed source and the three
approved digests. Broader release qualification, other environments,
the `chrono` advisory, the macOS CLI APFS case and Voiage admission
remain open. [Provider lock](../../../providers.lock.json) ·
[Companion plan](../P7-placeholder-assisted-qualification/plan.md#p74--external-qualifications-blocked-not-accepted)
