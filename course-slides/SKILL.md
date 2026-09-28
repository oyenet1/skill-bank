---
name: course-slides
description: Create or revise an editable Slidev teaching deck, storyboard, or slide handout PDF for one lesson or concept. Use for slide output whether or not a full course or video exists.
---

# Course Slides

Accept a lesson, concept brief, teacher story, or existing course map. Produce only the requested Slidev deck, storyboard, or slide PDF. A deck does not require written notes or a video. When a course exists, use stable lesson and concept IDs, save the deck under `lessons/{lesson-id}/slides/`, and register produced files in that lesson's `artifacts` map.

Show a relatable example, then What, Why, Where, When, How, a visual explanation, a demonstration, and a learner check. Make each reveal explain one causal step and leave a readable final state. Record storyboard beats with stable ID, concept ID, slide, visible content, asset IDs, caption, estimated duration, and effect ID. Keep the meaning clear in a static PDF.

Inspect supplied/course images first. When the `course-creator` bundle is present, search its `assets/` folders for a matching image or icon and inspect it. Include useful local visuals in the deck, copying selected files into the course folder so the deck and export remain portable. Then consider reusable web sources with usage terms and credit, generated art, or an editable SVG/diagram if needed. Record provenance and alt text; verify unknown public reuse terms before publication. Use the teacher's visual identity if supplied. Check current Slidev documentation for syntax and export commands. Export a PDF only when requested, and inspect the pages afterward.

Record actual dependencies in `artifactSources`, such as `"slidePdf": ["slides"]`; mark downstream outputs stale after source changes. The deck and storyboard may be passed to a video workflow later, but neither is produced as a side effect.
