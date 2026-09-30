"""Verify cancellation actually stops a worker and its process group on Linux."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

TOOLS = Path(__file__).resolve().parents[1] / 'skills-src/_shared/tools'

@unittest.skipUnless(sys.platform.startswith('linux'), 'Linux process-state inspection')
class AvatarRuntimeTests(unittest.TestCase):
    def test_sigterm_stops_worker_and_grandchild(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); pids = root/'pids.json'
            worker = "import subprocess,sys,time,json,os; from pathlib import Path; child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); Path(sys.argv[1]).write_text(json.dumps([os.getpid(),child.pid])); time.sleep(60)"
            parent = "import sys,signal; from pathlib import Path; import avatar_runtime as r; signal.signal(signal.SIGTERM,r.interrupted);\ntry:\n r.run([sys.executable,'-c',sys.argv[1],sys.argv[2]],Path(sys.argv[3]),r.environment(Path(sys.argv[4])))\nexcept KeyboardInterrupt:\n print('cancelled')"
            env = {**os.environ, 'PYTHONPATH': str(TOOLS)}
            process = subprocess.Popen([sys.executable, '-c', parent, worker, str(pids), str(root/'worker.log'), str(root)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                deadline = time.monotonic()+5
                while not pids.exists() and process.poll() is None and time.monotonic() < deadline:
                    time.sleep(.02)
                self.assertTrue(pids.exists())
                import json
                identities = json.loads(pids.read_text())
                process.terminate()
                stdout, stderr = process.communicate(timeout=8)
                self.assertIn('cancelled', stdout, stderr)
                for pid in identities:
                    status = Path(f'/proc/{pid}/stat')
                    if status.exists():
                        self.assertIn(status.read_text().split(') ',1)[1].split()[0], ('Z', 'X'))
            finally:
                if process.poll() is None:
                    process.kill(); process.wait(timeout=5)
                if pids.exists():
                    import json
                    try: os.killpg(json.loads(pids.read_text())[0], signal.SIGKILL)
                    except ProcessLookupError: pass

if __name__ == '__main__': unittest.main()
