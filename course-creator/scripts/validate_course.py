#!/usr/bin/env python3
"""Validate a course-creator map and keep its README table of contents in sync."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ARTIFACT_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
TOC_START = "<!-- course-creator:toc:start -->"
TOC_END = "<!-- course-creator:toc:end -->"


def title(node: object) -> str:
    if isinstance(node, dict) and isinstance(node.get("title"), str):
        return node["title"].strip()
    return ""


def object_list(value: object, location: str, errors: list[str]) -> list[dict]:
    if not isinstance(value, list) or not value:
        errors.append(f"{location}: expected a non-empty list")
        return []
    result = []
    for index, item in enumerate(value, 1):
        if isinstance(item, dict):
            result.append(item)
        else:
            errors.append(f"{location}[{index}]: expected an object")
    return result


def validate_map(data: object, root: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["course-plan.json: expected an object"]
    if data.get("schemaVersion") != 1:
        errors.append("schemaVersion: expected 1")

    seen_ids: set[str] = set()
    available: set[str] = set()
    concept_ids: set[str] = set()
    artifact_catalog: dict[str, set[str]] = {}
    pending_sources: list[tuple[str, str, dict]] = []

    def check_identity(node: dict, location: str) -> str:
        node_id = node.get("id")
        if not isinstance(node_id, str) or not ID_RE.fullmatch(node_id):
            errors.append(f"{location}.id: expected a lowercase kebab-case ID")
            return ""
        if node_id in seen_ids:
            errors.append(f"{location}.id: duplicate ID {node_id!r}")
        seen_ids.add(node_id)
        if not title(node):
            errors.append(f"{location}.title: expected non-empty text")
        return node_id

    def check_text(node: dict, key: str, location: str) -> None:
        if not isinstance(node.get(key), str) or not node[key].strip():
            errors.append(f"{location}.{key}: expected non-empty text")

    def check_prerequisites(node: dict, location: str) -> None:
        values = node.get("prerequisites")
        if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
            errors.append(f"{location}.prerequisites: expected a list of IDs")
            return
        for prerequisite in values:
            if prerequisite not in available:
                errors.append(
                    f"{location}.prerequisites: {prerequisite!r} must appear earlier in the map"
                )

    def check_artifacts(node: dict, location: str) -> None:
        artifacts = node.get("artifacts", {})
        if not isinstance(artifacts, dict):
            errors.append(f"{location}.artifacts: expected a map of names to relative file paths")
            return
        node_id = node.get("id")
        if isinstance(node_id, str) and ID_RE.fullmatch(node_id):
            artifact_catalog[node_id] = set(artifacts)
        for name, relative in artifacts.items():
            if not isinstance(name, str) or not isinstance(relative, str) or not relative:
                errors.append(f"{location}.artifacts: expected non-empty string names and paths")
                continue
            if not ARTIFACT_NAME_RE.fullmatch(name):
                errors.append(f"{location}.artifacts.{name}: use letters, digits, underscores, or hyphens; start with a letter")
            path = Path(relative)
            if path.is_absolute() or ".." in path.parts:
                errors.append(f"{location}.artifacts.{name}: path must stay inside the course")
            elif not (root / path).resolve().is_relative_to(root.resolve()):
                errors.append(f"{location}.artifacts.{name}: path resolves outside the course")
            elif not (root / path).is_file():
                errors.append(f"{location}.artifacts.{name}: file does not exist: {relative}")
        sources = node.get("artifactSources", {})
        if not isinstance(sources, dict):
            errors.append(f"{location}.artifactSources: expected a map of artifact names to input names")
        else:
            for output, inputs in sources.items():
                if output not in artifacts:
                    errors.append(f"{location}.artifactSources: unknown output {output!r}")
                if not isinstance(inputs, list) or any(not isinstance(v, str) for v in inputs):
                    errors.append(f"{location}.artifactSources.{output}: expected a list of artifact references")
                    continue
            if isinstance(node_id, str) and ID_RE.fullmatch(node_id):
                pending_sources.append((node_id, location, sources))
        stale = node.get("staleArtifacts", [])
        if not isinstance(stale, list) or any(not isinstance(v, str) for v in stale):
            errors.append(f"{location}.staleArtifacts: expected a list of artifact names")
        else:
            for name in stale:
                if name not in artifacts:
                    errors.append(f"{location}.staleArtifacts: unknown artifact {name!r}")

    def check_project(node: object, location: str) -> None:
        if not isinstance(node, dict):
            errors.append(f"{location}: expected a project object")
            return
        check_identity(node, location)
        concepts = node.get("conceptIds")
        if not isinstance(concepts, list) or not concepts or any(
            not isinstance(value, str) for value in concepts
        ):
            errors.append(f"{location}.conceptIds: expected a non-empty list of concept IDs")
        else:
            for concept in concepts:
                if concept not in concept_ids:
                    errors.append(f"{location}.conceptIds: {concept!r} has not been taught yet")
        if node.get("status", "proposed") not in {"proposed", "selected", "developed"}:
            errors.append(f"{location}.status: expected proposed, selected, or developed")
        check_artifacts(node, location)

    check_identity(data, "course")
    check_text(data, "subject", "course")
    check_text(data, "goal", "course")
    if not isinstance(data.get("audience"), dict) or not data["audience"].get("level"):
        errors.append("course.audience.level: expected learner level")
    check_artifacts(data, "course")

    chapter_project_count = 0
    first_section_project_seen = False
    for s_index, section in enumerate(object_list(data.get("sections"), "sections", errors), 1):
        s_loc = f"sections[{s_index}]"
        check_identity(section, s_loc)
        check_text(section, "outcome", s_loc)
        for c_index, chapter in enumerate(
            object_list(section.get("chapters"), f"{s_loc}.chapters", errors), 1
        ):
            c_loc = f"{s_loc}.chapters[{c_index}]"
            chapter_id = check_identity(chapter, c_loc)
            check_text(chapter, "outcome", c_loc)
            check_prerequisites(chapter, c_loc)
            for l_index, lesson in enumerate(
                object_list(chapter.get("lessons"), f"{c_loc}.lessons", errors), 1
            ):
                l_loc = f"{c_loc}.lessons[{l_index}]"
                lesson_id = check_identity(lesson, l_loc)
                check_text(lesson, "outcome", l_loc)
                check_prerequisites(lesson, l_loc)
                for x_index, concept in enumerate(
                    object_list(lesson.get("concepts"), f"{l_loc}.concepts", errors), 1
                ):
                    x_loc = f"{l_loc}.concepts[{x_index}]"
                    concept_id = check_identity(concept, x_loc)
                    check_prerequisites(concept, x_loc)
                    check_artifacts(concept, x_loc)
                    if concept_id:
                        available.add(concept_id)
                        concept_ids.add(concept_id)
                check_artifacts(lesson, l_loc)
                if lesson_id:
                    available.add(lesson_id)
            check_project(chapter.get("project"), f"{c_loc}.project")
            chapter_project_count += 1
            check_artifacts(chapter, c_loc)
            if chapter_id:
                available.add(chapter_id)
        if not first_section_project_seen and chapter_project_count < 3:
            errors.append(f"{s_loc}.project: first section project needs three earlier chapter projects")
        check_project(section.get("project"), f"{s_loc}.project")
        first_section_project_seen = True
        check_artifacts(section, s_loc)

    graph: dict[str, list[str]] = {}
    for node_id, location, sources in pending_sources:
        for output, inputs in sources.items():
            if not isinstance(inputs, list) or any(not isinstance(v, str) for v in inputs):
                continue
            output_ref = f"{node_id}.{output}"
            for source in inputs:
                source_node, separator, source_name = source.partition(".")
                if not separator:
                    source_node, source_name = node_id, source
                if source_node not in artifact_catalog or source_name not in artifact_catalog[source_node]:
                    errors.append(f"{location}.artifactSources.{output}: unknown input {source!r}")
                    continue
                source_ref = f"{source_node}.{source_name}"
                if source_ref == output_ref:
                    errors.append(f"{location}.artifactSources.{output}: output cannot source itself")
                else:
                    graph.setdefault(output_ref, []).append(source_ref)

    visited: set[str] = set()
    visiting: set[str] = set()

    def check_cycle(artifact: str) -> None:
        if artifact in visiting:
            errors.append(f"artifactSources: dependency cycle includes {artifact!r}")
            return
        if artifact in visited:
            return
        visiting.add(artifact)
        for source in graph.get(artifact, []):
            check_cycle(source)
        visiting.remove(artifact)
        visited.add(artifact)

    for artifact in graph:
        check_cycle(artifact)
    return errors


def render_toc(data: dict) -> str:
    def linked(label: str, node: dict, kind: str) -> str:
        path = node.get("artifacts", {}).get(kind)
        return f"[{label}]({path})" if path else label

    lines = [TOC_START, f"# {data['title']}", "", "## Table of contents", ""]
    for section in data["sections"]:
        lines.append(f"- <a id=\"{section['id']}\"></a> **Section: {section['title']}** — {section['outcome']}")
        for chapter in section["chapters"]:
            chapter_label = linked(chapter["title"], chapter, "overview")
            lines.append(
                f"  - <a id=\"{chapter['id']}\"></a> **Chapter: {chapter_label}** — {chapter['outcome']}"
            )
            for lesson in chapter["lessons"]:
                lesson_label = linked(lesson["title"], lesson, "lesson")
                lines.append(f"    - <a id=\"{lesson['id']}\"></a> Lesson: {lesson_label}")
                for concept in lesson["concepts"]:
                    lines.append(
                        f"      - <a id=\"{concept['id']}\"></a> Concept: {concept['title']}"
                    )
            project = chapter["project"]
            project_label = linked(project["title"], project, "brief")
            lines.append(
                f"    - <a id=\"{project['id']}\"></a> Small project: {project_label} ({project.get('status', 'proposed')})"
            )
        project = section["project"]
        project_label = linked(project["title"], project, "brief")
        lines.append(
            f"  - <a id=\"{project['id']}\"></a> Section project: {project_label} ({project.get('status', 'proposed')})"
        )
    lines.extend(["", TOC_END])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("map", type=Path, help="path to course-plan.json")
    parser.add_argument(
        "--sync-toc", action="store_true", help="update only the generated README table-of-contents block"
    )
    args = parser.parse_args()
    try:
        data = json.loads(args.map.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read course map: {exc}", file=sys.stderr)
        return 1

    root = args.map.resolve().parent
    errors = validate_map(data, root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    readme_path = root / "README.md"
    toc = render_toc(data)
    existing = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    if existing.count(TOC_START) != existing.count(TOC_END) or existing.count(TOC_START) > 1:
        print("ERROR: README.md has unmatched or duplicate table-of-contents markers", file=sys.stderr)
        return 1
    if args.sync_toc:
        if TOC_START in existing and TOC_END in existing:
            before = existing.split(TOC_START, 1)[0]
            after = existing.split(TOC_END, 1)[1]
            updated = before + toc + after
        else:
            updated = existing.rstrip() + ("\n\n" if existing.strip() else "") + toc + "\n"
        if updated != existing:
            readme_path.write_text(updated, encoding="utf-8")
        print(f"Validated course and synchronized {readme_path}")
    elif toc not in existing:
        print("ERROR: README.md table of contents is missing or stale; run with --sync-toc", file=sys.stderr)
        return 1
    else:
        print("Course map and table of contents are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
