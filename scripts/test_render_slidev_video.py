"""Check the Slidev export-to-assembler handoff with deterministic frames."""

import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zlib


TOOLS = Path(__file__).resolve().parent.parent / "skills-src/_shared/tools"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location("render_slidev_video", TOOLS / "render_slidev_video.py")
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)


def one_pixel_png(path):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    pixels = zlib.compress(b"\x00\x20\x70\xc0")
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
                     + chunk(b"IDAT", pixels) + chunk(b"IEND", b""))


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class SlidevAdapterTests(unittest.TestCase):
    def test_exported_click_states_become_timed_video(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            deck = root / "slides.md"
            deck.write_text("# Hello\n\n<v-click>World</v-click>\n")
            timing = root / "timing.json"
            timing.write_text(json.dumps({"title": "Slidev test", "scenes": [
                {"id": "opening", "duration_sec": 0.4, "caption": "Hello"},
                {"id": "reveal", "duration_sec": 0.4, "caption": "World"}]}))
            original_run = subprocess.run

            def export_or_run(args, *other, **kwargs):
                if args[0] == "slidev":
                    frames = Path(args[args.index("--output") + 1])
                    frames.mkdir()
                    one_pixel_png(frames / "001-01.png")
                    one_pixel_png(frames / "001-02.png")
                    return subprocess.CompletedProcess(args, 0)
                return original_run(args, *other, **kwargs)

            ready = {"ready": True, "paths": {"node": sys.executable, "slidev": "slidev",
                                               "ffmpeg": shutil.which("ffmpeg"),
                                               "ffprobe": shutil.which("ffprobe")}}
            with mock.patch.object(ADAPTER, "setup", return_value=ready), mock.patch.object(
                ADAPTER.subprocess, "run", side_effect=export_or_run
            ):
                result = ADAPTER.render(deck, timing, root / "video", root / "runtime")
            self.assertTrue(Path(result["video"]).is_file())
            self.assertTrue((root / "video/source/slides.md").is_file())
            captions = json.loads((root / "video/captions.json").read_text())["cues"]
            self.assertAlmostEqual(captions[1]["start"], 0.4, places=2)
            manifest = json.loads((root / "video/manifest.json").read_text())
            self.assertEqual(manifest["renderer"], "slidev")


if __name__ == "__main__":
    unittest.main()
