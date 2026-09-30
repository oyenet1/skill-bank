"""The installer can retry prerequisite setup after a partial install."""

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from scripts.install_video_skill import REPO, ROUTES, VOICE_SKILLS, check_avatar_provider, install


class InstallVideoSkillTests(unittest.TestCase):
    def test_install_delegates_parallel_setup_to_bootstrap_in_exact_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source/explainer-video"
            (source / "tools/kokoro").mkdir(parents=True)
            (source / "SKILL.md").write_text("---\nname: explainer-video\n---\n")
            (source / "tools/dependencies.json").write_text(json.dumps({"associated": ["voice-narration", "visual-assets"]}))
            target = root / "skills with spaces"
            with mock.patch("scripts.install_video_skill.REPO", root / "source"), mock.patch("scripts.install_video_skill.subprocess.run") as run:
                install("explainer-video", target)
            run.assert_called_once_with(
                [sys.executable, str(target / 'explainer-video/tools/bootstrap.py'),
                 '--yes', '--target', str(target)], check=True)

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
            self.assertEqual(run.call_count, 3)
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
            self.assertTrue((source / "tools/bootstrap.py").is_file(), skill)
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
                side_effect=[subprocess.CalledProcessError(1, "setup"), None],
            ) as run:
                with self.assertRaises(subprocess.CalledProcessError):
                    install("explainer-video", target)
                self.assertTrue((target / "explainer-video/SKILL.md").is_file())
                installed = install("explainer-video", target, resume=True)
                self.assertEqual(installed, target / "explainer-video")
                self.assertEqual(run.call_count, 2)
                self.assertEqual(Path(run.call_args_list[-1].args[0][1]).name, "bootstrap.py")

    def test_runtime_directory_is_forwarded_to_shared_bootstrap(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'installed'
            runtime = Path(temp) / 'private runtime'
            with mock.patch('scripts.install_video_skill.subprocess.run') as run:
                install('motion-graphics-video', target, runtime_dir=runtime)
            self.assertEqual(run.call_args.args[0][-2:], ['--runtime-dir', str(runtime)])

    def test_resume_requires_existing_skill(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError, "No installed skill"):
                install("explainer-video", Path(temp), resume=True)

    def test_existing_skill_is_reused_and_user_edits_survive(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            destination = target / 'motion-graphics-video'
            destination.mkdir()
            (destination / 'SKILL.md').write_text('user-customized skill')
            with mock.patch('scripts.install_video_skill.subprocess.run') as run:
                self.assertEqual(install('motion-graphics-video', target), destination)
            run.assert_called_once()
            self.assertEqual((destination / 'SKILL.md').read_text(), 'user-customized skill')

    def test_incomplete_destination_is_refused_without_overwriting(self):
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / 'motion-graphics-video'
            destination.mkdir()
            (destination / 'user-file').write_text('preserve')
            with self.assertRaisesRegex(RuntimeError, 'no files were overwritten'), mock.patch(
                'scripts.install_video_skill.subprocess.run') as run:
                install('motion-graphics-video', Path(temp))
            run.assert_not_called()
            self.assertEqual((destination / 'user-file').read_text(), 'preserve')


if __name__ == "__main__":
    unittest.main()
