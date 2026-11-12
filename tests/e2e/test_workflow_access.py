"""Synthetic registration fixtures exercise the public data gateway, not admission."""
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


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def sha(value):
    return hashlib.sha256(encoded(value)).hexdigest()


class WorkflowAccessE2E(unittest.TestCase):
    def test_registered_reads_and_prohibited_inputs(self):
        evidence: dict[str, Any] = {'status': 'fail', 'purpose': 'synthetic access fixture only', 'calls': []}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = root / 'run'
            (run / 'exports').mkdir(parents=True)
            manifest = {'schema': 'astrago-admission-v2', 'isolation': 'runner-workflow-v1'}
            (run / 'manifest.json').write_bytes(encoded(manifest))
            history = {'schema': 'astrago-full-history-v1', 'board_size': 19, 'moves': [],
                       'rules': {}, 'komi': 7.5, 'initial_player': 'B', 'next_player': 'B', 'terminal': False, 'phase': 0}
            candidate = {'id': sha(history), 'history': history, 'family_id': 'a'*64, 'split': 'training'}
            payload = {'candidates': [candidate], 'sealed_candidate_ids': ['f'*64], 'fixtures': {},
                       'private_artifact_sha256': 'b'*64, 'limitation': 'continuation-disjoint'}
            bundle = {'schema': 'astrago-public-data-v1', 'payload': payload, 'sha256': sha(payload)}
            public = root / 'data.json'
            public.write_bytes(encoded(bundle))
            registration = {'schema': 'astrago-consumer-registration-v1', 'isolation': 'runner-workflow-v1',
                            'manifest_sha256': sha(manifest), 'bundle_path': str(public.resolve()),
                            'bundle_sha256': hashlib.sha256(public.read_bytes()).hexdigest(),
                            'payload_sha256': sha(payload), 'artifact_sha256': 'b'*64,
                            'references': ['training', 'development']}
            (run / 'exports' / (sha(registration)+'.json')).write_bytes(encoded(registration))
            secret = run / 'records.json'
            secret.write_text('SEALED_CONTENT_MUST_NOT_BE_RETURNED')
            state = root / 'B-state.json'
            state.write_text('{"arm":"B"}')

            def invoke(*args):
                argv = [sys.executable, str(ROOT/'tools/campaign.py'), 'data-inputs', '--run', str(run), *map(str,args)]
                start = time.monotonic()
                p = subprocess.run(argv, capture_output=True, text=True)
                evidence['calls'].append(dict(argv=argv, stdout=p.stdout, stderr=p.stderr,
                                              exit_code=p.returncode, seconds=time.monotonic()-start))
                return p
            try:
                for arm in ['A', 'B']:
                    p = invoke('--split', 'training', '--arm', arm, '--candidate-id', candidate['id'])
                    self.assertEqual(p.returncode, 0, p.stderr)
                    self.assertEqual(json.loads(p.stdout)['candidates'][0]['id'], candidate['id'])
                self.assertEqual(invoke('--split','development').returncode, 0)
                for args in [('--split','sealed'), ('--split','training','--candidate-id','f'*64),
                             ('--split','training','--bundle',secret),
                             ('--split','training','--purpose','evaluation'),
                             ('--split','training','--arm','A','--arm-state',state),
                             ('--split','training','--arm','B','--arm-state',state)]:
                    p = invoke(*args)
                    self.assertNotEqual(p.returncode, 0)
                    self.assertNotIn('SEALED_CONTENT_MUST_NOT_BE_RETURNED', p.stdout+p.stderr)
                public.write_bytes(public.read_bytes()+b' ')
                self.assertNotEqual(invoke('--split','training').returncode, 0)
                logs = list((run/'access').glob('*.json'))
                self.assertEqual(len(logs),len(evidence['calls']))
                self.assertEqual(sum(json.loads(p.read_text())['decision']=='allow' for p in logs),3)
                for p in logs:
                    self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),p.stem)
                evidence['status']='pass'
            finally:
                evidence.update(failure=str(sys.exc_info()[1]) if sys.exc_info()[1] else None,
                    snapshot={p.relative_to(root).as_posix():p.read_text() for p in root.rglob('*') if p.is_file()},
                    python=sys.version, test_source=Path(__file__).read_text(),
                    software={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'tools').glob('*') if p.is_file()})
                destination=ROOT/'.local/issue-14/e2e';destination.mkdir(parents=True,exist_ok=True)
                raw=encoded(evidence);(destination/(hashlib.sha256(raw).hexdigest()+'.json')).write_bytes(raw)

