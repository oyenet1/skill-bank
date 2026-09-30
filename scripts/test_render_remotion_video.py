"""Check Remotion render packaging with a real encoded clip."""

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


TOOLS = Path(__file__).resolve().parent.parent / "skills-src/_shared/tools"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location("render_remotion_video", TOOLS / "render_remotion_video.py")
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class RemotionAdapterTests(unittest.TestCase):
    def test_existing_audio_requires_an_explicit_choice(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            entry = root / "index.tsx"
            entry.write_text("// editable entry\n")
            timing = root / "timing.json"
            timing.write_text(json.dumps({"scenes": [{"caption": "Screen text"}]}))
            ready = {"ready": True, "paths": {"node": sys.executable, "remotion": "remotion",
                                               "ffmpeg": shutil.which("ffmpeg"),
                                               "ffprobe": shutil.which("ffprobe")}}

            def fake_render(args, **kwargs):
                Path(args[4]).write_bytes(b"rendered")
                return subprocess.CompletedProcess(args, 0)

            with mock.patch.object(ADAPTER, "setup", return_value=ready), mock.patch.object(
                ADAPTER.subprocess, "run", side_effect=fake_render
            ), mock.patch.object(ADAPTER, "probe", return_value={"duration": 1, "streams": {"video", "audio"}}):
                with self.assertRaisesRegex(ValueError, "choose audio_from_visual"):
                    ADAPTER.render(entry, "Demo", timing, root / "out", root / "runtime")

    def test_rendered_composition_becomes_portable_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "src/index.ts").write_text("// editable entry\n")
            (root / "package.json").write_text('{"name":"sample","private":true}')
            (root / "public").mkdir()
            (root / "public/asset.txt").write_text("asset")
            (root / "node_modules").mkdir()
            (root / "node_modules/skip.txt").write_text("skip")
            clip = root / "sample.mp4"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                            "-f", "lavfi", "-i", "color=c=red:s=320x180:r=30:d=0.6",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip)], check=True)
            timing = root / "timing.json"
            timing.write_text(json.dumps({"title": "Remotion test", "scenes": [
                {"id": "demo", "caption": "A product demo"}]}))
            original_run = subprocess.run

            def render_or_run(args, *other, **kwargs):
                if args[0] == "remotion":
                    shutil.copy2(clip, args[4])
                    return subprocess.CompletedProcess(args, 0)
                return original_run(args, *other, **kwargs)

            ready = {"ready": True, "paths": {"node": sys.executable, "remotion": "remotion",
                                               "ffmpeg": shutil.which("ffmpeg"),
                                               "ffprobe": shutil.which("ffprobe")}}
            with mock.patch.object(ADAPTER, "setup", return_value=ready), mock.patch.object(
                ADAPTER.subprocess, "run", side_effect=render_or_run
            ):
                result = ADAPTER.render(root / "src/index.ts", "Demo", timing,
                                        root / "rendered", root / "runtime")
            self.assertTrue(Path(result["video"]).is_file())
            self.assertTrue((root / "rendered/source/src/index.ts").is_file())
            self.assertTrue((root / "rendered/source/public/asset.txt").is_file())
            self.assertFalse((root / "rendered/source/node_modules").exists())
            self.assertFalse((root / "rendered/source/rendered").exists())
            manifest = json.loads((root / "rendered/manifest.json").read_text())
            self.assertEqual(manifest["composition"], "Demo")
            self.assertEqual(manifest["sourceEntry"], "source/src/index.ts")


if __name__ == "__main__":
    unittest.main()
