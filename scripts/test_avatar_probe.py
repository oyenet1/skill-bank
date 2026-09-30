"""Deterministic local avatar capability and model-selection checks."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills-src/_shared/tools"))
import avatar_probe as avatar


class AvatarProbeTests(unittest.TestCase):
    def host(self, system, machine, output):
        with patch.object(avatar.platform, "system", return_value=system), patch.object(avatar.platform, "machine", return_value=machine), patch.object(avatar.platform, "mac_ver", return_value=("14.0", (), "arm64")), patch.object(avatar, "command", return_value=output):
            return avatar.probe()

    def test_cuda_memory_boundary_and_windows(self):
        for system in ("Windows", "Linux"):
            self.assertTrue(self.host(system, "AMD64", "NVIDIA Example, 6144, 550.1")["eligible"])
            low = self.host(system, "AMD64", "NVIDIA Example, 6143, 550.1")
            self.assertFalse(low["eligible"])
            self.assertEqual(low["accelerator"]["memoryBytes"], 6143 * 1048576)

    def test_mps_unified_memory_boundary(self):
        self.assertTrue(self.host("Darwin", "arm64", str(24 * 1024**3))["eligible"])
        self.assertFalse(self.host("Darwin", "arm64", str(24 * 1024**3 - 1))["eligible"])

    def test_old_macos_is_rejected_before_model_offer(self):
        with patch.object(avatar.platform, "system", return_value="Darwin"), patch.object(avatar.platform, "machine", return_value="arm64"), patch.object(avatar.platform, "mac_ver", return_value=("13.6", (), "arm64")), patch.object(avatar, "command", return_value=str(32 * 1024**3)):
            result = avatar.probe()
        self.assertFalse(result["eligible"])
        self.assertEqual(result["reason"], "unsupported-platform:macOS-14-required")

    def test_selects_largest_gpu_and_tracks_index(self):
        result = self.host("Linux", "x86_64", "Smaller, 6144, 550.1\nLarger, 12288, 550.1")
        self.assertEqual(result["accelerator"]["name"], "Larger")
        self.assertEqual(result["accelerator"]["deviceIndex"], 1)
        self.assertEqual(result["candidates"][0], "musetalk-15")
        self.assertNotIn("latentsync-15", result["candidates"])

    def test_restricted_is_explicit_and_defaults_override_quality(self):
        rows = avatar.compatible(avatar.manifest(), "cuda", 12 * 1024**3, allow_restricted=True)
        self.assertEqual(rows[0]["id"], "musetalk-15")
        self.assertIn("latentsync-15", [row["id"] for row in rows])
        self.assertEqual(avatar.compatible(avatar.manifest(), "cpu", 128 * 1024**3), [])
        self.assertEqual(avatar.compatible(avatar.manifest(), "rocm", 128 * 1024**3), [])

    def test_missing_command_and_malformed_output_do_not_crash(self):
        with patch.object(avatar.platform, "system", return_value="Linux"), patch.object(avatar.platform, "machine", return_value="x86_64"), patch.object(avatar.subprocess, "run", side_effect=FileNotFoundError()), patch.object(avatar.Path, "exists", return_value=False):
            result = avatar.probe()
        self.assertFalse(result["eligible"])
        self.assertEqual(result["sourcesFailed"][0]["reason"], "FileNotFoundError")
        self.assertFalse(self.host("Linux", "x86_64", "Bad GPU, nan, invalid")["eligible"])
        self.assertFalse(self.host("Darwin", "arm64", "invalid")["eligible"])

    def test_unpinned_backend_is_not_offered(self):
        config = avatar.manifest()
        for row in config["backends"]:
            row["files"][0]["sha256"] = None
        self.assertEqual(avatar.compatible(config, "cuda", 128 * 1024**3, allow_restricted=True), [])

    def test_probe_is_network_free_and_survives_bad_manifest(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("Unexpected network")):
            result = self.host("Windows", "x64", "NVIDIA Example, 6144, 550.1")
            self.assertTrue(result["eligible"])
        with patch.object(avatar, "manifest", side_effect=ValueError("bad manifest")):
            result = avatar.probe()
        self.assertFalse(result["eligible"])
        self.assertEqual(result["reason"], "probe-error")
        json.dumps(result)


if __name__ == "__main__":
    unittest.main()
