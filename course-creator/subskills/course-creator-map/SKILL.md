---
name: course-creator-map
description: Plan or revise a course hierarchy, prerequisite order, table of contents, and simple-to-complex project ladder inside the course-creator bundle.
---

# Course Map

Read the [course blueprint](../../references/course-blueprint.md). Use `course-plan.json`
as the ordered source for sections, chapters, lessons, concepts, prerequisites
and projects.

## 1. Intake

Read [intake](references/intake.md). Ask only what changes the map: subject, who the learner
actually is, their starting level, what they must be able to do at the end, and
roughly how long the course is meant to run. Batch the rest. Do not write full
lessons when a map was requested.

## 2. Structure

Start at the learner's real level. For absolute-beginner programming, include
computer and file foundations before code. Propose a small project per chapter
and a larger project per section, with at least three small projects before the
first section project. Projects increase in complexity. If a project needs a new
concept, teach that concept before its first practical step.

Create the complete outline before expanding lessons. Each later concept depends
only on knowledge already taught or introduced immediately before its use.

## 3. Keep it stable

Preserve stable IDs when reordering. Update only affected links and outputs,
then run:

```
python ../../scripts/validate_course.py <course-root>/course-plan.json --sync-toc
```

Register existing artifacts and their real dependencies; mark affected derived
files stale after source changes. Keep unrelated teacher-written material intact.

## 4. Report

Confirm the hierarchy, the prerequisite order, the project ladder and the
synchronized table of contents. Say what was changed and what was deliberately
left alone.
