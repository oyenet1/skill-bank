"""Honest unsupported modes, verified clips, cancellation and offline inference."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / "skills-src/_shared/tools"
sys.path.insert(0, str(TOOLS))
import avatar_generate as generator


class AvatarGenerateTests(unittest.TestCase):
    def test_unsupported_modes_and_rights_gate_leave_no_output(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output"
            for mode in ("avatar", "dub"):
                result = generator.generate(Path(temp), "musetalk-15", mode, None, None, output)
                self.assertEqual(result["reason"], f"local-{mode}-mode-unsupported")
                self.assertIsNone(result["video"])
            result = generator.generate(Path(temp), "musetalk-15", "photo", None, None, output)
            self.assertEqual(result["reason"], "image-rights-confirmation-required")
            self.assertFalse(output.exists())

    def test_worker_blocks_outbound_requests(self):
        code = "import avatar_infer_worker as w; w.block_network(); import urllib.request; urllib.request.urlopen('https://example.test/')"
        import os
        env = {**os.environ, "PYTHONPATH": str(TOOLS)}
        result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot access the network", result.stderr)

    def test_failure_and_cancellation_preserve_work_without_final_video(self):
        backend = generator.manifest()["backends"][0]
        capability = {"eligible": True, "accelerator": {"kind": "cuda", "memoryBytes": 8 * 1024**3}}
        for error in (RuntimeError("inference failed"), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                image, audio = root / "portrait.png", root / "speech.wav"
                image.write_bytes(b"fixture"); audio.write_bytes(b"fixture")
                with patch.object(generator, "probe", return_value=capability), patch.object(generator, "status", return_value={"ready": True, "state": {}}), patch.object(generator, "infer", side_effect=error):
                    result = generator.generate(root, backend["id"], "photo", image, audio, root / "output", rights_confirmed=True)
                self.assertFalse(result["ready"])
                self.assertTrue(Path(result["work"]).is_dir())
                self.assertFalse((root / "output/video.mp4").exists())

    def test_inference_verification_and_long_clip_warning(self):
        from avatar_runtime import paths
        for final_streams, clip_duration, succeeds, kind in ((["video", "audio"], 31, True, "musetalk"), (["video"], 31, False, "musetalk"), (["video", "audio"], 20, False, "musetalk"), (["video", "audio"], 32, True, "latentsync")):
            with self.subTest(streams=final_streams, duration=clip_duration), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                backend = json.loads(json.dumps(generator.manifest()["backends"][0]))
                backend["files"] = []
                backend["workerKind"] = kind
                location = paths(root, backend)
                location["source"].mkdir(parents=True)
                (location["source"] / "source.py").write_text("# fixture")
                image, audio = root / "image.png", root / "audio.wav"
                image.touch(); audio.touch()
                work = root / "work"; work.mkdir()
                commands = []
                def run(command, *args, **kwargs):
                    commands.append(command)
                    self.assertEqual(args[1]["TORCH_HOME"], str(work / "project"))
                    if any(str(arg).endswith("avatar_infer_worker.py") for arg in command):
                        result = work / "project/results/presenter.mp4"
                        result.parent.mkdir(parents=True)
                        result.write_bytes(b"fixture")
                    elif str(command[-1]).endswith("video.mp4"):
                        Path(command[-1]).write_bytes(b"fixture")
                probes = [{"streams": ["audio"], "duration": 31}, {"streams": ["video"], "duration": clip_duration}, {"streams": final_streams, "duration": 31}]
                state = {"accelerator": {"kind": "cuda"}, "mediaPaths": {"ffmpeg": "ffmpeg", "ffprobe": "ffprobe"}}
                with patch.object(generator, "run", side_effect=run), patch.object(generator, "inspect_media", side_effect=probes), patch.object(generator, "progress") as progress:
                    if succeeds:
                        self.assertTrue(generator.infer(root, backend, state, image, audio, work)[0].is_file())
                    else:
                        with self.assertRaises(RuntimeError):
                            generator.infer(root, backend, state, image, audio, work)
                    self.assertTrue(any(call.args[0] == "warning" for call in progress.call_args_list))
                    if kind == "latentsync":
                        self.assertTrue(any(any(str(arg).startswith("apad=whole_dur=") for arg in command) for command in commands))


if __name__ == "__main__":
    unittest.main()
