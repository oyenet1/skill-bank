---
name: course-creator
description: Plan and produce parts of a course through bundled subskills for curriculum maps, lessons, assets, Slidev, Remotion, Kokoro narration, marketing, and screenshot-based product launch ads. Use for teaching or selling a course, with a programming profile for technical subjects.
metadata:
  version: 2.1.0
  author: Bowofade Oyerinde (@oyenet1) - Bonifade Technologies
---

# Course Creator

Help a teacher build one useful part of a course at a time. A course is **sections → chapters → lessons → concepts**. Each later concept depends only on knowledge already taught or introduced immediately before its use. Preserve the teacher's choices about audience, subject, delivery, materials, and which asset to make next. This parent skill contains the focused subskills below; read the relevant subskill for each requested output. Top-level `content-authoring`, `slide-decks`, `explainer-video`, `voice-narration`, `sales-copy`, and `product-launch-video` remain independent entry points when installed separately.

## Choose one action

Identify the requested action and target before generating anything. Ask only for missing information that changes that action; use existing course files when present. Do not generate unrelated chapters, exercises, PDFs, or videos as a side effect.

| Request | Result | Subskill to read |
|---|---|---|
| Plan or reorder a course | `course-plan.json` plus a readable table of contents, prerequisites, and proposed projects | [course map](subskills/course-creator-map/SKILL.md) |
| Develop a chapter, lesson, concept, project, notes, exercises, assignment, index, schedule, or text PDF | Write only the selected teaching content or asset | [content authoring](subskills/course-creator-content-authoring/SKILL.md) |
| Source or create a visual | Resolve a relevant teaching image or icon and record provenance and alt text | [course assets](subskills/course-creator-assets/SKILL.md) |
| Create a Slidev deck or slide PDF | Create the selected lesson deck or export it | [slide decks](subskills/course-creator-slide-decks/SKILL.md) |
| Generate speech from text | Produce only the requested script and Kokoro WAV narration | [voice narration](subskills/course-creator-voice-narration/SKILL.md) |
| Create an educational video or CapCut handoff | Produce the selected lesson video artifacts and editing directions | [explainer video](subskills/course-creator-explainer-video/SKILL.md) |
| Sell a course or skill | Write only the requested hook, listing, page, post, email, or promotional script | [sales copy](subskills/course-creator-sales-copy/SKILL.md) |
| Launch a product with a Remotion ad or screenshot demo | Build a source-grounded product video from real screens and product information | [product launch](subskills/course-creator-product-launch-video/SKILL.md) |

If a request names several outputs, read only the relevant subskills and perform those actions in dependency order using shared IDs, text, and assets. Each subskill also works alone from a suitable supplied brief or existing artifact: a narration script need not wait for slides, and slides need not wait for a video. Register actual outputs in the map; mark affected downstream outputs as needing refresh after a source change unless the teacher requested regeneration. Nested subskills are instructions carried inside this parent package and are selected through this table; the separate top-level skills support direct installation and invocation.

For programming courses, also read [technical profile](references/technical-profile.md). Read [tech mapping](references/tech-mapping.md) only for the relevant track or stack. The [technical terms](references/technical-terms.md) and preserved [roadmap notes](references/pdf-derived-roadmap-notes.md) are optional text references, not checklists to teach in full. For nontechnical subjects, use appropriate authoritative sources rather than technology roadmaps.

## Shared course contract

- Start new courses with the full **map**, not full lessons. Include all sections, chapter titles, lesson titles, concept titles, prerequisites, outcomes, and project placements. The teacher may reorder the table of contents later. Write detailed content only for the chosen target.
- Store the hierarchy and stable IDs in `course-plan.json`; keep the human-readable table of contents in the course `README.md`. When a node moves, update its order and links while keeping its ID. Run `python <skill-root>/scripts/validate_course.py <course-root>/course-plan.json --sync-toc` after a map change; it replaces only its marked table-of-contents block. Do not overwrite unrelated teacher edits.
- Start at the learner's actual entry level. An absolute beginner programming course first teaches computer basics such as hardware, software, operating systems, files, and extensions. An experienced learner may begin later.
- Give every chapter a small tangible project. Place a larger project at the end of each section, with at least three chapter projects before the first larger project. Projects increase in complexity. Propose the ladder in the map, then develop only the project the teacher selects. If a project needs a new concept, teach that concept before its first practical step.
- Every substantial concept follows **relatable example or story → What → Why → Where → When → How → visual explanation → practical demonstration → learner check**. The *How* must show an action or process. Start with language a child could understand, then add depth appropriate to the actual audience. Accept a teacher-supplied story; otherwise create a consistent course story.
- Exercises are optional for each lesson. Offer a suitable number when they help, including none. Assignments and other assets are separate actions; do not impose fixed counts.
- Ground factual content in supplied materials first, then appropriate authoritative sources. Record source links where used. Do not invent source URLs or online page URLs.

## Video and media contract

- Each lesson can have its own editable Slidev deck, produced when requested. Written lesson, notes, slide handout PDF, online notes page, optional Kokoro narration, Remotion video, and CapCut handoff are distinct outputs that may also be combined. For visual outputs, inspect the [bundled images and icons](references/bundled-assets.md), use suitable ones in the teaching material, and keep selected copies inside the course.
- For every video creation request, load the relevant installed video skills before production. In environments with a video entrypoint skill, read it first; for Remotion output use its creation, markup, audio, caption, and rendering guidance as needed. The teacher's explicit renderer choice controls the deliverable. Check current official documentation for library-specific commands and APIs.
- Write a course-level visual identity and a concrete `style.md` for **each** video before authoring scenes. Record palette, fonts, tone, frame dimensions and layout, presenter placement, visual examples, and an effects bible: each effect's purpose, entry, exit, timing, and use conditions. Keep the Slidev deck, Remotion scenes, and CapCut directions aligned with that style.
- When teacher audio or footage is supplied, use it to set scene and caption timing. Text alone yields timed captions and a narration script; generate synthetic voice only on request. Provide editable Remotion source and render MP4 when rendering is available. A CapCut Desktop request also gets separate media and a timecoded editing guide.

## Finish the requested action

Before responding, check the requested output exists and links resolve. For map changes, run the course validator. For teaching assets, check alignment with outcomes, concept order, audience level, and supplied sources. For slides and video, inspect the actual visual states and timing, and check that every referenced asset exists. Report completed paths and any unavailable rendering or publishing step accurately.
