"""Caption edits remain consistent, bound to media, and recoverable."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

TOOLS = Path(__file__).resolve().parents[1] / "skills-src/_shared/tools"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location("review_captions", TOOLS / "review_captions.py")
REVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REVIEW)


class CaptionReviewTests(unittest.TestCase):
    def project(self, root):
        project = root / "project"
        project.mkdir()
        (project / "video.mp4").write_bytes(b"media whose recorded fingerprint must stay unchanged")
        (project / "captions.json").write_text(json.dumps({"duration_sec": 2, "review_required": True,
            "source": "local-asr", "cues": [{"start": 0, "end": 1, "text": "wrong text"}]}))
        (project / "captions.srt").write_text("original srt")
        (project / "captions.vtt").write_text("original vtt")
        (project / "transcript.json").write_text("original word timings")
        (project / "manifest.json").write_text(json.dumps({"status": "complete", "reviewRequired": True}))
        REVIEW.state_path(project).write_text(json.dumps({"status": "review_required", "durationSec": 2,
            "reviewRequired": True, "videoSha256": REVIEW.fingerprint(project / "video.mp4")}))
        return project

    def test_saves_matching_exports_and_review_state_without_changing_asr_words(self):
        with tempfile.TemporaryDirectory() as temp:
            project = self.project(Path(temp))
            draft = REVIEW.load_review(project)
            draft["cues"] = [{"start": 0.1, "end": 1.25, "text": "Corrected\n\ncaption"}]
            result = REVIEW.save_review(project, draft, draft["captionSha256"])
            self.assertFalse(result["review_required"])
            self.assertIn("00:00:00,100 --> 00:00:01,250\nCorrected\ncaption", (project / "captions.srt").read_text())
            self.assertIn("00:00:00.100 --> 00:00:01.250", (project / "captions.vtt").read_text())
            state = json.loads(REVIEW.state_path(project).read_text())
            self.assertEqual(state["status"], "complete")
            self.assertFalse(state["reviewRequired"])
            self.assertEqual(state["captionsSha256"], REVIEW.fingerprint(project / "captions.json"))
            self.assertTrue(Path(result["backup"]).is_dir())
            self.assertEqual((project / "transcript.json").read_text(), "original word timings")
            with self.assertRaisesRegex(ValueError, "reload"):
                REVIEW.save_review(project, draft, draft["captionSha256"])

    def test_rejects_changed_media_and_invalid_timing_before_any_export(self):
        with tempfile.TemporaryDirectory() as temp:
            project = self.project(Path(temp))
            draft = REVIEW.load_review(project)
            draft["cues"][0]["end"] = 3
            with self.assertRaisesRegex(ValueError, "duration"):
                REVIEW.save_review(project, draft, draft["captionSha256"])
            self.assertEqual((project / "captions.srt").read_text(), "original srt")
            (project / "video.mp4").write_bytes(b"a different video")
            with self.assertRaisesRegex(ValueError, "video changed"):
                REVIEW.load_review(project)

    def test_recovers_an_interrupted_bundle_before_reopening(self):
        with tempfile.TemporaryDirectory() as temp:
            project = self.project(Path(temp))
            draft = REVIEW.load_review(project)
            draft["cues"][0]["text"] = "new caption"
            original = REVIEW.atomic_write
            failed = False

            def interrupt(path, data):
                nonlocal failed
                if path.name == "captions.vtt":
                    failed = True
                if failed:
                    raise OSError("simulated interruption during commit and recovery")
                original(path, data)

            with mock.patch.object(REVIEW, "atomic_write", side_effect=interrupt):
                with self.assertRaises(OSError):
                    REVIEW.save_review(project, draft, draft["captionSha256"])
            self.assertTrue((project / ".caption-review.pending.json").is_file())
            restored = REVIEW.load_review(project)
            self.assertEqual(restored["captionSha256"], draft["captionSha256"])
            self.assertEqual((project / "captions.srt").read_text(), "original srt")
            self.assertFalse((project / ".caption-review.pending.json").exists())


if __name__ == "__main__":
    unittest.main()
