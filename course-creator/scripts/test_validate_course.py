"""Behavior checks for the course map validator and generated table of contents."""

from __future__ import annotations

import copy
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from validate_course import validate_map


SKILL_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = SKILL_ROOT / "scripts" / "validate_course.py"


def sample_map() -> dict:
    reference = (SKILL_ROOT / "references" / "course-blueprint.md").read_text(
        encoding="utf-8"
    )
    match = re.search(r"```json\n(.*?)\n```", reference, re.S)
    assert match is not None
    return json.loads(match.group(1))


class CourseValidatorTests(unittest.TestCase):
    def test_reference_example_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(validate_map(sample_map(), Path(temporary)), [])

    def test_forward_prerequisite_and_early_capstone_are_rejected(self) -> None:
        data = sample_map()
        data["sections"][0]["chapters"][0]["lessons"][0]["concepts"][0][
            "prerequisites"
        ] = ["file-extension"]
        data["sections"][0]["chapters"] = data["sections"][0]["chapters"][:2]
        with tempfile.TemporaryDirectory() as temporary:
            errors = validate_map(data, Path(temporary))
        self.assertTrue(any("must appear earlier" in error for error in errors))
        self.assertTrue(any("three earlier chapter projects" in error for error in errors))

    def test_declared_artifact_must_exist(self) -> None:
        data = sample_map()
        data["sections"][0]["chapters"][0]["lessons"][0]["artifacts"] = {
            "lesson": "lessons/hardware-and-software/lesson.md"
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertTrue(any("file does not exist" in e for e in validate_map(data, root)))
            path = root / "lessons/hardware-and-software/lesson.md"
            path.parent.mkdir(parents=True)
            path.write_text("# Hardware and Software\n", encoding="utf-8")
            self.assertEqual(validate_map(data, root), [])

    def test_composed_artifacts_track_sources_and_staleness(self) -> None:
        data = sample_map()
        lesson = data["sections"][0]["chapters"][0]["lessons"][0]
        lesson["artifacts"] = {
            "lesson": "lessons/hardware-and-software/lesson.md",
            "slides": "lessons/hardware-and-software/slides/slides.md",
            "narrationText": "lessons/hardware-and-software/audio/script.txt",
            "narrationAudio": "lessons/hardware-and-software/audio/voice.wav",
            "video": "lessons/hardware-and-software/video/lesson.mp4",
        }
        lesson["artifactSources"] = {
            "slides": ["lesson"],
            "narrationAudio": ["narrationText"],
            "video": ["slides", "narrationAudio"],
        }
        lesson["staleArtifacts"] = ["video"]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in lesson["artifacts"].values():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            self.assertEqual(validate_map(data, root), [])
            lesson["artifactSources"]["video"].append("missingSource")
            lesson["staleArtifacts"].append("missingOutput")
            errors = validate_map(data, root)
            self.assertTrue(any("unknown input 'missingSource'" in e for e in errors))
            self.assertTrue(any("unknown artifact 'missingOutput'" in e for e in errors))

    def test_course_and_concept_artifacts_can_depend_across_nodes(self) -> None:
        data = sample_map()
        concept = data["sections"][0]["chapters"][0]["lessons"][0]["concepts"][0]
        concept["artifacts"] = {"diagram": "assets/computer.svg"}
        data["artifacts"] = {"promo": "marketing/promo.md"}
        data["artifactSources"] = {"promo": ["computer.diagram"]}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for relative in ["assets/computer.svg", "marketing/promo.md"]:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            self.assertEqual(validate_map(data, root), [])
            data["artifactSources"]["promo"] = ["computer.missing"]
            self.assertTrue(any("unknown input 'computer.missing'" in e for e in validate_map(data, root)))

    def test_artifact_dependency_cycle_is_rejected(self) -> None:
        data = sample_map()
        lesson = data["sections"][0]["chapters"][0]["lessons"][0]
        lesson["artifacts"] = {"notes": "notes.md", "slides": "slides.md"}
        lesson["artifactSources"] = {"notes": ["slides"], "slides": ["notes"]}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "notes.md").touch()
            (root / "slides.md").touch()
            self.assertTrue(any("dependency cycle" in e for e in validate_map(data, root)))

    def test_artifact_name_cannot_ambiguously_contain_a_dot(self) -> None:
        data = sample_map()
        data["artifacts"] = {"promo.script": "marketing/script.md"}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "marketing").mkdir()
            (root / "marketing/script.md").touch()
            self.assertTrue(any("use letters, digits" in e for e in validate_map(data, root)))

    def test_sync_preserves_teacher_text_and_rejects_stale_toc(self) -> None:
        data = sample_map()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / "course-plan.json"
            manifest.write_text(json.dumps(data), encoding="utf-8")
            readme = root / "README.md"
            readme.write_text("Teacher introduction.\n", encoding="utf-8")

            def run(*flags: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    ["python", str(VALIDATOR), str(manifest), *flags],
                    capture_output=True,
                    text=True,
                    check=False,
                )

            self.assertEqual(run("--sync-toc").returncode, 0)
            self.assertEqual(run().returncode, 0)
            self.assertTrue(readme.read_text().startswith("Teacher introduction.\n"))
            data = copy.deepcopy(data)
            data["sections"][0]["chapters"][0]["title"] = "Computer Components"
            manifest.write_text(json.dumps(data), encoding="utf-8")
            self.assertNotEqual(run().returncode, 0)
            self.assertEqual(run("--sync-toc").returncode, 0)
            self.assertIn("Computer Components", readme.read_text())
            self.assertTrue(readme.read_text().startswith("Teacher introduction.\n"))

    def test_sync_rejects_broken_readme_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / "course-plan.json"
            manifest.write_text(json.dumps(sample_map()), encoding="utf-8")
            readme = root / "README.md"
            readme.write_text("Teacher notes.\n<!-- course-creator:toc:start -->\n", encoding="utf-8")
            result = subprocess.run(
                ["python", str(VALIDATOR), str(manifest), "--sync-toc"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(readme.read_text(), "Teacher notes.\n<!-- course-creator:toc:start -->\n")


if __name__ == "__main__":
    unittest.main()
