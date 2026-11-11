"""E2E tests invoke only the public runner; no native substitute passes a gate."""
import hashlib
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]


class CampaignE2E(unittest.TestCase):
    def test_execution_requires_instruction_and_retains_h0(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = []

            def run(*args):
                argv = [sys.executable, str(ROOT / 'tools/campaign.py'), *args]
                started = time.monotonic()
                p = subprocess.run(argv, capture_output=True, text=True)
                calls.append({'argv': argv, 'exit_code': p.returncode,
                              'stdout': p.stdout, 'stderr': p.stderr,
                              'duration_seconds': time.monotonic() - started})
                return p

            completed = False
            snapshot = {}
            try:
                manifest = root / 'manifest.json'
                self.assertEqual(run('plan', '--output', str(manifest)).returncode, 0)
                inventory = root / 'coordinator.json'
                self.assertEqual(run('inventory', '--output', str(inventory)).returncode, 0)
                campaign = root / 'campaign'
                self.assertNotEqual(run('start', '--manifest', str(manifest),
                                        '--run', str(campaign)).returncode, 0)
                self.assertFalse((campaign / 'h0.json').exists())
                p = run('start', '--manifest', str(manifest), '--run', str(campaign),
                        '--instruction', 'Authorize H0 and this ticket runtime execution')
                self.assertEqual(p.returncode, 0, p.stderr)
                h0 = (campaign / 'h0.json').read_bytes()
                p = run('start', '--manifest', str(manifest), '--run', str(campaign),
                        '--instruction', 'Authorize H0 and this ticket runtime execution')
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual((campaign / 'h0.json').read_bytes(), h0)
                low_capacity = json.loads(inventory.read_text())
                low_capacity['free_bytes'] = 19 * 2**30
                inventory.write_text(json.dumps(low_capacity))
                p = run('acquire', '--run', str(campaign), '--coordinator-inventory', str(inventory))
                self.assertNotEqual(p.returncode, 0)
                self.assertIn('20 GiB', json.loads(p.stdout)['reason'])
                self.assertFalse(json.loads(p.stdout)['advance'])
                p = run('smoke', '--run', str(campaign))
                self.assertNotEqual(p.returncode, 0)
                outcome = json.loads(p.stdout)
                self.assertEqual(outcome['status'], 'inconclusive')
                self.assertIn('runtime not available', outcome['reason'])
                self.assertFalse(outcome['advance'])
                p = run('smoke', '--run', str(campaign), '--retry')
                self.assertNotEqual(p.returncode, 0)
                self.assertEqual(json.loads(p.stdout)['status'], 'inconclusive')
                self.assertEqual((campaign / 'h0.json').read_bytes(), h0)
                # Retained public evidence from a process interrupted before its report.
                pending = json.dumps({'id': 'interrupted-smoke', 'phase': 'operation-start',
                                      'operation': 'smoke', 'started_utc': datetime.now(timezone.utc).isoformat()}).encode()
                pending_path = campaign / 'events' / (hashlib.sha256(pending).hexdigest() + '.json')
                pending_path.write_bytes(pending)
                p = run('smoke', '--run', str(campaign), '--retry')
                self.assertNotEqual(p.returncode, 0)
                self.assertIn('Unresolved operation dispatch', p.stderr)
                pending_path.unlink()  # Remove only this deliberately injected fixture.
                p = run('adopt-runner', '--run', str(campaign), '--reason', 'Audited implementation repair')
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual((campaign / 'h0.json').read_bytes(), h0)
                adopted_runner = json.loads(p.stdout)['runner']
                # A synthetic prior build identity exercises repair routing only;
                # it never stands in for a real native success artifact.
                fixture = json.dumps({'operation': 'build', 'status': 'pass', 'started_utc': datetime.now(timezone.utc).isoformat(),
                                      'adapter_sha256': '0' * 64}).encode()
                fixture_path = campaign / 'reports' / (hashlib.sha256(fixture).hexdigest() + '.json')
                fixture_path.write_bytes(fixture)
                p = run('adopt-runner', '--run', str(campaign), '--reason', 'Explicit pre-smoke refreeze')
                self.assertEqual(p.returncode, 0, p.stderr)
                p = run('smoke', '--run', str(campaign), '--retry')
                self.assertNotEqual(p.returncode, 0)
                self.assertIn('runtime not available', json.loads(p.stdout)['reason'])
                fixture_path.unlink()
                # A deliberately wrong adopted identity fails before execution.
                wrong = json.loads(manifest.read_text())
                wrong['source_revision'] = '0' * 40
                manifest.write_text(json.dumps(wrong))
                p = run('start', '--manifest', str(manifest), '--run', str(root / 'wrong'),
                        '--instruction', 'Authorize H0 and this ticket runtime execution')
                self.assertNotEqual(p.returncode, 0)
                self.assertFalse((root / 'wrong/h0.json').exists())
                p = run('stop', '--run', str(campaign), '--reason', 'E2E no runtime')
                self.assertEqual(p.returncode, 0, p.stderr)
                report = json.loads(p.stdout)
                self.assertEqual(report['status'], 'incomplete')
                self.assertIsNone(report['cost']['charge_usd'])
                artifact = json.loads((campaign / report['artifact']).read_text())
                self.assertEqual(artifact['replay'][1], adopted_runner)
                p = run('verify', '--offline', '--run', str(campaign))
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual((campaign / 'h0.json').read_bytes(), h0)
                p = run('resume-setup', '--run', str(campaign),
                        '--instruction', 'Continue the authorized setup after environmental repair',
                        '--coordinator-inventory', str(inventory))
                self.assertNotEqual(p.returncode, 0)
                self.assertIn('20 GiB', p.stderr)
                self.assertEqual((campaign / 'h0.json').read_bytes(), h0)
                snapshot = {p.relative_to(campaign).as_posix(): p.read_text()
                            for p in campaign.rglob('*') if p.is_file()}
                (campaign / 'software/campaign.py').write_text('tampered')
                self.assertNotEqual(run('verify', '--offline', '--run', str(campaign)).returncode, 0)
                completed = True
            finally:
                if not snapshot:
                    snapshot = {p.relative_to(campaign).as_posix(): p.read_text(errors='replace')
                                for p in campaign.rglob('*') if p.is_file()} if 'campaign' in locals() else {}
                evidence = ROOT / '.local/issue-13/e2e'
                evidence.mkdir(parents=True, exist_ok=True)
                data = json.dumps({'case': self.id(), 'status': 'pass' if completed else 'fail', 'failure': str(sys.exc_info()[1]) if sys.exc_info()[1] else None, 'calls': calls,
                                   'retained_inputs_outputs': snapshot, 'python': sys.version,
                                   'test_source': Path(__file__).read_text(),
                                   'test_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                                   'workspace_snapshot': {p.relative_to(root).as_posix(): p.read_text(errors='replace')
                                                          for p in root.rglob('*') if p.is_file()},
                                   'software': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                                for p in (ROOT / 'tools').glob('*.py')},
                                   'charge_usd': None, 'billing_status': 'unknown'},
                                  sort_keys=True, indent=2).encode()
                (evidence / (hashlib.sha256(data).hexdigest() + '.json')).write_bytes(data)



if __name__ == '__main__':
    unittest.main()
