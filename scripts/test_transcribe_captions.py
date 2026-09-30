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
    def test_explicit_managed_engine_remains_selected_with_native_installed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            worker = root / "fake_worker.py"
            worker.write_text("import json, pathlib\n"
                              "path=pathlib.Path(__file__).with_name('transcript.json')\n"
                              "path.write_text('[]')\n"
                              "print(json.dumps({'ok':True,'transcriptPath':str(path)}))\n")
            with mock.patch.object(BRIDGE, "native_whisper_available", return_value=True), mock.patch.object(BRIDGE, "isolated_command", return_value=([sys.executable, str(worker)], None)) as prepare:
                transcript = BRIDGE.run_transcriber(Path("managed"), root / "speech.wav", root, root / "log", "small.en", "en", runtime_dir=root / "runtime")
            prepare.assert_called_once()
            self.assertEqual(transcript, root / "transcript.json")

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
            with mock.patch.object(BRIDGE, "setup", return_value=ready), mock.patch.object(BRIDGE, "native_whisper_available", return_value=True):
                result = BRIDGE.transcribe(media, root / "out", root / "runtime", None, "en")
            self.assertTrue(result["reviewRequired"])
            self.assertEqual(result["cueCount"], 2)
            captions = json.loads((root / "out/captions.json").read_text())
            self.assertEqual(captions["source"], "local-asr")
            self.assertIn("Hello world.", (root / "out/captions.srt").read_text())
            self.assertIn("WEBVTT", (root / "out/captions.vtt").read_text())

    def test_managed_fallback_does_not_require_node_or_native_toolchain(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            media = root / "speech.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=2", str(media)], check=True)
            transcript = root / "words.json"
            transcript.write_text(json.dumps([{"text": "Bonjour", "start": .1, "end": .5}]))
            with mock.patch.object(BRIDGE, "native_whisper_available", return_value=False), mock.patch.object(BRIDGE, "setup") as renderer_setup, mock.patch.object(BRIDGE, "run_transcriber", return_value=transcript) as recognize:
                result = BRIDGE.transcribe(media, root / "out", root / "runtime", None, None)
            self.assertTrue(result["ready"])
            renderer_setup.assert_not_called()
            self.assertEqual(recognize.call_args.args[4], "small")
            self.assertEqual(recognize.call_args.args[-1], root / "runtime")
            captions = json.loads((root / "out/captions.json").read_text())
            self.assertEqual(captions["engine"], "faster-whisper")
            self.assertIn("Bonjour", (root / "out/captions.srt").read_text())

    def test_non_english_rejects_english_only_model(self):
        with tempfile.TemporaryDirectory() as temp:
            media = Path(temp) / "input.wav"
            media.write_bytes(b"sample")
            with self.assertRaisesRegex(ValueError, "multilingual"):
                BRIDGE.transcribe(media, Path(temp) / "out", Path(temp) / "runtime", "small.en", "es")


if __name__ == "__main__":
    unittest.main()
