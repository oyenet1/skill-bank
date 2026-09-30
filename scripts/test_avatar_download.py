"""Exercise resumable verified downloads without model or network dependencies."""
import hashlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills-src/_shared/tools"))
import avatar_download as downloader


class Response(io.BytesIO):
    def __init__(self, data, status=200, headers=None):
        super().__init__(data)
        self.status = status
        self.headers = headers or {}


class AvatarDownloadTests(unittest.TestCase):
    def record(self):
        data = b"verified model fixture"
        return data, {"name": "weights/model.bin", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "url": "https://example.test/model"}

    def test_resume_and_idempotency(self):
        data, file = self.record()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            partial = root / "weights/model.bin.part"
            partial.parent.mkdir()
            partial.write_bytes(data[:5])
            with patch.object(downloader.urllib.request, "urlopen", return_value=Response(data[5:], 206, {"Content-Range": f"bytes 5-{len(data)-1}/{len(data)}"})) as fetch:
                result = downloader.download(root, file)
            self.assertEqual(fetch.call_args.args[0].get_header("Range"), "bytes=5-")
            self.assertEqual(result.read_bytes(), data)
            self.assertFalse(partial.exists())
            with patch.object(downloader.urllib.request, "urlopen", side_effect=AssertionError("Already installed")):
                self.assertEqual(downloader.download(root, file), result)

    def test_server_without_range_restarts_safely(self):
        data, file = self.record()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            partial = root / "weights/model.bin.part"
            partial.parent.mkdir()
            partial.write_bytes(data[:5])
            with patch.object(downloader.urllib.request, "urlopen", return_value=Response(data)):
                self.assertEqual(downloader.download(root, file).read_bytes(), data)

    def test_mismatch_keeps_partial_without_final_model(self):
        data, file = self.record()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(downloader.urllib.request, "urlopen", return_value=Response(b"X" * len(data))):
                with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                    downloader.download(root, file)
            self.assertFalse((root / file["name"]).exists())
            self.assertTrue((root / (file["name"] + ".part")).exists())

    def test_invalid_resume_and_traversal_are_rejected(self):
        data, file = self.record()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(downloader.urllib.request, "urlopen", return_value=Response(data, 206, {"Content-Range": "bytes 1-20/21"})):
                with self.assertRaisesRegex(ValueError, "resume range"):
                    downloader.download(root, file)
            for name in ("../escape", "C:/escape", "bad\\escape"):
                with self.assertRaises(ValueError):
                    downloader.destination(root, name)


if __name__ == "__main__":
    unittest.main()
