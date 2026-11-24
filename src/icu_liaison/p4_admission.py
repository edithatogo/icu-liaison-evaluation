"""P4 preflight for the P2 clinical contract and P3 source metadata.

The pooled ANZICS benchmark serves as an external proxy. Independent
publisher-source admission and local CHHHS validation remain open.
"""
from __future__ import annotations
import hashlib
import json
from typing import Any

from .p4_model import EconomicScenario, REQUIRED_SAFETY
from .protocol import EvaluationProtocol
from .public_evidence import Catalogue, reconcile_catalogue, select_external_benchmark


def admit_p4(scenario: EconomicScenario, protocol: dict, catalogue: dict, register: dict) -> dict[str, Any]:
    s = EconomicScenario.model_validate(scenario.model_dump(mode='json'))
    if any(prior.evidence_status == 'local_aggregate_unvalidated' for prior in s.all_priors().values()):
        raise ValueError('local aggregate priors cannot enter a fictional P4 run')
    p = EvaluationProtocol.model_validate(protocol)
    benchmarks = reconcile_catalogue(Catalogue.model_validate(catalogue), register)
    rate = select_external_benchmark(benchmarks, 'CCR_2024_25_EXIT_BLOCK')
    reference = p.reference_benchmark
    if (s.currency != p.economics.currency or s.price_year != p.economics.price_year):
        raise ValueError('P4/P2 price year or currency mismatch')
    if s.horizon_months != p.economics.evaluation_horizon_months:
        raise ValueError('P4/P2 evaluation horizon mismatch')
    if set(s.safety.required_outcomes) != REQUIRED_SAFETY or set(s.safety.required_outcomes) != set(p.safety.required_endpoints):
        raise ValueError('P4/P2 safety endpoint mismatch')
    if s.safety.assessment_status != p.safety.measurements_status or p.status != 'draft_unapproved':
        raise ValueError('clinical safety not admitted')
    if {arm.id for arm in s.strategies[:2]} != {x.id for x in p.strategies} or s.strategies[1].id != 'liaison_service':
        raise ValueError('P4 primary comparator is not the P2 service definition')
    prior = s.baseline.exit_block_rate
    if (prior.evidence_status != 'public_proxy'
        or prior.source_ref != rate['id']
        or prior.nominal() != rate['value']
        or reference.value != rate['value']
        or reference.unit != rate['unit']
        or reference.source_id != rate['source_id']):
        raise ValueError('public proxy benchmark conflicts with P2/P3 evidence')
    if reference.period != rate['period']:
        raise ValueError('P4/P2 benchmark reporting period conflicts with P3 evidence')
    source = next((x for x in register['sources'] if x['id'] == rate['source_id']), None)
    if not source or source.get('url') != reference.url:
        raise ValueError('public proxy publisher source URL mismatch')
    if s.annual_volume_provenance.strip() == '':
        raise ValueError('local annual volume source undefined')
    digest = hashlib.sha256(json.dumps({
        'protocol': p.model_dump(mode='json'), 'catalogue': benchmarks, 'source_registry': register,
    },sort_keys=True,separators=(',', ':')).encode()).hexdigest()
    return {
        'admission': 'illustrative_only',
        'model_contract': 'P4-1',
        'protocol_id': p.protocol_id,
        'benchmark_id': rate['id'],
        'benchmark_rate': rate['value'],
        'benchmark_denominator': rate['denominator_key'],
        'source_status': rate['verification_status'],
        'document_verified': rate['verification_status'] == 'document_hash_attested_and_substantively_reviewed',
        'local_CHHHS_inputs_verified': False,
        'clinical_safety_approved': False,
        'economic_investment_ready': False,
        'evidence_digest_sha256': digest,
    }
