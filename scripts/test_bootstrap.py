"""Cross-platform first-use bootstrap: OS detection and install planning."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
BOOTSTRAP = REPO / "skills-src" / "_shared" / "tools" / "bootstrap.py"

spec = importlib.util.spec_from_file_location("skill_bootstrap", BOOTSTRAP)
bootstrap = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules["skill_bootstrap"] = bootstrap
spec.loader.exec_module(bootstrap)

sys.path.insert(0, str(REPO / "scripts"))
import gen_skills  # noqa: E402


class HostDetection(unittest.TestCase):
    def test_supported_combinations(self):
        for system, machine, arch in (
            ("Linux", "x86_64", "x64"),
            ("Linux", "aarch64", "arm64"),
            ("Darwin", "arm64", "arm64"),
            ("Windows", "AMD64", "x64"),
        ):
            with mock.patch("platform.system", return_value=system), mock.patch(
                "platform.machine", return_value=machine
            ):
                host = bootstrap.host()
            self.assertTrue(host["supported"], f"{system}/{machine}")
            self.assertEqual(host["arch"], arch)

    def test_unsupported_cpu_is_reported(self):
        with mock.patch("platform.system", return_value="Linux"), mock.patch(
            "platform.machine", return_value="riscv64"
        ):
            host = bootstrap.host()
        self.assertFalse(host["supported"])
        self.assertEqual(host["arch"], "unsupported")


class PlanBuilding(unittest.TestCase):
    SPEC = {
        "skill": "explainer-video",
        "routes": ["explainer-video"],
        "voice": True,
        "transcription": True,
        "associated": ["voice-narration", "product-launch-video"],
        "repo": "oyenet1/agent-skills",
    }

    def test_runtime_steps_cover_every_route(self):
        steps = bootstrap.runtime_steps(self.SPEC, None)
        self.assertEqual([s["kind"] for s in steps], ["runtime", "transcription", "voice"])
        self.assertIn("explainer-video", steps[0]["command"])
        self.assertIn("--prepare-transcription", steps[1]["command"])
        self.assertEqual(Path(steps[2]["command"][1]).name, "start.py")

    def test_voice_only_spec_skips_video_runtime(self):
        spec = {"routes": [], "voice": True, "associated": []}
        steps = bootstrap.runtime_steps(spec, None)
        self.assertEqual([s["kind"] for s in steps], ["voice"])

    def test_skill_steps_only_list_missing_siblings(self):
        with tempfile.TemporaryDirectory() as temp:
            skills = Path(temp)
            (skills / "voice-narration").mkdir()
            (skills / "voice-narration" / "SKILL.md").write_text("---\nname: voice-narration\n---\n")
            with mock.patch("shutil.which", return_value="/usr/bin/npx"):
                steps = bootstrap.skill_steps(self.SPEC, skills, install=True)
        self.assertEqual([s["name"] for s in steps], ["product-launch-video"])
        self.assertEqual(steps[0]["command"][:3], ["/usr/bin/npx", "skills", "add"])
        self.assertEqual(steps[0]["command"][3], "oyenet1/agent-skills@product-launch-video")

    def test_missing_npx_marks_the_step_unavailable(self):
        with tempfile.TemporaryDirectory() as temp, mock.patch("shutil.which", return_value=None):
            steps = bootstrap.skill_steps(self.SPEC, Path(temp), install=True)
        self.assertTrue(all(not s["available"] for s in steps))

    def test_unavailable_skill_step_reports_the_command(self):
        with tempfile.TemporaryDirectory() as temp, mock.patch("shutil.which", return_value=None):
            step = bootstrap.skill_steps(self.SPEC, Path(temp), install=True)[0]
        with mock.patch("subprocess.run") as run:
            result = bootstrap.run_step(step)
        run.assert_not_called()
        self.assertFalse(result["ok"])
        self.assertIn("npx skills add", result["prompt"])


class WindowsLaunchers(unittest.TestCase):
    def test_cmd_is_wrapped_with_comspec(self):
        with mock.patch("platform.system", return_value="Windows"):
            argv = bootstrap.windows_argv(["C:/tools/setup.cmd", "--check"])
        self.assertEqual(Path(argv[0]).name.lower(), "cmd.exe")
        self.assertEqual(argv[1], "/c")

    def test_unix_argv_is_untouched(self):
        with mock.patch("platform.system", return_value="Linux"):
            argv = bootstrap.windows_argv(["python3", "bootstrap.py"])
        self.assertEqual(argv, ["python3", "bootstrap.py"])


class LauncherFiles(unittest.TestCase):
    def test_every_bootstrap_capability_ships_the_launchers(self):
        man = gen_skills.load_manifest()
        for cap, spec in man["capabilities"].items():
            if not spec.get("bootstrap"):
                continue
            targets = [spec["standalone"]] if spec.get("standalone") else []
            if spec.get("bundle"):
                targets.append(f"course-creator/subskills/{spec['bundle']}")
            for target in targets:
                for name in gen_skills.BOOTSTRAP_TOOLS + ["dependencies.json"]:
                    self.assertTrue((REPO / target / "tools" / name).is_file(), f"{cap}: {target}/{name}")

    def test_dependencies_document_shape(self):
        man = gen_skills.load_manifest()
        doc = gen_skills.dependencies_document("explainer-video", man["capabilities"]["explainer-video"], "standalone")
        self.assertEqual(doc["skill"], "explainer-video")
        self.assertEqual(doc["routes"], ["explainer-video"])
        self.assertTrue(doc["voice"] and doc["transcription"])
        self.assertIn("voice-narration", doc["associated"])
        for key in ("schemaVersion", "capability", "repo"):
            self.assertIn(key, doc)

    def test_bundle_targets_do_not_own_full_first_use_setup(self):
        man = gen_skills.load_manifest()
        doc = gen_skills.dependencies_document("explainer-video", man["capabilities"]["explainer-video"], "bundle")
        self.assertEqual(doc["associated"], [])
        self.assertFalse(doc["voice"])
        self.assertEqual(doc["skill"], "course-creator-explainer-video")


class CheckModeStopsShort(unittest.TestCase):
    def test_check_installs_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "dependencies.json"
            manifest.write_text(json.dumps({
                "skill": "explainer-video", "routes": ["explainer-video"],
                "voice": True, "transcription": True, "associated": ["voice-narration"],
                "repo": "oyenet1/agent-skills",
            }))
            with mock.patch.object(bootstrap, "DEPENDENCIES", manifest), mock.patch(
                "subprocess.run"
            ) as run, mock.patch.object(sys, "argv", ["bootstrap.py", "--check"]):
                code = bootstrap.main()
        run.assert_not_called()
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
