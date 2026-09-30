"""Exercise the scene assembler with real media streams and cue boundaries."""

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
ASSEMBLER = ROOT / "skills-src/_shared/tools/assemble_video.py"


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class AssembleVideoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def command(self, *args):
        return subprocess.run(args, check=True, capture_output=True, text=True)

    def clip(self, name, sound=False):
        target = self.root / name
        args = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=30:d=0.6"]
        if sound:
            args += ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=0.6"]
        args += ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
        if sound:
            args += ["-c:a", "aac", "-shortest"]
        args += [str(target)]
        self.command(*args)
        return target

    def assemble(self, scenes, name, **options):
        plan = self.root / f"{name}.json"
        plan.write_text(json.dumps({"title": name, "scenes": scenes, **options}), encoding="utf-8")
        result = self.command("python3", str(ASSEMBLER), str(plan), "--out", str(self.root / name))
        return json.loads(result.stdout)

    def streams(self, file):
        result = self.command("ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
                              "-of", "json", str(file))
        return {stream["codec_type"] for stream in json.loads(result.stdout)["streams"]}

    def test_footage_audio_and_scene_relative_cues(self):
        footage = self.clip("sound.mp4", sound=True)
        music = self.root / "bed.wav"
        self.command("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                     "-f", "lavfi", "-i", "sine=frequency=220:duration=0.4", str(music))
        result = self.assemble([{"visual": str(footage), "audio_from_visual": True,
                                 "duration_sec": 0.5, "cues": [
                                     {"start": 0.05, "end": 0.3, "text": "A tone"}]},
                                {"visual": str(footage), "duration_sec": 0.4,
                                 "caption": "Silent card"}], "with-audio",
                               music={"file": str(music), "volume": 0.1})
        self.assertEqual(self.streams(result["video"]), {"video", "audio"})
        self.assertEqual(self.streams(result["audio"]), {"audio"})
        cues = json.loads((self.root / "with-audio/captions.json").read_text())["cues"]
        self.assertAlmostEqual(cues[0]["start"], 0.05, places=2)
        self.assertAlmostEqual(cues[1]["start"], 0.5, places=2)
        self.assertIn("Silent card", (self.root / "with-audio/captions.srt").read_text())
        portable = json.loads((self.root / "with-audio/project.json").read_text())
        self.assertEqual(portable["scenes"][0]["visual"], "assets/scene-001.mp4")
        self.assertTrue((self.root / "with-audio" / portable["scenes"][0]["visual"]).is_file())
        self.assertIn("A tone", (self.root / "with-audio/script.md").read_text())

    def test_genuinely_silent_video_has_no_audio_export(self):
        footage = self.clip("silent.mp4")
        result = self.assemble([{"visual": str(footage), "duration_sec": 0.4,
                                 "caption": "Read this"}], "silent")
        self.assertEqual(self.streams(result["video"]), {"video"})
        self.assertIsNone(result["audio"])
        self.assertFalse((self.root / "silent/audio.mp3").exists())

    def test_music_only_project_exports_audio(self):
        footage = self.clip("music-card.mp4")
        music = self.root / "music.wav"
        self.command("ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                     "-f", "lavfi", "-i", "sine=frequency=330:duration=0.4",
                     str(music))
        result = self.assemble([{"visual": str(footage), "duration_sec": 0.6,
                                 "caption": "Music only"}], "music-only",
                               music={"file": str(music), "volume": 0.2})
        self.assertEqual(self.streams(result["video"]), {"video", "audio"})
        self.assertEqual(self.streams(result["audio"]), {"audio"})
        portable = json.loads((self.root / "music-only/project.json").read_text())
        self.assertEqual(portable["music"]["file"], "audio/background.wav")


if __name__ == "__main__":
    unittest.main()
