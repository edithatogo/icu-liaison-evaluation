# P9 priority synthetic figures

The branch `codex/p9-synthetic-figures` implements F02, F10, F11, F15, F20
and F24 over the P5 synthetic workflow. Its companion report includes
source hashes, source CSVs and independently checked data marks. The
[verification receipt](../../../verification/p9-synthetic-figures-2026-11-20.json)
records the reviewed mobile, tablet, desktop and A4 grayscale renders on
20 November 2026. The exact-head CI result remains the integration gate.

## Review and integration follow-through

On 20 November 2026, chat 01a1f64b-ef56-75f3-a2dc-bafc0180b28e is the sole
writer for the F20 geometry review fix in this worktree,
`/Users/doughnut/.codex/worktrees/icu-liaison-p9-synthetic-figures/icu-liaison-evaluation`,
on `codex/p9-synthetic-figures`. Its scope is the P9 renderer, independent mark
review, focused tests, source manifest and this handoff. Native scope is none.
The next operation is to verify rendered coverage cells and demand positions,
then rerun the synthetic checks before proposing the PR for merge.

The F20 review now validates each paid-coverage and demand-cell rectangle and
its hourly position, as well as demand-label placement. Rehashed missing,
displaced and invisible-mark cases are rejected. The
[follow-through receipt](../../../verification/p9-f20-geometry-2026-11-20.json)
records a 5,000-draw rebuild: five SVGs match the prior visual-review bytes;
F20's markup changed to identify its cells, and its before/after raster is
identical. The original visual receipt remains historical rather than being
relabeled as a fresh independent review.

## Portable reporting completion

On 20 November 2026, chat 01a1f64b-ef56-75f3-a2dc-bafc0180b28e owns the
portable figure, measurement and integration changes in
`/Users/doughnut/.codex/worktrees/icu-renovate-onboarding/icu-liaison-evaluation`
on `codex/icu-portable-completion`. Scope includes P9 figure source and
review, P3/P10 index delay, P11 publication, their tests, the source manifest
and linked Conductor records. Native scope is none. The next operation is a
synthetic regression for each missing output, followed by a versioned suite run
and hosted validation. Earlier ownership entries are historical.

The expanded bundle produces 14 figures per scenario. P11 checks both manifest
inventories and the frozen source hashes, including archived six-figure
revisions. F01 checks its labelled bars and percentile intervals. All 72 paired
comparison rows matched the previous edition on every field other than the
model identifier. The source and browser checks, four display profiles,
unchanged rerun, recovery and P3 denominator result are recorded in the
[synthetic verification](../../../verification/portable-synthetic-2026-11-20.json).
The 33 P7 evidence obligations retain their existing owners.
