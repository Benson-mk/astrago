"""Score-free data admission through the public campaign runner."""
from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import Any

# The evaluator prepares private evidence; consumers use registered public
# exports through the audited single-account workflow gateway.
import hashlib
import base64
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
from datetime import datetime, timezone

from campaign import REVISION, digest, file_hash, now, verify, is_stopped

from campaign import encoded, exclusive, read


def plan() -> dict[str, Any]:
    return {'schema': 'astrago-admission-v2',
            'archive_dates': [f'2026-11-{day:02d}' for day in range(6, 0, -1)],
            'required_training_candidates': None,
            'required_development_candidates': None,
            'required_sealed_candidates': None,
            'required_development_families': None,
            'required_sealed_families': None,
            'native_parent': None, 'native_replay': None, 'native_checks': None, 'isolation': 'runner-workflow-v1',
            'archives': [], 'terms': [], 'lineage': [],
            'max_storage_bytes': None,
            'history_modes': {'alwaysComputePassAliveUnderSuicideRules': False,
                              'excludeTerritoryAdjacentToAtari': False},
            'limitation': 'continuation-disjoint; pretraining exposure unknown'}


def dispatch(args: Namespace) -> dict[str, Any]:
    if args.operation == 'data-plan':
        exclusive(args.output, encoded(plan()))
        return {'manifest': str(args.output), 'runtime_executed': False}
    if args.operation == 'data-freeze-fixtures':
        return freeze_fixtures(args.artifact, args.review, args.public_output, args.instruction, args.access_receipt)
    if args.operation == 'data-check-native':
        from admission_checks import run_checks
        return run_checks(args.native_lock, args.output, args.instruction)
    if args.operation == 'data-check-access':
        from workflow_access import probe
        return probe(args.run, args.output, args.export_id)
    if args.operation == 'data-build':
        return build_replay(args.source, args.output, args.native_parent, args.instruction)
    if args.operation == 'data-verify':
        return offline(args.artifact)
    if args.operation == 'data-inputs':
        from workflow_access import consume
        return consume(args.run, args.split, export_id=args.export_id, bundle_path=args.bundle,
                       purpose=args.purpose, arm=args.arm, arm_state=args.arm_state,
                       candidate_ids=args.candidate_id)
    if not args.instruction or not args.instruction.strip():
        raise ValueError('Explicit data execution instruction required')
    config = read(args.manifest)
    if config.get('schema') != plan()['schema']:
        raise ValueError('Admission v2 workflow manifest required; legacy OS contract is not silently migrated')
    unresolved = [key for key, value in config.items() if value is None]
    if unresolved:
        raise ValueError('Unresolved admission prerequisites: ' + ', '.join(unresolved))
    return admit(config, args.output, args.public_output, args.instruction)

COVERAGE = ['opening', 'quiet_midgame', 'capture_atari', 'immediate_ko',
            'later_legal_recapture', 'same_stones_different_history', 'single_pass',
            'late_endgame', 'seki', 'black_to_move', 'white_to_move', 'asymmetric_coordinates']


def decode_output(value: bytes | str | None) -> str:
    return value.decode(errors='replace') if isinstance(value, bytes) else value or ''


def raw_timeout_output(error: subprocess.TimeoutExpired) -> dict[str, Any]:
    result = {}
    for name, value in [('stdout', error.stdout), ('stderr', error.stderr)]:
        raw = value if isinstance(value, bytes) else (value or '').encode()
        result[name] = decode_output(value)
        result[name + '_bytes_base64'] = base64.b64encode(raw).decode()
    return result


def identity(value: Any) -> str:
    return digest(encoded(value))


def canonical(moves: list[Any], context: dict[str, Any]) -> tuple[str, dict[str, Any], int]:
    variants = []
    for symmetry in range(8):
        transformed = []
        for color, point in moves:
            if point is None:
                transformed.append([color, None])
                continue
            x, y = point
            if symmetry & 1:
                x, y = y, x
            if symmetry & 2:
                x = 18 - x
            if symmetry & 4:
                y = 18 - y
            transformed.append([color, [x, y]])
        value = {'schema': 'astrago-full-history-v1', 'board_size': 19,
                 **context, 'moves': transformed}
        variants.append((encoded(value), symmetry, value))
    data, orientation, value = min(variants, key=lambda item: (item[0], item[1]))
    return digest(data), value, orientation


def orient_stones(stones: str, symmetry: int) -> str:
    if len(stones) != 361:
        raise ValueError('Incomplete native board evidence')
    oriented = ['.'] * 361
    for index, stone in enumerate(stones):
        x, y = index % 19, index // 19
        if symmetry & 1:
            x, y = y, x
        if symmetry & 2:
            x = 18 - x
        if symmetry & 4:
            y = 18 - y
        oriented[y * 19 + x] = stone
    return ''.join(oriented)


