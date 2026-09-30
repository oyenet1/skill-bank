"""Exercise the app-facing video job contract with a real encoded project."""

import json
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


RUNNER = Path(__file__).resolve().parent.parent / "skills-src/_shared/tools/run_video_job.py"
sys.path.insert(0, str(RUNNER.parent))
SPEC = importlib.util.spec_from_file_location("run_video_job", RUNNER)
JOB = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(JOB)


class JobCancellationTests(unittest.TestCase):
    def test_windows_falls_back_when_taskkill_is_unavailable(self):
        child = mock.Mock()
        child.pid = 123
        child.poll.return_value = None
        with mock.patch.object(JOB, "ACTIVE_CHILD", child), mock.patch.object(
            JOB.platform, "system", return_value="Windows"
        ), mock.patch.object(JOB.subprocess, "run", side_effect=FileNotFoundError):
            JOB.stop_child()
        child.terminate.assert_called_once()
        child.wait.assert_called_once_with(timeout=5)


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "FFmpeg required")
class VideoJobTests(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "POSIX process groups required")
    def test_cancel_stops_active_process_group(self):
        child = subprocess.Popen(["sleep", "30"], start_new_session=True)
        JOB.ACTIVE_CHILD = child
        try:
            JOB.stop_child()
            self.assertIsNotNone(child.poll())
        finally:
            JOB.ACTIVE_CHILD = None
            if child.poll() is None:
                child.kill()
                child.wait()

    def test_failed_subtitles_resume_without_rerendering(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            visual = root / "visual.mp4"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                            "color=c=blue:s=320x180:r=30:d=0.5", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            str(visual)], check=True)
            (root / "timing.json").write_text(json.dumps({"scenes": [
                {"visual": "visual.mp4", "duration_sec": 0.5, "caption": "Hello"}]}))
            request = root / "request.json"
            request.write_text(json.dumps({"schemaVersion": 1, "route": "explainer-video", "renderer": "scenes",
                                           "timing": "timing.json", "output": "project", "captions": "transcribe"}))
            original = JOB.command_result
            calls = 0

            def subtitles_fail_then_succeed(command, log):
                nonlocal calls
                if not command[1].endswith("transcribe_captions.py"):
                    return original(command, log)
                calls += 1
                if calls == 1:
                    raise RuntimeError("model download unavailable")
                output = root / "project"
                (output / "captions.json").write_text(json.dumps({"source": "local-asr", "cues": []}))
                (output / "captions.srt").write_text("reviewed\n")
                (output / "captions.vtt").write_text("WEBVTT\n")
                return {"ready": True, "reviewRequired": True}

            with mock.patch.object(JOB, "command_result", side_effect=subtitles_fail_then_succeed):
                with self.assertRaisesRegex(RuntimeError, "model download unavailable"):
                    JOB.run_job(request)
                video = root / "project/video.mp4"
                self.assertTrue(video.is_file())
                first_mtime = video.stat().st_mtime_ns
                self.assertEqual(json.loads((root / "project.job-state.json").read_text())["status"], "failed")
                result = JOB.run_job(request, resume=True)
            self.assertEqual(result["status"], "review_required")
            self.assertEqual(video.stat().st_mtime_ns, first_mtime)
            self.assertEqual(calls, 2)

    def test_scene_job_and_resume_keep_final_output_verified(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            visual = root / "visual.mp4"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                            "color=c=purple:s=320x180:r=30:d=0.5", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            str(visual)], check=True)
            timing = root / "timing.json"
            timing.write_text(json.dumps({"title": "Job test", "scenes": [
                {"id": "intro", "visual": "visual.mp4", "duration_sec": 0.5, "caption": "Hello"}]}))
            request = root / "request.json"
            request.write_text(json.dumps({"schemaVersion": 1, "route": "explainer-video", "renderer": "scenes",
                                           "timing": "timing.json", "output": "project", "captions": "auto"}))
            first = subprocess.run([sys.executable, str(RUNNER), str(request)], capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            result = json.loads(first.stdout)
            self.assertEqual(result["status"], "complete")
            video = root / "project/video.mp4"
            self.assertTrue(video.is_file())
            first_mtime = video.stat().st_mtime_ns
            manifest = json.loads((root / "project/manifest.json").read_text())
            self.assertEqual(manifest["jobRoute"], "explainer-video")
            self.assertTrue((root / "project/request.json").is_file())
            resumed = subprocess.run([sys.executable, str(RUNNER), str(request), "--resume"],
                                     capture_output=True, text=True)
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertIn("Reusing verified complete project", resumed.stderr)
            self.assertEqual(video.stat().st_mtime_ns, first_mtime)
            state = json.loads((root / "project.job-state.json").read_text())
            self.assertEqual(state["status"], "complete")


if __name__ == "__main__":
    unittest.main()
