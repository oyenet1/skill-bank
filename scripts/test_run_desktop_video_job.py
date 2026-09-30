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

    def test_generated_image_provenance_is_preserved_without_unknown_secret_fields(self):
        import hashlib
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = self.payload(root)
            data = (root / "card.png").read_bytes()
            provenance = {"provider": "openai", "model": "gpt-image-2", "prompt": "Supporting illustration", "size": "1536x1024", "quality": "medium", "createdAt": "2026-09-30", "sha256": hashlib.sha256(data).hexdigest(), "termsUrl": "https://openai.com/policies/terms-of-use/", "sourceType": "generated", "apiKey": "not-for-export"}
            payload["request"]["sourceAssets"] = [{"name": "generated.png", "mime": "image/png", "dataBase64": base64.b64encode(data).decode(), "provenance": provenance}]
            payload["request"]["scenes"][0]["sourceAssetIndex"] = 0
            source = root / "form.json"; source.write_text(json.dumps(payload))
            result = DESKTOP.run_desktop_job(source, root / "job")
            self.assertTrue(result["assetReviewRequired"])
            final = Path(result["directory"])
            manifest = json.loads((final / "manifest.json").read_text())
            record = manifest["assetSources"][0]
            self.assertEqual(record["provenance"]["sha256"], hashlib.sha256(data).hexdigest())
            self.assertTrue((final / record["file"]).is_file())
            self.assertNotIn("not-for-export", (final / "source/desktop/desktop.json").read_text())
            self.assertNotIn("apiKey", record["provenance"])
            payload["request"]["sourceAssets"][0]["provenance"]["sha256"] = "wrong"
            source.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError, "does not match"):
                DESKTOP.prepare_request(source, root / "bad-job")

    def test_authored_sources_keep_real_assets_and_measured_narration(self):
        for renderer in ("hyperframes", "remotion", "slidev"):
            with self.subTest(renderer=renderer), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                payload = self.payload(root)
                request = payload["request"]
                request["renderer"] = renderer
                request.update(headlineFont="Outfit", bodyFont="Inter")
                request["title"] = '</script><script>unexpected()</script> {{ unsafe }}'
                image_bytes = (root / "card.png").read_bytes()
                request["sourceAssets"] = [{"name": "real screenshot.png", "mime": "image/png",
                                            "dataBase64": base64.b64encode(image_bytes).decode()}]
                scene = request["scenes"][0]
                scene["sourceAssetIndex"] = 0
                scene["visual"] = '<img onerror="unexpected()"> {{ unsafe }}'
                scene["screenText"] = '<img onerror="unexpected()"> {{ unsafe }}'
                wav = root / "narration.wav"
                subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=0.73", str(wav)], check=True)
                scene["audioSource"] = {"name": "narration.wav", "mime": "audio/wav", "dataBase64": base64.b64encode(wav.read_bytes()).decode()}
                source = root / "form.json"
                source.write_text(json.dumps(payload))
                job = DESKTOP.prepare_request(source, root / "job")
                config = json.loads(job.read_text())
                checked = DESKTOP.run_job.__globals__["request_config"](job)
                self.assertEqual(checked["renderer"], "storyboard")
                self.assertEqual(config["authoringRenderer"], renderer)
                contract = job.parent / config["source"]
                spec = json.loads(contract.read_text())
                entry = spec["scenes"][0]
                self.assertGreaterEqual(entry["duration_sec"], 0.73)
                self.assertLess(entry["duration_sec"], 0.73 + 1 / request["fps"])
                folder = contract.parent / entry["folder"]
                self.assertEqual((folder / "public/media.png").read_bytes(), image_bytes)
                self.assertEqual((job.parent / "inputs/narration-0001.wav").read_bytes(), wav.read_bytes())
                authored = (folder / entry["entry"]).read_text()
                self.assertNotIn('<script>unexpected()', authored)
                self.assertNotIn('<img onerror=', authored)
                self.assertTrue((folder / "scene.json").is_file())
                fonts = json.loads((folder / "scene.json").read_text())
                self.assertEqual(fonts["headlineFont"], "Outfit")
                self.assertEqual(fonts["bodyFont"], "Inter")

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
