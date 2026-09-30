"""Desktop trust roots remain verified when optional system stores fail."""
from pathlib import Path
import ssl
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills-src/_shared/tools'))
import network_tls as tls


class NetworkTlsTests(unittest.TestCase):
    def setUp(self):
        tls.tls_context.cache_clear()
        self.addCleanup(tls.tls_context.cache_clear)

    def test_default_context_keeps_hostname_and_certificate_verification(self):
        with patch.object(tls.platform, 'system', return_value='Windows'), patch.object(tls.Path, 'is_file', return_value=False):
            context = tls.tls_context()
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)

    def test_linux_optional_bundles_and_context_are_cached(self):
        context = Mock()
        context.load_verify_locations.side_effect = [ssl.SSLError('stale'), None, None, None]
        with patch.object(tls.ssl, 'create_default_context', return_value=context) as create, patch.object(tls.platform, 'system', return_value='Linux'), patch.object(tls.Path, 'is_file', return_value=True), patch.object(tls.subprocess, 'run') as run:
            self.assertIs(tls.tls_context(), context)
            self.assertIs(tls.tls_context(), context)
            self.assertEqual(context.load_verify_locations.call_count, 4)
            create.assert_called_once()
            run.assert_not_called()

    def test_missing_or_timed_out_keychains_keep_default_trust(self):
        with patch.object(tls.platform, 'system', return_value='Darwin'), patch.object(tls.Path, 'is_file', return_value=False), patch.object(tls.subprocess, 'run', side_effect=[OSError('missing'), subprocess.TimeoutExpired('security', 15)]):
            context = tls.tls_context()
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)


if __name__ == '__main__':
    unittest.main()
