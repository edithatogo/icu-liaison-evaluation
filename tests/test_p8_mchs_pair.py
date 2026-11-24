"""Consumer-first tests; the real MCHS calculator is NOT simulated or reimplemented."""
from __future__ import annotations

from decimal import Decimal
import copy
import pytest

from icu_liaison.adapters.p8_mchs import MchsPair, run_mchs_pair


def example(**changes):
    data = {
        'schema_version': 1, 'data_class': 'synthetic',
        'episode_id': 'synthetic-icu-episode-01', 'pricing_year': 2025,
        'drg': 'E62B', 'drg_edition': 'v11.0', 'hospital_los_days': 6,
        'icu_hours_current': '58.25', 'icu_hours_intervention': '54.25',
        'icu_other_hours': '0', 'pat_sameday_flag': 0, 'pat_private_flag': 0,
        'context': {'PAT_COVID_FLAG': 0, 'EST_ELIGIBLE_ICU_FLAG': 1},
        'source_bundle_sha256': 'a' * 64,
        'source_bundle_id': 'synthetic-ihacpa-bundle',
    }
    data.update(changes)
    return MchsPair.model_validate(data)


def stub_calculator(calls):
    def run(rows, *, year, ref_dir):
        calls.append((copy.deepcopy(rows), year, ref_dir))
        hours = Decimal(str(rows[0]['ICU_HOURS']))
        return [{'NWAU25': str(hours / Decimal('100') + Decimal('1.00')),
                 'Error_Code': 0}]
    return run


def test_paired_mchs_only_changes_icu_hours_and_keeps_funding_separate():
    calls = []
    out = run_mchs_pair(example(), provider=stub_calculator(calls))
    assert len(calls) == 2
    before, after = calls[0][0][0], calls[1][0][0]
    assert {k for k in before if before[k] != after[k]} == {'ICU_HOURS'}
    assert before['LOS'] == after['LOS'] == 6
    assert before['DRG'] == after['DRG'] == 'E62B'
    assert out['unit'] == 'NWAU' and out['actual_revenue_aud'] is None
    assert out['current_nwau'] == '1.5825'
    assert out['proposed_nwau'] == '1.5425'
    assert out['change_nwau'] == '-0.0400'
    assert out['execution_evidence'] == 'injected_contract_test_only'
    assert out['annual_calculator_parity'] == 'unverified'


def test_no_change_is_exact_zero_without_claiming_cash():
    calls=[]
    out=run_mchs_pair(example(icu_hours_intervention='58.25'),provider=stub_calculator(calls))
    assert out['change_nwau'] == '0.0000'
    assert out['actual_revenue_aud'] is None


@pytest.mark.parametrize('changes', [
    {'pricing_year': 2026, 'drg_edition': 'v12.0'},
    {'pricing_year': 2025, 'drg_edition': 'v12.0'},
    {'drg': ''}, {'episode_id':'real-person-123'},
    {'hospital_los_days': 0}, {'icu_hours_current':'-1'},
    {'icu_hours_intervention':'NaN'}, {'icu_hours_current':58.25},
    {'context': {'DRG': 'altered'}}, {'data_class':'patient_records'},
    {'source_bundle_sha256':'unverified'},
])
def test_reject_unsupported_year_version_and_unqualified_input(changes):
    with pytest.raises((ValueError, TypeError)):
        example(**changes)


def test_provider_error_and_wrong_output_column_fail_closed():
    with pytest.raises(ValueError, match='MCHS'):
        run_mchs_pair(example(), provider=lambda rows, **kw:[{'NWAU25_AUD':'123.00'}])
    with pytest.raises(ValueError, match='MCHS'):
        run_mchs_pair(example(), provider=lambda rows, **kw:[{'NWAU25':0,'Error_Code':3}])
    with pytest.raises(ValueError, match='MCHS'):
        run_mchs_pair(example(), provider=lambda rows, **kw:[{'NWAU25':'NaN','Error_Code':0}])
    with pytest.raises(ValueError, match='MCHS'):
        run_mchs_pair(example(), provider=lambda rows, **kw:[{'NWAU25':-1,'Error_Code':0}])


def _install_fictional_mchs(tmp_path, monkeypatch, body):
    package = tmp_path / 'runtime/nwau_py/calculators'
    package.mkdir(parents=True)
    for directory in (package, package.parent):
        (directory / '__init__.py').touch()
    (package / 'acute.py').write_text(body, encoding='utf-8')
    (package.parents[1] / 'polars.py').write_text('DataFrame = list\n', encoding='utf-8')
    monkeypatch.syspath_prepend(str(package.parents[1]))


def test_missing_mchs_installation_is_explicit_not_a_fake_success(tmp_path, monkeypatch):
    _install_fictional_mchs(tmp_path, monkeypatch, 'raise ImportError("not installed")\n')
    with pytest.raises(RuntimeError,match='MCHS.*not installed'):
        run_mchs_pair(example(),provider=None,ref_dir='/synthetic/reference')


def test_native_path_demands_an_explicit_reference_bundle_directory():
    with pytest.raises(ValueError,match='reference'):
        run_mchs_pair(example(),provider=None)


