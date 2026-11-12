"""Auditable single-account consumer gateway; not an OS security boundary."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import sys
import uuid

from campaign import digest, encoded, exclusive, file_hash, now, read, record

MODE = 'runner-workflow-v1'


def software_identity() -> str:
    return digest(encoded({name: file_hash(Path(__file__).with_name(name))
                           for name in ['workflow_access.py', 'admission.py', 'campaign.py']}))


class Denied(ValueError):
    def __init__(self, reason: str, event_id: str):
        super().__init__(reason)
        self.event_id = event_id


def registration(root: Path, export_id: str | None = None) -> tuple[dict[str, Any], str]:
    entries = list((root / 'exports').glob('*.json'))
    if export_id is not None:
        entries = [p for p in entries if p.stem == export_id]
    if len(entries) != 1:
        raise ValueError('Exactly one approved export reference required; specify --export-id')
    path = entries[0]
    value = read(path)
    if file_hash(path) != path.stem or value['schema'] != 'astrago-consumer-registration-v1' or value['isolation'] != MODE:
        raise ValueError('Consumer registration integrity mismatch')
    manifest = read(root / 'manifest.json')
    if manifest.get('schema') != 'astrago-admission-v2' or manifest.get('isolation') != MODE:
        raise ValueError('Explicit workflow admission v2 manifest required; legacy OS evidence is not migrated')
    if value['manifest_sha256'] != file_hash(root / 'manifest.json') or value['references'] != ['training', 'development']:
        raise ValueError('Consumer registration is stale or has forbidden references')
    return value, path.stem


def register_export(root: Path, bundle: Path, artifact_hash: str) -> str:
    from admission import check_public
    payload = check_public(read(bundle))
    if file_hash(root / 'artifacts' / (artifact_hash + '.json')) != artifact_hash:
        raise ValueError('Cannot register an unretained admission artifact')
    value = {'schema': 'astrago-consumer-registration-v1', 'isolation': MODE,
             'manifest_sha256': file_hash(root / 'manifest.json'),
             'bundle_path': str(bundle.resolve()), 'bundle_sha256': file_hash(bundle),
             'payload_sha256': read(bundle)['sha256'], 'artifact_sha256': artifact_hash,
             'references': ['training', 'development']}
    if payload['private_artifact_sha256'] != artifact_hash:
        raise ValueError('Export admission identity mismatch')
    return record(root, 'exports', value).stem


def consume(root: Path, split: str, *, export_id: str | None = None,
            bundle_path: Path | None = None, purpose: str = 'debugging',
            arm: str | None = None, arm_state: Path | None = None,
            candidate_ids: list[str] | None = None) -> dict[str, Any]:
    from admission import check_public
    event: dict[str, Any] = {'schema': 'astrago-workflow-access-event-v1',
        'request_id': uuid.uuid4().hex, 'timestamp_utc': now(), 'isolation': MODE,
        'reference': split, 'purpose': purpose, 'arm': arm,
        'requested_ids': candidate_ids or [],
        'supplied_path': str(bundle_path) if bundle_path else None,
        'arm_state': str(arm_state) if arm_state else None,
        'software_sha256': software_identity(), 'decision': 'deny'}
    rows = []
    try:
        approved, selected_id = registration(root, export_id)
        event['registration_sha256'] = selected_id
        if bundle_path is not None:
            raise ValueError('Path inputs are forbidden; use an approved training/development reference')
        if arm_state is not None:
            raise ValueError('Arm-state references are unsupported at this data-only boundary')
        if purpose not in ['training', 'selection', 'debugging', 'tuning']:
            raise ValueError('Evaluator access denied: final model/configuration freeze is not implemented')
        if split not in approved['references']:
            raise ValueError('Sealed or unknown reference denied')
        path = Path(approved['bundle_path'])
        if file_hash(path) != approved['bundle_sha256']:
            raise ValueError('Registered export bytes changed')
        bundle = read(path)
        payload = check_public(bundle)
        if bundle['sha256'] != approved['payload_sha256'] or payload['private_artifact_sha256'] != approved['artifact_sha256']:
            raise ValueError('Registered export identities changed')
        rows = [row for row in payload['candidates'] if row['split'] == split]
        if candidate_ids:
            requested = set(candidate_ids)
            if not requested <= {row['id'] for row in rows}:
                raise ValueError('Sealed, unknown, or wrong-split candidate ID denied')
            rows = [row for row in rows if row['id'] in requested]
        event.update(decision='allow', bundle_sha256=approved['bundle_sha256'], count=len(rows))
    except (ValueError, OSError, KeyError, TypeError) as error:
        event['reason'] = str(error)
    # Immutable records can be snapshotted without later reads modifying them.
    audit = record(root, 'access', event)
    if event['decision'] != 'allow':
        raise Denied(event.get('reason', 'Access denied'), audit.stem)
    return {'candidates': rows, 'access_record_sha256': audit.stem,
            'isolation': MODE, 'os_unreadability': False, 'runtime_executed': False}


def probe(root: Path, output: Path, export_id: str | None = None) -> dict[str, Any]:
    approved, selected = registration(root, export_id)
    payload = read(Path(approved['bundle_path']))['payload']
    sealed = payload['sealed_candidate_ids']
    attempts: list[tuple[str, dict[str, Any], bool]] = [
        ('training', {'split': 'training'}, True),
        ('development', {'split': 'development'}, True),
        ('sealed_reference', {'split': 'sealed'}, False),
        ('raw_source_path', {'split': 'training', 'bundle_path': root / 'records.json'}, False),
        ('all_source_path', {'split': 'training', 'bundle_path': root / 'inventory.json'}, False),
        ('evaluation', {'split': 'sealed', 'purpose': 'evaluation'}, False),
        ('foreign_arm_state', {'split': 'training', 'arm': 'A', 'arm_state': root / 'B/state.json'}, False)]
    if sealed:
        attempts.append(('sealed_id', {'split': 'training', 'candidate_ids': [sealed[0]]}, False))
    results = []
    for name, kwargs, expected in attempts:
        try:
            response = consume(root, export_id=selected, **kwargs)
            allowed, event_id = True, response['access_record_sha256']
        except Denied as error:
            allowed, event_id = False, error.event_id
        results.append({'case': name, 'expected_allow': expected, 'actual_allow': allowed, 'event_sha256': event_id})
    value = {'schema': 'astrago-workflow-access-receipt-v1', 'isolation': MODE,
             'status': 'pass' if all(row['expected_allow'] == row['actual_allow'] for row in results) else 'fail',
             'registration_sha256': selected, 'results': results, 'os_unreadability': False,
             'software_sha256': software_identity(), 'timestamp_utc': now(),
             'command': [sys.executable, *sys.argv]}
    exclusive(output, encoded(value))
    return value


def validate_receipt(root: Path, value: dict[str, Any], check_current: bool = True) -> None:
    if value.get('schema') != 'astrago-workflow-access-receipt-v1' or value.get('status') != 'pass' or value.get('os_unreadability') is not False:
        raise ValueError('Passing workflow receipt required; OS receipts cannot be reclassified')
    approved, _ = registration(root, value['registration_sha256'])
    if check_current and value['software_sha256'] != software_identity():
        raise ValueError('Fresh workflow probe required after software revision')
    sealed = read(Path(approved['bundle_path']))['payload']['sealed_candidate_ids']
    required = {'training', 'development', 'sealed_reference', 'raw_source_path', 'all_source_path', 'evaluation', 'foreign_arm_state'}
    if sealed:
        required.add('sealed_id')
    if not required <= {row['case'] for row in value['results']}:
        raise ValueError('Incomplete workflow access probes')
    expected_cases = {'training': True, 'development': True, 'sealed_reference': False,
                      'raw_source_path': False, 'all_source_path': False, 'evaluation': False,
                      'foreign_arm_state': False, 'sealed_id': False}
    if len({r['case'] for r in value['results']}) != len(value['results']):
        raise ValueError('Repeated workflow probe case')
    for row in value['results']:
        if row['case'] not in expected_cases or row['expected_allow'] != expected_cases[row['case']]:
            raise ValueError('Incorrect expected workflow access outcome')
        path = root / 'access' / (row['event_sha256'] + '.json')
        event = read(path)
        if file_hash(path) != path.stem or event['registration_sha256'] != value['registration_sha256'] or event['software_sha256'] != value['software_sha256']:
            raise ValueError('Workflow access evidence identity mismatch')
        if (event['decision'] == 'allow') != row['actual_allow'] or row['actual_allow'] != row['expected_allow']:
            raise ValueError('Workflow access result mismatch')

        expected_requests = {
            'training': ('training', 'debugging', None, None, None, []),
            'development': ('development', 'debugging', None, None, None, []),
            'sealed_reference': ('sealed', 'debugging', None, None, None, []),
            'raw_source_path': ('training', 'debugging', None, str(root / 'records.json'), None, []),
            'all_source_path': ('training', 'debugging', None, str(root / 'inventory.json'), None, []),
            'evaluation': ('sealed', 'evaluation', None, None, None, []),
            'foreign_arm_state': ('training', 'debugging', 'A', None, str(root / 'B/state.json'), []),
            'sealed_id': ('training', 'debugging', None, None, None, sealed[:1]),
        }
        actual_request = tuple(event.get(key) for key in
                               ['reference', 'purpose', 'arm', 'supplied_path', 'arm_state', 'requested_ids'])
        if actual_request != expected_requests[row['case']]:
            raise ValueError('Workflow probe request mismatch')
