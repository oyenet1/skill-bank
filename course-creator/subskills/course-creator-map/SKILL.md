---
name: course-creator-map
description: Plan or revise a course hierarchy, prerequisite order, table of contents, and simple-to-complex project ladder inside the course-creator bundle.
---

# Course Map

Read the [course blueprint](../../references/course-blueprint.md). Use `course-plan.json` as the ordered source for sections, chapters, lessons, concepts, prerequisites, and projects. Start at the learner's actual level; for absolute beginner programming, include computer and file foundations before code. Propose a small project per chapter and a larger project per section, with at least three small projects before the first section project.

Create the complete outline before expanding lessons. Preserve stable IDs when reordering. Update only affected links and outputs, then run `python <course-creator-root>/scripts/validate_course.py <course-root>/course-plan.json --sync-toc`. Register existing artifacts and their real dependencies; mark affected derived files stale after source changes. Keep unrelated teacher-written material intact.
