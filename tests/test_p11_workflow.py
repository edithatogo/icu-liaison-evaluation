"""End-to-end Snakemake rerun and recovery checks for synthetic scenarios."""
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SNAKEMAKE = Path(sys.executable).parent / 'snakemake'
CASES = ROOT / 'model-inputs/p11/cases'
STYLE = ROOT / 'model-inputs/p11/f01-style.json'
SUITE = ROOT / 'model-inputs/p11/suite.json'
SNAKEFILE = ROOT / 'workflow/Snakefile'

pytestmark = pytest.mark.skipif(
    not SNAKEMAKE.is_file(),
    reason='the separate qualified Snakemake environment is unavailable',
)


def pointer_set(root, category, cases):
    return {
        case: json.loads((root / 'state' / category / f'{case}.json').read_text())
        for case in cases
    }


def invoke(tmp_path, output, cases, style, *extra, expected=0, env_update=None):
    directory = tmp_path / 'scheduler'
    directory.mkdir(exist_ok=True)
    env = os.environ.copy()
    env.update(MPLBACKEND='Agg', PYTHONDONTWRITEBYTECODE='1',
               MPLCONFIGDIR=str(tmp_path / 'mpl'))
    env.update(env_update or {})
    command = [
        str(SNAKEMAKE), '--snakefile', str(SNAKEFILE), '--directory', str(directory),
        '--cores', '2', '--printshellcmds', '--rerun-incomplete',
        '--config', f'output={output}', f'cases={cases}', f'style={style}',
        *extra,
    ]
    result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=240)
    if result.returncode != expected:
        diagnostic = '\n'.join(line for line in (result.stdout + '\n' + result.stderr).splitlines()
                               if 'P11 INVALID' in line or 'Traceback' in line)
        pytest.fail(f'Snakemake returned {result.returncode} instead of {expected}\n'
                    f'{diagnostic}\n{result.stdout[-4000:]}\n{result.stderr[-6000:]}')
    return result


def test_reruns_and_failed_case_recover_without_overwriting(tmp_path):
    output, cases = tmp_path / 'store', tmp_path / 'cases'
    cases.mkdir()
    names = json.loads(SUITE.read_text())['cases']
    for name in names:
        value = json.loads((CASES / f'{name}.json').read_text())
        value['iterations'] = 32
        (cases / f'{name}.json').write_text(json.dumps(value))
    style = tmp_path / 'style.json'
    shutil.copyfile(STYLE, style)

    invoke(tmp_path, output, cases, style)
    models = pointer_set(output, 'models', names)
    figures = pointer_set(output, 'figures', names)
    summary = json.loads((output / 'state/summary.json').read_text())
    priorities = pointer_set(output, 'priority-figures', names)
    for priority in priorities.values():
        bundle = output / 'priority-figures' / priority['figure_revision'] / 'bundle'
        assert all((bundle / f'{figure}.svg').is_file()
                   for figure in ('f02', 'f10', 'f11', 'f15', 'f20', 'f24'))
    assert summary['scenario_count'] == 6 and summary['investment_ready'] is False
    summary_csv = output / 'summaries' / summary['summary_id'] / 'scenario-comparison.csv'
    with summary_csv.open(newline='') as stream:
        actual = list(csv.DictReader(stream))
    assert {row['case_id'] for row in actual} == set(names)
    assert {row['reference_strategy'] for row in actual} == {'current_care'}
    attempts_before = sorted((output / 'attempts').rglob('*.json'))

    no_op = invoke(tmp_path, output, cases, style)
    assert 'Nothing to be done' in no_op.stdout + no_op.stderr
    assert pointer_set(output, 'models', names) == models
    assert pointer_set(output, 'figures', names) == figures
    assert pointer_set(output, 'priority-figures', names) == priorities
    assert sorted((output / 'attempts').rglob('*.json')) == attempts_before

    case_file = cases / 'base.json'
    value = json.loads(case_file.read_text())
    value['seed'] = 20261119
    case_file.write_text(json.dumps(value))
    invoke(tmp_path, output, cases, style)
    models_after_case = pointer_set(output, 'models', names)
    figures_after_case = pointer_set(output, 'figures', names)
    summary_after_case = json.loads((output / 'state/summary.json').read_text())
    priorities_after_case = pointer_set(output, 'priority-figures', names)
    assert models_after_case['base']['model_run_id'] != models['base']['model_run_id']
    assert all(models_after_case[name] == models[name] for name in names if name != 'base')
    assert figures_after_case['base']['figure_revision'] != figures['base']['figure_revision']
    assert all(figures_after_case[name] == figures[name] for name in names if name != 'base')
    assert summary_after_case['summary_id'] != summary['summary_id']
    assert priorities_after_case['base']['figure_revision'] != priorities['base']['figure_revision']
    assert all(priorities_after_case[name] == priorities[name] for name in names if name != 'base')
    assert (output / 'priority-figures' / priorities['base']['figure_revision']).is_dir()

    settings = json.loads(style.read_text())
    settings['bar_color'] = '#9c4128'
    style.write_text(json.dumps(settings))
    invoke(tmp_path, output, cases, style)
    figures_after_style = pointer_set(output, 'figures', names)
    assert all(figures_after_style[name]['figure_revision'] != figures_after_case[name]['figure_revision']
               for name in names)
    assert pointer_set(output, 'models', names) == models_after_case
    assert json.loads((output / 'state/summary.json').read_text()) == summary_after_case
    assert pointer_set(output, 'priority-figures', names) == priorities_after_case

    # Exercise a renderer distribution version change without replacing the
    # real environment: metadata is shadowed only in this subprocess.
    metadata = tmp_path / 'version-override' / 'matplotlib-99.0.0.dist-info'
    metadata.mkdir(parents=True)
    (metadata / 'METADATA').write_text('Metadata-Version: 2.1\nName: matplotlib\nVersion: 99.0.0\n')
    # Preserve the checkout's src/ when the distribution is installed as a
    # wheel, as on hosted CI, instead of relying on an editable installation.
    pythonpath = os.pathsep.join((str(metadata.parent), str(ROOT / 'src')))
    invoke(tmp_path, output, cases, style, env_update={'PYTHONPATH': pythonpath})
    figures_after_runtime = pointer_set(output, 'figures', names)
    assert all(figures_after_runtime[name]['figure_revision'] != figures_after_style[name]['figure_revision']
               for name in names)
    assert pointer_set(output, 'models', names) == models_after_case
    assert json.loads((output / 'state/summary.json').read_text()) == summary_after_case
    priorities_after_runtime = pointer_set(output, 'priority-figures', names)
    assert all(priorities_after_runtime[name]['figure_revision'] != priorities_after_case[name]['figure_revision']
               for name in names)

    old_models = set((output / 'models').iterdir())
    previous = dict(value)
    value['iterations'] = 1
    case_file.write_text(json.dumps(value))
    failed = invoke(tmp_path, output, cases, style, expected=1)
    assert 'P11 INVALID_OR_UNVERIFIED' in failed.stderr
    assert set((output / 'models').iterdir()) == old_models
    case_file.write_text(json.dumps(previous))
    invoke(tmp_path, output, cases, style)
    assert pointer_set(output, 'models', names) == models_after_case
    assert all(path.is_dir() for path in old_models)