@pytest.mark.parametrize('change', ['none', 'before', 'during'])
def test_installed_route_binds_the_sas_table_bytes(tmp_path, monkeypatch, change):
    import icu_liaison.adapters.p8_mchs as module

    table = tmp_path / 'nep25_aa_price_weights.sas7bdat'
    table.write_bytes(b'fictional reference bytes')
    (tmp_path / 'nep25_aa_adj_icu.sas7bdat').write_bytes(b'fictional ICU adjustment bytes')
    case = example(source_bundle_sha256=module.mchs_reference_sha256(tmp_path))
    calls = tmp_path / 'calls.txt'
    _install_fictional_mchs(tmp_path, monkeypatch, f'''
AcuteParams = object

def calculate_acute(rows, _params, *, year, ref_dir):
    with (ref_dir / 'calls.txt').open('a', encoding='utf-8') as file:
        file.write(year + '\\n')
    if {change == 'during'!r}:
        (ref_dir / 'nep25_aa_price_weights.sas7bdat').write_bytes(b'changed reference bytes')
    return [{{'NWAU25': '1.0', 'Error_Code': 0}}]
''')
    if change == 'before':
        table.write_bytes(b'changed reference bytes')
        with pytest.raises(ValueError, match='SHA-256 differs'):
            run_mchs_pair(case, ref_dir=str(tmp_path))
        assert not calls.exists()
    elif change == 'during':
        with pytest.raises(ValueError, match='changed during'):
            run_mchs_pair(case, ref_dir=str(tmp_path))
    else:
        result = run_mchs_pair(case, ref_dir=str(tmp_path))
        assert result['source_bundle_sha256_declared'] == case.source_bundle_sha256
        assert result['annual_calculator_parity'] == 'unverified'
        assert calls.read_text(encoding='utf-8').splitlines() == ['2025', '2025']


def test_installed_route_leaves_caller_cache_untouched(tmp_path, monkeypatch):
    from icu_liaison.adapters.p8_mchs import mchs_reference_sha256

    refs = tmp_path / 'references'
    refs.mkdir()
    (refs / 'nep25_aa_price_weights.sas7bdat').write_text('1.0', encoding='utf-8')
    (refs / 'nep25_aa_adj_icu.sas7bdat').write_bytes(b'fictional ICU adjustment bytes')
    caller = tmp_path / 'caller'
    cache = caller / '.cache' / 'nep25_aa_price_weights.txt'
    cache.parent.mkdir(parents=True)
    cache.write_text('999.0', encoding='utf-8')
    _install_fictional_mchs(tmp_path, monkeypatch, '''
from pathlib import Path

AcuteParams = object

def calculate_acute(rows, _params, *, year, ref_dir):
    cached_table = Path('.cache/nep25_aa_price_weights.txt')
    cached_table.parent.mkdir(exist_ok=True)
    if not cached_table.exists():
        cached_table.write_bytes((ref_dir / 'nep25_aa_price_weights.sas7bdat').read_bytes())
    return [{'NWAU25': cached_table.read_text(encoding='utf-8'), 'Error_Code': 0}]
''')
    monkeypatch.chdir(caller)

    result = run_mchs_pair(example(source_bundle_sha256=mchs_reference_sha256(refs)), ref_dir=str(refs))

    assert result['current_nwau'] == result['proposed_nwau'] == '1.0'
    assert cache.read_text(encoding='utf-8') == '999.0'


@pytest.mark.parametrize('present_table', ['price_weights', 'adj_icu'])
def test_installed_route_requires_price_weights_and_icu_adjustment(tmp_path, monkeypatch, present_table):
    from icu_liaison.adapters.p8_mchs import mchs_reference_sha256

    (tmp_path / f'nep25_aa_{present_table}.sas7bdat').write_bytes(b'fictional reference bytes')
    _install_fictional_mchs(tmp_path, monkeypatch, '''
AcuteParams = object

def calculate_acute(rows, _params, **kwargs):
    return [{'NWAU25': '1.0', 'Error_Code': 0}]
''')
    case = example(source_bundle_sha256=mchs_reference_sha256(tmp_path))

    with pytest.raises(ValueError, match='price weights and ICU adjustment'):
        run_mchs_pair(case, ref_dir=str(tmp_path))


def test_reader_preserves_exact_delta_at_the_supported_precision():
    expected = '1.123456789012345678901234567891'
    outputs = iter(([{'NWAU25': '0', 'Error_Code': 0}], [{'NWAU25': expected, 'Error_Code': 0}]))
    result = run_mchs_pair(example(), provider=lambda *_a, **_k: next(outputs))
    assert result['change_nwau'] == expected


def test_reference_fingerprint_rejects_linked_tables(tmp_path):
    from icu_liaison.adapters.p8_mchs import mchs_reference_sha256

    table = tmp_path / 'table.txt'
    table.write_bytes(b'fictional reference bytes')
    (tmp_path / 'nep25_aa_price_weights.sas7bdat').symlink_to(table)
    with pytest.raises(ValueError, match='regular files'):
        mchs_reference_sha256(tmp_path)


def test_provider_output_requires_single_complete_row_and_keeps_comparator_copy():
    calls=[]
    with pytest.raises(ValueError,match='MCHS'):
        run_mchs_pair(example(),provider=lambda *a,**k:[{'NWAU25':'1','Error_Code':0}]*2)
    s=example()
    run_mchs_pair(s,provider=stub_calculator(calls))
    assert s.icu_hours_current == Decimal('58.25')
    assert s.icu_hours_intervention == Decimal('54.25')
