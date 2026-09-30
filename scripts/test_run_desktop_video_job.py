"""Exercise the desktop form import and runner handoff with real media."""

import base64
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parents[1] / "skills-src/_shared/tools"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location("run_desktop_video_job", TOOLS / "run_desktop_video_job.py")
DESKTOP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DESKTOP)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class DesktopVideoJobTests(unittest.TestCase):
    def payload(self, root):
        png = root / "card.png"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:s=320x180",
                        "-frames:v", "1", "-threads", "1", str(png)], check=True)
        return {"schemaVersion": 1, "captions": "plan", "request": {
            "title": "Desktop form", "category": "explainer", "language": "en", "aspect": "16:9", "fps": 30,
            "brandPrimary": "#123456", "sourceAssets": [], "scenes": [
                {"id": "intro", "durationSec": 0.5, "caption": "Hello", "visual": "Blue card",
                 "imagePngBase64": base64.b64encode(png.read_bytes()).decode()}]}}

    def test_form_to_verified_project_and_resume(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = self.payload(root)
            source = root / "form.json"
            source.write_text(json.dumps(payload))
            result = DESKTOP.run_desktop_job(source, root / "job")
            self.assertTrue(result["ready"])
            self.assertTrue(Path(result["video"]).is_file())
            self.assertTrue(Path(result["captionsSrt"]).is_file())
            self.assertIsNone(result["mixedAudio"])
            style = Path(result["directory"]) / "style.md"
            style.write_text("Reviewed style\n")
            resumed = DESKTOP.run_desktop_job(source, root / "job", resume=True)
            self.assertTrue(resumed["ready"])
            self.assertEqual(style.read_text(), "Reviewed style\n")
            self.assertTrue((Path(result["directory"]) / "source/desktop/desktop.json").is_file())
            payload["request"]["title"] = "Changed request"
            source.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "original desktop request"):
                DESKTOP.run_desktop_job(source, root / "job", resume=True)

    def test_uploaded_names_are_metadata_and_narration_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = self.payload(root)
            wav = root / "audio.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.4",
                            str(wav)], check=True)
            payload["request"]["scenes"][0]["audioSource"] = {
                "name": "../../escape.wav", "mime": "audio/wav", "dataBase64": base64.b64encode(wav.read_bytes()).decode()}
            source = root / "form.json"
            source.write_text(json.dumps(payload))
            job = DESKTOP.prepare_request(source, root / "job")
            timing = json.loads((job.parent / "inputs/timing.json").read_text())
            self.assertEqual(timing["scenes"][0]["narration"], "narration-0001.wav")
            self.assertTrue((job.parent / "inputs/narration-0001.wav").is_file())
            self.assertFalse((root / "escape.wav").exists())

    def test_rejects_two_narration_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = self.payload(root)
            payload["request"]["scenes"][0].update(audioSource={"name": "audio.wav"}, audioWavBase64="duplicate")
            source = root / "form.json"
            source.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "two narration sources"):
                DESKTOP.prepare_request(source, root / "job")


if __name__ == "__main__":
    unittest.main()