def inventories(records: list[dict[str, Any]], lineage: list[dict[str, Any]] | None = None, assign_splits: bool = True) -> dict[str, Any]:
    """Pure retained-evidence transformation; never establishes native truth."""
    games: dict[str, Any] = {}
    excluded = []
    by_source = {r['id']: r for r in records}
    source_games: dict[str, str] = {}
    links = lineage or []
    for link in links:
        if set(link) != {'child_source_id', 'parent_source_id', 'provenance', 'reviewer'} or not link['reviewer'].strip() or not link['provenance'].strip():
            raise ValueError('Verified source ancestry needs a named review and provenance trace')
        child, parent = link['child_source_id'], link['parent_source_id']
        if child not in by_source or parent not in by_source or child == parent:
            raise ValueError('Unresolved ancestry source identity')
    resolved = {r['id'] for r in records if r['native']['status'] == 'admitted'}
    for _ in range(len(links)):
        resolved.update(link['child_source_id'] for link in links
                        if link['parent_source_id'] in resolved and
                        by_source[link['child_source_id']]['native']['status'] == 'lineage_required')
    for source in sorted(records, key=lambda row: row['id']):
        report = source['native']
        if source['id'] not in resolved:
            excluded.append({'source_id': source['id'], 'reason': report.get('reason', 'unresolved-ancestry')})
            continue
        if report['schema'] != 'astrago-native-admission-v1' or report['history_modes'] != [False, False]:
            raise ValueError('Unsupported native replay evidence')
        moves, states = report['moves'], report['states']
        if len(moves) != len(states) or not moves:
            raise ValueError('Incomplete native history evidence')
        context = {'rules': report['rules'], 'komi': report['komi'], 'initial_player': report['initial_player']}
        game_id, history, orientation = canonical(moves, context)
        source_games[source['id']] = game_id
        alias = {'source_id': source['id'], 'symmetry': orientation}
        if game_id in games:
            games[game_id]['sources'].append(alias)
        else:
            games[game_id] = {'id': game_id, 'history': history, 'sources': [alias],
                              'native': report}
    parent_ids = {key: key for key in games}

    def representative(key: str) -> str:
        while parent_ids[key] != key:
            key = parent_ids[key]
        return key

    for link in links:
        child, parent = link['child_source_id'], link['parent_source_id']
        if child not in source_games or parent not in source_games:
            raise ValueError('Ancestry link refers to excluded source')
        left, right = representative(source_games[child]), representative(source_games[parent])
        parent_ids[max(left, right)] = min(left, right)
    components: dict[str, list[str]] = {}
    for key in sorted(games):
        components.setdefault(representative(key), []).append(key)
    ordered = sorted(components, key=lambda key: (hashlib.sha256(
        ('astrago-issue8-split-v1' + key).encode()).hexdigest(), key))
    n = len(ordered)
    families = []
    candidates: dict[str, Any] = {}
    duplicates = []
    priority = {'unassigned': 0, 'training': 0, 'development': 1, 'sealed': 2}
    for index, key in enumerate(ordered):
        split = 'unassigned' if not assign_splits else 'training' if index < 8 * n // 10 else 'development' if index < 8 * n // 10 + n // 10 else 'sealed'
        families.append({'id': key, 'split': split, 'sources': sorted(
            [alias for game_id in components[key] for alias in games[game_id]['sources']], key=lambda alias: alias['source_id'])})
        for game_id in components[key]:
            game = games[game_id]
            report = game['native']
            for ply, state in enumerate(report['states']):
                if state['terminal']:
                    raise ValueError('Terminal analysis candidate')
                context = {'rules': report['rules'], 'komi': report['komi'],
                           'initial_player': report['initial_player'], 'next_player': state['next_player'],
                           'terminal': False, 'phase': state['phase']}
                candidate_id, history, symmetry = canonical(report['moves'][:ply], context)
                aliases = [{'source_id': alias['source_id'], 'ply': ply,
                            'symmetry': canonical(by_source[alias['source_id']]['native']['moves'][:ply], context)[2]}
                           for alias in game['sources']]
                candidate = {'id': candidate_id, 'history': history, 'symmetry': symmetry,
                             'family_id': key, 'split': split, 'aliases': aliases,
                             'state': {**state, 'stones': orient_stones(state['stones'], symmetry)}}
                prior = candidates.get(candidate_id)
                if prior is None:
                    candidates[candidate_id] = candidate
                elif priority[split] > priority[prior['split']]:
                    duplicates.append({'candidate_id': candidate_id, 'removed_split': prior['split'],
                                       'family_id': prior['family_id'], 'reason': 'duplicate-history'})
                    candidate['aliases'] += prior['aliases']
                    candidates[candidate_id] = candidate
                else:
                    duplicates.append({'candidate_id': candidate_id, 'removed_split': split,
                                       'family_id': key, 'reason': 'duplicate-history'})
                    prior['aliases'] += aliases
    return {'families': families, 'candidates': sorted(candidates.values(), key=lambda row: row['id']),
            'exclusions': excluded, 'duplicate_exclusions': duplicates}


def unassigned_inventory(records: list[dict[str, Any]], links: list[dict[str, Any]]) -> tuple[dict[str, Any], bool]:
    available_ids = {r['id'] for r in records}
    unresolved = {link['child_source_id'] for link in links
                  if link['child_source_id'] in available_ids and link['parent_source_id'] not in available_ids}
    for _ in links:
        unresolved.update(link['child_source_id'] for link in links if link['parent_source_id'] in unresolved)
    available_links = [link for link in links
                       if link['child_source_id'] in available_ids and link['parent_source_id'] in available_ids
                       and link['child_source_id'] not in unresolved]
    return inventories([r for r in records if r['id'] not in unresolved], available_links, assign_splits=False), bool(unresolved)


