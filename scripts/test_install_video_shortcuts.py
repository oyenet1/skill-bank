"""Check shortcut installation and preservation of existing host commands."""

from pathlib import Path
import tempfile
import unittest

import install_video_shortcuts


class ShortcutInstallation(unittest.TestCase):
    def test_both_hosts_install_complete_templates_and_are_repeatable(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / "commands"
                paths = install_video_shortcuts.install(host, target)
                self.assertEqual(len(paths), 6)
                for dest in paths:
                    source = install_video_shortcuts.REPO / "commands" / host / dest.name
                    self.assertEqual(dest.read_bytes(), source.read_bytes())
                self.assertEqual(install_video_shortcuts.install(host, target), paths)

    def test_conflict_preserves_user_file_and_writes_no_other_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            existing = target / "tutorial.md"
            existing.write_text("My existing tutorial command")
            with self.assertRaisesRegex(ValueError, "Existing shortcut differs"):
                install_video_shortcuts.install("codex", target)
            self.assertEqual(existing.read_text(), "My existing tutorial command")
            self.assertEqual(list(target.iterdir()), [existing])

    def test_symlink_is_rejected_even_with_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root / "original.md"
            original.write_text("Keep this unrelated file")
            target = root / "commands"
            target.mkdir()
            (target / "tutorial.md").symlink_to(original)
            with self.assertRaisesRegex(ValueError, "non-regular destination"):
                install_video_shortcuts.install("claude", target, overwrite=True)
            self.assertEqual(original.read_text(), "Keep this unrelated file")
            self.assertEqual(len(list(target.iterdir())), 1)

    def test_explicit_overwrite_replaces_conflicting_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "tutorial.md").write_text("Old command")
            paths = install_video_shortcuts.install("claude", target, overwrite=True)
            self.assertEqual(len(paths), 6)
            self.assertEqual(
                (target / "tutorial.md").read_bytes(),
                (install_video_shortcuts.REPO / "commands/claude/tutorial.md").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
