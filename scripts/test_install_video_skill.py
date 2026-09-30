"""The installer can retry prerequisite setup after a partial install."""

from pathlib import Path
import json
import subprocess
import tempfile
import unittest
from unittest import mock

from scripts.install_video_skill import REPO, ROUTES, VOICE_SKILLS, check_avatar_provider, install


class InstallVideoSkillTests(unittest.TestCase):
    def test_install_prepares_associated_skills_in_the_exact_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source/explainer-video"
            (source / "tools/kokoro").mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: explainer-video\n---\n")
            (source / "tools/dependencies.json").write_text(json.dumps({"associated": ["voice-narration", "visual-assets"]}))
            target = root / "skills with spaces"
            with mock.patch("scripts.install_video_skill.REPO", root / "source"), mock.patch("scripts.install_video_skill.subprocess.run") as run:
                install("explainer-video", target)
            commands = [call.args[0] for call in run.call_args_list]
            associated = [command for command in commands if Path(command[1]).name == "install_sibling_skill.py"]
            self.assertEqual([command[2] for command in associated], ["voice-narration", "visual-assets"])
            self.assertTrue(all(command[3:] == ["--target", str(target)] for command in associated))
            self.assertNotIn("npx", str(associated))

    def test_avatar_install_keeps_fallback_when_hosted_provider_is_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source/avatar-video"
            (source / "tools/kokoro").mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: avatar-video\n---\n")
            for name in ("ensure_video_runtime.py", "ensure_python_runtime.py", "avatar_ensure.py", "avatar_provider.py", "kokoro/start.py"):
                (source / "tools" / name).write_text("# test fixture\n")
            with mock.patch("scripts.install_video_skill.REPO", root / "source"), mock.patch("scripts.install_video_skill.subprocess.run") as run, mock.patch("scripts.install_video_skill.check_avatar_provider", side_effect=AssertionError("Installer must let the dispatcher prefer local or fallback")):
                result = install("avatar-video", root / "installed")
            self.assertTrue((result / "SKILL.md").is_file())
            self.assertEqual(Path(run.call_args.args[0][1]).name, "avatar_provider.py")
            self.assertEqual(run.call_count, 5)
            self.assertEqual(Path(run.call_args_list[-2].args[0][1]).name, "avatar_ensure.py")
            self.assertIn("--check", run.call_args_list[-2].args[0])
            self.assertNotIn("--accept", str(run.call_args_list))

    def test_avatar_provider_must_be_installed_and_authenticated(self):
        with mock.patch("scripts.install_video_skill.platform.system", return_value="Linux"), mock.patch(
            "scripts.install_video_skill.shutil.which", return_value=None
        ):
            with self.assertRaisesRegex(RuntimeError, "HeyGen CLI is missing"):
                check_avatar_provider()
        with mock.patch("scripts.install_video_skill.platform.system", return_value="Linux"), mock.patch(
            "scripts.install_video_skill.shutil.which", return_value="/usr/bin/heygen"
        ), mock.patch("scripts.install_video_skill.subprocess.run", return_value=subprocess.CompletedProcess([], 3)):
            with self.assertRaisesRegex(RuntimeError, "not authenticated"):
                check_avatar_provider()

    def test_avatar_provider_uses_wsl_on_windows_when_needed(self):
        def which(name):
            return "C:/Windows/System32/wsl.exe" if name == "wsl.exe" else None
        with mock.patch("scripts.install_video_skill.platform.system", return_value="Windows"), mock.patch(
            "scripts.install_video_skill.shutil.which", side_effect=which
        ), mock.patch("scripts.install_video_skill.subprocess.run", return_value=subprocess.CompletedProcess([], 0)) as run:
            check_avatar_provider()
            self.assertEqual(run.call_args.args[0][:3], ["C:/Windows/System32/wsl.exe", "--exec", "heygen"])

    def test_every_declared_skill_ships_its_setup_tools(self):
        for skill, routes in ROUTES.items():
            source = REPO / skill
            self.assertTrue((source / "SKILL.md").is_file(), skill)
            if skill in VOICE_SKILLS:
                self.assertTrue((source / "tools/kokoro/start.py").is_file(), skill)
            if routes:
                runtime_tool = (source / "subskills/course-creator-explainer-video/tools/ensure_video_runtime.py"
                                if skill == "course-creator" else source / "tools/ensure_video_runtime.py")
                self.assertTrue(runtime_tool.is_file(), skill)
                if skill != "slide-decks":
                    self.assertTrue(runtime_tool.with_name("ensure_python_runtime.py").is_file(), skill)

    def test_resume_after_runtime_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source/explainer-video"
            (source / "tools/kokoro").mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: explainer-video\n---\n")
            (source / "tools/ensure_video_runtime.py").write_text("# installer test\n")
            (source / "tools/ensure_python_runtime.py").write_text("# installer test\n")
            (source / "tools/kokoro/start.py").write_text("# installer test\n")
            target = root / "installed"
            with mock.patch("scripts.install_video_skill.REPO", root / "source"), mock.patch(
                "scripts.install_video_skill.subprocess.run",
                side_effect=[subprocess.CalledProcessError(1, "setup"), None, None, None],
            ) as run:
                with self.assertRaises(subprocess.CalledProcessError):
                    install("explainer-video", target)
                self.assertTrue((target / "explainer-video/SKILL.md").is_file())
                installed = install("explainer-video", target, resume=True)
                self.assertEqual(installed, target / "explainer-video")
                self.assertEqual(run.call_count, 4)
                self.assertIn("--prepare-transcription", run.call_args_list[-2].args[0])
                self.assertEqual(Path(run.call_args_list[-1].args[0][1]).name, "start.py")

    def test_resume_requires_existing_skill(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError, "No installed skill"):
                install("explainer-video", Path(temp), resume=True)


if __name__ == "__main__":
    unittest.main()