def shortages(table: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    missing = {}
    for split in ['training', 'development', 'sealed']:
        rows = [row for row in table['candidates'] if row['split'] == split]
        for kind, observed in [('candidates', len(rows)), ('families', len({r['family_id'] for r in rows}))]:
            field = f'required_{split}_{kind}'
            if field in config and observed < config[field]:
                missing[field] = {'required': config[field], 'observed': observed}
    return missing


def fixtures(table: dict[str, Any]) -> dict[str, Any]:
    # Semantic categories such as seki require separate evidenced review. Never
    # infer them from move number or pretend empty coverage has passed.
    rows = [r for r in table['candidates'] if r['split'] == 'development']
    covered: dict[str, list[str]] = {key: [] for key in COVERAGE}
    boards: dict[str, list[str]] = {}
    for row in rows:
        state = row['state']
        categories = ['black_to_move' if state['next_player'] == 'B' else 'white_to_move']
        if state['atari']:
            categories.append('capture_atari')
        if state['ko']:
            categories.append('immediate_ko')
        if state['single_pass']:
            categories.append('single_pass')
        boards.setdefault(state['stones'], []).append(row['id'])
        for category in categories:
            covered[category].append(row['id'])
    covered['same_stones_different_history'] = sorted({key for group in boards.values() if len(group) > 1 for key in group})
    return {'status': 'incomplete', 'playable_available': len(rows), 'required_playable': 32,
            'selected': [], 'category_candidates': covered,
            'unverified_categories': [key for key, values in covered.items() if not values],
            'reason': 'Coverage review and 32-history freeze required; no fabricated fixtures',
            'terminal_checks': []}


def check_public(bundle: dict[str, Any]) -> dict[str, Any]:
    if bundle.get('schema') != 'astrago-public-data-v1':
        raise ValueError('Expected a verified public data bundle; board-only identities are insufficient')
    payload = bundle['payload']
    if identity(payload) != bundle['sha256']:
        raise ValueError('Public data bundle identity mismatch')
    seen = set()
    sealed = set(payload['sealed_candidate_ids'])
    for row in payload['candidates']:
        history = row['history']
        if row['split'] not in ['training', 'development'] or row['id'] in sealed or row['id'] in seen:
            raise ValueError('Cross-split or sealed debugging fixture rejected')
        if history.get('schema') != 'astrago-full-history-v1' or 'moves' not in history:
            raise ValueError('Board-only candidate identity rejected')
        key, canonical_history, _ = canonical(history['moves'], {k: v for k, v in history.items() if k not in ['moves', 'schema', 'board_size']})
        if key != row['id'] or canonical_history != history:
            raise ValueError('Noncanonical candidate identity')
        seen.add(row['id'])
    return payload


def public_bundle(table: dict[str, Any], fixture_report: dict[str, Any], artifact_hash: str) -> dict[str, Any]:
    # Source aliases may refer to sealed duplicates: keep them evaluator-private.
    rows = [{key: row[key] for key in ['id', 'history', 'family_id', 'split']}
            for row in table['candidates'] if row['split'] != 'sealed']
    payload = {'candidates': rows, 'sealed_candidate_ids': [r['id'] for r in table['candidates'] if r['split'] == 'sealed'],
               'private_artifact_sha256': artifact_hash,
               'fixtures': fixture_report, 'limitation': plan()['limitation']}
    return {'schema': 'astrago-public-data-v1', 'payload': payload, 'sha256': identity(payload)}


def private_directory(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=False)
    if path.stat().st_mode & 0o077:
        raise ValueError('Evaluator directory must be private')


def parent_evidence(root: Path) -> dict[str, Any]:
    report = verify(root)
    if not is_stopped(root):
        raise ValueError('Linked data stage requires an immutable stopped native parent')
    if report['native_smoke'] != 'pass':
        raise ValueError('Native parent smoke prerequisite not passed')
    h0 = read(root / 'h0.json')
    elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(h0['timestamp_utc'])).total_seconds()
    if not 0 <= elapsed < 86400:
        raise ValueError('Original H0–24 expired; explicit replan required')
    return {'artifact_sha256': report['artifact_sha256'], 'h0': h0,
            'elapsed_seconds': elapsed, 'original_campaign_remains_stopped': True}


def retain_artifact(root: Path, report: dict[str, Any], config: dict[str, Any], public_bytes: int = 0) -> Path:
    files = {p.relative_to(root).as_posix(): {'sha256': file_hash(p), 'bytes': p.stat().st_size}
             for p in sorted(root.rglob('*')) if p.is_file() and 'artifacts' not in p.relative_to(root).parts}
    location = root / 'export-location.json'
    if not location.exists():
        location = root / 'access-challenge.json'  # Historical v1 evidence only.
    previous_public = Path(read(location)['public_bundle'])
    data_files = measured_files([root, previous_public])
    campaign_files = measured_files([root, previous_public, Path(config['native_parent']),
                                     Path(config['native_replay']).parent.parent.parent,
                                     *[Path(a['path']) for a in config['archives']]])
    data_bytes, combined_bytes = sum(data_files.values()), sum(campaign_files.values())
    report['storage_measurements'] = {'data_files': data_files, 'campaign_files': campaign_files}
    value = {'schema': 'astrago-data-evidence-v1', 'report': report, 'files': files,
             'replay': ['python3', 'software/campaign.py', 'data-verify', '--offline', '--artifact', 'artifacts/<sha256>.json']}
    # Serialize the actual index/report; its byte length is not bounded by a
    # fixed per-run allowance. Iterate only the decimal byte-count field widths.
    def serialized() -> bytes:
        previous_size = -1
        while True:
            data = encoded(value)
            if len(data) == previous_size:
                return data
            previous_size = len(data)
            report['storage'] = {'data_bytes_including_new_export': data_bytes + public_bytes + len(data),
                                 'campaign_bytes_including_new_export': combined_bytes + public_bytes + len(data),
                                 'artifact_bytes': len(data), 'new_public_bytes': public_bytes}

    if report['status'] not in ['pass', 'incomplete']:
        public_bytes = 0
    data = serialized()
    if (report['storage']['data_bytes_including_new_export'] > config['max_storage_bytes'] or
            report['storage']['campaign_bytes_including_new_export'] > 50 * 2**30):
        report.update(status='fail', advance=False, reason='Actual serialized evidence/export exceeds storage cap',
                      rejected_public_bytes=public_bytes)
        public_bytes = 0
        data = serialized()
    destination = root / 'artifacts' / (digest(data) + '.json')
    exclusive(destination, data)
    return destination