class RetainedWorkflowE2E(unittest.TestCase):
    def test_retained_probe_rejects_mislabelled_evidence(self):
        import os
        artifact = os.environ.get('ASTRAGO_WORKFLOW_ARTIFACT')
        if not artifact:
            raw = encoded({'case': self.id(), 'status': 'skipped',
                           'reason': 'Authorized admission artifact not supplied',
                           'test_source': Path(__file__).read_text()})
            target = ROOT/'.local/issue-14/e2e'; target.mkdir(parents=True, exist_ok=True)
            (target/(hashlib.sha256(raw).hexdigest()+'.json')).write_bytes(raw)
            self.skipTest('Authorized real admission artifact not supplied')
        run = Path(artifact).parent.parent
        evidence: dict[str, Any] = {'case': self.id(), 'status': 'fail', 'calls': [],
                                   'purpose': 'Retained gateway evidence; this test does not establish source provenance',
                                   'artifact_sha256': None}
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            def invoke(*args):
                argv=[sys.executable,str(ROOT/'tools/campaign.py'),*map(str,args)]
                start=time.monotonic(); p=subprocess.run(argv,capture_output=True,text=True)
                evidence['calls'].append(dict(argv=argv,stdout=p.stdout,stderr=p.stderr,exit_code=p.returncode,seconds=time.monotonic()-start))
                return p
            receipt=work/'receipt.json'
            try:
                evidence['artifact_sha256'] = hashlib.sha256(Path(artifact).read_bytes()).hexdigest()
                p=invoke('data-check-access','--run',run,'--output',receipt)
                self.assertEqual(p.returncode,0,p.stderr)
                value=json.loads(receipt.read_text())
                self.assertEqual(value['status'],'pass')
                self.assertFalse(value['os_unreadability'])
                # Later access records must not change the old admission artifact.
                p=invoke('data-verify','--offline','--artifact',artifact)
                self.assertEqual(p.returncode,0,p.stderr)
                self.assertEqual(json.loads(p.stdout)['deterministic_replay'],'pass')
                # A denied raw-path event cannot establish the sealed-reference case.
                raw_event=next(r['event_sha256'] for r in value['results'] if r['case']=='raw_source_path')
                for row in value['results']:
                    if row['case']=='sealed_reference':row['event_sha256']=raw_event
                forged=work/'mislabelled.json';forged.write_bytes(encoded(value))
                p=invoke('data-freeze-fixtures','--artifact',artifact,'--review',work/'absent-review.json',
                         '--access-receipt',forged,'--public-output',work/'public',
                         '--instruction','User approved issue-14 workflow probe; deliberately invalid evidence')
                self.assertNotEqual(p.returncode,0)
                self.assertIn('Workflow probe request mismatch',p.stderr)
                evidence['status']='pass'
            finally:
                evidence.update(failure=str(sys.exc_info()[1]) if sys.exc_info()[1] else None,
                    test_source=Path(__file__).read_text(),
                    software={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'tools').glob('*') if p.is_file()},
                    receipt=receipt.read_text() if receipt.exists() else None)
                destination=ROOT/'.local/issue-14/e2e';destination.mkdir(parents=True,exist_ok=True)
                raw=encoded(evidence);(destination/(hashlib.sha256(raw).hexdigest()+'.json')).write_bytes(raw)
