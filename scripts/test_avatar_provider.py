"""Provider ordering and explicit override behavior without live hosted calls."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills-src/_shared/tools"))
import avatar_provider as provider


class AvatarProviderTests(unittest.TestCase):
    def setUp(self):
        self.capability = {"eligible": True, "reason": "eligible", "accelerator": {"kind": "cuda", "memoryBytes": 8 * 1024**3}}

    def test_local_precedes_hosted_and_does_not_need_cli(self):
        with patch.object(provider, "probe", return_value=self.capability), patch.object(provider, "status", return_value={"ready": True}), patch.object(provider, "hosted_ready", side_effect=AssertionError("Local does not need HeyGen")):
            self.assertEqual(provider.resolve(Path("/unused"))["provider"], "local")

    def test_hosted_precedes_fallback_when_local_is_missing(self):
        with patch.object(provider, "probe", return_value=self.capability), patch.object(provider, "status", return_value={"ready": False}), patch.object(provider, "hosted_ready", return_value=(True, "authenticated")):
            self.assertEqual(provider.resolve(Path("/unused"))["provider"], "heygen")

    def test_explicit_unavailable_provider_fails_loudly(self):
        with patch.object(provider, "probe", return_value=self.capability), patch.object(provider, "status", return_value={"ready": False}), patch.object(provider, "hosted_ready", return_value=(False, "not authenticated")):
            self.assertFalse(provider.resolve(Path("/unused"), "local")["ready"])
            self.assertFalse(provider.resolve(Path("/unused"), "heygen")["ready"])
            fallback = provider.resolve(Path("/unused"))
            self.assertEqual(fallback["provider"], "fallback")
            self.assertEqual(fallback["blocked"], "presenter-generation")

    def test_explicit_hosted_never_inspects_local_runtime(self):
        with patch.object(provider, "probe", side_effect=AssertionError("Hosted requests do not need local hardware")), patch.object(provider, "hosted_ready", return_value=(True, "authenticated")):
            self.assertTrue(provider.resolve(Path("/unused"), "heygen")["ready"])

    @unittest.skipUnless(__import__('shutil').which('ffmpeg') and __import__('shutil').which('ffprobe'), 'FFmpeg required')
    def test_fallback_exports_actual_verified_audio(self):
        import subprocess
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            script = root / 'script.md'; script.write_text('Hello presenter')
            audio = root / 'voice.wav'
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=220:duration=0.3', str(audio)], check=True)
            result = provider.deliver_fallback(script, audio, root / 'fallback')
            self.assertTrue(result['ready'])
            self.assertIsNone(result['video'])
            self.assertEqual(result['blocked'], 'presenter-generation')
            self.assertTrue(all(Path(path).is_file() for path in result['artifacts']))


if __name__ == "__main__":
    unittest.main()