def offline(artifact: Path) -> dict[str, Any]:
    if file_hash(artifact) != artifact.stem:
        raise ValueError('Data artifact identity mismatch')
    evidence = read(artifact)
    root = artifact.parent.parent
    if evidence['schema'] != 'astrago-data-evidence-v1':
        raise ValueError('Unknown data artifact')
    for name, expected in evidence['files'].items():
        path = root / name
        if not path.resolve().is_relative_to(root.resolve()) or file_hash(path) != expected['sha256'] or path.stat().st_size != expected['bytes']:
            raise ValueError('Retained data identity mismatch: ' + name)
    storage = evidence['report']['storage']
    measurements = evidence['report']['storage_measurements']
    for kind in ['data', 'campaign']:
        expected = sum(measurements[kind + '_files'].values()) + storage['new_public_bytes'] + artifact.stat().st_size
        if storage[kind + '_bytes_including_new_export'] != expected:
            raise ValueError('Retained storage arithmetic mismatch')
    if storage['artifact_bytes'] != artifact.stat().st_size:
        raise ValueError('Artifact byte count mismatch')
    records_path = root / 'records.json'
    replay_status = 'not_run'
    if records_path.exists() and any((root / name).exists() for name in ['inventory.json', 'eligibility.json']):
        records = read(records_path)
        events = read(root / 'events.json')
        by_source = {event['source_id']: event for event in events}
        if len(by_source) != len(events) or any(event['duration_seconds'] < 0 for event in events):
            raise ValueError('Invalid native attempt accounting')
        for source in records:
            raw = (root / 'sgfs' / (source['id'] + '.sgf')).read_bytes()
            origin = {key: source[key] for key in ['archive_sha256', 'member', 'record_index', 'sgf_sha256']}
            if digest(raw) != source['sgf_sha256'] or identity(origin) != source['id']:
                raise ValueError('Source record identity mismatch')
            member = (root / 'members' / (identity([source['archive_sha256'], source['member']]) + '.bin')).read_bytes()
            chunks = member.splitlines(keepends=True) if source['member'].endswith('.sgfs') else [member]
            if chunks[source['record_index']] != raw:
                raise ValueError('Source extraction replay mismatch')
            event = by_source[source['id']]
            if event['status'] == 'encoding-rejected':
                try:
                    raw.decode('utf-8')
                except UnicodeDecodeError:
                    pass
                else:
                    raise ValueError('Incorrect encoding exclusion')
                expected_native = {'status': 'excluded', 'reason': 'invalid-utf8'}
            else:
                if event['status'] != 'completed' or event['exit_code'] != 0:
                    raise ValueError('Failed native attempt became an admitted record')
                expected_native = json.loads(event['stdout'])
            if source['native'] != expected_native:
                raise ValueError('Native response parsing replay mismatch')
        config = read(root / 'manifest.json')
        if (root / 'inventory.json').exists():
            actual = inventories(records, config['lineage'])
            if actual != read(root / 'inventory.json'):
                raise ValueError('Deterministic admission replay mismatch')
            if fixtures(actual) != read(root / 'fixtures.json'):
                raise ValueError('Development fixture replay mismatch')
        else:
            actual, unresolved = unassigned_inventory(records, config['lineage'])
            if actual != read(root / 'eligibility.json') or actual != unassigned_inventory(list(reversed(records)), config['lineage'])[0]:
                raise ValueError('Unassigned admission replay mismatch')
            counts = {'families': len(actual['families']), 'candidates': len(actual['candidates'])}
            required = {'families': 10 * max(config['required_development_families'], config['required_sealed_families']),
                        'candidates': sum(config['required_' + split + '_candidates'] for split in ['training', 'development', 'sealed'])}
            examined = read(root / 'sources-examined.json')
            dates = [a['date'] for a in examined]
            report = evidence['report']
            if (not dates or dates != config['archive_dates'][:len(dates)] or len(dates) >= len(config['archive_dates']) or
                    report.get('source_expansion') != 'next-archive-required' or
                    report.get('next_archive_date') != config['archive_dates'][len(dates)] or
                    report.get('gross_eligibility') != counts or report.get('gross_required') != required or
                    (not unresolved and all(counts[k] >= required[k] for k in counts)) or
                    (root / 'sources-frozen.json').exists()):
                raise ValueError('Unassigned expansion decision replay mismatch')
        if evidence['report']['status'] == 'pass':
            if read(root / 'manifest.json')['schema'] == 'astrago-admission-v2':
                from workflow_access import validate_receipt
                validate_receipt(root, read(root / 'access-receipt.json'), check_current=False)
            else:
                validate_access(root, read(root / 'access-receipt.json'), check_current=False)
            result = validate_fixture_review(actual, read(records_path), read(root / 'development-review.json'))
            if result != evidence['report']['fixtures'] or shortages(actual, read(root / 'manifest.json')):
                raise ValueError('Final fixture/capacity gate replay mismatch')
        replay_status = 'pass'
    return {'status': 'pass', 'deterministic_replay': replay_status,
            'native_status': evidence['report']['status'], 'runtime_executed': False,
            'role': 'evaluator', 'purpose': 'retained-evidence-verification',
            'artifact_sha256': artifact.stem, 'limitation': plan()['limitation']}


