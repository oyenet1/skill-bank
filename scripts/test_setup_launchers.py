"""Exercise real Unix launchers with isolated executable discovery."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / 'skills-src/_shared/tools/setup.sh'


@unittest.skipUnless(shutil.which('sh'), 'Unix launcher checks')
class SetupLaunchers(unittest.TestCase):
    def environment(self, root):
        tools = root / 'bin'; tools.mkdir()
        for name in ('dirname', 'uname', 'mkdir'):
            source = shutil.which(name)
            if source:
                (tools / name).symlink_to(source)
        return dict(os.environ, PATH=str(tools), SKILL_BANK_PYTHON_HOME=str(root / 'runtime'), TEST_LOG=str(root / 'calls'))

    def run_launcher(self, env, *args):
        return subprocess.run([shutil.which('sh'), str(LAUNCHER), *args], env=env, capture_output=True, text=True)

    def test_missing_python_check_is_read_only_and_reports_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); env = self.environment(root)
            result = self.run_launcher(env, '--check')
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)['missing'], ['Python 3.10+'])
            self.assertFalse((root / 'runtime').exists())

    def test_old_python_is_skipped_without_attempting_to_run_bootstrap(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); env = self.environment(root)
            old = root / 'bin/python3'
            old.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$TEST_LOG"\nexit 1\n'); old.chmod(0o755)
            result = self.run_launcher(env, '--check')
            self.assertEqual(result.returncode, 1)
            calls = (root / 'calls').read_text()
            self.assertIn('version_info < (3,10)', calls)
            self.assertNotIn('bootstrap.py', calls)
            self.assertFalse((root / 'runtime').exists())

    def test_suitable_python_preserves_arguments_with_spaces(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); env = self.environment(root)
            python = root / 'bin/python3'
            python.write_text('#!/bin/sh\nif [ "$1" = -c ]; then exit 0; fi\nprintf "%s\\n" "$@" > "$TEST_LOG"\nexit 7\n'); python.chmod(0o755)
            result = self.run_launcher(env, '--target', '/tmp/skills with spaces')
            self.assertEqual(result.returncode, 7)
            self.assertEqual((root / 'calls').read_text().splitlines(), [str(LAUNCHER.with_name('bootstrap.py')), '--target', '/tmp/skills with spaces'])
            self.assertFalse((root / 'runtime').exists())


if __name__ == '__main__': unittest.main()
