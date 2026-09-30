"""Offline tests for the bundled Kokoro first-run helpers."""

import os
import hashlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock


TOOLS = Path(__file__).resolve().parent.parent / "course-creator/tools/kokoro"
SPEC = importlib.util.spec_from_file_location("kokoro_start", TOOLS / "start.py")
start = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(start)


class KokoroSetup(unittest.TestCase):
    @unittest.skipUnless(shutil.which("bash"), "Unix shell wrapper check")
    def test_uses_existing_uv_without_installing(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            shutil.copyfile(TOOLS / "ensure_uv.sh", root / "ensure_uv.sh")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            uv = bin_dir / "uv"
            uv.write_text("#!/bin/sh\necho uv-test\n")
            uv.chmod(0o755)
            env = dict(os.environ, PATH=f"{bin_dir}:/usr/bin:/bin")
            result = subprocess.run(
                ["bash", str(root / "ensure_uv.sh")],
                env=env, capture_output=True, text=True, check=True,
            )
            self.assertEqual(result.stdout.strip(), str(uv))
            self.assertFalse((root / ".tooling").exists())

    @unittest.skipUnless(shutil.which("bash"), "Unix shell wrapper check")
    def test_rejects_incomplete_model_download(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            models = root / "models"
            models.mkdir()
            target = models / "kokoro-v1.0.onnx"
            target.write_bytes(b"not a model")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            curl = bin_dir / "curl"
            curl.write_text(
                "#!/bin/sh\n"
                "while [ $# -gt 0 ]; do\n"
                "  if [ \"$1\" = '--output' ]; then shift; printf 'broken' > \"$1\"; exit 0; fi\n"
                "  shift\n"
                "done\nexit 2\n"
            )
            curl.chmod(0o755)
            env = dict(os.environ, PATH=f"{bin_dir}:/usr/bin:/bin")
            result = subprocess.run(
                ["bash", str(TOOLS / "download_models.sh"), str(models)],
                env=env, capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("failed size or SHA-256 verification", result.stderr)
            self.assertFalse(target.exists())
            self.assertTrue((models / "kokoro-v1.0.onnx.part").exists())

    def test_python_bootstrap_keeps_verified_model(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            payload = b"verified small model"
            name = "test.onnx"
            (root / name).write_bytes(payload)
            with mock.patch.object(start, "MODELS", root), mock.patch.object(start.urllib.request, "urlopen") as fetch:
                start.download_model(name, len(payload), hashlib.sha256(payload).hexdigest())
            fetch.assert_not_called()

    def test_python_bootstrap_rejects_bad_model(self):
        class Response:
            status = 200

            def __init__(self):
                self.remaining = [b"bad data", b""]

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self, _size):
                return self.remaining.pop(0)

        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            with mock.patch.object(start, "MODELS", root), mock.patch.object(start.urllib.request, "urlopen", return_value=Response()):
                with self.assertRaisesRegex(RuntimeError, "SHA-256 verification"):
                    start.download_model("test.onnx", 10, "0" * 64)
            self.assertFalse((root / "test.onnx").exists())
            self.assertTrue((root / "test.onnx.part").is_file())


if __name__ == "__main__":
    unittest.main()