def admit(config: dict[str, Any], root: Path, public: Path, instruction: str) -> dict[str, Any]:
    expected = plan()
    if set(config) != set(expected):
        raise ValueError('Admission manifest fields differ from schema')
    if config['archive_dates'] != expected['archive_dates'] or config['history_modes'] != expected['history_modes']:
        raise ValueError('Adopted source range or replay modes changed')
    for key in [key for key in expected if key.startswith('required_')] + ['max_storage_bytes']:
        if type(config[key]) is not int or config[key] <= 0:
            raise ValueError('Positive measured capacity parameter required: ' + key)
    if config['max_storage_bytes'] > 50 * 2**30:
        raise ValueError('Adopted 50 GiB storage cap exceeded')
    if config['isolation'] != 'runner-workflow-v1':
        raise ValueError('User-approved runner workflow isolation required')
    if public.exists() or root.exists() or public.resolve().is_relative_to(root.resolve()) or root.resolve().is_relative_to(public.resolve()):
        raise ValueError('Fresh separate private and public destinations required')
    parent = parent_evidence(Path(config['native_parent']))
    lock_path = Path(config['native_replay'])
    if file_hash(lock_path) != lock_path.stem:
        raise ValueError('Native build lock identity mismatch')
    lock = read(lock_path)
    if lock['parent']['artifact_sha256'] != parent['artifact_sha256']:
        raise ValueError('Replay build belongs to another native parent')
    binary = Path(lock['binary'])
    if lock['source_revision'] != REVISION or lock['adapter_sha256'] != file_hash(Path(__file__).with_name('admission_replay.cpp')) or file_hash(binary) != lock['binary_sha256']:
        raise ValueError('Native replay identity mismatch')
    for asset in config['archives']:
        original_stat = Path(asset['path']).stat()
        if original_stat.st_uid != os.getuid() or original_stat.st_mode & 0o077:
            raise ValueError('Original SGF archives must be evaluator-owned and mode 0600')
    checks_path = Path(config['native_checks'])
    checks = read(checks_path)
    if file_hash(checks_path) != checks_path.stem or checks['status'] != 'pass' or checks['binary_sha256'] != lock['binary_sha256'] or checks['adapter_sha256'] != lock['adapter_sha256']:
        raise ValueError('Native runner diagnostics prerequisite unmet')
    if any(checks.get('software', {}).get(name) != file_hash(Path(__file__).with_name(name))
           for name in ['admission.py', 'admission_checks.py']):
        raise ValueError('Stale native transformation diagnostics; rerun data-check-native')
    dates = [row['date'] for row in config['archives']]
    if not dates or dates != expected['archive_dates'][:len(dates)]:
        raise ValueError('Archives must begin November 6 and proceed daily through November 1')
    term_urls = {'https://katagoarchive.org/kata1/README.txt',
                 'https://katagoarchive.org/kata1/DISCLAIMER.txt', 'https://katagotraining.org/privacy/'}
    if {term['url'] for term in config['terms']} != term_urls:
        raise ValueError('All three data origin/terms records required')
    if retained_size([Path(config['native_parent']), Path(config['native_replay']).parent.parent.parent, *[Path(a['path']) for a in config['archives']]]) >= 50 * 2**30:
        raise ValueError('Inherited campaign/source storage already exceeds cap')
    if shutil.disk_usage(root.parent).free < config['max_storage_bytes']:
        raise ValueError('Measured storage headroom insufficient')
    private_directory(root)
    start, clock = now(), time.monotonic()
    records: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    report: dict[str, Any] = {'status': 'inconclusive', 'advance': False, 'reason': 'Interrupted admission',
                              'started_utc': start, 'instruction': instruction, 'parent': parent,
                              'limitation': expected['limitation'], 'charge_usd': None}
    exclusive(root / 'manifest.json', encoded(config))
    exclusive(root / 'native-lock.json', encoded(lock))
    exclusive(root / 'native-checks.json', encoded(checks))
    for name in ['campaign.py', 'admission.py', 'admission_checks.py', 'workflow_access.py', 'admission_replay.cpp', 'native_slice.py', 'checkpoint_audit.py']:
        exclusive(root / 'software' / name, Path(__file__).with_name(name).read_bytes())

    written_bytes = retained_size([root])

    def retain_asset(asset: dict[str, Any], destination: str) -> Path:
        nonlocal written_bytes
        path = Path(asset['path'])
        if file_hash(path) != asset['sha256']:
            raise ValueError('Source asset identity mismatch')
        datetime.fromisoformat(asset['retrieved_utc'])
        if asset['bytes'] != path.stat().st_size or asset['acquisition_seconds'] < 0:
            raise ValueError('Invalid measured acquisition evidence')
        target = root / destination / asset['sha256']
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copyfile(path, target)
            written_bytes += target.stat().st_size
        return target

    try:
        for term in config['terms']:
            retain_asset(term, 'terms')
        for archive in config['archives']:
            expected_url = 'https://katagoarchive.org/kata1/traininggames/' + archive['date'] + 'sgfs.tar.bz2'
            if archive['url'] != expected_url:
                raise ValueError('Unapproved SGF source URL')
            extraction_start = time.monotonic()
            original = retain_asset(archive, 'archives')
            member_count = 0
            with tarfile.open(original, 'r:bz2') as tar:
                for member in tar:
                    if member.isdir():
                        continue
                    if not member.isfile() or member.name.startswith('/') or '..' in Path(member.name).parts:
                        raise ValueError('Unsafe source archive member')
                    if member.size > config['max_storage_bytes']:
                        raise ValueError('Archive member exceeds storage allowance')
                    stream = tar.extractfile(member)
                    if stream is None:
                        raise ValueError('Unreadable source member')
                    raw = stream.read()
                    written_bytes += len(raw)
                    exclusive(root / 'members' / (identity([archive['sha256'], member.name]) + '.bin'), raw)
                    # Official .sgfs is one SGF per line; .sgf is a full record.
                    chunks = raw.splitlines(keepends=True) if member.name.endswith('.sgfs') else [raw]
                    for line_number, chunk in enumerate(chunks):
                        if not chunk.strip():
                            continue
                        source = {'archive_sha256': archive['sha256'], 'member': member.name,
                                  'record_index': line_number, 'sgf_sha256': digest(chunk)}
                        source['id'] = identity(source)
                        exclusive(root / 'sgfs' / (source['id'] + '.sgf'), chunk)
                        written_bytes += len(chunk)
                        command = [str(binary.resolve()), 'astrago-admit']
                        dispatch_time = time.monotonic()
                        event: dict[str, Any] = {'source_id': source['id'], 'command': command,
                                                 'started_utc': now(), 'status': 'dispatched'}
                        dispatch_bytes = encoded(event)
                        exclusive(root / 'dispatches' / (source['id'] + '.json'), dispatch_bytes)
                        written_bytes += len(dispatch_bytes)
                        try:
                            request = json.dumps({'sgf': chunk.decode('utf-8')}) + '\n'
                            result = subprocess.run(command, input=request, capture_output=True, text=True, timeout=120)
                            event.update(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr,
                                         status='completed')
                            if result.returncode != 0:
                                raise ValueError('Native replay process failed')
                            native = json.loads(result.stdout)
                        except UnicodeDecodeError:
                            native = {'status': 'excluded', 'reason': 'invalid-utf8'}
                            event.update(status='encoding-rejected')
                        except subprocess.TimeoutExpired as error:
                            event.update(status='timeout', exit_code=None, **raw_timeout_output(error))
                            raise
                        except OSError as error:
                            event.update(status='launch-error', reason=str(error), exit_code=None)
                            raise
                        finally:
                            event['duration_seconds'] = time.monotonic() - dispatch_time
                            events.append(event)
                        source['native'] = native
                        records.append(source)
                        member_count += 1
                        if written_bytes > config['max_storage_bytes']:
                            raise ValueError('Measured retained storage exceeds capacity')
            selected.append({**archive, 'records': member_count, 'extraction_and_replay_seconds': time.monotonic() - extraction_start})
            # Score-free gross eligibility only; freeze archives before splitting.
            eligibility, unresolved_children = unassigned_inventory(records, config['lineage'])
            required_candidates = sum(config['required_' + split + '_candidates'] for split in ['training', 'development', 'sealed'])
            family_floor = 10 * max(config['required_development_families'], config['required_sealed_families'])
            if not unresolved_children and len(eligibility['families']) >= family_floor and len(eligibility['candidates']) >= required_candidates:
                break
        gross_counts = {'families': len(eligibility['families']), 'candidates': len(eligibility['candidates'])}
        if len(selected) < len(expected['archive_dates']) and (unresolved_children or
                gross_counts['families'] < family_floor or gross_counts['candidates'] < required_candidates):
            report.update(status='incomplete', reason='Next approved archive required before source freeze',
                          source_expansion='next-archive-required',
                          next_archive_date=expected['archive_dates'][len(selected)],
                          gross_eligibility=gross_counts,
                          gross_required={'families': family_floor, 'candidates': required_candidates})
            exclusive(root / 'sources-examined.json', encoded(selected))
            # Retain an unassigned inventory for inspection, never a split/public export.
            exclusive(root / 'eligibility.json', encoded(eligibility))
        else:
            exclusive(root / 'sources-frozen.json', encoded(selected))
            table = inventories(records, config['lineage'])
            if table != inventories(list(reversed(records)), config['lineage']):
                raise ValueError('Input-order-dependent admission identities or exclusions')
            exclusive(root / 'inventory.json', encoded(table))
            fixture_report = fixtures(table)
            exclusive(root / 'fixtures.json', encoded(fixture_report))
            report.update(status='incomplete', reason='Development coverage freeze remains unmet',
                          shortages=shortages(table, config), fixtures=fixture_report,
                          deterministic_replay='pass', source_expansion='eligibility-only-before-split',
                          isolation=config['isolation'], os_unreadability=False)
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError, tarfile.TarError) as error:
        report.update(status='fail', reason=str(error))
    finally:
        exclusive(root / 'records.json', encoded(records))
        exclusive(root / 'events.json', encoded(events))
        combined_bytes = retained_size([root, Path(config['native_parent']), Path(config['native_replay']).parent.parent.parent, *[Path(a['path']) for a in config['archives']]])
        if combined_bytes > 50 * 2**30 or retained_size([root]) > config['max_storage_bytes']:
            report.update(status='fail', reason='Generated/inherited data exceeds retained storage cap')
        report['combined_retained_bytes'] = combined_bytes
        report.update(ended_utc=now(), duration_seconds=time.monotonic() - clock,
                      retained_bytes=sum(p.stat().st_size for p in root.rglob('*') if p.is_file()))
        exclusive(root / 'export-location.json', encoded({'schema': 'astrago-export-location-v2', 'isolation': config['isolation'], 'public_bundle': str((public / 'data.json').resolve())}))
        projected_public = 0
        if (root / 'inventory.json').exists():
            projected_public = len(encoded(public_bundle(read(root / 'inventory.json'), read(root / 'fixtures.json'), '0' * 64)))
        artifact = retain_artifact(root, report, config, projected_public)
    if report['status'] == 'incomplete' and (root / 'inventory.json').exists():
        report['registration_sha256'] = export_public(root, public, read(root / 'inventory.json'), read(root / 'fixtures.json'), artifact.stem)
    return {**report, 'artifact': str(artifact)}


