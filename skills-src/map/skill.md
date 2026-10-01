---
standalone:
  name: curriculum-map
  description: >-
    Plan or revise a learning structure — sections, units, concepts, prerequisites
    and a simple-to-complex project ladder — from any brief or existing outline.
    Keeps stable IDs so items can be reordered without breaking links. Use for
    curriculum, workshop or learning-path planning.
bundle:
  name: course-creator-map
  description: >-
    Plan or revise a course hierarchy, prerequisite order, table of contents, and
    simple-to-complex project ladder inside the course-creator bundle.
---

# Curriculum Map

Use a plan file as the ordered source for sections, units, concepts, prerequisites
and projects, and keep a readable outline beside it.

## Social media output

Read {{ref:social-media}} before producing audience-facing text or video.
Resolve the publishing platform and audience, keep the hook and payoff clear,
and verify mobile readability, captions and the chosen channel's format.
Ask for missing material choices at intake. Aim for shareability without
claiming guaranteed viral performance; preserve the requested teaching depth.

## Clarify before production

Read {{ref:intake}} before starting. If missing or ambiguous inputs would change
the result, ask a concise batch of questions and wait for answers. Offer
recommended choices; apply them only when the requester selects them or
explicitly asks you to choose. Use details already supplied rather than asking
again. Continue directly when the brief is complete.

## 1. Intake

Read {{ref:intake}}. Ask only what changes the map: the subject, who it is for,
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

{{mode:bundle}}
## Course integration

Read the {{doc:course-blueprint.md|course blueprint}}. Use `course-plan.json` as
the ordered source and keep the human-readable table of contents in the course
`README.md`.

After a structural change, run:

```
python {{asset:scripts/validate_course.py}} <course-root>/course-plan.json --sync-toc
```

It replaces only its marked table-of-contents block. Register existing artifacts
and their real dependencies; mark affected derived files stale after source
changes. Keep unrelated teacher-written material intact.
{{/mode}}

{{mode:standalone}}
## Standalone output

Write the plan where the requester names it — `curriculum-plan.json` plus a
readable outline beside it. If a `course-plan.json` already exists and the
requester points at it, use the course layout instead: keep the human-readable
table of contents in the course `README.md`, and validate with
`course-creator/scripts/validate_course.py` when that bundle is installed.
{{/mode}}
