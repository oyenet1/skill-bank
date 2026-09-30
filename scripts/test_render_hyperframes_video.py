"""Check HyperFrames composition packaging with a real encoded clip."""

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
SPEC = importlib.util.spec_from_file_location("render_hyperframes_video", TOOLS / "render_hyperframes_video.py")
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class HyperFramesAdapterTests(unittest.TestCase):
    def test_rendered_html_becomes_portable_project(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            composition = root / "index.html"
            composition.write_text("<html><body>Editable composition</body></html>")
            (root / "assets").mkdir()
            (root / "assets/image.txt").write_text("asset")
            (root / "node_modules").mkdir()
            (root / "node_modules/skip.txt").write_text("skip")
            clip = root / "sample.mp4"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                            "-f", "lavfi", "-i", "color=c=green:s=320x180:r=30:d=0.6",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip)], check=True)
            timing = root / "timing.json"
            timing.write_text(json.dumps({"title": "HyperFrames test", "scenes": [
                {"id": "demo", "caption": "A product demo"}]}))
            original_run = subprocess.run
            seen_commands = []

            def render_or_run(args, *other, **kwargs):
                if args[0] == "hyperframes":
                    seen_commands.append(args)
                    shutil.copy2(clip, args[args.index("--output") + 1])
                    return subprocess.CompletedProcess(args, 0)
                return original_run(args, *other, **kwargs)

            ready = {"ready": True, "paths": {"node": sys.executable, "hyperframes": "hyperframes",
                                               "ffmpeg": shutil.which("ffmpeg"),
                                               "ffprobe": shutil.which("ffprobe")}}
            with mock.patch.object(ADAPTER, "setup", return_value=ready), mock.patch.object(
                ADAPTER.subprocess, "run", side_effect=render_or_run
            ):
                result = ADAPTER.render(composition, timing, root / "rendered", root / "runtime")
            self.assertTrue(Path(result["video"]).is_file())
            self.assertTrue((root / "rendered/source/index.html").is_file())
            self.assertTrue((root / "rendered/source/assets/image.txt").is_file())
            self.assertFalse((root / "rendered/source/node_modules").exists())
            self.assertFalse((root / "rendered/source/rendered").exists())
            manifest = json.loads((root / "rendered/manifest.json").read_text())
            self.assertEqual(manifest["renderer"], "hyperframes")
            self.assertEqual(manifest["sourceComposition"], "source/index.html")
            self.assertEqual(seen_commands[0][seen_commands[0].index("-c") + 1], "index.html")


if __name__ == "__main__":
    unittest.main()
