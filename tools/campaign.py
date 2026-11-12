#!/usr/bin/env python3
"""Audited first campaign slice. Run on the training role; transport stays private."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import tempfile
from typing import Any

REVISION = 'd91ea855110dae533f0aada947b2b7d78cc8a4e1'
PLAN_HASH = '7d2887926344923e701a197cead61344461edad83ce151e45652547175550b88'
CANDIDATES = ['kata1-tf2-b10c384-s2941M-d5872M',
              'kata1-tf3-b10c512-s3203M-d5937M',
              'kata1-tf3-b11c768-s12382M-d6533M']
RULES = {'ko': 'SIMPLE', 'scoring': 'AREA', 'tax': 'NONE', 'suicide': False,
         'hasButton': False, 'whiteHandicapBonus': 'N', 'friendlyPassOk': True}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def encoded(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def exclusive(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        os.unlink(temporary)


def record(root: Path, kind: str, value: Any) -> Path:
    data = encoded(value)
    path = root / kind / (digest(data) + '.json')
    if not path.exists():
        exclusive(path, data)
    return path


def plan() -> dict[str, Any]:
    return {'schema': 'astrago-native-v1', 'source_revision': REVISION,
            'execution_plan_sha256': PLAN_HASH, 'candidates': CANDIDATES,
            'role': 'training', 'board_size': 19, 'rules': RULES, 'komi': 7.5,
            'handicap': 0, 'scope': 'acquisition-build-native-smoke',
            'complete_game_gate': False, 'm4_deployment_gate': False}


def manifest(root: Path) -> dict[str, Any]:
    value = read(root / 'manifest.json')
    if value != plan():
        raise ValueError('Manifest differs from the adopted native slice')
    h0 = read(root / 'h0.json')
    if h0['manifest_sha256'] != file_hash(root / 'manifest.json'):
        raise ValueError('Manifest identity changed after H0')
    return value


def start(root: Path, source: Path, instruction: str | None) -> dict[str, Any]:
    if not instruction or not instruction.strip():
        raise ValueError('Explicit campaign execution instruction required')
    value = read(source)
    if value != plan():
        raise ValueError('Manifest differs from adopted native slice')
    if (root / 'h0.json').exists():
        manifest(root)
        if (root / 'manifest.json').read_bytes() != encoded(value):
            raise ValueError('Cannot replace manifest or reset H0')
        return read(root / 'h0.json')
    root.mkdir(parents=True, exist_ok=True)
    # A pre-existing partial start is never overwritten or silently recovered.
    exclusive(root / 'manifest.json', encoded(value))
    for name in ['campaign.py', 'native_slice.py', 'checkpoint_audit.py']:
        exclusive(root / 'software' / name, Path(__file__).with_name(name).read_bytes())
    h0 = {'schema': 'astrago-h0-v1', 'timestamp_utc': now(),
          'instruction': instruction, 'manifest_sha256': file_hash(root / 'manifest.json'),
          'runner_sha256': file_hash(root / 'software/campaign.py'),
          'software': {p.name: file_hash(p) for p in (root / 'software').glob('*.py')}}
    exclusive(root / 'h0.json', encoded(h0))
    return h0


def latest_stop(root: Path) -> Path | None:
    return max((root / 'stops').glob('*.json'), key=lambda p: read(p)['timestamp_utc'], default=None)


def retained_record(root: Path, folder: str, identity: str) -> dict[str, Any]:
    if not re.fullmatch(r'[0-9a-f]{64}', identity):
        raise ValueError('Invalid retained record identity')
    path = root / folder / (identity + '.json')
    if file_hash(path) != identity:
        raise ValueError('Retained record identity mismatch: ' + folder)
    return read(path)


def validate_resume(root: Path, path: Path) -> dict[str, Any]:
    value = retained_record(root, 'resumes', path.stem)
    if value['h0_sha256'] != file_hash(root / 'h0.json') or value['manifest_sha256'] != file_hash(root / 'manifest.json'):
        raise ValueError('Setup resume identity mismatch')
    stopped = retained_record(root, 'stops', value['stop_sha256'])
    when = datetime.fromisoformat(value['timestamp_utc'])
    h0 = datetime.fromisoformat(read(root / 'h0.json')['timestamp_utc'])
    if when <= datetime.fromisoformat(stopped['timestamp_utc']) or not 0 <= (when - h0).total_seconds() < 86400:
        raise ValueError('Setup resume outside original stop/H24 bounds')
    if value['schema'] == 'astrago-setup-resume-v1':
        # Preserve the historical receipt, without inventing its missing measurements.
        inventories = [read(p) for p in (root / 'evidence').glob('*.json')
                       if read(p).get('type') == 'coordinator_inventory']
        if not any(digest(encoded(v['inventory'])) == value['coordinator_inventory_sha256'] for v in inventories):
            raise ValueError('Legacy coordinator inventory identity missing')
        if not any(read(p)['software']['campaign.py'] == value['runner_sha256'] for p in (root / 'revisions').glob('*.json')):
            raise ValueError('Legacy resume runner identity missing')
        return {'sha256': path.stem, 'eligibility': 'inconclusive', 'active': False,
                'reason': 'Legacy receipt lacks complete contemporaneous eligibility evidence'}
    if value['schema'] != 'astrago-setup-resume-v2':
        raise ValueError('Unknown setup resume schema')
    capacity = retained_record(root, 'evidence', value['capacity_evidence_sha256'])
    coordinator = capacity['coordinator_inventory']
    if digest(encoded(coordinator)) != value['coordinator_inventory_sha256'] or capacity['coordinator_inventory_sha256'] != value['coordinator_inventory_sha256']:
        raise ValueError('Resume coordinator inventory mismatch')
    checked = datetime.fromisoformat(capacity['timestamp_utc'])
    if checked > when or not math.isclose(value['elapsed_since_h0_seconds'], (checked - h0).total_seconds(), rel_tol=0, abs_tol=1e-6):
        raise ValueError('Resume elapsed-time arithmetic mismatch')
    age = (when - datetime.fromisoformat(coordinator['timestamp_utc'])).total_seconds()
    if coordinator['schema'] != 'astrago-coordinator-inventory-v1' or coordinator['role'] != 'coordinator' or not 0 <= age <= 3600:
        raise ValueError('Resume coordinator evidence is stale or invalid')
    if coordinator['free_bytes'] < 20 * 2**30 or capacity['training_free_bytes'] < 50 * 2**30 or not 0 <= capacity['campaign_bytes'] <= 50 * 2**30:
        raise ValueError('Resume capacity eligibility failed')
    revision = retained_record(root, 'revisions', value['software_record_sha256'])
    if set(revision['software']) != {'campaign.py', 'native_slice.py', 'checkpoint_audit.py'} or digest(encoded(revision['software'])) != revision['revision']:
        raise ValueError('Resume software bundle identity mismatch')
    if revision['software']['campaign.py'] != value['runner_sha256']:
        raise ValueError('Resume runner identity mismatch')
    for name, identity in revision['software'].items():
        if file_hash(root / 'updates' / revision['revision'] / name) != identity:
            raise ValueError('Retained resume software changed')
    reports = [retained_record(root, 'reports', identity) for identity in value['reports']]
    events = [retained_record(root, 'events', identity) for identity in value['events']]
    expected_reports = {p.stem for p in (root / 'reports').glob('*.json') if datetime.fromisoformat(read(p)['ended_utc']) <= when}
    expected_events = {p.stem for p in (root / 'events').glob('*.json') if datetime.fromisoformat(read(p).get('ended_utc', read(p)['started_utc'])) <= when}
    if set(value['reports']) != expected_reports or set(value['events']) != expected_events:
        raise ValueError('Resume eligibility snapshot omitted retained records')
    completed = {(r['operation'], r['started_utc']) for r in reports}
    if any(r['operation'] in ['build', 'smoke'] and r['status'] == 'pass' for r in reports):
        raise ValueError('Resume follows a native pass')
    if physical_cost(events)['unresolved_event_ids'] or any(e.get('phase') == 'operation-start' and (e['operation'], e['started_utc']) not in completed for e in events):
        raise ValueError('Resume contains unresolved work')
    current_stop = latest_stop(root)
    return {'sha256': path.stem, 'eligibility': 'pass',
            'active': current_stop is not None and current_stop.stem == value['stop_sha256']}


def is_stopped(root: Path) -> bool:
    stopped = latest_stop(root)
    if stopped is None:
        return False
    retained_record(root, 'stops', stopped.stem)
    return not any(validate_resume(root, p)['active'] for p in (root / 'resumes').glob('*.json'))


def resume_setup(root: Path, instruction: str, inventory: Path) -> dict[str, Any]:
    manifest(root)
    if not instruction.strip():
        raise ValueError('Continuation instruction required')
    claim = root / 'claims/resume-setup.json'
    exclusive(claim, encoded({'timestamp_utc': now()}))
    try:
        stopped = latest_stop(root)
        if stopped is None or not is_stopped(root):
            raise ValueError('No stopped setup to resume')
        verify(root)
        h0 = read(root / 'h0.json')
        elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(h0['timestamp_utc'])).total_seconds()
        if elapsed < 0 or elapsed >= 24 * 3600:
            raise ValueError('Original H0–24 setup window expired; explicit replan required')
        if any(p != claim for p in (root / 'claims').glob('*.json')):
            raise ValueError('Unresolved operation claim')
        reports = [read(p) for p in (root / 'reports').glob('*.json')]
        if any(r['operation'] in ['build', 'smoke'] and r['status'] == 'pass' for r in reports):
            raise ValueError('Setup resume excludes native passes and downstream recovery')
        events = [read(p) for p in (root / 'events').glob('*.json')]
        completed = {(r['operation'], r['started_utc']) for r in reports}
        if any(e.get('phase') == 'operation-start' and (e['operation'], e['started_utc']) not in completed for e in events):
            raise ValueError('Unresolved operation start')
        if physical_cost(events)['unresolved_event_ids']:
            raise ValueError('Unresolved physical dispatch')
        from native_slice import check_capacity, Unavailable
        try:
            capacity = check_capacity(root, inventory)
        except Unavailable as error:
            raise ValueError(str(error)) from error
        revision = retain_runner(root, 'Retain executing setup-resume verifier and modules')
        elapsed = (datetime.fromisoformat(capacity['timestamp_utc']) - datetime.fromisoformat(h0['timestamp_utc'])).total_seconds()
        if (datetime.now(timezone.utc) - datetime.fromisoformat(h0['timestamp_utc'])).total_seconds() >= 86400:
            raise ValueError('Original H24 window expired during setup validation')
        value = {'schema': 'astrago-setup-resume-v2', 'timestamp_utc': now(),
                 'instruction': instruction, 'stop_sha256': stopped.stem,
                 'h0_sha256': file_hash(root / 'h0.json'),
                 'manifest_sha256': file_hash(root / 'manifest.json'),
                 'coordinator_inventory_sha256': capacity['coordinator_inventory_sha256'],
                 'capacity_evidence_sha256': capacity['record_sha256'],
                 'software_record_sha256': revision['record_sha256'],
                 'reports': sorted(p.stem for p in (root / 'reports').glob('*.json')),
                 'events': sorted(p.stem for p in (root / 'events').glob('*.json')),
                 'elapsed_since_h0_seconds': elapsed,
                 'runner_sha256': file_hash(Path(__file__))}
        path = record(root, 'resumes', value)
        validate_resume(root, path)
        artifact = seal(root)
        return {**value, 'artifact': artifact.relative_to(root).as_posix()}
    finally:
        claim.unlink()


def adopt_runner(root: Path, reason: str) -> dict[str, Any]:
    manifest(root)
    if is_stopped(root):
        raise ValueError('Cannot change a stopped campaign')
    if any(read(p)['status'] == 'pass' and read(p)['operation'] == 'smoke'
           for p in (root / 'reports').glob('*.json')):
        raise ValueError('Runner repair after native smoke pass is not supported')
    if any((root / 'claims').glob('*.json')):
        raise ValueError('Reconcile operation claims before runner repair')
    events = [read(p) for p in (root / 'events').glob('*.json')]
    if physical_cost(events)['unresolved_event_ids']:
        raise ValueError('Reconcile dispatches before runner repair')
    result = retain_runner(root, reason)
    seal(root)
    return result


def retain_runner(root: Path, reason: str) -> dict[str, Any]:
    software = {name: file_hash(Path(__file__).with_name(name))
                for name in ['campaign.py', 'native_slice.py', 'checkpoint_audit.py']}
    revision = digest(encoded(software))
    for name in software:
        target = root / 'updates' / revision / name
        if not target.exists():
            exclusive(target, Path(__file__).with_name(name).read_bytes())
    value = {'timestamp_utc': now(), 'software': software, 'revision': revision,
             'reason': reason, 'h0_sha256': file_hash(root / 'h0.json'),
             'runner': 'updates/' + revision + '/campaign.py'}
    path = record(root, 'revisions', value)
    return {**value, 'record_sha256': path.stem}


def active(root: Path) -> None:
    manifest(root)
    elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(read(root / 'h0.json')['timestamp_utc'])).total_seconds()
    if not 0 <= elapsed < 86400:
        raise ValueError('Original H0–24 setup window expired')
    if is_stopped(root):
        raise ValueError('Campaign stopped; replay evidence instead of restarting')
    revisions = sorted((root / 'revisions').glob('*.json'), key=lambda p: read(p)['timestamp_utc'])
    software = read(revisions[-1])['software'] if revisions else read(root / 'h0.json')['software']
    for name, identity in software.items():
        if file_hash(Path(__file__).with_name(name)) != identity:
            raise ValueError('Runner changed since H0; use retained runner')


def seal(root: Path) -> Path:
    files = {}
    for folder in ['manifest.json', 'h0.json', 'software', 'events', 'reports', 'stops', 'evidence', 'revisions', 'updates', 'resumes']:
        path = root / folder
        for p in ([path] if path.is_file() else sorted(path.rglob('*'))):
            if p.is_file():
                files[p.relative_to(root).as_posix()] = {'sha256': file_hash(p), 'bytes': p.stat().st_size}
    revisions = sorted((root / 'revisions').glob('*.json'), key=lambda p: read(p)['timestamp_utc'])
    runner = 'updates/' + read(revisions[-1])['revision'] + '/campaign.py' if revisions else 'software/campaign.py'
    return record(root, 'artifacts', {'schema': 'astrago-evidence-v1', 'files': files,
                                    'replay': ['python3', runner, 'verify',
                                               '--offline', '--run', '.']})


def physical_cost(events: list[dict[str, Any]]) -> dict[str, Any]:
    results = [e for e in events if e.get('phase') == 'result']
    by_id = {e['id']: e for e in results}
    if len(results) != len(by_id):
        raise ValueError('Duplicate physical result identity')
    if any(e['duration_seconds'] < 0 for e in results):
        raise ValueError('Negative physical event duration')
    pending = sorted({e['id'] for e in events if e.get('phase') == 'dispatch'} - by_id.keys())
    return {'charge_usd': None, 'billing_status': 'unknown',
            'known_physical_duration_seconds': math.fsum(e['duration_seconds'] for e in results),
            'physical_event_ids': sorted(by_id), 'unresolved_event_ids': pending}


def stop(root: Path, reason: str) -> dict[str, Any]:
    manifest(root)
    events = [read(p) for p in (root / 'events').glob('*.json')]
    report = {'schema': 'astrago-stop-v1', 'timestamp_utc': now(), 'status': 'incomplete',
              'reason': reason, 'h0_sha256': file_hash(root / 'h0.json'),
              'manifest_sha256': file_hash(root / 'manifest.json'),
              'cost': physical_cost(events),
              'research_success': None, 'deployment_success': None,
              'events': sorted(p.stem for p in (root / 'events').glob('*.json'))}
    record(root, 'stops', report)
    artifact = seal(root)
    return {**report, 'artifact': artifact.relative_to(root).as_posix()}


def verify(root: Path) -> dict[str, Any]:
    manifest(root)
    artifacts = sorted((root / 'artifacts').glob('*.json'), key=lambda p: p.stat().st_mtime_ns)
    if not artifacts:
        raise ValueError('No retained artifact')
    artifact = artifacts[-1]
    if file_hash(artifact) != artifact.stem:
        raise ValueError('Artifact identity mismatch')
    for name, identity in read(artifact)['files'].items():
        path = root / name
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError('Evidence path escapes campaign')
        if file_hash(path) != identity['sha256'] or path.stat().st_size != identity['bytes']:
            raise ValueError('Retained identity mismatch: ' + name)
    for folder in ['events', 'reports', 'stops', 'resumes']:
        for path in (root / folder).glob('*.json'):
            if file_hash(path) != path.stem:
                raise ValueError('Content-addressed record changed: ' + folder)
    for path in (root / 'stops').glob('*.json'):
        stopped = read(path)
        expected = physical_cost([read(root / 'events' / (identity + '.json')) for identity in stopped['events']])
        actual = dict(stopped['cost'])
        if not math.isclose(actual.pop('known_physical_duration_seconds'), expected.pop('known_physical_duration_seconds'), rel_tol=0, abs_tol=1e-6):
            raise ValueError('Stopped physical cost arithmetic mismatch')
        if actual != expected:
            raise ValueError('Stopped event reconciliation mismatch')
    setup_resumes = [validate_resume(root, p) for p in (root / 'resumes').glob('*.json')]
    from native_slice import check_transcript, verify_libraries
    smoke_status = 'not_run'
    for path in sorted((root / 'reports').glob('*.json'), key=lambda p: read(p)['started_utc']):
        report = read(path)
        if report['manifest_sha256'] != file_hash(root / 'manifest.json'):
            raise ValueError('Stale gate report')
        if report['advance'] != (report['status'] == 'pass'):
            raise ValueError('Failed gate advances campaign')
        if report['operation'] == 'acquire' and report['status'] == 'pass':
            for asset in report['result']['assets']:
                if file_hash(root / asset['path']) != asset['sha256']:
                    raise ValueError('Retained asset identity mismatch')
        if report['operation'] == 'build' and report['status'] == 'pass':
            for binary in report['result']['binaries'].values():
                if file_hash(root / binary['path']) != binary['sha256']:
                    raise ValueError('Retained runtime identity mismatch')
                verify_libraries(root, binary['libraries'])
        if report['operation'] == 'smoke':
            smoke_status = report['status']
            if smoke_status == 'pass':
                check_transcript(report['result']['transcript'])
                if report['result']['config_sha256'] != file_hash(root / report['result'].get('config_path', 'evidence/smoke.cfg')):
                    raise ValueError('Smoke configuration changed')
    return {'status': 'pass', 'operation': 'offline-evidence-verification',
            'artifact_sha256': artifact.stem, 'h0': read(root / 'h0.json')['timestamp_utc'],
            'runtime_executed': False, 'native_smoke': smoke_status, 'setup_resumes': setup_resumes}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='operation', required=True)
    p = sub.add_parser('data-plan'); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('data-admit'); p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--public-output', type=Path, required=True); p.add_argument('--instruction')
    p = sub.add_parser('data-check-native'); p.add_argument('--native-lock', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--instruction')
    p = sub.add_parser('data-check-access'); p.add_argument('--run', type=Path, required=True)
    p.add_argument('--export-id'); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('data-freeze-fixtures'); p.add_argument('--artifact', type=Path, required=True)
    p.add_argument('--access-receipt', type=Path, required=True)
    p.add_argument('--review', type=Path, required=True); p.add_argument('--public-output', type=Path, required=True)
    p.add_argument('--instruction')
    p = sub.add_parser('data-build'); p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--native-parent', type=Path, required=True)
    p.add_argument('--instruction')
    p = sub.add_parser('data-verify'); p.add_argument('--artifact', type=Path, required=True)
    p.add_argument('--offline', action='store_true', required=True)
    p = sub.add_parser('data-inputs'); p.add_argument('--run', type=Path, required=True)
    p.add_argument('--bundle', type=Path); p.add_argument('--split', required=True)
    p.add_argument('--export-id'); p.add_argument('--purpose', default='debugging')
    p.add_argument('--arm', choices=['A', 'B', 'C']); p.add_argument('--arm-state', type=Path)
    p.add_argument('--candidate-id', action='append')
    p = sub.add_parser('plan'); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('inventory'); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('start'); p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--run', type=Path, required=True); p.add_argument('--instruction')
    p = sub.add_parser('resume-setup'); p.add_argument('--run', type=Path, required=True)
    p.add_argument('--instruction', required=True); p.add_argument('--coordinator-inventory', type=Path, required=True)
    p = sub.add_parser('adopt-runner'); p.add_argument('--run', type=Path, required=True)
    p.add_argument('--reason', required=True)
    p = sub.add_parser('stop'); p.add_argument('--run', type=Path, required=True)
    p.add_argument('--reason', required=True)
    for operation in ['provision', 'acquire', 'build', 'smoke']:
        p = sub.add_parser(operation); p.add_argument('--run', type=Path, required=True)
        p.add_argument('--retry', action='store_true')
        p.add_argument('--coordinator-inventory', type=Path)
    p = sub.add_parser('verify'); p.add_argument('--run', type=Path, required=True)
    p.add_argument('--offline', action='store_true', required=True)
    args = parser.parse_args()
    result: dict[str, Any]
    try:
        if args.operation.startswith('data-'):
            from admission import dispatch
            result = dispatch(args)
        elif args.operation == 'plan':
            exclusive(args.output, encoded(plan())); result = {'manifest': str(args.output)}
        elif args.operation == 'inventory':
            result = {'schema': 'astrago-coordinator-inventory-v1', 'role': 'coordinator',
                      'timestamp_utc': now(), 'free_bytes': shutil.disk_usage(Path.cwd()).free}
            exclusive(args.output, encoded(result))
        elif args.operation == 'start':
            result = start(args.run, args.manifest, args.instruction)
        elif args.operation == 'resume-setup':
            result = resume_setup(args.run, args.instruction, args.coordinator_inventory)
        elif args.operation == 'adopt-runner':
            result = adopt_runner(args.run, args.reason)
        elif args.operation == 'stop':
            result = stop(args.run, args.reason)
        elif args.operation in ['provision', 'acquire', 'build', 'smoke']:
            from native_slice import execute
            result = execute(args.run, args.operation, args.retry, args.coordinator_inventory)
        else:
            result = verify(args.run)
        print(json.dumps(result, sort_keys=True))
        return 1 if result.get('status') in ['fail', 'inconclusive'] or (args.operation.startswith('data-') and result.get('status') == 'incomplete') else 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'fail', 'reason': str(error)}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
