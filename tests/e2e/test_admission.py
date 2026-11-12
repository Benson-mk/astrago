"""Admission tests use only the confirmed public campaign runner boundary."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


class AdmissionE2E(unittest.TestCase):
    def test_plan_and_fail_closed_without_execution_authority(self):
        calls = []
        passed = False
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)

            def run(*args):
                argv = [sys.executable, str(ROOT / 'tools/campaign.py'), *map(str, args)]
                start = time.monotonic()
                result = subprocess.run(argv, capture_output=True, text=True)
                calls.append(dict(argv=argv, stdout=result.stdout, stderr=result.stderr,
                                  exit_code=result.returncode, seconds=time.monotonic() - start))
                return result

            try:
                config = work / 'data.json'
                p = run('data-plan', '--output', config)
                self.assertEqual(p.returncode, 0, p.stderr)
                plan = json.loads(config.read_text())
                self.assertEqual(plan['archive_dates'], ['2026-11-06', '2026-11-05', '2026-11-04',
                                                        '2026-11-03', '2026-11-02', '2026-11-01'])
                self.assertIsNone(plan['required_training_candidates'])
                p = run('data-admit', '--manifest', config, '--output', work / 'private',
                        '--public-output', work / 'public')
                self.assertNotEqual(p.returncode, 0)
                self.assertIn('Explicit data execution instruction required', p.stderr)
                self.assertFalse((work / 'private').exists())
                p = run('data-admit', '--manifest', config, '--output', work / 'private',
                        '--public-output', work / 'public', '--instruction', 'Synthetic rejection case only')
                self.assertNotEqual(p.returncode, 0)
                self.assertIn('Unresolved', p.stderr)
                self.assertFalse((work / 'private').exists())
                # Board-only or forged cross-split fixtures never enter debugging.
                bad = work / 'bad.json'
                bad.write_text(json.dumps({'schema': 'board-only-v1', 'board_hash': '0' * 64}))
                p = run('data-inputs', '--run', work / 'unregistered', '--bundle', bad, '--split', 'development')
                self.assertNotEqual(p.returncode, 0)
                self.assertIn('approved export reference', p.stderr)
                p = run('data-inputs', '--run', work / 'unregistered', '--bundle', bad, '--split', 'sealed')
                self.assertNotEqual(p.returncode, 0)
                self.assertNotIn('board_hash', p.stdout)
                # A retained failed gate must still have exact storage arithmetic.
                artifact_dir = work / 'failed-run/artifacts'
                artifact_dir.mkdir(parents=True)
                stale = {'schema': 'astrago-data-evidence-v1', 'files': {},
                         'report': {'status': 'fail',
                                    'storage_measurements': {'data_files': {}, 'campaign_files': {}},
                                    'storage': {'artifact_bytes': 0, 'new_public_bytes': 0,
                                                'data_bytes_including_new_export': 0,
                                                'campaign_bytes_including_new_export': 0}}}
                raw = json.dumps(stale, sort_keys=True).encode()
                artifact = artifact_dir / (hashlib.sha256(raw).hexdigest() + '.json')
                artifact.write_bytes(raw)
                p = run('data-verify', '--artifact', artifact, '--offline')
                self.assertNotEqual(p.returncode, 0)
                self.assertIn('storage arithmetic mismatch', p.stderr)
                passed = True
            finally:
                data = json.dumps({'schema': 'astrago-admission-e2e-v1', 'status': 'pass' if passed else 'fail',
                                   'native_admission': 'not_run', 'calls': calls, 'python': sys.version,
                                   'inputs_outputs': {p.relative_to(work).as_posix(): p.read_text()
                                                      for p in work.rglob('*') if p.is_file()},
                                   'test_source': Path(__file__).read_text(),
                                   'software': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                                for p in (ROOT / 'tools').glob('*') if p.is_file()}},
                                  sort_keys=True, indent=2).encode()
                target = ROOT / '.local/issue-14/e2e'
                target.mkdir(parents=True, exist_ok=True)
                (target / (hashlib.sha256(data).hexdigest() + '.json')).write_bytes(data)

# Actual corpus verification is deliberately opt-in: it consumes a retained
# artifact from separately authorized native admission, never fabricated games.
class RetainedAdmissionE2E(unittest.TestCase):
    def test_real_retained_admission(self):
        import os
        retained = os.environ.get('ASTRAGO_ADMISSION_ARTIFACT')
        evidence: dict[str, Any] = {'case': self.id(), 'status': 'skipped', 'native_admission': 'unverified',
                    'python': sys.version, 'calls': []}
        try:
            if not retained:
                self.skipTest('Passing fixture-frozen corpus artifact not supplied; positive corpus gate unverified')
            evidence['status'] = 'fail'
            evidence['input_sha256'] = hashlib.sha256(Path(retained).read_bytes()).hexdigest()
            argv = [sys.executable, str(ROOT / 'tools/campaign.py'), 'data-verify',
                    '--artifact', retained, '--offline']
            p = subprocess.run(argv, capture_output=True, text=True)
            evidence['calls'].append(dict(argv=argv, stdout=p.stdout, stderr=p.stderr, exit_code=p.returncode))
            evidence['status'] = 'fail'
            self.assertEqual(p.returncode, 0, p.stderr)
            report = json.loads(p.stdout)
            self.assertEqual(report['deterministic_replay'], 'pass')
            self.assertEqual(report['native_status'], 'pass')
            self.assertFalse(report['runtime_executed'])
            evidence['status'] = 'pass'
            evidence['native_admission'] = 'retained_pass'
        finally:
            evidence['software'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / 'tools').glob('*') if p.is_file()}
            evidence['test_source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
            evidence['failure'] = str(sys.exc_info()[1]) if sys.exc_info()[1] else None
            data = json.dumps(evidence, sort_keys=True, indent=2).encode()
            target = ROOT / '.local/issue-14/e2e'
            target.mkdir(parents=True, exist_ok=True)
            (target / (hashlib.sha256(data).hexdigest() + '.json')).write_bytes(data)


class NativeAdmissionE2E(unittest.TestCase):
    def test_native_rejection_and_identity_cases(self):
        import os
        lock = os.environ.get('ASTRAGO_NATIVE_REPLAY_LOCK')
        instruction = os.environ.get('ASTRAGO_DATA_EXECUTION_INSTRUCTION')
        evidence: dict[str, Any] = {'case': self.id(), 'status': 'skipped', 'calls': [], 'python': sys.version}
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            try:
                if not lock or not instruction:
                    self.skipTest('Separate native diagnostic execution authorization/lock not supplied')
                evidence['status'] = 'fail'
                argv = [sys.executable, str(ROOT / 'tools/campaign.py'), 'data-check-native',
                        '--native-lock', lock, '--output', str(work / 'check'), '--instruction', instruction]
                p = subprocess.run(argv, capture_output=True, text=True)
                evidence['calls'].append(dict(argv=argv, stdout=p.stdout, stderr=p.stderr, exit_code=p.returncode))
                evidence['status'] = 'fail'
                self.assertEqual(p.returncode, 0, p.stderr)
                report = json.loads(p.stdout)
                for case in ['illegal', 'post_terminal', 'wrong_rules', 'setup', 'wrong_player',
                             'trailing_content', 'main_line', 'symmetry', 'color', 'ancestry',
                             'split_priority', 'input_order', 'board_only', 'cross_split']:
                    self.assertEqual(report['cases'][case], 'pass', case)
                evidence['status'] = 'pass'
            finally:
                evidence['software'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / 'tools').glob('*') if p.is_file()}
                evidence['test_source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
                evidence['failure'] = str(sys.exc_info()[1]) if sys.exc_info()[1] else None
                evidence['retained'] = {p.relative_to(work).as_posix(): p.read_text(errors='replace')
                                        for p in work.rglob('*') if p.is_file()}
                data = json.dumps(evidence, sort_keys=True, indent=2).encode()
                target = ROOT / '.local/issue-14/e2e'
                target.mkdir(parents=True, exist_ok=True)
                (target / (hashlib.sha256(data).hexdigest() + '.json')).write_bytes(data)



class ArchivePrefixE2E(unittest.TestCase):
    def test_insufficient_prefix_remains_unfrozen(self):
        import os
        manifest = os.environ.get('ASTRAGO_PREFIX_MANIFEST')
        output = os.environ.get('ASTRAGO_PREFIX_OUTPUT')
        if not manifest or not output:
            raw = json.dumps({'case': self.id(), 'status': 'skipped',
                              'reason': 'Authorized archive prefix not supplied',
                              'test_source': Path(__file__).read_text()}, sort_keys=True).encode()
            target = ROOT/'.local/issue-14/e2e'; target.mkdir(parents=True, exist_ok=True)
            (target/(hashlib.sha256(raw).hexdigest()+'.json')).write_bytes(raw)
            self.skipTest('Authorized real archive prefix not supplied')
        root = Path(output)
        argv = [sys.executable, str(ROOT/'tools/campaign.py'), 'data-admit',
                '--manifest', manifest, '--output', str(root), '--public-output', str(root)+'-public',
                '--instruction', 'User approved bounded issue-14 admission under original H0']
        start = time.monotonic()
        evidence: dict[str, Any] = {'case': self.id(), 'status': 'fail', 'argv': argv,
                    'purpose': 'Prefix control flow; source provenance requires separate acquisition evidence',
                    'test_source': Path(__file__).read_text()}
        try:
            evidence['manifest_sha256'] = hashlib.sha256(Path(manifest).read_bytes()).hexdigest()
            result = subprocess.run(argv, capture_output=True, text=True)
            evidence.update(stdout=result.stdout, stderr=result.stderr, exit_code=result.returncode, seconds=time.monotonic()-start)
            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report['status'], 'incomplete')
            self.assertEqual(report['source_expansion'], 'next-archive-required')
            self.assertEqual(report['next_archive_date'], '2026-11-05')
            self.assertFalse((root/'sources-frozen.json').exists())
            self.assertFalse((root/'inventory.json').exists())
            self.assertFalse(Path(str(root)+'-public').exists())
            check = subprocess.run([sys.executable, str(ROOT/'tools/campaign.py'), 'data-verify',
                                    '--artifact', report['artifact'], '--offline'], capture_output=True, text=True)
            evidence['offline'] = {'stdout': check.stdout, 'stderr': check.stderr, 'exit_code': check.returncode}
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertEqual(json.loads(check.stdout)['deterministic_replay'], 'pass')
            evidence['status'] = 'pass'
        finally:
            evidence['failure'] = str(sys.exc_info()[1]) if sys.exc_info()[1] else None
            raw = json.dumps(evidence, sort_keys=True, indent=2).encode()
            target = ROOT/'.local/issue-14/e2e'; target.mkdir(parents=True,exist_ok=True)
            (target/(hashlib.sha256(raw).hexdigest()+'.json')).write_bytes(raw)

class StaleDiagnosticsE2E(unittest.TestCase):
    def test_stale_transform_diagnostics_reject_before_admission(self):
        import os
        manifest = os.environ.get('ASTRAGO_PREFIX_MANIFEST')
        evidence: dict[str, Any] = {'case': self.id(), 'status': 'skipped', 'calls': [],
                                   'test_source': Path(__file__).read_text()}
        try:
            if not manifest:
                self.skipTest('Authorized native diagnostic manifest not supplied')
            evidence['status'] = 'fail'
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                config = json.loads(Path(manifest).read_text())
                checks = json.loads(Path(config['native_checks']).read_text())
                checks['software']['admission.py'] = '0'*64
                raw = (json.dumps(checks,sort_keys=True,indent=2)+'\n').encode()
                check_file = root/(hashlib.sha256(raw).hexdigest()+'.json');check_file.write_bytes(raw)
                config['native_checks'] = str(check_file)
                plan_file=root/'plan.json';plan_file.write_text(json.dumps(config))
                argv=[sys.executable,str(ROOT/'tools/campaign.py'),'data-admit','--manifest',str(plan_file),
                      '--output',str(root/'private'),'--public-output',str(root/'public'),
                      '--instruction','User-approved synthetic stale-diagnostic rejection']
                p=subprocess.run(argv,capture_output=True,text=True)
                evidence['calls'].append(dict(argv=argv,stdout=p.stdout,stderr=p.stderr,exit_code=p.returncode))
                self.assertNotEqual(p.returncode,0)
                self.assertIn('Stale native transformation diagnostics',p.stderr)
                self.assertFalse((root/'private').exists())
                evidence['status']='pass'
        finally:
            evidence['failure']=str(sys.exc_info()[1]) if sys.exc_info()[1] else None
            raw=json.dumps(evidence,sort_keys=True,indent=2).encode()
            target=ROOT/'.local/issue-14/e2e';target.mkdir(parents=True,exist_ok=True)
            (target/(hashlib.sha256(raw).hexdigest()+'.json')).write_bytes(raw)

class BoundedEmptyAdmissionE2E(unittest.TestCase):
    def test_bounded_empty_corpus_reports_unmet_gate(self):
        import os
        retained = os.environ.get('ASTRAGO_BOUNDED_ZERO_ARTIFACT')
        evidence: dict[str, Any] = {'case': self.id(), 'status': 'skipped', 'calls': [],
                                   'purpose': 'Verify the explicitly expected bounded-empty outcome; never a passing fixture seal',
                                   'test_source': Path(__file__).read_text(), 'python': sys.version}
        try:
            if not retained:
                self.skipTest('Fully bounded expected-empty corpus artifact not supplied')
            evidence['status'] = 'fail'
            artifact = Path(retained)
            root = artifact.parent.parent
            evidence['input_artifact_path'] = str(artifact.resolve())
            evidence['input_artifact_sha256'] = hashlib.sha256(artifact.read_bytes()).hexdigest()
            value = json.loads(artifact.read_text())
            report = value['report']
            # These are the runner's retained output artifacts, not internal helpers.
            frozen = json.loads((root/'sources-frozen.json').read_text())
            config = json.loads((root/'manifest.json').read_text())
            evidence.update(sources=frozen, configuration=config,
                            native_checks_sha256=hashlib.sha256((root/'native-checks.json').read_bytes()).hexdigest(),
                            configuration_sha256=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest(),
                            measured_storage=report['storage'], shortages=report.get('shortages'))
            self.assertEqual([row['date'] for row in frozen],
                             ['2026-11-06','2026-11-05','2026-11-04','2026-11-03','2026-11-02','2026-11-01'])
            self.assertEqual(report['status'], 'incomplete')
            self.assertFalse(report['advance'])
            self.assertEqual(report['source_expansion'], 'eligibility-only-before-split')
            expected_shortages = {'required_training_candidates', 'required_development_candidates',
                                  'required_sealed_candidates', 'required_development_families', 'required_sealed_families'}
            self.assertEqual(set(report['shortages']), expected_shortages)
            for shortfall in report['shortages'].values():
                self.assertEqual(shortfall['observed'], 0)
                self.assertGreater(shortfall['required'], 0)
            categories = ['opening','quiet_midgame','capture_atari','immediate_ko',
                          'later_legal_recapture','same_stones_different_history','single_pass',
                          'late_endgame','seki','black_to_move','white_to_move','asymmetric_coordinates']
            fixtures = report['fixtures']
            self.assertEqual(fixtures['playable_available'], 0)
            self.assertEqual(fixtures['required_playable'], 32)
            self.assertEqual(set(fixtures['unverified_categories']), set(categories))
            self.assertEqual(fixtures['selected'], [])
            self.assertEqual(fixtures['terminal_checks'], [])

            def invoke(*args, expected_exit=0):
                argv = [sys.executable, str(ROOT/'tools/campaign.py'), *map(str,args)]
                start = time.monotonic()
                p = subprocess.run(argv, capture_output=True, text=True)
                evidence['calls'].append(dict(argv=argv, stdout=p.stdout, stderr=p.stderr,
                                              exit_code=p.returncode, seconds=time.monotonic()-start))
                self.assertEqual(p.returncode, expected_exit, p.stderr)
                if expected_exit:
                    self.assertEqual(p.stdout, '')
                    return json.loads(p.stderr)
                return json.loads(p.stdout)

            first = invoke('data-verify','--offline','--artifact',artifact)
            self.assertEqual(first['deterministic_replay'], 'pass')
            self.assertEqual(first['native_status'], 'incomplete')
            self.assertFalse(first['runtime_executed'])
            for split in ['training','development']:
                response = invoke('data-inputs','--run',root,'--split',split)
                self.assertEqual(response['candidates'], [])
                self.assertFalse(response['os_unreadability'])
            with tempfile.TemporaryDirectory() as directory:
                receipt = Path(directory)/'access.json'
                access = invoke('data-check-access','--run',root,'--output',receipt)
                self.assertEqual(access['status'], 'pass')
                self.assertFalse(access['os_unreadability'])
                evidence['workflow_receipt'] = json.loads(receipt.read_text())
                # The real empty pool has no sealed ID; synthetic E2E covers that denial.
                self.assertNotIn('sealed_id', {row['case'] for row in access['results']})
                public = Path(directory)/'forbidden-public'
                denied = invoke('data-freeze-fixtures','--artifact',artifact,
                                '--review',Path(directory)/'absent-review.json',
                                '--access-receipt',receipt,'--public-output',public,
                                '--instruction','User-approved E2E: an empty source gate must not advance',
                                expected_exit=1)
                self.assertIn('Candidate/family capacity shortfall remains', denied['reason'])
                self.assertFalse(public.exists())
            for source in config['archives']:
                denied = invoke('data-inputs','--run',root,'--split','training',
                                '--purpose','selection','--bundle',source['path'], expected_exit=1)
                self.assertEqual(denied['status'], 'fail')
                self.assertIn('Path inputs are forbidden', denied['reason'])
            second = invoke('data-verify','--offline','--artifact',artifact)
            self.assertEqual(second, first)
            evidence.update(status='pass', campaign_source_gate='incomplete', fixture_seal='not_passed',
                            unavailable_categories=categories, eligible_terminal_fixtures=0,
                            unavailable_reason='Zero admitted development histories after all six approved archives',
                            real_sealed_candidate_exists=False,
                            limitation='continuation-disjoint; pretraining exposure unknown')
        finally:
            evidence['failure'] = str(sys.exc_info()[1]) if sys.exc_info()[1] else None
            evidence['software'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in (ROOT/'tools').glob('*') if p.is_file()}
            raw = json.dumps(evidence, sort_keys=True, indent=2).encode()
            target = ROOT/'.local/issue-14/e2e'; target.mkdir(parents=True,exist_ok=True)
            (target/(hashlib.sha256(raw).hexdigest()+'.json')).write_bytes(raw)


if __name__ == '__main__':
    unittest.main()
