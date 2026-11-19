"""The full portability runner cannot claim provider, CHHHS or clinical acceptance."""
from pathlib import Path
import importlib.util


def test_synthetic_qualification_runner_is_fail_closed():
    root=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location('qualify_current_portable',root/'tools/qualify_current_portable.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result=module.qualify()
    assert result['status']=='SOURCE_ORACLES_PASSED_SYNTHETIC_ONLY'
    assert result['p4_independent_accounting']['draws_checked']==18
    assert result['p3_synthetic_quality']['return_72h']['unknown']==1
    assert result['native_kairos_executed'] is False
    assert result['dapane_native_executed'] is False
    assert result['voiage_native_executed'] is False
    assert result['clinical_or_causal_validation'] is False
    assert result['investment_ready'] is False
