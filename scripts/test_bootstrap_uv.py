"""Private wheel installation integrity, platform selection, and fallback checks."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock
import urllib.error
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills-src/_shared/tools'))
import bootstrap_uv as bootstrap
import ensure_python_runtime as runtime


class BootstrapUvTests(unittest.TestCase):
    def fixture(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as wheel:
            wheel.writestr('uv-0.12.13.data/scripts/uv', b'fixture-binary')
            for name in ('LICENSE-APACHE', 'LICENSE-MIT'):
                wheel.writestr('uv-0.12.13.dist-info/licenses/' + name, name.encode())
            # An unrelated unsafe entry must never be extracted.
            wheel.writestr('../../unexpected', b'never extract')
        data = stream.getvalue()
        pins = {'version': '0.12.13', 'platforms': {'linux-x86_64': {
            'url': 'https://files.pythonhosted.org/fixture.whl',
            'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
        }}}
        return data, pins

    def test_exact_binary_and_licenses_install_without_pip_or_extra_archive_entries(self):
        data, pins = self.fixture()
        with tempfile.TemporaryDirectory() as temp, patch.object(bootstrap, 'PINS', pins):
            target = Path(temp) / 'tools/uv'
            bootstrap.install_pinned_uv(target, key='linux-x86_64', opener=Mock(return_value=io.BytesIO(data)))
            self.assertEqual(target.read_bytes(), b'fixture-binary')
            self.assertEqual((target.parent / 'uv-LICENSE-MIT').read_text(), 'LICENSE-MIT')
            self.assertEqual(set(p.name for p in target.parent.iterdir()), {'uv', 'uv-LICENSE-MIT', 'uv-LICENSE-APACHE'})

    def test_truncated_oversized_or_wrong_digest_wheel_preserves_existing_binary(self):
        data, pins = self.fixture()
        for invalid in (data[:-1], data + b'oversized', data[:-1] + b'x'):
            with self.subTest(length=len(invalid)), tempfile.TemporaryDirectory() as temp, patch.object(bootstrap, 'PINS', pins):
                target = Path(temp) / 'uv'; target.write_bytes(b'previous')
                with self.assertRaises(RuntimeError):
                    bootstrap.install_pinned_uv(target, key='linux-x86_64', opener=Mock(return_value=io.BytesIO(invalid)))
                self.assertEqual(target.read_bytes(), b'previous')
                self.assertEqual(list(Path(temp).iterdir()), [target])

    def test_platform_pins_cover_desktop_architectures_and_reject_unknown(self):
        for system, machine, libc, key in (
            ('Windows', 'AMD64', '', 'windows-x86_64'),
            ('Windows', 'ARM64', '', 'windows-aarch64'),
            ('Darwin', 'arm64', '', 'darwin-aarch64'),
            ('Darwin', 'x86_64', '', 'darwin-x86_64'),
            ('Linux', 'x86_64', 'glibc', 'linux-x86_64'),
            ('Linux', 'x86_64', 'musl', 'linux-musl-x86_64'),
            ('Linux', 'aarch64', 'glibc', 'linux-aarch64'),
        ):
            with self.subTest(key=key), patch.object(bootstrap.platform, 'system', return_value=system), patch.object(bootstrap.platform, 'machine', return_value=machine), patch.object(bootstrap.platform, 'libc_ver', return_value=(libc, '')):
                self.assertEqual(bootstrap.platform_key(), key)
                self.assertIn(key, bootstrap.PINS['platforms'])
        with self.assertRaisesRegex(RuntimeError, 'No prebuilt'):
            bootstrap.install_pinned_uv(Path('unused'), key='other-unknown')

    def test_http_failure_uses_private_verified_wheel_and_rechecks_version(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(runtime.shutil, 'which', return_value=None), patch.object(runtime.urllib.request, 'urlopen', side_effect=urllib.error.HTTPError('https://astral.sh',403,'denied',{},None)), patch.object(runtime, 'install_pinned_uv') as fallback, patch.object(runtime.subprocess, 'run', return_value=Mock(returncode=0, stdout='uv 0.12.13')):
            target = Path(temp) / 'python-tools' / ('uv.exe' if runtime.platform.system() == 'Windows' else 'uv')
            fallback.side_effect = lambda path: path.write_bytes(b'private-wheel')
            self.assertEqual(runtime.ensure_uv(Path(temp), minimum_version=(0,12,13)), target)
            fallback.assert_called_once_with(target)

    def test_cancellation_does_not_start_fallback_download(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(runtime.shutil, 'which', return_value=None), patch.object(runtime.urllib.request, 'urlopen', side_effect=KeyboardInterrupt), patch.object(runtime, 'install_pinned_uv') as fallback:
            with self.assertRaises(KeyboardInterrupt):
                runtime.ensure_uv(Path(temp))
            fallback.assert_not_called()


if __name__ == '__main__': unittest.main()
