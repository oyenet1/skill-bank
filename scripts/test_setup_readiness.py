"""Readiness must verify cached tools and preserve a stable private interpreter."""
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills-src/_shared/tools'))
import bootstrap
import ensure_python_runtime as runtime


class SetupReadiness(unittest.TestCase):
    def test_missing_transcription_check_installs_nothing(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(runtime, 'ensure_uv', side_effect=AssertionError('No setup during check')):
            root = Path(temp)
            self.assertFalse(runtime.check_transcription(root, 'tiny.en')['ready'])
            self.assertEqual(list(root.iterdir()), [])

    def test_persistent_environment_is_reused_and_installation_accepts_only_wheels(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(runtime, 'ensure_uv', return_value=Path('/private/uv')):
            root = Path(temp)
            def install(command, **kwargs):
                if command[1] == 'venv':
                    venv = Path(command[2])
                    interpreter = venv / ('Scripts/python.exe' if runtime.platform.system() == 'Windows' else 'bin/python')
                    interpreter.parent.mkdir(parents=True)
                    interpreter.write_bytes(b'fixture')
                return Mock(returncode=0)
            with patch.object(runtime.subprocess, 'run', side_effect=install) as run:
                command, env = runtime.isolated_command(root, {'fixture': '1.0'}, root / 'worker.py', [])
                self.assertTrue(Path(command[0]).is_file())
                self.assertIn('python-environments', command[0])
                self.assertIn('--only-binary', run.call_args.args[0])
                self.assertNotIn('--system', str(run.call_args_list))
            with patch.object(runtime.subprocess, 'run', side_effect=AssertionError('Cached setup must not reinstall')):
                again, _ = runtime.isolated_command(root, {'fixture': '1.0'}, root / 'worker.py', [])
            self.assertEqual(command, again)

    def test_download_limits_default_and_preserve_user_configuration(self):
        def install(command, **kwargs):
            if command[1] == 'venv':
                Path(command[2]).mkdir(parents=True, exist_ok=True)
            return Mock(returncode=0)
        with tempfile.TemporaryDirectory() as temp, patch.object(runtime, 'ensure_uv', return_value=Path('/private/uv')), patch.object(runtime.subprocess, 'run', side_effect=install):
            root = Path(temp)
            with patch.dict(os.environ, {}, clear=True):
                _, env = runtime.isolated_command(root, {}, root / 'worker.py', [])
                self.assertEqual(env['UV_HTTP_TIMEOUT'], '120')
                self.assertEqual(env['UV_CONCURRENT_DOWNLOADS'], '4')
            with patch.dict(os.environ, {'UV_HTTP_TIMEOUT': '240', 'UV_CONCURRENT_DOWNLOADS': '2'}):
                _, env = runtime.isolated_command(root, {}, root / 'worker.py', [])
                self.assertEqual(env['UV_HTTP_TIMEOUT'], '240')
                self.assertEqual(env['UV_CONCURRENT_DOWNLOADS'], '2')

    def test_pretty_json_result_is_preserved_and_child_logs_are_relayed(self):
        command = [sys.executable, '-c', 'import json,sys; print("live progress",file=sys.stderr); print(json.dumps({"ready":True,"paths":{"node":"private node"}},indent=2))']
        with patch.object(bootstrap.sys, 'stderr', new_callable=io.StringIO) as output:
            result = bootstrap.run_step({'kind': 'runtime', 'name': 'fixture', 'command': command})
        self.assertTrue(result['ok'])
        self.assertEqual(result['result']['paths']['node'], 'private node')
        self.assertIn('live progress', output.getvalue())

    def test_success_exit_without_a_ready_response_is_not_readiness(self):
        for response in ('not JSON', '{"ready":false}', '{"ready":"false"}'):
            with self.subTest(response=response):
                result = bootstrap.run_step({'kind':'runtime','name':'fixture',
                    'command':[sys.executable, '-c', 'print(' + repr(response) + ')']})
                self.assertFalse(result['ok'])

    def test_course_bundle_has_its_own_complete_bootstrap(self):
        tools = ROOT / 'course-creator/tools'
        spec = json.loads((tools / 'dependencies.json').read_text())
        self.assertTrue(spec['voice'])
        self.assertTrue(spec['transcription'])
        for name in ('setup.sh', 'setup.ps1', 'bootstrap.py', 'ensure_video_runtime.py', 'ensure_python_runtime.py', 'kokoro/start.py'):
            self.assertTrue((tools / name).is_file(), name)


if __name__ == '__main__': unittest.main()
