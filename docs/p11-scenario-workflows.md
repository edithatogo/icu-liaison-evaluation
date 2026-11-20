# P11 synthetic scenario workflows

P11 runs a small, local Snakemake pilot over the existing P4 and P5 calculations.
It uses a baseline and the five P10 stress scenarios: no effect, harmful returns,
no addressable delay, no usable capacity and no cash realisability. Each run
compares current care with each modelled liaison strategy using shared draws
within that run. Its quantiles describe parameter uncertainty, not confidence
intervals; differences between scenarios are not asserted to be paired. Results
are fictional illustrations, not evidence of local clinical or financial benefit.

## Set up and run

Run the commands from the repository root. Install into a separate environment
because Snakemake 9.27.2 needs a different `packaging` release from the base
test environment. The fully pinned runtime and build constraints were qualified
on Python 3.15.2; the active patch is selected by `.python-version`.

```sh
uv venv --python "$(cat .python-version)" private/venv-p11
test "$(private/venv-p11/bin/python --version)" = "Python $(cat .python-version)"
uv pip install --python private/venv-p11/bin/python -r requirements-p11.txt \
  -c requirements-p11.txt --build-constraints requirements-p11-build.txt \
  -e '.[test,report,workflow]'
uv pip check --python private/venv-p11/bin/python
mkdir -p outputs/p11
private/venv-p11/bin/snakemake --snakefile workflow/Snakefile \
  --directory outputs/p11 --cores 2 --rerun-incomplete
private/venv-p11/bin/python -m icu_liaison.p11_verify --output outputs/p11
```

The workflow's default profile selects Snakemake's built-in greedy scheduler;
the bundled CBC solver was not executable on the qualified macOS ARM host. This
does not change the model. The normal base commands in the README remain available.
Each scenario produces F01 and 13 companion figures. Six priority plots cover
resources, break-even, paired capacity, discharge journeys, nursing coverage
and clinical-effect sensitivity. Seven more cover resources versus cash, the
sign and distribution of paired differences, one-way sensitivity, occupancy,
index discharge flow and a fictional controlled event-study design. F09, F13,
F15, F18 and F20 use separate fictional fixtures shared across scenarios.

The F24 CSV expresses each cell as the joint-null resource result plus delay,
return and interaction contrasts, computed on the same parameter draws. F10
displays a fixed parameter as one value. P11 records the provider execution
status and checks source values against the rendered SVG marks.

## Define a scenario

`model-inputs/p11/suite.json` lists case IDs, each backed by a same-named JSON
file in `model-inputs/p11/cases/`. A case selects a P10 `variant`, descriptive
text and optional seed, draw count and full P4 prior overrides. `null` retains
the seed or draw count from `model-inputs/p4/illustrative.json`. For example,
copy `base.json` to a new case ID, update the `case_id` and description, and add
the ID to the suite. The following replaces the existing P4 prior in that case:

```json
"overrides": {
  "resource.addressable_delay_fraction": {
    "family": "fixed",
    "params": {"value": 0.3},
    "unit": "proportion",
    "evidence_status": "illustrative_assumption",
    "source_ref": "P4-ILLUSTRATIVE"
  }
}
```

Use complete P4 prior objects and existing keys from the baseline input; case
and underlying P4 validation reject unknown or invalid fields. Add only
synthetic/public assumptions to this portable suite. Fixed-value overrides
remove those variables from inherited correlation groups; any remaining
correlations are retained, and the effective scenario snapshot records the
resulting groups. After an input change,
rerun the command above. Snakemake rebuilds the affected model, its figures and
the comparison, while other model runs remain available. Presentation settings
are in `model-inputs/p11/f01-style.json`; changing them creates new figure
revisions without rebuilding the model reports.

## Locate and check results

`outputs/p11/state/summary.json` points to the current summary ID. Its
`summaries/<summary-id>/scenario-comparison.csv` contains the within-run
strategy differences, uncertainty quantiles, units, seed and model-run IDs.
The corresponding `summary.json` binds the suite, falsification audit and
constituent model records. `state/models/<case>.json` identifies each immutable
`models/<model-run-id>/` bundle: input snapshots, effective scenario, P5 report,
paired outcomes, independent numerical review, run metadata and SHA-256 hashes.
`state/figures/<case>.json` links to its immutable F01 figure revision.
`state/priority-figures/<case>.json` links to the corresponding immutable
`priority-figures/<revision>/bundle/index.html`, 13 SVGs, source CSVs and
a P9 manifest. Each new revision retains the P3 feeds and dictionary, P6 trace,
P9 fixtures, catalogue, metric registry and a separate mark review. Attempt files under `attempts/`
record model execution separately from model identity.

The run identity uses input snapshots, the effective scenario, relevant source
hashes, Python and numerical runtime versions, and provider execution status.
It records the Git revision and whether executed source was dirty separately;
timestamps do not change the run ID. A relevant code, runtime, input or seed
change makes a new ID. Figure revisions bind the model record, renderer source,
relevant input snapshots and Matplotlib version; F01 also binds its style. File
hashes support integrity checks, not scientific
approval. Existing content-addressed objects are never silently overwritten.

Run `icu_liaison.p11_verify` after a workflow run to check current pointers,
file hashes, model and figure links, the F01 bars and percentile intervals, the
registered P9 outputs per scenario and the combined rows. Edition 1 retains its
six-figure inventory. Edition 2 requires all 13 P9 figures. For matching source, inputs and runtime it also replays the P4/P5
and P9 numerical and mark reviews; historical runs with a different runtime are
checked for recorded file integrity without claiming a new replay. Snakemake's
no-op check alone checks workflow freshness,
not corruption inside published object directories.

## Reruns and recovery

An unchanged second execution schedules no analytical rebuild. On failure or
interruption, retain the existing output directory and rerun the same command
with `--rerun-incomplete`: staging is separate from published objects, and
atomic pointer updates expose only completed objects. Previous immutable runs
remain available. A missing or altered immutable object is rejected by the
verification command; retain it for inspection and run into a fresh output
directory if recovery is needed. Do not treat a matching hash or successful
retry as clinical acceptance, real-data admission or provider qualification.

The synthetic rerun, change and interruption tests can be repeated with:

```sh
private/venv-p11/bin/python -m pytest -q tests/test_p11_cases.py \
  tests/test_p11_outputs.py tests/test_p11_workflow.py
```
