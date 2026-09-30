"""Consent, disk, reproducibility and installer checks without GPU downloads."""
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills-src/_shared/tools"))
import avatar_ensure as installer
from avatar_runtime import fingerprint, paths


class AvatarEnsureTests(unittest.TestCase):
    def fixture(self, base):
        model = b"model fixture"
        code = base / "source.tar.gz"
        with tarfile.open(code, "w:gz") as archive:
            content = b"# pinned source fixture\n"
            info = tarfile.TarInfo("repo/inference.py")
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
        backend = json.loads(json.dumps(installer.manifest()["backends"][0]))
        backend.update(id="fixture", requiresSmokeTest=False, downloadBytes=100, diskBytes=100,
                       files=[{"name": "weight.bin", "bytes": len(model), "sha256": hashlib.sha256(model).hexdigest(), "url": "https://example.test/weight"}],
                       code={"name": "source.tar.gz", "bytes": code.stat().st_size, "sha256": hashlib.sha256(code.read_bytes()).hexdigest(), "url": "https://example.test/source"})
        config = {"thresholds": {"cudaBytes": 6 * 1024**3}, "defaults": {"cuda": "fixture"}, "backends": [backend]}
        capability = {"eligible": True, "reason": "eligible", "accelerator": {"kind": "cuda", "memoryBytes": 8 * 1024**3, "name": "Fixture NVIDIA"}}
        return config, capability, code, model

    def test_no_environment_or_download_before_consent_and_readonly_check(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            config, capability, _, _ = self.fixture(base)
            root = base / "not-created"
            with patch.object(installer, "manifest", return_value=config), patch.object(installer, "probe", return_value=capability), patch.object(installer, "prepare_environment") as prepare, patch.object(installer, "download") as download:
                result = installer.ensure(root, "fixture")
                self.assertTrue(result["consentRequired"])
                checked = installer.ensure(root, "fixture", check=True)
                self.assertFalse(checked["ready"])
                prepare.assert_not_called()
                download.assert_not_called()
                self.assertFalse(root.exists())

    def test_disk_refusal_and_stale_consent_do_not_create_runtime(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            config, capability, _, _ = self.fixture(base)
            root = base / "not-created"
            with patch.object(installer, "manifest", return_value=config), patch.object(installer, "probe", return_value=capability):
                with self.assertRaisesRegex(ValueError, "manifest changed"):
                    installer.ensure(root, "fixture", accept=True, consent_token="stale")
                with patch.object(installer.shutil, "disk_usage", return_value=shutil._ntuple_diskusage(100, 99, 1)):
                    with self.assertRaisesRegex(RuntimeError, "Not enough free disk"):
                        installer.ensure(root, "fixture", accept=True)
            self.assertFalse(root.exists())

    def test_accepted_install_verifies_files_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            config, capability, code, model = self.fixture(base)
            backend = config["backends"][0]
            root = base / "private"
            media = base / "media"
            media.write_bytes(b"fixture tool")
            def prepare(root, backend, kind, location):
                location["python"].parent.mkdir(parents=True)
                location["python"].write_bytes(b"private interpreter fixture")
                value = fingerprint({"python": backend["pythonVersion"], "environment": backend["environment"], "accelerator": kind})
                (location["base"] / "requirements.sha256").write_text(value)
            def download(root, file):
                target = root / file["name"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(code.read_bytes() if file["name"] == "source.tar.gz" else model)
                return target
            with patch.object(installer, "manifest", return_value=config), patch.object(installer, "probe", return_value=capability), patch.object(installer, "prepare_environment", side_effect=prepare), patch.object(installer, "download", side_effect=download), patch("run_video_job.media_paths", return_value=(media, media)):
                result = installer.ensure(root, "fixture", accept=True, consent_token=fingerprint(backend))
                self.assertTrue(result["ready"])
            with patch.object(installer, "manifest", return_value=config), patch.object(installer, "probe", return_value=capability), patch.object(installer, "download", side_effect=AssertionError("No second download")):
                self.assertTrue(installer.ensure(root, "fixture", accept=True)["ready"])
                (root / "models/fixture/weight.bin").write_bytes(b"tampered")
                self.assertFalse(installer.ensure(root, "fixture", check=True)["ready"])

    def test_backend_cannot_override_accelerator_compatibility(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            config, capability, _, _ = self.fixture(base)
            capability["accelerator"]["kind"] = "mps"
            with patch.object(installer, "manifest", return_value=config), patch.object(installer, "probe", return_value=capability), patch.object(installer, "download") as download:
                result = installer.ensure(base / "private", "fixture", accept=True)
                self.assertFalse(result["ready"])
                download.assert_not_called()

    def test_failed_mps_smoke_cannot_publish_readiness_or_install_disabled_fallback(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            config, capability, code, model = self.fixture(base)
            backend = config["backends"][0]
            backend.update(accel=["mps"], minAccelMemoryBytes=24 * 1024**3, requiresSmokeTest=True, fallbackBackend="sadtalker")
            capability["accelerator"].update(kind="mps", memoryBytes=32 * 1024**3)
            root = base / "private"
            media = base / "media"; media.touch()
            def download(directory, file):
                target = directory / file["name"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(code.read_bytes() if file["name"] == "source.tar.gz" else model)
                return target
            with patch.object(installer, "manifest", return_value=config), patch.object(installer, "probe", return_value=capability), patch.object(installer, "prepare_environment"), patch.object(installer, "download", side_effect=download), patch("run_video_job.media_paths", return_value=(media, media)), patch("avatar_generate.smoke", side_effect=RuntimeError("unsupported MPS operation")):
                result = installer.ensure(root, "fixture", accept=True)
            self.assertFalse(result["ready"])
            self.assertIsNone(result["fallbackBackend"])
            self.assertEqual(result["reason"], "inference-smoke-failed")
            self.assertFalse((root / "backends/fixture/installed.json").exists())
            self.assertFalse((root / "backends/sadtalker").exists())


if __name__ == "__main__":
    unittest.main()
