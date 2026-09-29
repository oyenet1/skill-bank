---
name: content-authoring
description: "Write or revise the written part of a course: maps, chapters, lessons, notes, projects, exercises, assignments, indexes, schedules, and text PDF sources. Use when the teacher wants text learning materials without media production."
---

# Course Text

Work on the exact written asset the teacher requests. Accept a standalone brief or an existing `course-plan.json`. For a mapped course, use stable section, chapter, lesson, concept, and project IDs and store the output under the matching ID. Register only files that exist in that node's `artifacts` map; preserve teacher edits and validate the map with `course-creator/scripts/validate_course.py` when the coordinating skill is available.

For a new course, map **sections → chapters → lessons → concepts** in prerequisite order before writing full lessons. A chapter ends with a small project; a section ends with a larger project, with at least three chapter projects before the first larger project. Start at the learner's actual level. Beginner programming may need computer hardware, software, operating systems, and files before code.

For a selected concept, teach with a relatable example or teacher-supplied story, then What, Why, Where, When, How, a visual explanation in words or a still diagram, a practical demonstration, and a learner check. Explain new terms before the learner must use them. Write only requested notes, exercises, assignments, project prompts, index, schedule, or PDF. Exercises are optional and have no fixed count. Keep answers separate from learner materials.

When an output derives from another registered file, record `artifactSources`, such as `"notesPdf": ["notes"]`. On a source edit, list affected outputs in `staleArtifacts` until refreshed. Text material must remain understandable without slides, audio, or video. Use an appropriate still image or icon when it helps; if `course-creator` is installed, inspect its bundled assets and copy selected files into the course before using them in notes or PDFs. Its written-course, teaching-content, teaching-assets, projects, and technical references provide richer guidance; this skill works from the teacher brief without them.
