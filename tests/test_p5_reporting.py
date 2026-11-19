"""RED: P5 reporting is a consumer of the accepted P4 draw table."""
from __future__ import annotations
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest

from icu_liaison.p4_model import EconomicScenario, evaluate_scenarios

ROOT=Path(__file__).resolve().parents[1]


def case():
    return EconomicScenario.model_validate_json((ROOT/'model-inputs/p4/illustrative.json').read_text())


def test_p5_bundle_contains_nonoverlapping_outcomes_and_explicit_source_status(tmp_path):
    from icu_liaison.p5_reporting import build_report, verify_manifest
    out=tmp_path/'report'
    build_report(case(),out,voiage_mode='skip')
    assert verify_manifest(out) is True
    assert {'model-summary.json','cost-consequence.csv','paired-comparisons.csv',
            'one-way-sensitivity.csv','decision-surface.csv','dapane-nominal-requests.json',
            'evidence-admission.json','report.md','manifest.json'}<=set(x.name for x in out.iterdir())
    model=json.loads((out/'model-summary.json').read_text())
    assert model['investment_ready'] is False
    assert model['voiage_evpi']['status']=='not_executed'
    assert model['P4_source_admission']['document_verified'] is False
    body=(out/'report.md').read_text()
    assert 'Illustrative' in body and 'not a CHHHS' in body
    assert 'COVID' not in body
    assert 'Clinical safety' in body


def test_p5_independent_accounting_detects_tampered_array():
    from icu_liaison.p5_reporting import audit_p4_accounting
    r=evaluate_scenarios(case())
    assert audit_p4_accounting(r)['passed'] is True
    bad=r.strategies['liaison_service']
    tampered=replace(bad,net_resource_benefit_aud=bad.net_resource_benefit_aud+10)
    r.strategies['liaison_service']=tampered
    with pytest.raises(ValueError,match='accounting'):
        audit_p4_accounting(r)


def test_p5_reproducible_content_and_refuses_existing_output(tmp_path):
    from icu_liaison.p5_reporting import build_report
    a=tmp_path/'a';b=tmp_path/'b'
    build_report(case(),a,voiage_mode='skip')
    build_report(case(),b,voiage_mode='skip')
    for file in a.iterdir():
        assert file.read_bytes()==(b/file.name).read_bytes(),file.name
    with pytest.raises(FileExistsError):
        build_report(case(),a,voiage_mode='skip')


def test_p5_voiage_only_uses_provider_not_homegrown_evpi(tmp_path):
    from icu_liaison.p5_reporting import build_report
    class Stub:
        def __init__(self, value):self.value=value
        def evpi(self):return 123.45
    def value_array(arr,labels):
        assert arr.shape==(5000,3)
        assert labels==['current_care','liaison_service','extended_cover']
        return arr
    dest=tmp_path/'with-voiage'
    build_report(case(),dest,voiage_mode='provider',
                 value_array_factory=value_array,analysis_factory=lambda x:Stub(x))
    d=json.loads((dest/'model-summary.json').read_text())
    assert d['voiage_evpi']['value_aud']==123.45
    assert d['voiage_evpi']['status']=='injected_contract_test_only'
    assert d['investment_ready'] is False


def test_p5_requires_provider_and_does_not_publish_partial_bundle(tmp_path):
    from icu_liaison.p5_reporting import build_report
    out=tmp_path/'not-published'
    with pytest.raises((RuntimeError,ValueError)):
        build_report(case(),out,voiage_mode='provider',analysis_factory=lambda x: object(),
                     value_array_factory=lambda a,b:a)
    assert not out.exists()


def test_p5_cli_generates_and_checks_bundle_without_local_claim(tmp_path):
    out=tmp_path/'report'
    r=subprocess.run([sys.executable,'-m','icu_liaison.p5_cli',str(ROOT/'model-inputs/p4/illustrative.json'),
                      '--output-dir',str(out)],cwd=ROOT,env={'PYTHONPATH':str(ROOT/'src')},capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    assert json.loads(r.stdout)['status']=='illustrative_report_built'
    assert out.exists()
    r=subprocess.run([sys.executable,'-m','icu_liaison.p5_cli',str(ROOT/'model-inputs/p4/illustrative.json'),
                      '--output-dir',str(tmp_path/'blocked'),'--require-investment-ready'],
                      cwd=ROOT,env={'PYTHONPATH':str(ROOT/'src')},capture_output=True,text=True)
    assert r.returncode==2
    assert not (tmp_path/'blocked').exists()


def test_voiage_invalid_negative_and_nonfinite_result_rejected(tmp_path):
    from icu_liaison.p5_reporting import build_report
    class Stub:
        def __init__(self,value):self.value=value
        def evpi(self):return self.value
    for bad in [-0.1,float('nan'),float('inf')]:
        with pytest.raises(ValueError,match='EVPI'):
            build_report(case(),tmp_path/str(bad),voiage_mode='provider',
                         value_array_factory=lambda a,b:a,
                         analysis_factory=lambda _:Stub(bad))


def test_p5_manifest_detects_tampering_and_missing_files(tmp_path):
    from icu_liaison.p5_reporting import build_report, verify_manifest
    d=tmp_path/'signed-bundle';build_report(case(),d,voiage_mode='skip')
    a=d/'report.md'
    a.write_text(a.read_text()+'\nchanged without receipt\n')
    with pytest.raises(ValueError,match='hash mismatch'):
        verify_manifest(d)
    # File-set membership also fails, preventing silent attachment substitution.
    a.write_text('validity restoration not attempted')
    (d/'extra.csv').write_text('not approved')
    with pytest.raises(ValueError,match='file-set mismatch'):
        verify_manifest(d)


def test_p5_optional_chart_is_labelled_and_does_not_change_decision_inputs(tmp_path):
    from icu_liaison.p5_reporting import build_report, verify_manifest
    import pytest
    pytest.importorskip('matplotlib')
    d=tmp_path/'with-chart';build_report(case(),d,voiage_mode='skip',plots=True)
    chart=(d/'scenario-comparison.svg').read_text()
    assert '<svg' in chart and 'Synthetic ICU liaison' in chart
    assert 'not CHHHS predictions' in chart
    assert verify_manifest(d)


def test_p5_cost_consequence_rows_have_separate_budget_and_capacity_units(tmp_path):
    from icu_liaison.p5_reporting import build_report
    import csv
    d=tmp_path/'audit';build_report(case(),d,voiage_mode='skip')
    with (d/'cost-consequence.csv').open() as stream:
        rows=list(csv.DictReader(stream))
    assert len(rows)==len(case().strategies)*7
    assert {r['boundary'] for r in rows if r['measure']=='usable_bed_days'}=={'capacity_not_monetised'}
    assert {r['boundary'] for r in rows if r['measure']=='net_budget_impact_aud'}=={'hypothetical_cash_realisability_only'}
    assert {r['unit'] for r in rows if r['measure']=='net_budget_impact_aud'}=={'AUD_2026'}


def test_p5_report_contains_nominal_thresholds_and_important_sensitivity_drivers(tmp_path):
    from icu_liaison.p5_reporting import build_report
    target=tmp_path/'report';build_report(case(),target)
    body=(target/'report.md').read_text(encoding='utf-8')
    assert 'Break-even' in body
    assert 'Required coverage' in body
    assert 'One-way sensitivity' in body
    assert 'public proxy' in body.lower() or 'Public ANZICS benchmark' in body
    assert 'Unverified' in body or 'unverified' in body