def build_replay(source: Path, root: Path, parent: Path, instruction: str | None) -> dict[str, Any]:
    if not instruction or not instruction.strip():
        raise ValueError('Explicit data execution instruction required')
    inherited = parent_evidence(parent)
    revision = subprocess.run(['git', '-C', str(source), 'rev-parse', 'HEAD'], check=True, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(['git', '-C', str(source), 'status', '--porcelain'], check=True, capture_output=True, text=True).stdout.strip()
    if revision != REVISION or dirty:
        raise ValueError('Pinned pristine native source required')
    if shutil.disk_usage(root.parent).free < 50 * 2**30:
        raise ValueError('Native replay build requires adopted training storage headroom')
    private_directory(root)
    start = time.monotonic()
    commands: list[dict[str, Any]] = []
    report: dict[str, Any] = {'status': 'inconclusive', 'advance': False, 'parent': inherited,
                             'instruction': instruction, 'started_utc': now(), 'charge_usd': None}
    try:
        target = root / 'source'
        shutil.copytree(source, target)
        adapter = Path(__file__).with_name('admission_replay.cpp')
        shutil.copyfile(adapter, target / 'cpp/admission_replay.cpp')
        modifications = {
            'cpp/CMakeLists.txt': ('add_executable(katago\n', 'add_executable(katago\n  admission_replay.cpp\n'),
            'cpp/main.cpp': ('  if(subcommand == "analysis")',
                            '  if(subcommand == "astrago-admit")\n    return astragoAdmission(subArgs);\n  else if(subcommand == "analysis")'),
            'cpp/dataio/sgf.cpp': ('  std::unique_ptr<Sgf> sgf = maybeParseSgf(str,pos);',
                                '  std::unique_ptr<Sgf> sgf = maybeParseSgf(str,pos);\n  while(pos < str.size() && Global::isWhitespace(str[pos])) pos++;\n  if(pos != str.size()) sgfFail("Trailing SGF content",str,pos);')}
        patches = {}
        for name, (old, new) in modifications.items():
            path = target / name
            before = path.read_text()
            if before.count(old) != 1:
                raise ValueError('Pinned source patch context changed')
            after = before.replace(old, new)
            if name == 'cpp/main.cpp':
                after = after.replace('static int handleSubcommand',
                    'int astragoAdmission(const std::vector<std::string>&);\n\nstatic int handleSubcommand', 1)
            path.write_text(after)
            patches[name] = {'original_sha256': digest(before.encode()), 'patched_sha256': file_hash(path),
                             'original': before, 'patched': after}
        exclusive(root / 'patches.json', encoded(patches))
        for argv in [['cmake', '-S', str(target / 'cpp'), '-B', str(root / 'build'),
                      '-DUSE_BACKEND=', '-DCMAKE_BUILD_TYPE=Release'],
                     ['cmake', '--build', str(root / 'build'), '--parallel', '2']]:
            tick = time.monotonic()
            call: dict[str, Any] = {'argv': argv, 'started_utc': now()}
            commands.append(call)
            try:
                result = subprocess.run(argv, capture_output=True, text=True, timeout=1800)
                call.update(exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr, status='completed')
                if result.returncode:
                    raise ValueError('Native replay build failed')
            except subprocess.TimeoutExpired as error:
                call.update(status='timeout', exit_code=None, **raw_timeout_output(error))
                raise
            except OSError as error:
                call.update(status='launch-error', reason=str(error), exit_code=None)
                raise
            finally:
                call['duration_seconds'] = time.monotonic() - tick
        binary = root / 'build/katago'
        lock = {'schema': 'astrago-replay-build-v1', 'source_revision': REVISION,
                'adapter_sha256': file_hash(adapter), 'binary': str(binary.resolve()),
                'binary_sha256': file_hash(binary), 'parent': inherited,
                'patches_sha256': file_hash(root / 'patches.json'), 'commands': commands}
        path = root / 'locks' / (identity(lock) + '.json')
        exclusive(path, encoded(lock))
        if retained_size([root.parent, parent]) > 50 * 2**30:
            raise ValueError('Replay build plus inherited campaign exceeds storage cap')
        report.update(status='pass', lock=str(path))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        report.update(status='fail', reason=str(error))
    finally:
        report.update(ended_utc=now(), duration_seconds=time.monotonic() - start, commands=commands)
        exclusive(root / 'build-report.json', encoded(report))
    return report


def validate_fixture_review(table: dict[str, Any], records: list[dict[str, Any]], review: dict[str, Any]) -> dict[str, Any]:
    if review.get('schema') != 'astrago-development-review-v1' or not review.get('reviewer', '').strip():
        raise ValueError('Named development coverage review required')
    available = {r['id']: r for r in table['candidates'] if r['split'] == 'development'}
    selected = review['selected']
    if len(selected) != 32 or len(set(selected)) != 32 or not set(selected) <= available.keys():
        raise ValueError('Exactly 32 distinct playable development histories required')
    coverage = review['coverage']
    if set(coverage) != set(COVERAGE):
        raise ValueError('Every adopted fixture category needs evidence')
    mechanical = fixtures(table)['category_candidates']
    automatic = {'capture_atari', 'immediate_ko', 'single_pass', 'black_to_move', 'white_to_move'}
    for category, assertions in coverage.items():
        if not assertions:
            raise ValueError('Unavailable fixture category: ' + category)
        for assertion in assertions:
            key = assertion['candidate_id']
            if key not in selected or not assertion['evidence'].strip():
                raise ValueError('Coverage must reference selected histories with explicit evidence')
            if category in automatic and key not in mechanical[category]:
                raise ValueError('Coverage contradicts native evidence: ' + category)
    same_board = [a['candidate_id'] for a in coverage['same_stones_different_history']]
    if len(set(same_board)) < 2 or len({available[key]['state']['stones'] for key in same_board}) != 1:
        raise ValueError('Same-stone fixture requires distinct histories with identical native stones')
    development_sources = {s['source_id'] for f in table['families'] if f['split'] == 'development' for s in f['sources']}
    by_source = {r['id']: r for r in records}
    terminals = review['terminal_sources']
    if not terminals or not set(terminals) <= development_sources:
        raise ValueError('Separate development-only terminal fixture required')
    for source in terminals:
        endpoint = by_source[source]['native']['endpoint']
        if not endpoint['terminal'] or not endpoint['two_pass']:
            raise ValueError('Terminal check lacks native two-pass termination')
    return {'status': 'pass', 'selected': selected, 'coverage': coverage,
            'terminal_sources': terminals, 'reviewer': review['reviewer'],
            'review_sha256': identity(review), 'semantic_categories': 'evidenced operator classification',
            'mechanical_categories': sorted(automatic), 'required_playable': 32}


def freeze_fixtures(artifact: Path, review_path: Path, public: Path, instruction: str | None, access_receipt: Path) -> dict[str, Any]:
    if not instruction or not instruction.strip():
        raise ValueError('Explicit data execution instruction required')
    replay = offline(artifact)
    if replay['deterministic_replay'] != 'pass':
        raise ValueError('Complete deterministic admission prerequisite required')
    root = artifact.parent.parent
    config = read(root / 'manifest.json')
    parent_evidence(Path(config['native_parent']))
    receipt = read(access_receipt)
    from workflow_access import validate_receipt
    validate_receipt(root, receipt)
    table = read(root / 'inventory.json')
    if shortages(table, config):
        raise ValueError('Candidate/family capacity shortfall remains')
    review = read(review_path)
    result = validate_fixture_review(table, read(root / 'records.json'), review)
    if public.exists():
        raise ValueError('Fresh public export directory required')
    projected_public = len(encoded(public_bundle(table, result, '0' * 64)))
    exclusive(root / 'access-receipt.json', encoded(receipt))
    exclusive(root / 'development-review.json', encoded(review))
    report = {**read(artifact)['report'], 'status': 'pass', 'advance': True,
              'reason': 'Native admission, deterministic split and reviewed development coverage passed',
              'fixtures': result, 'fixture_freeze_utc': now(), 'fixture_instruction': instruction,
              'previous_artifact_sha256': artifact.stem}
    final_artifact = retain_artifact(root, report, config, projected_public)
    if report['status'] == 'pass':
        report['registration_sha256'] = export_public(root, public, table, result, final_artifact.stem)
    return {**report, 'artifact': str(final_artifact)}


def measured_files(paths: list[Path]) -> dict[str, int]:
    files: dict[str, int] = {}
    for path in paths:
        for child in [path] if path.is_file() else path.rglob('*'):
            if child.is_file():
                files[str(child.resolve())] = child.stat().st_size
    return files


def retained_size(paths: list[Path]) -> int:
    return sum(measured_files(paths).values())


def export_public(root: Path, public: Path, table: dict[str, Any], fixture_report: dict[str, Any], artifact_hash: str) -> str:
    bundle = public_bundle(table, fixture_report, artifact_hash)
    check_public(bundle)
    public.mkdir(mode=0o755, parents=True, exist_ok=False)
    exclusive(public / 'data.json', encoded(bundle))
    (public / 'data.json').chmod(0o644)
    from workflow_access import register_export
    return register_export(root, public / 'data.json', artifact_hash)


def validate_access(root: Path, receipt: dict[str, Any], check_current: bool = True) -> None:
    challenge = read(root / 'access-challenge.json')
    if (receipt['schema'] != 'astrago-data-access-result-v1' or receipt['status'] != 'pass' or
            receipt['consumer_uid'] != challenge['consumer_uid'] or receipt['effective_uid'] != challenge['consumer_uid'] or
            receipt['challenge_sha256'] != identity(challenge) or
            receipt['software_sha256'] != challenge['software_sha256'] or
            sorted(receipt['denied']) != challenge['protected_paths'] or
            receipt['accessible'] or receipt['errors']):
        raise ValueError('Evaluator/consumer access boundary not verified')
    # Receipt is retained operator evidence, not a cryptographic OS attestation.
    if not check_current:
        return
    for name in challenge['protected_paths']:
        stat = Path(name).stat()
        if stat.st_uid != os.getuid() or stat.st_mode & 0o077:
            # Files inside the private run may be 0644 under its 0700 directory.
            if not Path(name).is_relative_to(root.resolve()) or root.stat().st_mode & 0o077:
                raise ValueError('Protected source ownership or permissions changed')