@pytest.mark.skipif(os.name != 'posix', reason='process-group interruption requires POSIX signals')
def test_interrupted_snakemake_run_recovers_existing_versions(tmp_path):
    import signal
    import time

    output, cases = tmp_path / 'store', tmp_path / 'cases'
    cases.mkdir()
    value = json.loads((CASES / 'base.json').read_text())
    value['iterations'] = 32
    case_file = cases / 'base.json'
    case_file.write_text(json.dumps(value))
    style = tmp_path / 'style.json'
    shutil.copyfile(STYLE, style)
    scheduler = tmp_path / 'scheduler'
    scheduler.mkdir()
    target = output / 'state/models/base.json'
    command = [
        str(SNAKEMAKE), str(target), '--snakefile', str(SNAKEFILE),
        '--directory', str(scheduler), '--cores', '1',
        '--rerun-incomplete', '--config', f'output={output}', f'cases={cases}', f'style={style}',
    ]
    env = os.environ.copy()
    env.update(MPLBACKEND='Agg', PYTHONDONTWRITEBYTECODE='1')
    first = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
    assert first.returncode == 0, first.stderr[-5000:]
    existing = json.loads(target.read_text())
    existing_dir = output / 'models' / existing['model_run_id']
    previous = set((output / 'attempts/base').glob('*.json'))

    value['seed'] = 20261119
    value['iterations'] = 100000
    case_file.write_text(json.dumps(value))
    proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        deadline = time.monotonic() + 45
        started = False
        while time.monotonic() < deadline and proc.poll() is None:
            attempts = set((output / 'attempts/base').glob('*.json')) - previous
            stages = list((output / 'models').glob('.p11-stage-*'))
            if attempts and stages:
                started = True
                break
            time.sleep(.05)
        assert started, 'synthetic workflow did not reach its unpublished staging step'
        os.killpg(proc.pid, signal.SIGINT)
        assert proc.wait(timeout=30) != 0
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait(timeout=10)
    assert (existing_dir / 'run.json').is_file()

    value['iterations'] = 32
    case_file.write_text(json.dumps(value))
    resumed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, timeout=120)
    assert resumed.returncode == 0, resumed.stderr[-5000:]
    recovered = json.loads(target.read_text())
    assert recovered['model_run_id'] != existing['model_run_id']
    assert existing_dir.is_dir()
    assert (output / 'models' / recovered['model_run_id'] / 'run.json').is_file()
