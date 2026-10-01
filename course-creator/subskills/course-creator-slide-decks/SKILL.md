---
name: course-creator-slide-decks
description: Build or revise one editable Slidev lesson deck, storyboard, or slide PDF inside the course-creator bundle, registering the deck and its exports under the lesson's artifacts.
---

# Slide Decks

## Automatic first-use setup

Before production, run the bundled launcher with `--yes`; it detects the host, prepares private runtimes, and installs the declared sibling dependency graph. Do not ask the requester to install packages manually.

- Linux/macOS: `sh tools/setup.sh --yes`
- Windows: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/setup.ps1 --yes`

Use `--check` for a read-only readiness check. If prerequisites are missing, rerun setup. Follow the returned `pythonExecutable` and runtime paths for later commands. Model-license acceptance, image rights and account credentials remain explicit inputs.

Accept a topic brief, a lesson, a concept, a story, or existing course files.
Produce only the requested deck, storyboard or slide PDF. A deck does not require
written notes or a video.

Before building, read [preflight](references/preflight.md) and run
`python3 tools/ensure_video_runtime.py slide-decks` from this skill directory.
Use the verified executable paths in its JSON result for Slidev and exports.

## Clarify before production

Read [intake](references/intake.md) before starting. If missing or ambiguous inputs would change
the result, ask a concise batch of questions and wait for answers. Offer
recommended choices; apply them only when the requester selects them or
explicitly asks you to choose. Use details already supplied rather than asking
again. Continue directly when the brief is complete.

## 1. Intake

Read [intake](references/intake.md). Resolve palette, type and imagery from [brand](references/brand.md).
Ask what changes the deliverable: topic, audience level, roughly how many slides,
what the audience must be able to do afterwards, and whether a PDF handout is
wanted. Batch the rest.

## 2. Structure

A relatable example first, then **What / Why / Where / When / How**, a visual
explanation, a demonstration, and a learner check. Each reveal explains one
causal step and leaves a readable final state. Record storyboard beats with a
stable ID, the concept ID, the slide, visible content, asset IDs, caption,
estimated duration and effect ID.

## 3. Visuals

Inspect supplied and project-local images first, then the asset bank. If it is not
there, **go online** for a reusable source and record its URL, licence and
retrieval date. Only when it cannot be found online, generate or draw it — prefer
an editable SVG diagram, and label generated art as generated. Draw from
[objects](references/objects.md) before hand-building a layout. Include useful local visuals in the
deck and copy selected files into the project folder so the deck and its export
stay portable. Record provenance and alt text, and verify unknown public reuse
terms before publication.

## 4. Diagrams

When the content is structure rather than narrative — architecture, request
paths, sequences, entities, state, schedule — draw it with a Mermaid block
instead of describing it. Slidev renders ` ```mermaid ` natively; style it from
the brand palette with `defineMermaidSetup` in `setup/mermaid.ts`
(`theme: 'base'` plus `themeVariables`). Pick the diagram kind from the table in
[objects](references/objects.md).

Show the whole diagram first, then `v-click` one node or edge at a time as the
narration reaches it, colouring the active element with the brand accent and
dimming the rest. Label edges that have names. Keep node labels to 2–4 words and
put detail beside the diagram. For architecture, draw the real components and
boundaries — never invent a component that is not in the system.

## 5. Animation

Use Slidev's real primitives — `v-click` (`.up`, `.fade-in`, `.fade.right.scale`),
`v-motion` for continuous movement, `v-mark` to annotate a phrase, and named
`transition` frontmatter — rather than hand-rolled keyframes. The full rack of
layouts, built-in components, code highlighting, diagrams, UnoCSS, global layers
and presenter features is in [slidev](references/slidev.md): use what exists before building a
component. Keep the meaning clear in a static PDF — an exported handout must
still work with every reveal already open.

## 6. Edit and verify through the MCP server

The Slidev MCP server is always enabled — see [slidev](references/slidev.md) and [preflight](references/preflight.md).
List the slides to confirm numbering, edit through `slidev-update-slide`,
`slidev-insert-slide`, `slidev-move-slide` and `slidev-remove-slide` rather than
rewriting the file, then `slidev-goto-slide` and inspect the rendered slide at
delivery size. A structured edit still needs a visual check.

Check current Slidev documentation for syntax and export commands. Export a PDF
only when requested, then inspect the pages afterwards.

## 7. Code on slides

When a deck contains code, it must be lint-clean and actually run — see
[code](references/code.md). Lint it before it goes into the deck. Use Shiki highlighting and
step highlighting: `{1|3|all}` magic-move to show a change between two states, or
`{monaco}` when the viewer should be able to edit it. Keep lines short enough to
read at the delivery size.





## Course integration

Use stable lesson and concept IDs, save the deck under
`lessons/{lesson-id}/slides/`, and register produced files in that lesson's
`artifacts` map. Inspect the [bundled assets](../../references/bundled-assets.md) and the
visual-sourcing section of [visual media](../../references/visual-media.md) first; for a
missing illustration read the [course-creator-assets](../course-creator-assets/SKILL.md) subskill.

Record actual dependencies in `artifactSources` such as
`"slidePdf": ["slides"]`, and mark downstream outputs stale after a source
change. The deck and storyboard may be passed to [course-creator-explainer-video](../course-creator-explainer-video/SKILL.md)
later, but neither is produced as a side effect.
