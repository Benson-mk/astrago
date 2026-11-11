"""Native asset/build/smoke operations for the campaign runner's first slice."""
from __future__ import annotations

import gzip
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import selectors
import signal
import shutil
import subprocess
import sys
import time
from typing import Any
import urllib.request
import urllib.parse
import uuid
import zipfile

# The entry point is also importable when the retained runner is replayed.
from campaign import (CANDIDATES, REVISION, RULES, active, digest, encoded,
                      exclusive, file_hash, manifest, now, read, record, seal, is_stopped)


HTTP_HEADERS = {'User-Agent': 'AstraGo-campaign/1.0 (+https://github.com/Benson-mk/astrago)'}


class Unavailable(RuntimeError):
    pass


def portable(root: Path, text: str) -> str:
    text = text.replace(str(root.resolve()), 'training:.').replace(str(Path.home()), 'training:home')
    for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'http_proxy', 'https_proxy', 'all_proxy']:
        value = os.environ.get(key)
        if value:
            parsed = urllib.parse.urlsplit(value)
            for private in [value, parsed.netloc, parsed.hostname, parsed.username, parsed.password]:
                if private:
                    text = text.replace(private, '<REDACTED>')
                    text = text.replace(urllib.parse.unquote(private), '<REDACTED>')
    return text


def command(root: Path, argv: list[str], timeout: int = 600) -> str:
    if any(re.search(r'\$|\{\{|<[^>]+>', word) for word in argv):
        raise ValueError('Unresolved command variable')
    event_id = uuid.uuid4().hex
    start = now(); clock = time.monotonic()
    executable = (root / argv[0]).resolve() if '/' in argv[0] else Path(shutil.which(argv[0]) or '/nonexistent')
    invocation: dict[str, Any] = {'argv': argv, 'cwd': '.', 'role': 'training', 'environment_overrides': {},
                  'executable_sha256': file_hash(executable) if executable.is_file() else None}
    record(root, 'private-invocations', {'id': event_id, 'invocation': invocation,
                                         'physical_cwd': str(root.resolve()),
                                         'transport_environment': {k: os.environ[k] for k in
                                             ['HTTPS_PROXY', 'HTTP_PROXY', 'SSL_CERT_FILE', 'PIP_CERT', 'GIT_SSL_CAINFO']
                                             if k in os.environ}})
    # A pre-dispatch record makes interrupted work visible and non-replayable.
    record(root, 'events', {'id': event_id, 'phase': 'dispatch', 'started_utc': start,
                            'invocation': json.loads(portable(root, json.dumps(invocation))), 'charge_usd': None})
    code = None; out = ''; err = ''; status = 'inconclusive'
    try:
        p = subprocess.Popen(argv, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             text=True, start_new_session=True)
        try:
            out, err = p.communicate(timeout=timeout)
            code = p.returncode
            status = 'pass' if code == 0 else 'fail'
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            os.killpg(p.pid, signal.SIGKILL)
            out, err = p.communicate()
            err += '\nCommand interrupted or watchdog expired'
    except FileNotFoundError:
        err = 'Executable unavailable: ' + argv[0]
    finally:
        value = {'id': event_id, 'phase': 'result', 'started_utc': start, 'ended_utc': now(),
                 'duration_seconds': time.monotonic() - clock, 'invocation': json.loads(portable(root, json.dumps(invocation))),
                 'status': status, 'exit_code': code, 'stdout': portable(root, out),
                 'stderr': portable(root, err), 'charge_usd': None, 'billing_status': 'unknown'}
        record(root, 'events', value)
    if code is None:
        raise Unavailable(err)
    if code != 0:
        raise ValueError('Command failed: ' + argv[0] + '; inspect retained event')
    return out


