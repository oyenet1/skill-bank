---
name: course-creator-content-authoring
description: Write one requested chapter, lesson, concept, notes file, PDF source, project brief, exercise, assignment, or other written course asset inside the course-creator bundle, using stable IDs and registering real artifacts.
---

# Content Authoring

Work on the exact written asset the requester asks for. Accept a brief or
existing files. Produce only what was requested — not an adjacent chapter, not
an exercise bank nobody asked for.

## When storytelling is selected

Follow [storytelling](references/storytelling.md) when the requester selects a storytelling treatment.
Resolve post / video / both before production. Story videos use Slidev unless
explicitly overridden, with relevant object visuals, clear flows and smooth
entrances/exits; programming explanations use Mermaid. Posts remain text-only.

## Clarify before production

Read [intake](references/intake.md) before starting. If missing or ambiguous inputs would change
the result, ask a concise batch of questions and wait for answers. Offer
recommended choices; apply them only when the requester selects them or
explicitly asks you to choose. Use details already supplied rather than asking
again. Continue directly when the brief is complete.

## 1. Intake

Read [intake](references/intake.md). Resolve tone and vocabulary from [brand](references/brand.md) when a
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





## Course integration

Read [teaching content](../../references/teaching-content.md), [teaching
assets](../../references/teaching-assets.md), [projects](../../references/projects.md) and the
[text production reference](../../references/text-course-production.md). Use stable
section, chapter, lesson, concept and project IDs and store output under the
matching ID. Register only files that exist in that node's `artifacts` map.

Validate the map with `python ../../scripts/validate_course.py <course-root>/course-plan.json --sync-toc`
after a structural change. For programming subjects also read the
[technical profile](../../references/technical-profile.md); read [tech
mapping](../../references/tech-mapping.md) only for the relevant stack. For a missing
visual, read the [course-creator-assets](../course-creator-assets/SKILL.md) subskill.
