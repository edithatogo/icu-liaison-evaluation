"""P3 public ANZICS source reconciliation, not authentication of report bytes.

A curated source register can check internal transcriptions, denominators and
scenario bindings; only a signed/independently verified source snapshot could
justify claiming that external PDF content was authenticated.
"""
from __future__ import annotations

from collections.abc import Mapping
from math import isfinite, isclose

ANZICS_CCR = 'ANZICS-CCR-2024-25'
ANZICS_APD = 'ANZICS-CORE-2024'
KNOWN_CC_DELAY = 'live_ward_home_discharge_delay_ge12h'
RESTRICTED_MODEL_ROLES = {'local_CHHHS_rate', 'unplanned_72h_return',
                          'incremental_cost_per_readmission_aud', 'net_avoidable_cost_per_icu_day_aud'}


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_public_benchmarks(register: Mapping, contract: Mapping, protocol: Mapping) -> dict:
    """Validate all ten locked public aggregate rows and declared denominator roles.

    This detects drift between the P2 source register, P3 external benchmark
    contract and P2 protocol; it does NOT claim to re-extract a publisher PDF.
    """
    _check(register.get('schema_version') == contract.get('schema_version') == 1,
           'public source schema version mismatch')
    _check(contract.get('data_class') == 'public_aggregated_only',
           'public source data class mismatch')
    doc = contract.get('document_verification', {})
    _check(doc.get('status') == 'publisher_pdf_sha256_unavailable' and
           doc.get('publisher_file_sha256') is None, 'document_verification: unsupported authentication claim')
    sources = register.get('sources', [])
    _check(isinstance(sources, list) and all(isinstance(x, dict) for x in sources),
           'public source list invalid')
    ids = [s.get('id') for s in sources]
    _check(len(ids) == len(set(ids)), 'duplicate public source ID')
    by_source = {s['id']: s for s in sources}
    _check(ANZICS_CCR in by_source and ANZICS_APD in by_source,
           'required public source not in source register')
    _check('2024/25' in by_source[ANZICS_CCR]['title'] and
           by_source[ANZICS_CCR].get('period') == '2024-07-01/2025-06-30',
           'CCR source report/period mismatch')
    _check(by_source[ANZICS_APD].get('data_period') == '2023/24',
           'APD source report/period mismatch')

    observations = contract.get('observations', [])
    _check(isinstance(observations, list) and len(observations) == 10,
           'public source observations must include exactly 10 locked metrics')
    pairs = [(row.get('source_id'), row.get('name')) for row in observations]
    _check(len(pairs) == len(set(pairs)), 'duplicate public outcome declaration')
    _check(set(contract.get('forbidden_uses', [])) == RESTRICTED_MODEL_ROLES,
           'public source forbidden local uses modified')
    checked = 0
    for item in observations:
        srcid = item.get('source_id')
        _check(srcid in (ANZICS_CCR, ANZICS_APD), 'unexpected source identity')
        registered = next((x for x in by_source[srcid].get('outcomes', [])
                           if x.get('name') == item.get('name')), None)
        _check(registered is not None, 'public source metric not found')
        for key in ('unit', 'denominator', 'page', 'contributors'):
            if key in item or key in registered:
                _check(item.get(key) == registered.get(key), f'public source {key} mismatch')
        val = item.get('value')
        _check(type(val) in (int, float) and isfinite(val) and
               type(registered.get('value')) in (int, float) and
               isclose(val, registered['value'], abs_tol=0, rel_tol=0),
               'public source value mismatch')
        expected_pop = ('binational_all_age_mixed' if srcid == ANZICS_CCR else 'australia_adult')
        _check(item.get('population') == expected_pop, 'public source population mismatch')
        expected_use = ('illustrative_exit_block_proxy' if srcid == ANZICS_CCR and
                        item['name'] == KNOWN_CC_DELAY else 'external_context_only')
        _check(item.get('local_use') == expected_use, 'local_use/denominator incompatible with public source')
        if item.get('unit') == 'proportion':
            _check(0 <= val <= 1, 'invalid public proportion')
        checked += 1
    _check(set(pairs) == {(srcid, x['name']) for srcid in (ANZICS_CCR, ANZICS_APD)
                          for x in by_source[srcid].get('outcomes', [])},
           'public source outcome coverage differs from register')
    anchor = next(x for x in observations if x['source_id'] == ANZICS_CCR and
                  x['name'] == KNOWN_CC_DELAY)
    _check(anchor['value'] == 0.204 and anchor['unit'] == 'proportion' and
           anchor['contributors'] == 162 and anchor['denominator'] == 'live ward/home discharges',
           'public source CCR delay anchor mismatch')
    p = protocol.get('reference_benchmark', {})
    _check(p.get('value') == anchor['value'] and
           p.get('source_id') == ANZICS_CCR and
           p.get('measure') == 'exit_block_ge12h' and
           p.get('unit') == anchor['unit'] and
           p.get('denominator') == 'all_live_ward_home_discharges' and
           p.get('url') == by_source[ANZICS_CCR]['url'],
           'protocol public benchmark does not match source anchor')
    _check(protocol.get('external_benchmark_role') == 'external_comparator_not_CHHHS_observed',
           'protocol permits misleading site inference')
    return {
        'status': 'PUBLIC_TRANSCRIPTION_RECONCILED_NOT_DOCUMENT_AUTHENTICATED',
        'checked_observations': checked,
        'source_ids': [ANZICS_CCR, ANZICS_APD],
        'local_72h_readmission_available': False,
        'local_cost_per_icu_day_available': False,
        'cairns_rates_verified': False,
        'discharge_delay_public_proxy': {'value': 0.204, 'denominator': 'live ward/home discharges',
                                         'population': 'mixed_reporting_units', 'year': '2024/25'},
        'publisher_document_sha256_available': False,
        'caveat': 'Versioned transcription concordance only; report PDF bytes have not been authenticated.',
    }