def download(root: Path, url: str, relative: str) -> dict[str, Any]:
    target = root / relative
    if target.exists() or target.with_suffix(target.suffix + '.partial').exists():
        raise ValueError('Acquisition target already exists; do not replay uncertain work')
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + '.partial')
    event_id = uuid.uuid4().hex; start = now(); clock = time.monotonic()
    record(root, 'events', {'id': event_id, 'phase': 'dispatch', 'started_utc': start,
                            'operation': 'https-acquisition', 'url': url, 'target': relative, 'request_headers': HTTP_HEADERS,
                            'charge_usd': None})
    status = 'inconclusive'
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=HTTP_HEADERS), timeout=120) as response, partial.open('xb') as output:
            shutil.copyfileobj(response, output)
        partial.rename(target); status = 'pass'
    finally:
        measured = target if target.exists() else partial
        record(root, 'events', {'id': event_id, 'phase': 'result', 'started_utc': start,
                               'ended_utc': now(), 'duration_seconds': time.monotonic() - clock,
                               'status': status, 'operation': 'https-acquisition', 'url': url, 'request_headers': HTTP_HEADERS,
                               'target': relative, 'bytes': measured.stat().st_size if measured.exists() else 0,
                               'charge_usd': None, 'billing_status': 'unknown'})
    return {'path': relative, 'url': url, 'retrieved_utc': now(), 'sha256': file_hash(target),
            'bytes': target.stat().st_size, 'kind': 'original', 'parents': []}


def provision(root: Path) -> dict[str, Any]:
    # Exact top-level versions; download resolves transitive versions once and
    # preserves every wheel before installation from the resulting offline lock.
    command(root, ['python3', '-m', 'venv', 'runtime'], 120)
    python = 'runtime/bin/python3'
    wheels = ['cmake==3.31.6', 'numpy==2.2.6', 'packaging==25.0', 'torch==2.9.1']
    command(root, [python, '-m', 'pip', 'download', '--dest', 'inputs/wheels',
                   '--index-url', 'https://pypi.org/simple', '--only-binary=:all:', '--timeout', '30', '--retries', '1', *wheels], 1800)
    wheel_records = [{'path': p.relative_to(root).as_posix(), 'sha256': file_hash(p),
                      'bytes': p.stat().st_size} for p in sorted((root / 'inputs/wheels').glob('*'))]
    command(root, [python, '-m', 'pip', 'install', '--no-index', '--find-links',
                   'inputs/wheels', *wheels], 1800)
    freeze = command(root, [python, '-m', 'pip', 'freeze', '--all'])
    # Retain distribution archives and their copyright notices, without root.
    packages = ['libeigen3-dev', 'libzip-dev', 'libzip4t64']
    (root / 'inputs/debs').mkdir(parents=True, exist_ok=True)
    for package in packages:
        metadata = command(root, ['apt-cache', 'show', package])
        match = re.search(r'^Version: (.+)$', metadata, re.MULTILINE)
        if match is None:
            raise Unavailable('Missing distribution package: ' + package)
        command(root, ['apt-get', 'download', package + '=' + match.group(1)], 600)
    debs = []
    for path in sorted(root.glob('*.deb')):
        destination = root / 'inputs/debs' / path.name
        path.rename(destination)
        command(root, ['dpkg-deb', '-x', str(destination.relative_to(root)), 'runtime/system'])
        debs.append({'path': destination.relative_to(root).as_posix(),
                     'sha256': file_hash(destination), 'bytes': destination.stat().st_size})
    notices = []
    for path in sorted((root / 'runtime/system/usr/share/doc').rglob('copyright')):
        dest = root / 'evidence/notices' / (path.parent.name + '-copyright')
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        notices.append({'path': dest.relative_to(root).as_posix(), 'sha256': file_hash(dest)})

    for directory in sorted((root / 'runtime').glob('lib/python*/site-packages/*.dist-info')):
        for path in directory.rglob('*'):
            if path.is_file() and ('license' in path.name.lower() or 'notice' in path.name.lower() or 'licenses' in path.parts):
                dest = root / 'evidence/notices' / directory.name / path.relative_to(directory)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, dest)
                notices.append({'path': dest.relative_to(root).as_posix(), 'sha256': file_hash(dest)})
    lock = {'type': 'python-package-lock', 'requirements': wheels,
            'artifacts': wheel_records, 'installed': freeze,
            'index': 'https://pypi.org/simple', 'distribution_archives': debs, 'notices': notices}
    record(root, 'evidence', lock)
    return lock


