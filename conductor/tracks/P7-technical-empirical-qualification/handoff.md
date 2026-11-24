# Independent acceptance handoff

18 November 2026. P7 source-level quality controls added without modifying the P4 economic engine, P6 native source, provider packages or the user's GitHub repositories. P3 aggregate QA is descriptive and not a prevalence inference with missing censoring. Independent Decimal P4 arithmetic checks selected random draws; it is not independent validation of intervention efficacy, QALY, local Finance data, or installed Dapane/Voiage. Publisher 2023/24 document pages were viewed; publisher PDF digest unavailable. See the dated verification receipt for the exact executed tests/tooling.

The initial handoff requested the 2024/25 PDF, dedicated repository and native
Kairos execution. The [current plan](plan.md) records each completed check and
the remaining admission, attestation, comparator and governance requirements.

## Dapane wheel evidence review — 19 November 2026

The build owner checked the exact rebuilt macOS arm64 wheel identified in the
[migration receipt](../../../verification/python-315-migration-2026-11-19.json).
Pinned source and build products matched the installed wheel's content as
recorded in the [P1.4 review](../P1-provider-reuse/plan.md#rebuilt-dapane-wheel-evidence-review).
Detailed candidate evidence is held with the retained build. An independent
reviewer can use it for the [P7.5 provenance decision](plan.md#p75-independent-provider-review).

## Independent Dapane disposition — 19 November 2026

Separate Codex reviewer `dapane_reviewer` verified the exact candidate wheel
and extension, then withheld binary-pin sign-off. The Rust 1.99.1 values in
the migration receipt came from preflight. The wheel's compiler evidence and
the replayed tool resolution point to Homebrew Rust 1.100.0. Controlled
builds under the pinned recipe produced different bytes. The detailed
review and build logs are retained in private evidence.
[P7.5 decision](plan.md#p75-independent-provider-review)

## Corrected Dapane approval — 19 November 2026

Separate Codex reviewer `dapane_reviewer` approved the exact corrected
Rust 1.99.1 Dapane 0.1.0 wheel and native extension for macOS arm64 with
CPython 3.15.2. P1 and P5 passed on the exact installation. The lock now
records the reviewed extension hash and its paired wheel. The dated
technical verdict and reconstruction evidence are retained privately.
[P7.5 corrected artifact decision](plan.md#corrected-dapane-artifact-decision)

## Dapane native execution approval — 19 November 2026

Separate Codex reviewer `dapane_reviewer` approved the native execution
receipt for the pinned wheel and extension after verifying pricing and
component conservation against frozen independent expectations. The lock
records the receipt digest for macOS arm64 and CPython 3.15.2. Broader
provider qualification, release review and Voiage admission remain open.
[P7.5 native execution decision](plan.md#dapane-native-execution-decision)

## Linux and Windows Dapane approvals — 19 November 2026

Separate Codex reviewer `dapane_reviewer` signed off on the exact Ubuntu
24.04.5 LTS x86-64 and Windows Server 2025 Datacenter x86-64 wheels,
extensions and native execution receipts. The Windows decision covers the
follow-up build and full vendor rerun with the two fixture key corrections.
The provider lock records the approved hashes for each tested host and the
signed decisions are retained privately. [P7.5 platform decisions](plan.md#linux-and-windows-dapane-decisions)

## Windows upstream rebuild approval

On 19 November 2026 AEST, separate Codex reviewer `dapane_reviewer`
approved the exact Windows rebuild from the landed upstream fixture fix.
All 215 vendor Python tests passed using that checkout, including the
original 196 cases. The Windows lock entry records the approved source,
wheel, extension and native replay receipt. The verdict and sealed
evidence are retained privately. [P7.5 decision](plan.md#windows-upstream-rebuild-decision)

## Portable qualification follow-through on 24 November 2026

The [chat recorded for P1](../P1-provider-reuse/handoff.md#p1-artifact-review-on-24-november-2026)
owns the P7 portable runner, independent aggregate audit and request-pack
verification on `codex/icu-p7-technical-qualification` in the attached
`icu-p6-review-recovery/icu-liaison-evaluation` worktree. This lane ran the
portable Python checks and matched the retained public PDF. The native
evidence is the previously recorded P1 and P6 decisions and replay receipts.
The next operation is hosted source validation. Independent publisher
admission, release attestation and site review remain open.
[Verification](test-matrix.md#repeat-the-current-qualification)

## Review follow-through on 24 November 2026

The same attached worktree and chat carry `codex/icu-p7-review-fixes`. This
lane owns the aggregate audit, the portable qualification runner and the
request exporter. The local checks reproduced the verified publisher match
and the authored request exports. The next operation is exact-head hosted
validation. [Review verification](test-matrix.md#p7-review-on-24-november-2026)
