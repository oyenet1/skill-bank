"""Focused checks for the shared video runtime installer."""

import importlib.util
import json
import shutil
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest import mock


SOURCE = Path(__file__).resolve().parents[1] / "skills-src/_shared/tools/ensure_video_runtime.py"
SPEC = importlib.util.spec_from_file_location("ensure_video_runtime", SOURCE)
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class VideoRuntimeTests(unittest.TestCase):
    def test_platform_archives(self):
        self.assertEqual(runtime.platform_archive("v24.1.0", "Linux", "x86_64"), "node-v24.1.0-linux-x64.tar.xz")
        self.assertEqual(runtime.platform_archive("v24.1.0", "Darwin", "arm64"), "node-v24.1.0-darwin-arm64.tar.xz")
        self.assertEqual(runtime.platform_archive("v24.1.0", "Windows", "AMD64"), "node-v24.1.0-win-x64.zip")

    def test_windows_npm_tools_preserve_paths_and_arguments_without_shell(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node is needed to exercise the JavaScript launcher")
        with tempfile.TemporaryDirectory(prefix="video runtime & space ") as scratch:
            root = Path(scratch)
            modules = root / "node_modules"
            entries = {"npm": root / "node_modules/npm", "slidev": modules / "@slidev/cli",
                       "remotion": modules / "@remotion/cli", "hyperframes": modules / "hyperframes",
                       "playwright": modules / "playwright-chromium"}
            payload = 'caption & title; $(echo unexpected) "quoted"'
            for name, package in entries.items():
                package.mkdir(parents=True, exist_ok=True)
                (package / "cli.js").write_text("console.log(JSON.stringify(process.argv.slice(2)))")
                (package / "package.json").write_text(json.dumps({"bin": {name: "cli.js"}}))
                binary = root / "npm.cmd" if name == "npm" else modules / ".bin" / f"{name}.cmd"
                binary.parent.mkdir(parents=True, exist_ok=True)
                binary.write_text("This batch wrapper must never execute")
                with self.subTest(tool=name), mock.patch.object(runtime.platform, "system", return_value="Windows"), mock.patch.object(runtime, "progress"):
                    output = runtime.run([binary, "render", payload], Path(node), cwd=root)
                    self.assertEqual(json.loads(output), ["render", payload])

    def test_version_comparison(self):
        self.assertLess(runtime.parse_version("v22.11.0"), runtime.parse_version(runtime.MANIFEST["minimumNode"]))
        self.assertGreater(runtime.parse_version("v24.21.0"), runtime.parse_version(runtime.MANIFEST["minimumNode"]))

    def test_rejects_archive_escape(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            archive = root / "node.tar.xz"
            with tarfile.open(archive, "w:xz") as bundle:
                member = tarfile.TarInfo("../outside")
                member.size = 0
                bundle.addfile(member)
            with self.assertRaisesRegex(RuntimeError, "unsafe"):
                runtime.extract_node_archive(archive, root / "unpacked")

    def test_route_manifest_contains_runtime_packages(self):
        self.assertEqual(runtime.MANIFEST["routes"]["slide-decks"], ["slidev"])
        self.assertIn("remotion", runtime.MANIFEST["routes"]["product-launch-video"])
        self.assertIn("hyperframes", runtime.MANIFEST["routes"]["product-launch-video"])
        self.assertIn("hyperframes", runtime.MANIFEST["routes"]["explainer-video"])
        self.assertEqual(runtime.MANIFEST["routes"]["talking-head-video"], ["hyperframes"])
        self.assertEqual(runtime.MANIFEST["routes"]["avatar-video"], ["hyperframes"])
        self.assertIn("ffmpeg-static", runtime.MANIFEST["mediaPackages"])

    def test_every_profile_is_installable(self):
        for name, spec in runtime.MANIFEST["profiles"].items():
            self.assertTrue(spec["packages"], name)
            self.assertTrue(spec["binary"], name)
            self.assertIsInstance(spec.get("readyArgs", ["--version"]), list)

    def test_stale_browser_marker_does_not_report_ready(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            profile = root / "remotion"
            profile.mkdir()
            (profile / ".browser-ready").write_text("stale\n")
            with mock.patch.object(runtime, "install_profile", return_value=profile / "remotion"), mock.patch.object(
                runtime, "renderer_browser_ready", return_value=False
            ):
                paths, missing = runtime.ensure_profiles("product-launch-video", root, Path("node"), Path("npm"),
                                                         ensure=False, only="remotion")
            self.assertIn("remotion-browser", missing)
            self.assertIn("remotion", paths)
            self.assertEqual((profile / ".browser-ready").read_text(), "stale\n")

    def test_missing_browser_is_repaired_then_verified(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            profile = root / "hyperframes"
            profile.mkdir()
            binary = profile / "hyperframes"
            with mock.patch.object(runtime, "install_profile", return_value=binary), mock.patch.object(
                runtime, "renderer_browser_ready", side_effect=[False, True]
            ), mock.patch.object(runtime, "run") as run:
                _, missing = runtime.ensure_profiles("product-launch-video", root, Path("node"), Path("npm"),
                                                     ensure=True, only="hyperframes")
            self.assertEqual(missing, [])
            run.assert_called_once_with([binary, "browser", "ensure"], Path("node"), cwd=profile)
            self.assertTrue((profile / ".browser-ready").is_file())


if __name__ == "__main__":
    unittest.main()
