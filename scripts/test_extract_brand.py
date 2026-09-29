"""Behavior checks for local brand extraction."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_brand  # noqa: E402


def make_project(root: Path) -> None:
    (root / "package.json").write_text(json.dumps({"name": "acme-lms"}))
    (root / "README.md").write_text(
        "# Acme Learning\n\nTeach anything in ten minutes.\n\nSome more prose.\n"
    )
    (root / "tailwind.config.js").write_text(
        """
        module.exports = {
          theme: {
            extend: {
              colors: {
                background: '#0B0B0F',
                surface: '#FAFAF8',
                accent: '#4F7CFF',
                success: '#12B981',
              },
              fontFamily: {
                display: ['Space Grotesk', 'sans-serif'],
                body: ['Inter', 'sans-serif'],
              },
            },
          },
        };
        """
    )
    (root / "app").mkdir()
    (root / "app" / "globals.css").write_text(
        ":root {\n  --color-danger: #E11D48;\n  --font-mono: 'JetBrains Mono';\n}\n"
        "body { font-family: 'Source Sans 3', sans-serif; }\n"
    )
    (root / "public").mkdir()
    (root / "public" / "logo-light.svg").write_text("<svg/>")
    (root / "public" / "favicon.ico").write_bytes(b"\x00")
    (root / ".env").write_text("API_KEY=super-secret-value-12345\n")


class Extraction(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        make_project(self.root)
        self.data = extract_brand.extract(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_reads_name_and_tagline(self):
        self.assertEqual(self.data["brand_name"][0], "Acme Learning")
        self.assertEqual(self.data["product_name"][0], "acme-lms")
        self.assertEqual(self.data["tagline"][0], "Teach anything in ten minutes.")

    def test_reads_palette_from_tailwind_and_css(self):
        self.assertEqual(self.data["palette.Background"][0], "#0B0B0F")
        self.assertEqual(self.data["palette.Accent"][0], "#4F7CFF")
        self.assertEqual(self.data["palette.Positive"][0], "#12B981")
        self.assertEqual(self.data["palette.Negative"][0], "#E11D48")

    def test_reads_fonts(self):
        self.assertEqual(self.data["font.display"][0], "Space Grotesk")
        self.assertEqual(self.data["font.body"][0], "Inter")
        self.assertEqual(self.data["font.mono"][0], "JetBrains Mono")

    def test_finds_logos(self):
        self.assertIn("public/logo-light.svg", self.data["logos"][0])

    def test_every_value_carries_provenance(self):
        for key, value in self.data.items():
            self.assertIsInstance(value, tuple, key)
            self.assertEqual(len(value), 2, key)
            self.assertIn("extracted-from", value[1], f"{key} has no provenance")

    def test_never_reads_env(self):
        text = extract_brand.to_markdown(self.data, self.root)
        self.assertNotIn("super-secret-value-12345", text)

    def test_json_round_trips(self):
        self.assertIn("brand_name", json.dumps(self.data, default=str))


class Safety(unittest.TestCase):
    def test_is_secret_flags_env_and_keys(self):
        for name in (".env", ".env.local", "id_rsa", "cert.pem", "credentials.json"):
            self.assertTrue(
                extract_brand.is_secret(Path(name)), f"{name} must be treated as secret"
            )
        for name in ("package.json", "globals.css", "README.md", "logo.svg"):
            self.assertFalse(extract_brand.is_secret(Path(name)), name)

    def test_missing_directory_fails_loudly(self):
        with self.assertRaises(SystemExit):
            extract_brand.extract(Path("/nonexistent/path/for/sure"))

    def test_skips_dependency_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "node_modules" / "evil").mkdir(parents=True)
            (root / "node_modules" / "evil" / "theme.json").write_text(
                '{"color": "#FF0000"}'
            )
            (root / "package.json").write_text('{"name": "clean"}')
            data = extract_brand.extract(root)
            self.assertNotIn("palette.#FF0000", data)


if __name__ == "__main__":
    unittest.main()
