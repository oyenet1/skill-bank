"""Timed subtitle export checks."""

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parent.parent / "skills-src/_shared/tools/write_subtitles.py"
SPEC = importlib.util.spec_from_file_location("write_subtitles", SCRIPT)
subtitles = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(subtitles)


class SubtitleExport(unittest.TestCase):
    def test_formats_and_millisecond_rollover(self):
        cues = subtitles.validate({"duration_sec": 62, "cues": [
            {"start": 0.0, "end": 1.9996, "text": "Hello"},
            {"start": 2.1, "end": 61.5, "text": "Next line"},
        ]})
        self.assertIn("00:00:00,000 --> 00:00:02,000", subtitles.render(cues))
        self.assertIn("00:01:01.500", subtitles.render(cues, webvtt=True))
        self.assertTrue(subtitles.render(cues, webvtt=True).startswith("WEBVTT\n\n"))

    def test_rejects_unmeasured_or_invalid_timing(self):
        for data in (
            {"cues": []},
            {"duration_sec": 1, "cues": [{"start": 0, "end": 2, "text": "too long"}]},
            {"duration_sec": 2, "cues": [{"start": 0, "end": 1, "text": "first"},
                      {"start": 0.9, "end": 2, "text": "overlap"}]},
            {"duration_sec": 2, "cues": [{"start": 0, "end": 1, "text": ""}]},
            {"duration_sec": 2, "cues": [{"start": -0.0001, "end": 1, "text": "negative"}]},
            {"duration_sec": 2, "cues": [{"start": 0.0001, "end": 0.0002, "text": "zero milliseconds"}]},
        ):
            with self.subTest(data=data), self.assertRaises(ValueError):
                subtitles.validate(data)


if __name__ == "__main__":
    unittest.main()
