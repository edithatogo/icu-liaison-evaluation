import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
SCENARIO=ROOT/'model-inputs/p4/illustrative.json'


def run(*args):
    return subprocess.run([sys.executable,'-m','icu_liaison.p4_cli',str(SCENARIO),*args],
                          cwd=ROOT,env={'PYTHONPATH':str(ROOT/'src')},text=True,capture_output=True,check=False)


def test_real_cli_runs_and_prints_only_labelled_synthetic_aggregates():
    r=run()
    assert r.returncode==0,r.stderr
    out=json.loads(r.stdout)
    assert out['investment_ready'] is False
    assert out['clinical_safety']=='unmeasured'
    assert 'liaison_service' in out['strategies']
    assert 'hospitalisation_pseudonym' not in r.stdout


def test_cli_fail_closed_on_require_local_ready():
    r=run('--require-local-ready')
    assert r.returncode==2
    assert 'UNVERIFIED' in r.stderr
    assert json.loads(r.stdout)['investment_ready'] is False


def test_cli_emits_no_synthetic_patient_rows_and_optional_decision_matrix(tmp_path):
    out=tmp_path/'decision.csv'
    r=run('--decision-surface',str(out))
    assert r.returncode==0,r.stderr
    lines=out.read_text().splitlines()
    assert lines[0]=='current_care,liaison_service,extended_cover'
    assert len(lines)==5001
    assert all('patient' not in line for line in lines)


def test_cli_rejects_overwriting_existing_decision_file(tmp_path):
    out=tmp_path/'decision.csv';out.write_text('do-not-overwrite')
    r=run('--decision-surface',str(out))
    assert r.returncode==2
    assert out.read_text()=='do-not-overwrite'


def test_cli_one_way_sensitivity_has_explicit_illustrative_status():
    r=run('--one-way-strategy','liaison_service')
    assert r.returncode==0,r.stderr
    out=json.loads(r.stdout)
    sensitivity=out['one_way_sensitivity']
    assert sensitivity['strategy_id']=='liaison_service'
    assert len(sensitivity['drivers'])>=5
    assert all(row['interpretation']=='one_at_a_time_prior_quantile_not_joint_posterior'
               for row in sensitivity['drivers'])
