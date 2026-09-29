---
name: course-creator-map
description: Plan or revise a course hierarchy, prerequisite order, table of contents, and simple-to-complex project ladder inside the course-creator bundle.
---

# Curriculum Map

Use a plan file as the ordered source for sections, units, concepts, prerequisites
and projects, and keep a readable outline beside it.

## 1. Intake

Read [intake](references/intake.md). Ask only what changes the map: the subject, who it is for,
their real starting level, what they must be able to do at the end, and roughly
how long it should run. Batch the rest. Do not write full lessons when a map was
requested.

## 2. Structure

Start at the real starting level. For absolute-beginner programming, include
computer and file foundations before code. Propose a small project per unit and a
larger project per section, with at least three small projects before the first
section project. Projects increase in complexity. If a project needs a new
concept, teach that concept before its first practical step.

Create the complete outline before expanding detail. Each later concept depends
only on knowledge already introduced immediately before its use.

## 3. Keep it stable

Preserve stable IDs when reordering. Update only the links and outputs that
actually move, and keep unrelated material intact.

## 4. Report

Confirm the hierarchy, the prerequisite order, the project ladder and the
synchronized outline. Say what changed and what was deliberately left alone.





## Course integration

Read the [course blueprint](../../references/course-blueprint.md). Use `course-plan.json` as
the ordered source and keep the human-readable table of contents in the course
`README.md`.

After a structural change, run:

```
python ../../scripts/validate_course.py <course-root>/course-plan.json --sync-toc
```

It replaces only its marked table-of-contents block. Register existing artifacts
and their real dependencies; mark affected derived files stale after source
changes. Keep unrelated teacher-written material intact.
