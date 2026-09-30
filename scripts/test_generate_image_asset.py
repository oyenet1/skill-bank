"""Provider adapter checks with valid PNG data and no paid network requests."""
import base64
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import urllib.error
import zlib
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'skills-src/_shared/tools'))
import generate_image_asset as images
import network_tls as tls


def png():
    def chunk(kind, data):
        return struct.pack('>I', len(data))+kind+data+struct.pack('>I', zlib.crc32(kind+data)&0xffffffff)
    header = struct.pack('>IIBBBBB', 1024, 1024, 8, 2, 0, 0, 0)
    pixels = (b'\0' + b'\x20\x30\x40'*1024)*1024
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', header)+chunk(b'IDAT', zlib.compress(pixels))+chunk(b'IEND', b'')


class ImageAssetTests(unittest.TestCase):
    def spec(self):
        return {'model':'gpt-image-2', 'prompt':'A simple supporting illustration', 'quality':'medium', 'size':'1024x1024'}

    def test_image_and_public_provenance_are_verified_and_reused(self):
        data = png()
        response = json.dumps({'data':[{'b64_json':base64.b64encode(data).decode()}]}).encode()
        calls = []
        def api(request, timeout):
            calls.append(request)
            self.assertEqual(request.full_url, images.ENDPOINT)
            self.assertEqual(json.loads(request.data)['output_format'], 'png')
            self.assertEqual(timeout, 600)
            return io.BytesIO(response)
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)/'generated'
            result = images.generate(self.spec(), output, key='one-time-fixture-secret', opener=api)
            self.assertTrue(result['ready'])
            self.assertEqual((output/'image.png').read_bytes(), data)
            self.assertEqual(result['provenance']['sha256'], hashlib.sha256(data).hexdigest())
            self.assertTrue(result['provenance']['rightsReviewRequired'])
            self.assertNotIn('one-time-fixture-secret', (output/'asset.json').read_text())
            self.assertTrue(images.generate(self.spec(), output, key='', opener=Mock(side_effect=AssertionError('No repeat API call')))['reused'])
            self.assertEqual(len(calls), 1)
            (output/'image.png').write_bytes(data+b'changed')
            with self.assertRaisesRegex(ValueError, 'changed'):
                images.generate(self.spec(), output, key='fixture', opener=api)

    def test_missing_credential_and_bad_requests_make_no_directory_or_call(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)/'not-created'
            api = Mock(side_effect=AssertionError('No API request allowed'))
            with self.assertRaisesRegex(ValueError, 'API key'):
                images.generate(self.spec(), output, key='', opener=api)
            with self.assertRaisesRegex(ValueError, 'quality'):
                images.generate({**self.spec(), 'quality':'unexpected'}, output, key='fixture', opener=api)
            self.assertFalse(output.exists())
            api.assert_not_called()

    def test_provider_failure_corruption_and_cancellation_publish_no_partial_asset(self):
        corrupted = bytearray(png()); corrupted[45] ^= 1
        for api in (
            Mock(side_effect=urllib.error.HTTPError(images.ENDPOINT,401,'secret should not be echoed',{},None)),
            Mock(return_value=io.BytesIO(json.dumps({'data':[{'b64_json':base64.b64encode(corrupted).decode()}]}).encode())),
            Mock(side_effect=KeyboardInterrupt()),
        ):
            with self.subTest(api=api), tempfile.TemporaryDirectory() as temp:
                output = Path(temp)/'output'
                with self.assertRaises((RuntimeError, ValueError, KeyboardInterrupt)) as caught:
                    images.generate(self.spec(), output, key='fixture-secret', opener=api)
                self.assertNotIn('secret should not be echoed', str(caught.exception))
                self.assertFalse(output.exists())

    def test_platform_tls_roots_and_authenticated_redirect_rejection(self):
        tls.tls_context.cache_clear()
        self.addCleanup(tls.tls_context.cache_clear)
        context = Mock()
        manager = Mock()
        request = images.urllib.request.Request(images.ENDPOINT, headers={'Authorization': 'Bearer fixture'})
        with patch.object(tls.ssl, 'create_default_context', return_value=context), patch.object(tls.Path, 'is_file', return_value=False), patch.object(tls.platform, 'system', return_value='Darwin'), patch.object(tls.subprocess, 'run', return_value=Mock(returncode=0, stdout='fixture-root-certificate')), patch.object(images.urllib.request, 'build_opener', return_value=manager) as build:
            images.api_open(request, timeout=30)
            self.assertEqual(context.load_verify_locations.call_count, 2)
            handlers = build.call_args.args
            reject = next(handler for handler in handlers if isinstance(handler, images.urllib.request.HTTPRedirectHandler))
            with self.assertRaises(images.urllib.error.HTTPError):
                reject.redirect_request(request, None, None, None, None, 'https://unexpected.example/')
            manager.open.assert_called_once_with(request, timeout=30)

if __name__ == '__main__': unittest.main()
