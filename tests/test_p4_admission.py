"""RED: P4 must admit P2/P3 contracts before producing a decision report."""
import copy
import json
from pathlib import Path
import pytest
from icu_liaison.p4_model import EconomicScenario

ROOT = Path(__file__).resolve().parents[1]


def inputs():
    return (json.loads((ROOT/'model-inputs/p4/illustrative.json').read_text()),
            json.loads((ROOT/'model-inputs/clinical-economic-protocol.json').read_text()),
            json.loads((ROOT/'model-inputs/anzics-benchmarks.json').read_text()),
            json.loads((ROOT/'conductor/evidence/source-register.json').read_text()))


def test_accepts_valid_synthetic_p4_with_unverified_public_source():
    from icu_liaison.p4_admission import admit_p4
    s,p,c,r=inputs()
    report=admit_p4(EconomicScenario.model_validate(s),p,c,r)
    assert report['admission']=='illustrative_only'
    assert report['document_verified'] is False
    assert report['source_status']=='previous_transcription_not_independently_reverified'
    assert report['local_CHHHS_inputs_verified'] is False


def test_rejects_wrong_price_year_and_horizon():
    from icu_liaison.p4_admission import admit_p4
    s,p,c,r=inputs()
    p['economics']['price_year']=2025
    with pytest.raises(ValueError,match='price year'):
        admit_p4(EconomicScenario.model_validate(s),p,c,r)
    s,p,c,r=inputs();p['economics']['evaluation_horizon_months']=24
    with pytest.raises(ValueError,match='horizon'):
        admit_p4(EconomicScenario.model_validate(s),p,c,r)


def test_rejects_changed_external_benchmark_and_source_registry():
    from icu_liaison.p4_admission import admit_p4
    s,p,c,r=inputs();c['metrics'][0]['value']=0.211
    with pytest.raises(ValueError,match='source|benchmark|proxy'):
        admit_p4(EconomicScenario.model_validate(s),p,c,r)
    s,p,c,r=inputs();p['reference_benchmark']['value']=0.199
    with pytest.raises(ValueError,match='protocol|proxy|benchmark'):
        admit_p4(EconomicScenario.model_validate(s),p,c,r)


def test_rejects_protocol_benchmark_period_that_disagrees_with_p3():
    from icu_liaison.p4_admission import admit_p4

    scenario, protocol, catalogue, register = inputs()
    protocol['reference_benchmark']['period'] = '2023-07-01/2024-06-30'
    with pytest.raises(ValueError, match='benchmark reporting period'):
        admit_p4(EconomicScenario.model_validate(scenario), protocol, catalogue, register)


@pytest.mark.parametrize('parameter', [
    'baseline.unplanned_72h_return_rate',
    'resource.net_index_delay_cost_aud_per_day',
    'strategy.liaison_service.annual_incremental_cost_aud',
])
def test_rejects_local_aggregate_priors_in_fictional_admission(parameter):
    from icu_liaison.p4_admission import admit_p4

    scenario_data, protocol, catalogue, register = inputs()
    scenario = EconomicScenario.model_validate(scenario_data)
    scenario.all_priors()[parameter].evidence_status = 'local_aggregate_unvalidated'
    with pytest.raises(ValueError, match='local aggregate priors'):
        admit_p4(scenario, protocol, catalogue, register)


def test_rejects_missing_required_safety_and_unapproved_source_promotion():
    from icu_liaison.p4_admission import admit_p4
    s,p,c,r=inputs();p['safety']['required_endpoints'].remove('ward_workload')
    with pytest.raises(ValueError,match='safety'):
        admit_p4(EconomicScenario.model_validate(s),p,c,r)
    s,p,c,r=inputs();c['metrics'][0]['verification_status']='document_hash_attested_and_substantively_reviewed'
    with pytest.raises(ValueError):
        admit_p4(EconomicScenario.model_validate(s),p,c,r)


def test_p4_cli_reports_evidence_admission_and_rejects_tampered_protocol(tmp_path):
    import subprocess
    import sys
    root=ROOT
    cli=[sys.executable,'-m','icu_liaison.p4_cli',str(root/'model-inputs/p4/illustrative.json')]
    environment={'PYTHONPATH':str(root/'src')}
    clean=subprocess.run(cli,cwd=root,env=environment,capture_output=True,text=True)
    assert clean.returncode==0,clean.stderr
    output=json.loads(clean.stdout)
    assert output['P4_source_admission']['admission']=='illustrative_only'
    assert output['P4_source_admission']['document_verified'] is False

    protocol=json.loads((root/'model-inputs/clinical-economic-protocol.json').read_text())
    protocol['economics']['price_year']=2024
    file=tmp_path/'bad.json'
    file.write_text(json.dumps(protocol))
    failed=subprocess.run(cli+['--protocol',str(file)],cwd=root,env=environment,capture_output=True,text=True)
    assert failed.returncode==2
    assert 'UNVERIFIED' in failed.stderr