def acquire(root: Path) -> dict[str, Any]:
    (root / 'source').mkdir(exist_ok=True)
    command(root, ['git', 'init', 'source/katago-clean'])
    command(root, ['git', '-C', 'source/katago-clean', 'remote', 'add', 'origin',
                   'https://github.com/lightvector/KataGo.git'])
    command(root, ['git', '-C', 'source/katago-clean', 'fetch', '--depth', '1', 'origin', REVISION], 600)
    command(root, ['git', '-C', 'source/katago-clean', 'checkout', '--detach', REVISION])
    actual = command(root, ['git', '-C', 'source/katago-clean', 'rev-parse', 'HEAD']).strip()
    if actual != REVISION:
        raise ValueError('Wrong KataGo source revision')
    assets = []
    for candidate in CANDIDATES:
        for suffix, route, role in [('.zip', 'zips', 'checkpoint_archive'),
                                     ('.bin.gz', 'models', 'official_playable')]:
            asset_path = 'inputs/' + candidate + suffix
            asset = download(root, f'https://media.katagotraining.org/uploaded/networks/{route}/kata1/{candidate}{suffix}', asset_path)
            asset.update(candidate=candidate, role=role, license='evidence/network-license.html')
            assets.append(asset)
        with zipfile.ZipFile(root / ('inputs/' + candidate + '.zip')) as archive:
            destination = root / 'inputs/extracted' / candidate
            for member in archive.infolist():
                target = destination / member.filename
                if not target.resolve().is_relative_to(destination.resolve()) or (member.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('Unsafe archive member')
            archive.extractall(destination)
        parent = next(a['sha256'] for a in assets if a.get('candidate') == candidate and a['role'] == 'checkpoint_archive')
        for path in sorted(destination.rglob('*')):
            if path.is_file():
                assets.append({'path': path.relative_to(root).as_posix(), 'candidate': candidate,
                               'role': 'archive_member', 'sha256': file_hash(path),
                               'bytes': path.stat().st_size, 'kind': 'derived', 'parents': [parent],
                               'license': 'evidence/network-license.html'})
    license_asset = download(root, 'https://katagotraining.org/network_license/', 'evidence/network-license.html')
    assets.append(license_asset)
    engine_license = root / 'source/katago-clean/LICENSE'
    shutil.copyfile(engine_license, root / 'evidence/engine-LICENSE')
    assets.append({'path': 'evidence/engine-LICENSE', 'sha256': file_hash(engine_license),
                   'bytes': engine_license.stat().st_size, 'kind': 'derived', 'parents': [REVISION]})
    # Original official model headers are read separately from trainable state.
    headers = {}
    for candidate in CANDIDATES:
        with gzip.open(root / ('inputs/' + candidate + '.bin.gz'), 'rb') as stream:
            headers[candidate] = [stream.readline().decode().strip() for _ in range(2)]
        if headers[candidate][1] != '17':
            raise ValueError('Official artifact is not model version 17')
    record(root, 'evidence', {'type': 'assets', 'assets': assets, 'official_headers': headers,
                             'source_revision': actual, 'regular_equals_official': 'unknown'})
    return {'assets': assets, 'official_headers': headers, 'source_revision': actual}


def asset_report(root: Path) -> dict[str, Any]:
    matches = [read(p) for p in (root / 'reports').glob('*.json') if read(p).get('operation') == 'acquire' and read(p)['status'] == 'pass']
    if len(matches) != 1:
        raise Unavailable('Exactly one completed acquisition report required')
    report = matches[0]
    if report['manifest_sha256'] != file_hash(root / 'manifest.json'):
        raise ValueError('Stale acquisition report')
    for asset in report['result']['assets']:
        if file_hash(root / asset['path']) != asset['sha256']:
            raise ValueError('Wrong asset identity: ' + asset['path'])
    return report


def build(root: Path) -> dict[str, Any]:
    assets = asset_report(root)
    package_locks = [read(p) for p in (root / 'reports').glob('*.json')
                     if read(p).get('operation') == 'provision' and read(p)['status'] == 'pass']
    if len(package_locks) != 1:
        raise Unavailable('Exactly one completed package lock required')
    for asset in package_locks[0]['result']['artifacts'] + package_locks[0]['result']['distribution_archives']:
        if file_hash(root / asset['path']) != asset['sha256']:
            raise ValueError('Dependency package identity changed')
    if command(root, ['git', '-C', 'source/katago-clean', 'rev-parse', 'HEAD']).strip() != REVISION:
        raise ValueError('Wrong source revision')
    if command(root, ['git', '-C', 'source/katago-clean', 'status', '--porcelain']).strip():
        raise ValueError('Pristine source is dirty')
    # The caller provisions the exact runtime before this operation. Never upgrade the OS/driver.
    tools = {}
    for argv in [['runtime/bin/cmake', '--version'], ['g++-12', '--version'], ['nvcc', '--version'],
                 ['runtime/bin/python3', '-m', 'pip', 'freeze', '--all']]:
        tools[argv[0] + ':' + argv[-1]] = portable(root, command(root, argv))
    runtime = json.loads(command(root, ['runtime/bin/python3', '-c',
        'import torch,numpy,packaging,json; print(json.dumps({"torch":torch.__version__,"numpy":numpy.__version__,"packaging":packaging.__version__,"cuda":torch.version.cuda,"available":torch.cuda.is_available(),"bf16":torch.cuda.is_bf16_supported()}))']))
    if not runtime['available'] or not runtime['bf16']:
        raise Unavailable('Training Python CUDA/BF16 runtime unavailable')
    audits = []
    for candidate, width in zip(CANDIDATES, [384, 512, 768]):
        checkpoints = list((root / 'inputs/extracted' / candidate).rglob(candidate + '.ckpt'))
        if len(checkpoints) != 1:
            raise ValueError('Exactly one original candidate checkpoint required')
        output = command(root, ['runtime/bin/python3', os.path.relpath(Path(__file__).with_name('checkpoint_audit.py').resolve(), root.resolve()),
                                str(checkpoints[0].relative_to(root)), str(width)])
        audits.append(json.loads(output))
    record(root, 'evidence', {'type': 'checkpoint_audits', 'audits': audits})
    binaries = {}
    attempt = uuid.uuid4().hex
    for backend in ['EIGEN', 'CUDA']:
        destination = 'build/' + attempt + '/' + backend.lower()
        options = ['-DUSE_BACKEND=' + backend, '-DCMAKE_BUILD_TYPE=Release',
                   '-DCMAKE_C_COMPILER=/usr/bin/gcc-12', '-DCMAKE_CXX_COMPILER=/usr/bin/g++-12',
                   '-DCUDA_HOST_COMPILER=/usr/bin/gcc-12',
                   '-DCMAKE_PREFIX_PATH=' + str(root.resolve() / 'runtime/system/usr')]
        if backend == 'CUDA':
            includes = list((root / 'runtime').glob('lib/python*/site-packages/nvidia/cudnn/include'))
            if len(includes) != 1:
                raise Unavailable('Exactly one cuDNN wheel installation required')
            cudnn = includes[0].resolve()
            options += ['-DCUDNN_INCLUDE_DIR=' + str(cudnn),
                        '-DCUDNN_LIBRARY=' + str(cudnn.parent / 'lib/libcudnn.so.9')]
        command(root, ['runtime/bin/cmake', '-S', 'source/katago-clean/cpp', '-B', destination,
                       *options], 600)
        command(root, ['runtime/bin/cmake', '--build', destination, '--parallel', '2'], 3600)
        binary = destination + '/katago'
        version = command(root, [binary, 'version'])
        cache = root / destination / 'CMakeCache.txt'
        # Keep build locks and tool diagnostics within the artifact.
        cache_copy = root / ('evidence/build-' + attempt + '/' + backend.lower() + '-CMakeCache.txt')
        cache_copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(cache, cache_copy)
        dependencies = command(root, ['ldd', binary])
        if 'not found' in dependencies:
            raise Unavailable('Native dynamic dependency unresolved')
        libraries = []
        linked = set(re.findall(r'(?:=> )?(/\S+) \(', dependencies))
        linked.update(str(p.resolve()) for p in (root / 'runtime').glob('lib/python*/site-packages/nvidia/**/*.so*') if p.is_file())
        for name in sorted(linked):
            path = Path(name)
            location = str(path.relative_to(root.resolve())) if path.is_relative_to(root.resolve()) else str(path)
            libraries.append({'name': path.name, 'path': location, 'sha256': file_hash(path)})
        binaries[backend] = {'path': binary, 'sha256': file_hash(root / binary),
                             'version': version, 'libraries': libraries}
    lock = {'type': 'runtime_lock', 'tools': tools, 'python': runtime, 'binaries': binaries,
            'source_revision': REVISION, 'acquisition_sha256': digest(encoded(assets)),
            'audits': audits}
    record(root, 'evidence', lock)
    return lock


def exchange(process: subprocess.Popen[bytes], selector: selectors.BaseSelector,
             request: str, sequence: int, transcript: list[dict[str, Any]]) -> str:
    assert process.stdin is not None and process.stdout is not None
    started = now(); clock = time.monotonic(); raw = b''
    process.stdin.write(f'{sequence} {request}\n'.encode()); process.stdin.flush()
    try:
        while b'\n\n' not in raw.replace(b'\r\n', b'\n'):
            if not selector.select(max(0, 300 - (time.monotonic() - clock))):
                raise Unavailable('Native response watchdog expired')
            chunk = os.read(process.stdout.fileno(), 65536)
            if not chunk:
                raise ValueError('Native process ended before complete response')
            raw += chunk
        response = raw.decode().strip()
        match = re.fullmatch(r'=' + str(sequence) + r'(?:\s+(.*))?', response, re.DOTALL)
        if not match:
            raise ValueError('Native protocol error')
        return match.group(1) or ''
    finally:
        transcript.append({'request': f'{sequence} {request}', 'response': raw.decode(errors='replace'),
                           'started_utc': started, 'duration_seconds': time.monotonic() - clock})


def check_transcript(transcript: list[dict[str, Any]]) -> str:
    expected = ['protocol_version', 'boardsize 19', 'clear_board', 'kata-set-rules chinese',
                'komi 7.5', 'kata-get-rules', 'get_komi', 'genmove b', 'undo']
    if len(transcript) != 11:
        raise ValueError('Incomplete native smoke transcript')
    replies = []
    for i, entry in enumerate(transcript, 1):
        match = re.fullmatch(r'=' + str(i) + r'(?:\s+(.*))?', entry['response'].strip(), re.DOTALL)
        if not match or entry['duration_seconds'] < 0:
            raise ValueError('Invalid native response')
        replies.append(match.group(1) or '')
    move = replies[7]
    if not re.fullmatch(r'(?:[A-HJ-T](?:[1-9]|1[0-9])|pass)', move, re.I):
        raise ValueError('Invalid move coordinate or resignation')
    expected += ['play b ' + move, 'quit']
    if [t['request'] for t in transcript] != [f'{i} {r}' for i, r in enumerate(expected, 1)]:
        raise ValueError('Native command sequence mismatch')
    if replies[0] != '2' or json.loads(replies[5]) != RULES or float(replies[6]) != 7.5:
        raise ValueError('Effective native settings mismatch')
    return move


CONFIG = '''rules = chinese
komi = 7.5
maxVisits = 1
numSearchThreads = 1
nnCacheSizePowerOfTwo = 16
nnMutexPoolSizePowerOfTwo = 12
numNNServerThreadsPerModel = 1
ponderingEnabled = false
allowResignation = false
resignThreshold = -1.0
logToStderr = true
logAllGTPCommunication = true
logSearchInfo = true
cudaUseFP16 = true
'''


def verify_libraries(root: Path, libraries: list[dict[str, Any]]) -> None:
    for library in libraries:
        path = Path(library['path'])
        if not path.is_absolute():
            path = root / path
        if file_hash(path) != library['sha256']:
            raise ValueError('Runtime dependency identity mismatch: ' + library['name'])


def smoke(root: Path) -> dict[str, Any]:
    asset_report(root)
    builds = [read(p) for p in (root / 'reports').glob('*.json') if read(p).get('operation') == 'build' and read(p)['status'] == 'pass' and read(p).get('adapter_sha256') == file_hash(Path(__file__))]
    if len(builds) != 1:
        raise Unavailable('Pinned training/CPU-reference runtime not available')
    build_report = builds[0]
    if build_report.get('adapter_sha256') != file_hash(Path(__file__)):
        raise ValueError('Stale native build software identity')
    if build_report['manifest_sha256'] != file_hash(root / 'manifest.json'):
        raise ValueError('Stale build report')
    for binary in build_report['result']['binaries'].values():
        if file_hash(root / binary['path']) != binary['sha256']:
            raise ValueError('Runtime binary identity mismatch')
        verify_libraries(root, binary['libraries'])
    attempt_dir = root / 'evidence' / ('smoke-' + uuid.uuid4().hex)
    config_path = (attempt_dir / 'smoke.cfg').relative_to(root).as_posix()
    exclusive(root / config_path, CONFIG.encode())
    binary = build_report['result']['binaries']['CUDA']['path']
    argv = [binary, 'gtp', '-model', 'inputs/' + CANDIDATES[0] + '.bin.gz',
            '-config', config_path]
    transcript: list[dict[str, Any]] = []
    invocation: dict[str, Any] = {'argv': argv, 'cwd': '.', 'role': 'training', 'environment_overrides': {}}
    event_id = uuid.uuid4().hex; start = now(); clock = time.monotonic()
    record(root, 'events', {'id': event_id, 'phase': 'dispatch', 'operation': 'native-smoke',
                            'started_utc': start, 'invocation': invocation, 'charge_usd': None})
    with (attempt_dir / 'native-stderr.txt').open('xb') as stderr:
        process = subprocess.Popen(argv, cwd=root, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr)
        try:
            with selectors.DefaultSelector() as selector:
                assert process.stdout is not None
                selector.register(process.stdout, selectors.EVENT_READ)
                for request in ['protocol_version', 'boardsize 19', 'clear_board', 'kata-set-rules chinese',
                                'komi 7.5', 'kata-get-rules', 'get_komi', 'genmove b', 'undo']:
                    exchange(process, selector, request, len(transcript) + 1, transcript)
                move = transcript[7]['response'].strip().split(maxsplit=1)[1]
                for request in ['play b ' + move, 'quit']:
                    exchange(process, selector, request, len(transcript) + 1, transcript)
                process.wait(timeout=10)
                if process.returncode != 0:
                    raise ValueError('Native runtime exited unsuccessfully')
        finally:
            if process.poll() is None:
                process.kill(); process.wait()
            record(root, 'events', {'id': event_id, 'phase': 'result', 'operation': 'native-smoke',
                                    'started_utc': start, 'ended_utc': now(),
                                    'duration_seconds': time.monotonic() - clock,
                                    'status': 'pass' if len(transcript) == 11 and process.returncode == 0 else 'inconclusive',
                                    'charge_usd': None, 'billing_status': 'unknown'})
            record(root, 'evidence', {'type': 'native_transcript', 'invocation': invocation,
                                     'transcript': transcript})
    move = check_transcript(transcript)
    return {'move': move, 'transcript': transcript, 'invocation': invocation,
            'build_sha256': digest(encoded(build_report)), 'config_path': config_path, 'config_sha256': file_hash(root / config_path),
            'complete_game_gate': False, 'm4_deployment_gate': False}


def check_capacity(root: Path, inventory: Path | None) -> dict[str, Any]:
    if inventory is None:
        raise Unavailable('Fresh coordinator inventory required before runtime dispatch')
    evidence = read(inventory)
    record(root, 'evidence', {'type': 'coordinator_inventory', 'inventory': evidence})
    if evidence.get('schema') != 'astrago-coordinator-inventory-v1' or evidence.get('role') != 'coordinator':
        raise ValueError('Wrong coordinator inventory schema or role')
    observed = datetime.fromisoformat(evidence['timestamp_utc'])
    age = (datetime.now(timezone.utc) - observed).total_seconds()
    if age < 0 or age > 3600:
        raise Unavailable('Coordinator capacity inventory is stale')
    if evidence['free_bytes'] < 20 * 2**30:
        raise Unavailable('Coordinator has less than adopted 20 GiB free-space floor')
    training_free = shutil.disk_usage(root).free
    campaign_bytes = sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
    if training_free < 50 * 2**30:
        raise Unavailable('Training free space cannot cover the adopted 50 GiB pilot envelope')
    if campaign_bytes > 50 * 2**30:
        raise Unavailable('Training campaign exceeds adopted 50 GiB pilot cap')
    capacity = {'type': 'capacity_check', 'timestamp_utc': now(),
                'coordinator_inventory': evidence, 'coordinator_inventory_sha256': digest(encoded(evidence)),
                'training_free_bytes': training_free, 'campaign_bytes': campaign_bytes}
    path = record(root, 'evidence', capacity)
    return {**capacity, 'record_sha256': path.stem}


def execute(root: Path, operation: str, retry: bool = False, inventory: Path | None = None) -> dict[str, Any]:
    active(root)
    claim = root / 'claims' / (operation + '.json')
    exclusive(claim, encoded({'operation': operation, 'timestamp_utc': now()}))
    try:
        active(root)
        previous = [read(p) for p in (root / 'reports').glob('*.json')
                    if read(p).get('operation') == operation]
        if previous and (not retry or any(r['status'] == 'pass' and
                (operation != 'build' or r.get('adapter_sha256') == file_hash(Path(__file__))) for r in previous)):
            raise ValueError('Operation already attempted; explicit retry only after failure')
        if retry and not previous:
            raise ValueError('No completed failure to retry; unresolved dispatch must be reconciled')
        completed = {(read(p)['operation'], read(p)['started_utc']) for p in (root / 'reports').glob('*.json')}
        for path in (root / 'events').glob('*.json'):
            event = read(path)
            if event.get('phase') == 'operation-start' and event['operation'] == operation:
                if (operation, event['started_utc']) not in completed:
                    raise ValueError('Unresolved operation dispatch; reconcile before retry')
    except BaseException:
        # No dispatch or relocation has happened; release only our own claim.
        claim.unlink()
        raise
    if retry and operation == 'acquire':
        retained = root / 'failed-attempts' / uuid.uuid4().hex
        for name in ['source', 'inputs/extracted']:
            path = root / name
            if path.exists():
                destination = retained / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                path.rename(destination)
        for path in (root / 'inputs').glob('kata1-*'):
            destination = retained / 'inputs' / path.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            path.rename(destination)
        record(root, 'evidence', {'type': 'failed-acquisition-retained',
                                 'files': [{'path': p.relative_to(root).as_posix(),
                                            'sha256': file_hash(p), 'bytes': p.stat().st_size}
                                           for p in retained.rglob('*') if p.is_file()]})
    start = now(); clock = time.monotonic(); status = 'inconclusive'; result = {}; reason = ''
    record(root, 'events', {'id': uuid.uuid4().hex, 'phase': 'operation-start',
                            'operation': operation, 'started_utc': start, 'charge_usd': None})
    inventory_sha256 = None
    try:
        if operation == 'smoke' and not any(read(p).get('operation') == 'build' and read(p)['status'] == 'pass' and read(p).get('adapter_sha256') == file_hash(Path(__file__)) for p in (root / 'reports').glob('*.json')):
            raise Unavailable('Pinned training/CPU-reference runtime not available')
        capacity = check_capacity(root, inventory)
        inventory_sha256 = capacity['coordinator_inventory_sha256']
        result = {'provision': provision, 'acquire': acquire, 'build': build, 'smoke': smoke}[operation](root)
        status = 'pass'
    except (Unavailable, OSError, subprocess.TimeoutExpired) as error:
        reason = portable(root, str(error))
    except (ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        status = 'fail'; reason = portable(root, str(error))
    report = {'schema': 'astrago-gate-v1', 'operation': operation, 'status': status,
              'advance': status == 'pass', 'reason': reason, 'result': result,
              'coordinator_inventory_sha256': inventory_sha256,
              'manifest_sha256': file_hash(root / 'manifest.json'),
              'runner_sha256': file_hash(Path(__file__).with_name('campaign.py')),
              'adapter_sha256': file_hash(Path(__file__)),
              'started_utc': start, 'ended_utc': now(), 'duration_seconds': time.monotonic() - clock,
              'charge_usd': None, 'billing_status': 'unknown'}
    if is_stopped(root):
        report.update(status='incomplete', advance=False, reason='Campaign stopped during operation')
    record(root, 'reports', report)
    claim.unlink()
    artifact = seal(root)
    return {**report, 'artifact': artifact.relative_to(root).as_posix()}
