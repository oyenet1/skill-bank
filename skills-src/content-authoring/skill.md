---
standalone:
  name: content-authoring
  description: >-
    Write or revise any requested written material — lessons, notes, guides,
    chapters, project briefs, exercises, assignments, indexes, schedules, docs,
    or PDF sources. Works from any brief or existing files and keeps answer keys
    separate from the material people read. Use for written output without media
    production.
bundle:
  name: course-creator-content-authoring
  description: >-
    Write one requested chapter, lesson, concept, notes file, PDF source, project
    brief, exercise, assignment, or other written course asset inside the
    course-creator bundle, using stable IDs and registering real artifacts.
---

# Content Authoring

Work on the exact written asset the requester asks for. Accept a brief or
existing files. Produce only what was requested — not an adjacent chapter, not
an exercise bank nobody asked for.

## 1. Intake

Read {{ref:intake}}. Resolve tone and vocabulary from {{ref:brand}} when a
`brand.md` exists. Ask only what changes the deliverable: audience level, target
length, what to cover and what to leave out, and whether answers or keys are
needed. Batch the rest.

## 2. Structure before prose

For new material, map **sections → chapters → concepts** in prerequisite order
before writing full content. Each concept depends only on knowledge already
taught or introduced immediately before its use. Where the material teaches, a
chapter ends with a small practical project and a section ends with a larger one,
with at least three chapter projects before the first larger one.

Start at the reader's actual level. A true beginner may need hardware, files and
terminology before code; an experienced reader may begin later. For material that
is reference rather than instruction, structure by lookup need instead — group by
task, not by narrative.

## 3. Develop each unit

When the material teaches, use: relatable example or supplied story → **What** →
**Why** → **Where** → **When** → **How** → visual explanation → practical
demonstration → a short check. The *How* must show an actual action or process.

When the material documents or explains rather than teaches, lead with the task
or the answer, then the reasoning, then the edge cases. Explain a new term before
the reader must use it. Use an appropriate still image or icon where it helps.

Ground factual content in supplied material first, then authoritative sources.
Record source links where used. Never invent a source or page URL.

## 4. Keep it separable

Written material must stay understandable without slides, audio or video. Keep
answer keys and solutions separate from the material people read. When an output
derives from another file, record `artifactSources` such as
`"notesPdf": ["notes"]`, and list affected outputs in `staleArtifacts` until
refreshed. Preserve the requester's edits.

{{mode:bundle}}
## Course integration

Read {{doc:teaching-content.md|teaching content}}, {{doc:teaching-assets.md|teaching
assets}}, {{doc:projects.md|projects}} and the
{{doc:text-course-production.md|text production reference}}. Use stable
section, chapter, lesson, concept and project IDs and store output under the
matching ID. Register only files that exist in that node's `artifacts` map.

Validate the map with `python {{asset:scripts/validate_course.py}} <course-root>/course-plan.json --sync-toc`
after a structural change. For programming subjects also read the
{{doc:technical-profile.md|technical profile}}; read {{doc:tech-mapping.md|tech
mapping}} only for the relevant stack. For a missing
visual, read the {{sibling:assets}} subskill.
{{/mode}}

{{mode:standalone}}
## Standalone output

If a `course-plan.json` is present and the requester names a lesson, use stable
IDs, store output under the matching ID and register real artifacts; validate
with `course-creator/scripts/validate_course.py` when that bundle is installed.
Otherwise write to the directory the requester names.
{{/mode}}
