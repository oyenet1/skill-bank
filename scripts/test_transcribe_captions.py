"""Check measured-word grouping and the local transcription bridge."""

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
SPEC = importlib.util.spec_from_file_location("transcribe_captions", TOOLS / "transcribe_captions.py")
BRIDGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BRIDGE)


class TranscriptGroupingTests(unittest.TestCase):
    def test_cues_follow_word_pauses_and_punctuation(self):
        words = [{"start": 0.1, "end": 0.3, "text": "Hello"},
                 {"start": 0.32, "end": 0.5, "text": "world."},
                 {"start": 1.2, "end": 1.5, "text": "Next"},
                 {"start": 1.52, "end": 1.8, "text": "scene"}]
        cues = BRIDGE.group_words(words, 2)
        self.assertEqual([cue["text"] for cue in cues], ["Hello world.", "Next scene"])
        self.assertEqual(cues[1]["start"], 1.2)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class TranscriptionBridgeTests(unittest.TestCase):
    def test_final_media_produces_reviewable_caption_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            media = root / "speech.wav"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                            "sine=frequency=440:duration=2", str(media)], check=True)
            fake_cli = root / "hyperframes"
            fake_cli.write_text("#!/usr/bin/env python3\n"
                                "import json, pathlib, sys\n"
                                "folder=pathlib.Path(sys.argv[sys.argv.index('--dir')+1])\n"
                                "words=[{'text':'Hello','start':0.1,'end':0.3},"
                                "{'text':'world.','start':0.32,'end':0.5},"
                                "{'text':'Next','start':1.2,'end':1.5}]\n"
                                "path=folder/'transcript.json'\n"
                                "path.write_text(json.dumps(words))\n"
                                "print(json.dumps({'ok':True,'transcriptPath':str(path)}))\n")
            fake_cli.chmod(0o755)
            ready = {"ready": True, "paths": {"hyperframes": str(fake_cli), "ffprobe": shutil.which("ffprobe")}}
            with mock.patch.object(BRIDGE, "setup", return_value=ready):
                result = BRIDGE.transcribe(media, root / "out", root / "runtime", None, "en")
            self.assertTrue(result["reviewRequired"])
            self.assertEqual(result["cueCount"], 2)
            captions = json.loads((root / "out/captions.json").read_text())
            self.assertEqual(captions["source"], "local-asr")
            self.assertIn("Hello world.", (root / "out/captions.srt").read_text())
            self.assertIn("WEBVTT", (root / "out/captions.vtt").read_text())

    def test_non_english_rejects_english_only_model(self):
        with tempfile.TemporaryDirectory() as temp:
            media = Path(temp) / "input.wav"
            media.write_bytes(b"sample")
            with self.assertRaisesRegex(ValueError, "multilingual"):
                BRIDGE.transcribe(media, Path(temp) / "out", Path(temp) / "runtime", "small.en", "es")


if __name__ == "__main__":
    unittest.main()
