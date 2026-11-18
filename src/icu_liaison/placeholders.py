"""P7: explicit replacement-gated placeholders for portable ICU liaison evaluation.

This orchestrates existing P3/P4/P5/P6 code; it is not a new valuation,
statistical, patient-flow, readmission, or clinical approval engine. No locally
restricted rows or assertion of observed CHHHS effects may be published here.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

REQUIRED_IDS = frozenset({
    'anzics_primary_pdf', 'local_icu_episodes', 'local_followup',
    'local_liaison_activity', 'local_patient_costing', 'clinical_safety_outcomes',
    'current_service_workforce', 'proposed_service_workforce',
    'eligible_annual_volume', 'local_exit_block_rate',
    'local_unplanned_72h_return', 'addressable_delay_share',
    'hours_released_per_improvement', 'causal_delay_success',
    'causal_return_effect', 'incremental_service_cost',
    'marginal_index_icu_cost', 'incremental_readmission_cost',
    'usable_capacity_fraction', 'cash_realisability_fraction',
    'local_case_mix', 'ward_staffed_capacity', 'icu_staffed_capacity',
    'icu_request_demand', 'holdout_wait_observations',
    'native_kairos_receipt', 'native_dapane_receipt', 'native_voiage_receipt',
    'clinical_safety_approval', 'finance_approval',
    'first_nations_data_governance', 'independent_economic_review',
    'dedicated_repo_ci',
})

EVIDENCE_TYPES = {
    'publisher_document', 'approved_site_extract', 'statistical_estimate',
    'costing_schedule', 'staffing_roster', 'native_execution_receipt',
    'governance_signoff', 'repository_ci',
}


def _valid_relative_artifact(raw: str) -> bool:
    if '\\' in raw or not raw.endswith('.json') or raw.startswith('/'):
        return False
    posix = PurePosixPath(raw)
    return bool(raw and '..' not in posix.parts and '.' not in posix.parts and
                posix.parts and all(x not in ('', '.', '..') for x in posix.parts))


class _Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, strict=True)


class Binding(_Strict):
    artifact: str
    pointer: str = Field(min_length=2)
    shape: Literal[
        'synthetic_scalar', 'synthetic_prior', 'synthetic_array', 'sample_file',
        'unknown', 'unverified_provider', 'unverified_document', 'unmeasured_safety',
    ]
    expected_evidence_status: Literal['public_proxy', 'illustrative_assumption'] | None = None

    @model_validator(mode='after')
    def validate_locator(self) -> 'Binding':
        if not _valid_relative_artifact(self.artifact):
            raise ValueError('binding artifact must be a safe relative JSON path')
        if not self.pointer.startswith('/') or not all(x for x in self.pointer[1:].split('/')):
            raise ValueError('binding pointer must be a nonempty JSON pointer')
        if self.shape == 'synthetic_prior' and self.expected_evidence_status is None:
            raise ValueError('placeholder prior requires explicit evidence status')
        if self.shape != 'synthetic_prior' and self.expected_evidence_status is not None:
            raise ValueError('non-prior placeholder cannot declare prior status')
        return self


class Replacement(_Strict):
    evidence_type: Literal[
        'publisher_document', 'approved_site_extract', 'statistical_estimate',
        'costing_schedule', 'staffing_roster', 'native_execution_receipt',
        'governance_signoff', 'repository_ci',
    ]
    requirements: list[str] = Field(min_length=2)


class Placeholder(_Strict):
    id: str = Field(pattern=r'^[a-z][a-z0-9_]{2,80}$')
    track: Literal['P0', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6']
    kind: str = Field(min_length=1)
    status: Literal['placeholder']
    source_class: Literal['synthetic', 'missing', 'unverified_public_metadata']
    binding: Binding
    prospective_source: str = Field(min_length=1)
    owner_role: str = Field(min_length=1)
    replacement: Replacement
    blocks: list[str] = Field(min_length=1)

    @model_validator(mode='after')
    def no_fake_evidence_promotion(self) -> 'Placeholder':
        if self.kind != self.replacement.evidence_type:
            raise ValueError('replacement type differs from source placeholder kind')
        if self.kind not in EVIDENCE_TYPES:
            raise ValueError('unsupported placeholder evidence kind')
        if self.source_class == 'missing' and self.binding.shape not in {'unknown', 'unverified_provider'}:
            raise ValueError('missing must have an unknown or unverified-provider binding')
        if self.source_class == 'unverified_public_metadata' and self.binding.shape != 'unverified_document':
            raise ValueError('unverified public claim needs documentary binding')
        if len(set(self.blocks)) != len(self.blocks) or any(not x.strip() for x in self.blocks):
            raise ValueError('duplicate/blank external approval gate')
        return self


class PlaceholderRegistry(_Strict):
    schema_version: Literal[1]
    project_id: Literal['icu-liaison-evaluation']
    policy: Literal['synthetic_development_only_never_site_approved']
    scope: str = Field(min_length=1)
    entries: list[Placeholder] = Field(min_length=len(REQUIRED_IDS))

    @model_validator(mode='after')
    def all_required_independent_evidence(self) -> 'PlaceholderRegistry':
        ids = [x.id for x in self.entries]
        if len(ids) != len(set(ids)) or set(ids) != REQUIRED_IDS:
            raise ValueError('placeholder register must include each required unresolved evidence ID')
        sources = [(x.binding.artifact, x.binding.pointer) for x in self.entries]
        if len(sources) != len(set(sources)):
            raise ValueError('placeholder bindings must not collide')
        return self


class Candidate(_Strict):
    id: str
    evidence_type: str
    artifact_path: str = Field(min_length=1)
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    source_custodian_role: str = Field(min_length=1)
    approval_reference: str = Field(min_length=1)


class CandidateEnvelope(_Strict):
    schema_version: Literal[1]
    status: Literal['candidates_for_independent_review']
    entries: list[Candidate] = Field(min_length=1)


def load_registry(path: Path) -> PlaceholderRegistry:
    source = Path(path)
    if source.is_symlink() or not source.is_file() or source.stat().st_size > 256_000:
        raise ValueError('missing/oversized/symlinked placeholder register')
    return PlaceholderRegistry.model_validate_json(source.read_text(encoding='utf-8'))


def _public_artifact(root: Path, relative_path: str) -> Path:
    if not _valid_relative_artifact(relative_path):
        raise ValueError('invalid binding source artifact path')
    file = root / relative_path
    if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(root.resolve()):
        raise ValueError('missing, symlinked or escaped source artifact for placeholder binding')
    if file.stat().st_size > 1_000_000:
        raise ValueError('oversized placeholder source artifact')
    return file


def _json_pointer(doc: object, pointer: str) -> object:
    current = doc
    for token in pointer.lstrip('/').split('/'):
        if '~' in token and re.search(r'~(?![01])', token):
            raise ValueError('malformed JSON pointer binding')
        part = token.replace('~1', '/').replace('~0', '~')
        try:
            if isinstance(current, dict):
                current = current[part]
            elif isinstance(current, list):
                if not part.isdigit() or (len(part) > 1 and part.startswith('0')):
                    raise ValueError('array pointer index invalid')
                current = current[int(part)]
            else:
                raise ValueError('pointer traverses noncontainer')
        except (IndexError, KeyError) as exc:
            raise ValueError('placeholder binding JSON pointer not found') from exc
    return current


def audit_placeholders(registry: PlaceholderRegistry, *, root: Path) -> dict:
    """Validate every source binding, but **never** close an evidence gate."""
    reg = PlaceholderRegistry.model_validate(registry.model_dump(mode='json'))
    root = Path(root)
    digests: dict[str, str] = {}
    for entry in reg.entries:
        name = entry.binding.artifact
        source = _public_artifact(root, name)
        raw = source.read_bytes()
        digests[name] = hashlib.sha256(raw).hexdigest()
        try:
            value = _json_pointer(json.loads(raw), entry.binding.pointer)
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError('invalid placeholder binding or source JSON') from exc
        shape = entry.binding.shape
        if shape == 'unknown' and value is not None:
            raise ValueError(f'{entry.id}: missing placeholder value was populated without review')
        if shape == 'unverified_provider' and value is not None:
            raise ValueError(f'{entry.id}: native provider receipt must be qualified independently')
        if shape == 'unverified_document' and value != 'publisher_pdf_sha256_unavailable':
            raise ValueError(f'{entry.id}: publisher document requires independent admission')
        if shape == 'unmeasured_safety' and value != 'unmeasured':
            raise ValueError(f'{entry.id}: safety outcome status cannot be self-promoted')
        if shape == 'synthetic_scalar' and (isinstance(value, bool) or not isinstance(value, (int, float))):
            raise ValueError(f'{entry.id}: expected a synthetic scalar')
        if shape == 'synthetic_array' and (not isinstance(value, list) or not value):
            raise ValueError(f'{entry.id}: expected nonempty synthetic array')
        if shape == 'synthetic_prior':
            if not isinstance(value, dict) or value.get('evidence_status') != entry.binding.expected_evidence_status:
                raise ValueError(f'{entry.id}: placeholder prior lost its original evidence status')
            if not value.get('source_ref'):
                raise ValueError(f'{entry.id}: placeholder prior missing source trace')
        if shape == 'sample_file':
            if not isinstance(value, dict) or not isinstance(value.get('path'), str):
                raise ValueError(f'{entry.id}: synthetic feed binding must name a file')
            source_dir = source.parent
            reference = value['path']
            if Path(reference).is_absolute() or '..' in Path(reference).parts or '\\' in reference:
                raise ValueError(f'{entry.id}: source fixture path escaped')
            feed = source_dir / reference
            if feed.is_symlink() or not feed.is_file() or not feed.resolve().is_relative_to(source_dir.resolve()):
                raise ValueError(f'{entry.id}: source fixture is missing or escaped')
            if hashlib.sha256(feed.read_bytes()).hexdigest() != value.get('sha256'):
                raise ValueError(f'{entry.id}: source fixture digest mismatch')

    gates = sorted({gate for entry in reg.entries for gate in entry.blocks})
    return {
        'schema_version': 1,
        'status': 'development_placeholders_only',
        'source_bindings_verified': len(reg.entries),
        'source_artifact_sha256': dict(sorted(digests.items())),
        'placeholder_count_by_track': dict(sorted(Counter(x.track for x in reg.entries).items())),
        'unresolved_count': len(reg.entries),
        'unresolved_ids': sorted(x.id for x in reg.entries),
        'external_gates_pending': gates,
        'observed_CHHHS_data_used': False,
        'native_providers_qualified': False,
        'clinical_safety_approved': False,
        'finance_approved': False,
        'investment_ready': False,
        'interpretation': 'reviewable_development_scaffold_not_observed_inputs_or_approval',
    }


def inspect_replacement_candidates(
    envelope: Mapping, registry: PlaceholderRegistry, *, project_root: Path
) -> dict:
    """Hash-check private evidence candidates, but never confer clinical approval.

    Even all 33 hash matches cannot satisfy a clinical, privacy, causal or
    financial review. This function intentionally returns every gate open.
    """
    body = CandidateEnvelope.model_validate(envelope)
    reg = PlaceholderRegistry.model_validate(registry.model_dump(mode='json'))
    known = {x.id: x for x in reg.entries}
    if len({x.id for x in body.entries}) != len(body.entries):
        raise ValueError('duplicate evidence candidate')
    for item in body.entries:
        entry = known.get(item.id)
        if entry is None or item.evidence_type != entry.replacement.evidence_type:
            raise ValueError('unknown or mismatched evidence candidate')
        artifact = Path(item.artifact_path)
        if not artifact.is_absolute() or not artifact.is_file() or artifact.is_symlink():
            raise ValueError('evidence candidate must be an existing private regular file')
        if artifact.stat().st_size > 100 * 1024 * 1024:
            raise ValueError('candidate evidence file is too large')
        root = Path(project_root).resolve()
        resolved = artifact.resolve()
        if resolved.is_relative_to(root):
            sub = resolved.relative_to(root)
            if not (sub.parts and sub.parts[0] in {'.local', 'private'}):
                raise ValueError('evidence candidates must remain in private storage')
        if hashlib.sha256(artifact.read_bytes()).hexdigest() != item.sha256:
            raise ValueError('candidate digest did not match verified bytes')

    return {
        'schema_version': 1,
        'status': 'candidate_hashes_checked_not_evidence_admitted',
        'candidate_hashes_matched': len(body.entries),
        'candidate_ids': sorted(item.id for item in body.entries),
        'independently_approved': False,
        'unresolved_count': len(reg.entries),
        'clinical_validation': False,
        'investment_ready': False,
        'note': 'Caller claims and file digests do not establish truth, site authority or causal validity.',
    }


def _json_write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')


def verify_progress_manifest(directory: Path) -> bool:
    """Verify every published file except the manifest itself, without trusting paths."""
    root = Path(directory)
    manifest_file = root / 'manifest.json'
    if manifest_file.is_symlink() or not manifest_file.is_file():
        raise ValueError('missing or unsafe progress manifest')
    manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
    if (manifest.get('schema_version') != 1 or manifest.get('data_class') != 'synthetic'
            or manifest.get('investment_ready') is not False):
        raise ValueError('invalid progress publication status')
    expected = manifest.get('files_sha256')
    if not isinstance(expected, dict):
        raise ValueError('invalid progress file inventory')
    found = {
        p.relative_to(root).as_posix(): p
        for p in root.rglob('*') if p.is_file() and p != manifest_file
    }
    if set(expected) != set(found):
        raise ValueError('missing/extra file in progress report')
    for name, path in found.items():
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('symlink or escaped progress report')
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected[name]:
            raise ValueError('progress report file hash drift')
    return True


def build_synthetic_progress_bundle(*, root: Path, registry_path: Path, output_dir: Path) -> dict:
    """Generate synthetic QA + P4/P5 economic + P6 trace/holdout receipts.

    All computational engines are imported from the existing tracks. Publication
    is fail-closed and atomic; outputs carry explicit source and qualification
    limitations, not local site calibration or actual provider execution.
    """
    from .local_data import load_and_audit
    from .p4_model import EconomicScenario
    from .p5_reporting import build_report, review_report
    from .p6_capacity import TraceBundle, audit_trace_bundle
    from .p6_holdout import HoldoutBundle, compare_holdout, gate_readiness
    from .p6_native import check_native_binary_capability, KairosScenario

    root = Path(root)
    destination = Path(output_dir)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('refuse to overwrite existing synthetic progress output')
    registry = load_registry(registry_path)
    registered = audit_placeholders(registry, root=root)

    clinical = load_and_audit(
        root / 'model-inputs/placeholders/p3-synthetic/manifest.json',
        data_dictionary_path=root / 'model-inputs/clinical-data-dictionary.json',
    )
    if clinical['data_class'] != 'synthetic' or clinical['investment_ready'] is not False:
        raise ValueError('P3 placeholder workflow accepts only synthetic clinical fixtures')
    scenario = EconomicScenario.model_validate_json(
        _public_artifact(root, 'model-inputs/p4/illustrative.json').read_text(encoding='utf-8')
    )
    trace = audit_trace_bundle(TraceBundle.model_validate_json(
        _public_artifact(root, 'model-inputs/p6/synthetic-trace.json').read_text(encoding='utf-8')
    ))
    holdout = compare_holdout(HoldoutBundle.model_validate_json(
        _public_artifact(root, 'model-inputs/p6/synthetic-holdout.json').read_text(encoding='utf-8')
    ))
    KairosScenario.model_validate_json(
        _public_artifact(root, 'model-inputs/p6/kairos-synthetic-input.json').read_text(encoding='utf-8')
    )
    native_capability = check_native_binary_capability(root/'native/kairos-icu-liaison')
    if trace['status'] != 'synthetic_trace_admitted_not_a_DES_run':
        raise ValueError('P6 fixture cannot claim native execution')
    if holdout['local_CHHHS_data_used'] is not False:
        raise ValueError('P6 holdout cannot claim observed site data')

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.icu-liaison-placeholder-', dir=destination.parent) as temp:
        staging = Path(temp) / 'bundle'
        staging.mkdir()
        report = build_report(
            scenario, staging/'p5-report',
            protocol=root/'model-inputs/clinical-economic-protocol.json',
            catalogue=root/'model-inputs/anzics-benchmarks.json',
            source_register=root/'conductor/evidence/source-register.json',
            voiage_mode='skip',dapane_mode='skip',plots=False,
        )
        reviewed = review_report(staging/'p5-report')
        model = json.loads((staging/'p5-report/model-summary.json').read_text(encoding='utf-8'))
        if model.get('investment_ready') is not False or reviewed.get('provider_qualification') is not False:
            raise ValueError('P5 model cannot be promoted into an accepted site finding')
        progress = {
            'schema_version': 1,
            'status': 'synthetic_progress_complete_external_gates_open',
            'data_class': 'synthetic',
            'placeholders': registered,
            'p3': clinical,
            'p4': model,
            'p5': {'status': report['status'], 'independent_report_consumer': reviewed},
            'p6': {
                'trace': trace,
                'holdout': holdout,
                'readiness': gate_readiness({}),
                'native_source_capability': native_capability,
            },
            'native_kairos_executed': False,
            'native_dapane_executed': False,
            'native_voiage_executed': False,
            'observed_CHHHS_data_used': False,
            'investment_ready': False,
        }
        _json_write(staging/'progress.json', progress)
        with (staging/'replacement-checklist.csv').open('w',newline='',encoding='utf-8') as stream:
            writer = csv.writer(stream)
            writer.writerow(['id','track','owner_role','prospective_source','replacement_type',
                             'acceptance_criteria','blocking_gates','status'])
            for e in registry.entries:
                writer.writerow([e.id,e.track,e.owner_role,e.prospective_source,
                    e.replacement.evidence_type,'; '.join(e.replacement.requirements),
                    '; '.join(e.blocks),'UNRESOLVED_PLACEHOLDER'])
        manifest = {
            'schema_version':1,
            'data_class':'synthetic',
            'status':'portable_dry_run_only',
            'investment_ready':False,
            'files_sha256':{
                p.relative_to(staging).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(staging.rglob('*')) if p.is_file()
            },
        }
        _json_write(staging/'manifest.json', manifest)
        verify_progress_manifest(staging)
        if destination.exists() or destination.is_symlink():
            raise FileExistsError('output appeared while synthetic progress was building')
        staging.rename(destination)
    return {
        'status':'synthetic_progress_complete_external_gates_open',
        'output_directory':str(destination),
        'unresolved_count':len(registry.entries),
        'manifest_verified':verify_progress_manifest(destination),
        'native_kairos_executed':False,
        'investment_ready':False,
    }
