"""Named synthetic runner diagnostics; never a real source/development corpus."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import time
from typing import Any

from campaign import encoded, exclusive, file_hash, read, now
from admission import (canonical, check_public, decode_output, identity, inventories,
                       private_directory, public_bundle, fixtures, raw_timeout_output)


def run_checks(lock_path: Path, output: Path, instruction: str | None) -> dict[str, Any]:
    if not instruction or not instruction.strip():
        raise ValueError('Explicit data execution instruction required')
    if file_hash(lock_path) != lock_path.stem:
        raise ValueError('Native diagnostic lock identity mismatch')
    lock = read(lock_path)
    binary = Path(lock['binary'])
    if file_hash(binary) != lock['binary_sha256']:
        raise ValueError('Native diagnostic binary identity mismatch')
    private_directory(output)
    calls: list[dict[str, Any]] = []
    cases: dict[str, str] = {}
    report: dict[str, Any] = {'schema': 'astrago-native-admission-checks-v1', 'status': 'fail',
                              'purpose': 'synthetic diagnostics only; not admitted source or development evidence',
                              'instruction': instruction, 'binary_sha256': lock['binary_sha256'],
                              'adapter_sha256': lock['adapter_sha256'], 'started_utc': now()}
    clock = time.monotonic()
    header = 'GM[1]FF[4]SZ[19]KM[7.5]RU[Chinese]C[startTurnIdx=0,initTurnNum=0,gameHash=' + '0' * 32 + ',gtype=normal]'

    def native(name: str, sgf: str) -> dict[str, Any]:
        call: dict[str, Any] = {'name': name, 'sgf': sgf, 'argv': [str(binary), 'astrago-admit'],
                                'started_utc': now(), 'status': 'dispatched'}
        calls.append(call)
        start = time.monotonic()
        try:
            result = subprocess.run(call['argv'], input=json.dumps({'sgf': sgf}) + '\n',
                                    capture_output=True, text=True, timeout=120)
            call.update(stdout=result.stdout, stderr=result.stderr, exit_code=result.returncode, status='completed')
            if result.returncode:
                raise ValueError('Native diagnostic process failed: ' + name)
            return json.loads(result.stdout)
        except subprocess.TimeoutExpired as error:
            call.update(status='timeout', **raw_timeout_output(error))
            raise
        except OSError as error:
            call.update(status='launch-error', reason=str(error))
            raise
        finally:
            call['duration_seconds'] = time.monotonic() - start

    def require(name: str, condition: bool) -> None:
        cases[name] = 'pass' if condition else 'fail'
        if not condition:
            raise ValueError('Native runner diagnostic failed: ' + name)

    try:
        for name, body in {'illegal': ';B[aa];W[aa]',
                           'post_terminal': ';B[aa];W[];B[];W[bb]',
                           'wrong_player': ';B[aa];B[bb]', 'setup': 'AB[aa];B[bb]'}.items():
            require(name, native(name, '(;' + header + body + ')')['status'] == 'excluded')
        require('wrong_rules', native('wrong_rules', '(;' + header.replace('RU[Chinese]', 'RU[Japanese]') + ';B[aa])')['status'] == 'excluded')
        require('trailing_content', native('trailing_content', '(;' + header + ';B[aa])garbage')['status'] == 'excluded')
        main = native('main_line', '(;' + header + ';B[aa](;W[bb])(;W[cc];B[dd]))')
        require('main_line', main['status'] == 'admitted' and main['moves'] == [['B', [0, 0]], ['W', [1, 1]]])
        records = []
        for x in range(1, 19):
            sgf = '(;' + header + ';B[aa];W[' + chr(97 + x) + 'b];B[' + chr(97 + x) + 'c])'
            result = native('independent_' + str(x), sgf)
            require('source_' + str(x), result['status'] == 'admitted')
            records.append({'id': identity(['synthetic', x]), 'native': result})
        table = inventories(records)
        counts = {split: sum(f['split'] == split for f in table['families']) for split in ['training', 'development', 'sealed']}
        require('input_order', table == inventories(list(reversed(records))))
        common = [r for r in table['candidates'] if len(r['history']['moves']) <= 1]
        require('split_priority', len(table['families']) == 18 and counts == {'training': 14, 'development': 1, 'sealed': 3}
                and len(common) == 2 and all(r['split'] == 'sealed' for r in common))
        mirrored = native('mirrored', '(;' + header + ';B[ss];W[rr];B[rq])')
        duplicated = inventories([*records, {'id': identity('synthetic-mirror'), 'native': mirrored}])
        require('symmetry', len(duplicated['families']) == 18 and len(duplicated['candidates']) == len(table['candidates']))
        context = {'rules': main['rules'], 'komi': 7.5, 'initial_player': 'B'}
        require('color', canonical([['B', [0, 0]], ['W', [1, 1]]], context)[0] !=
                canonical([['W', [0, 0]], ['B', [1, 1]]], context)[0])
        linked = inventories(records, [{'child_source_id': records[0]['id'], 'parent_source_id': records[1]['id'],
                                        'reviewer': 'synthetic diagnostic', 'provenance': 'Known diagnostic-only parent edge'}])
        require('ancestry', len(linked['families']) == 17 and any(len(f['sources']) == 2 for f in linked['families']))
        bundle = public_bundle(table, fixtures(table), '0' * 64)
        check_public(bundle)
        for name in ['board_only', 'cross_split']:
            bad = copy.deepcopy(bundle)
            if name == 'board_only':
                bad['payload']['candidates'][0]['history'] = {'schema': 'board-only-v1'}
            else:
                bad['payload']['sealed_candidate_ids'].append(bad['payload']['candidates'][0]['id'])
            bad['sha256'] = identity(bad['payload'])
            rejected = False
            try:
                check_public(bad)
            except ValueError:
                rejected = True
            require(name, rejected)
        report['status'] = 'pass'
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        report['reason'] = str(error)
    finally:
        report.update(cases=cases, calls=calls, duration_seconds=time.monotonic() - clock,
                      ended_utc=now(), software={p.name: file_hash(p) for p in Path(__file__).parent.glob('admission*') if p.is_file()})
        destination = output / (identity(report) + '.json')
        exclusive(destination, encoded(report))
    return {**report, 'artifact': str(destination)}
