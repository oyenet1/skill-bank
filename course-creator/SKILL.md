---
name: course-creator
description: Plan, teach, revise, and publish parts of a dependency-ordered course. Use for course maps, chapters, lessons, concept explanations, projects, instructor assets, Slidev lessons, and educational video handoffs. Works for any subject, with a programming profile for technical courses.
metadata:
  version: 2.0.0
  author: Bowofade Oyerinde (@oyenet1) - Bonifade Technologies
---

# Course Creator

Help a teacher build one useful part of a course at a time. A course is **sections → chapters → lessons → concepts**. Each later concept depends only on knowledge already taught or introduced immediately before its use. Preserve the teacher's choices about audience, subject, delivery, materials, and which asset to make next. This skill coordinates multiple outputs; the sibling `course-text`, `course-slides`, `course-video`, `course-tts`, and `course-marketing` skills are independent entry points when installed.

## Choose one action

Identify the requested action and target before generating anything. Ask only for missing information that changes that action; use existing course files when present. Do not generate unrelated chapters, exercises, PDFs, or videos as a side effect.

| Request | Result | Read |
|---|---|---|
| Plan a course | `course-plan.json` plus a readable table of contents with all sections, chapters, lessons, concepts, prerequisites, and proposed projects | [course blueprint](references/course-blueprint.md) |
| Reorder or revise the map | Update targeted nodes, numbering, prerequisites, links, and affected artifact references | [course blueprint](references/course-blueprint.md) |
| Develop a chapter, lesson, or concept | Write only the selected teaching content and its directly affected navigation | [teaching content](references/teaching-content.md), [written course production](references/text-course-production.md) |
| Create notes, a page, exercises, assignment, quiz, exam, rubric, index, schedule, or handout | Write only the requested teaching asset | [teaching assets](references/teaching-assets.md), [written course production](references/text-course-production.md) |
| Select or develop a project | Develop one teacher-selected project and its needed concept lessons | [projects](references/projects.md) |
| Source or create a visual | Resolve one teaching visual and record its provenance and accessible description | [visual and media workflow](references/visual-media.md) |
| Create a Slidev deck or slide PDF | Create the selected lesson deck or export it | [visual and media workflow](references/visual-media.md) |
| Generate speech from text | Produce only the requested script and Kokoro WAV narration | [narration](references/narration.md) |
| Create a lesson video or CapCut handoff | Produce the selected video artifacts and editing directions | [visual and media workflow](references/visual-media.md) |
| Sell a course or skill | Write only the requested hook, listing, page, post, email, or promotional script | [marketing copy](references/marketing-copy.md) |
| Launch a product with a Remotion ad or screenshot demo | Build a source-grounded product video from real screens and product information | [product launch handoff](references/product-launch.md), [marketing copy](references/marketing-copy.md) |

If a request names several outputs, perform only those selected actions in dependency order and reuse their shared IDs, text, and assets. Each action must also work alone from a suitable supplied brief or existing artifact: a narration script need not wait for slides, and slides need not wait for a video. Register actual outputs in the map; mark affected downstream outputs as needing refresh after a source change unless the teacher requested regeneration.

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
