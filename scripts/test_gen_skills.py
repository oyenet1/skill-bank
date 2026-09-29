"""Behavior checks for the skill target generator."""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GEN = REPO / "scripts" / "gen_skills.py"
SRC = REPO / "skills-src"

sys.path.insert(0, str(REPO / "scripts"))
import gen_skills  # noqa: E402

LINK = re.compile(r"(?<!\!)\[([^\]]*)\]\(([^)#\s]+)\)")
TOKEN = re.compile(r"\{\{\w+:")


def generated() -> dict[Path, str]:
    return gen_skills.build()


def readable_files() -> list[Path]:
    out = []
    for p in REPO.rglob("*.md"):
        s = str(p)
        if any(x in s for x in ("skills-src", ".git", ".venv", "tools/", "node_modules")):
            continue
        out.append(p)
    return out


class NoTokensLeft(unittest.TestCase):
    def test_tokens_are_resolved(self):
        for path, content in generated().items():
            self.assertIsNone(TOKEN.search(content), f"unresolved token in {path}")


class LinksResolve(unittest.TestCase):
    def test_every_markdown_link_resolves(self):
        broken = []
        for f in readable_files():
            for m in LINK.finditer(f.read_text()):
                target = m.group(2)
                if target.startswith(("http", "mailto")):
                    continue
                if not (f.parent / target).resolve().exists():
                    broken.append(f"{f.relative_to(REPO)} -> {target}")
        self.assertEqual(broken, [], "broken links:\n" + "\n".join(broken))


class Frontmatter(unittest.TestCase):
    def test_standalone_and_bundle_differ(self):
        for cap, spec in gen_skills.load_manifest()["capabilities"].items():
            fm, _ = gen_skills.parse_skill(SRC / cap / "skill.md")
            if spec.get("standalone") and spec.get("bundle"):
                self.assertEqual(fm["standalone"]["name"], spec["standalone"])
                self.assertEqual(fm["bundle"]["name"], spec["bundle"])
                self.assertNotEqual(
                    fm["standalone"]["description"],
                    fm["bundle"]["description"],
                    f"{cap}: descriptions must differ per target",
                )
            if spec.get("bundle") and not spec.get("standalone"):
                self.assertEqual(fm["bundle"]["name"], spec["bundle"])
                self.assertNotIn("standalone", fm, f"{cap} is bundle-only")

    def test_bundle_names_are_namespaced(self):
        for cap, spec in gen_skills.load_manifest()["capabilities"].items():
            self.assertTrue(
                spec["bundle"].startswith("course-creator-"),
                f"{cap}: bundle name must be namespaced",
            )


class CraftFirst(unittest.TestCase):
    """A standalone skill must not be framed as course-only.

    Deliverable nouns ("lessons", "chapters") are fine in a list of what the
    skill produces; role and structure nouns are not, because they imply the
    course context is required.
    """

    BANNED = ("teacher", "learner", "course-plan")

    def test_description_avoids_course_framing(self):
        for cap, spec in gen_skills.load_manifest()["capabilities"].items():
            if not spec.get("standalone"):
                continue
            desc = gen_skills.parse_skill(SRC / cap / "skill.md")[0]["standalone"]["description"]
            lowered = desc.lower()
            for word in self.BANNED:
                self.assertNotIn(word, lowered, f"{cap}: standalone description uses {word!r}")

    def test_description_signals_generality(self):
        for cap, spec in gen_skills.load_manifest()["capabilities"].items():
            if not spec.get("standalone"):
                continue
            desc = gen_skills.parse_skill(SRC / cap / "skill.md")[0]["standalone"]["description"]
            lowered = desc.lower()
            self.assertTrue(
                "any " in lowered or " or " in lowered,
                f"{cap}: standalone description does not signal cross-domain use",
            )


class IntakeCoverage(unittest.TestCase):
    def test_video_skills_ship_the_intake_modules(self):
        man = gen_skills.load_manifest()
        for cap in ("explainer-video", "product-launch-video"):
            mods = set(man["capabilities"][cap]["modules"])
            self.assertLessEqual(
                {
                    "intake",
                    "brand",
                    "video",
                    "voice",
                    "preflight",
                    "objects",
                    "slidev",
                    "code",
                    "prompts",
                },
                mods,
                f"{cap} is missing an intake module",
            )

    def test_slidev_skills_ship_the_slidev_rack(self):
        man = gen_skills.load_manifest()
        for cap in ("slide-decks", "explainer-video"):
            self.assertIn("slidev", man["capabilities"][cap]["modules"], cap)

    def test_prompt_samples_cover_every_category(self):
        prompts = SRC / "_shared" / "prompts"
        for cat in (
            "motion-graphic",
            "explainer-lesson",
            "screencast-demo",
            "footage-overlay",
            "launch-ad",
            "slideshow-montage",
        ):
            files = list((prompts / cat).glob("*.md"))
            self.assertTrue(files, f"no prompt samples for {cat}")

    def test_motion_graphic_is_the_largest_set(self):
        counts = {
            d.name: len(list(d.glob("*.md")))
            for d in (SRC / "_shared" / "prompts").iterdir()
            if d.is_dir()
        }
        self.assertGreaterEqual(
            counts["motion-graphic"],
            max(counts.values()),
            "motion-graphic is the default category and needs the most patterns",
        )


class CheckMode(unittest.TestCase):
    def test_check_passes_when_output_is_current(self):
        self.assertEqual(subprocess.run([sys.executable, GEN, "--check"]).returncode, 0)


if __name__ == "__main__":
    unittest.main()
