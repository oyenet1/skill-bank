<!--
  ──────────────────────────────────────────────────────────────────
  🏢 Company Name: Bonifade Technologies
  👨‍💻 Developer: Bowofade Oyerinde
  🐙 GitHub: oyenet1
  📅 Created Date: 2026-04-05
  🔄 Updated Date: 2026-04-05
  ──────────────────────────────────────────────────────────────────
-->

# Agent Skills

A collection of reusable AI agent skills by [Bowofade Oyerinde](https://github.com/oyenet1) / **Bonifade Technologies**.

## Available Skills

### [course-creator](./course-creator/)

Plans and builds instructor-led courses one action at a time, for technology or other subjects. A course map contains sections, chapters, lessons, concepts, prerequisites, and a simple-to-complex project ladder. Teachers can reorder it without losing stable lesson IDs.

Independent actions include lesson writing; notes as PDF or an online page; optional exercises; publishable assignments, quizzes, and rubrics; lesson-by-lesson Slidev decks; optional local Kokoro TTS narration; Remotion videos using supplied text, audio, or teacher footage; and a timecoded CapCut Desktop handoff. Text, slides, TTS, and video can be produced separately or combined. Visual outputs can use the 580 bundled SVG images and icons. Videos use a shared course style and a per-video `style.md`.

For separate invocation, install [course-text](./course-text/SKILL.md), [course-slides](./course-slides/SKILL.md), [course-video](./course-video/SKILL.md), [course-tts](./course-tts/SKILL.md), or [course-marketing](./course-marketing/SKILL.md). Each accepts a standalone brief or existing course files. `course-creator` coordinates selected outputs and their dependencies. The marketing skill draws from the LodgeStatus campaign notes to write credible hooks and sales copy for skills and courses.

The separate [product-launch-remotion](./product-launch-remotion/SKILL.md) skill turns supplied screenshots and product information into a motion ad or screenshot-based demo. It reads the available product source, uses genuine screens as evidence, writes a per-video `style.md`, and delivers editable Remotion source plus an MP4 when rendering is available. It can promote a course or another product.

The skill teaches each concept through a relatable example, **What, Why, Where, When, and How**, a visual explanation, and a practical demonstration. Absolute beginner programming courses begin with computer basics. Each chapter has a small project; a larger section project follows at least three small projects.

The canonical course map is `course-plan.json`. The bundled validator checks prerequisite order, project placement, artifact paths, and table-of-contents synchronization:

```bash
python course-creator/scripts/validate_course.py path/to/course-plan.json --sync-toc
```

See [the skill](./course-creator/SKILL.md) and its linked references for each action's output contract. The original written-course guidance is retained in the [text production reference](./course-creator/references/text-course-production.md), [technical depth reference](./course-creator/references/technical-depth.md), [term bank](./course-creator/references/technical-terms.md), and [roadmap notes](./course-creator/references/pdf-derived-roadmap-notes.md).

Example prompts:

```text
Map a beginner programming course from computer basics through a first web app. List every section, chapter, lesson, concept, and proposed project; do not write lessons yet.
Write the lesson on file extensions from my course map, then create its Slidev deck.
Make a Remotion lesson video from this deck and my recorded narration; include a CapCut Desktop editing pack.
Create a Remotion launch ad from these product screenshots and the product website; show only real UI states.
```

**Install:**
```bash
npx skills add oyenet1/agent-skills@course-creator
```

---

### 🔬 [spec-driven-development](./spec-driven-development/)

**Specification-Driven Development (SDD)** — transforms vague ideas into structured, implementation-ready specifications.

Takes any rough requirement and produces:
- `requirements.md` — User stories + testable acceptance criteria (WHEN/SHALL/IF)
- `design.md` — Architecture, components, data model, API contracts
- `tasks.md` — Ordered, dependency-aware implementation checklist

**Install:**
```bash
npx skills add oyenet1/agent-skills@spec-driven-development
```

**Triggers on:** "spec this", "SDD", "plan this feature", "break this down", "generate requirements", "write a spec", and more.

---

## Installing Skills

```bash
# Install a specific skill globally
npx skills add oyenet1/agent-skills@course-creator -g

# Install another specific skill globally
npx skills add oyenet1/agent-skills@spec-driven-development -g

# Install one course output skill independently
npx skills add oyenet1/agent-skills@course-tts -g

# Install screenshot-driven Remotion product ads independently
npx skills add oyenet1/agent-skills@product-launch-remotion -g

# Install all skills from this repo
npx skills add oyenet1/agent-skills --all
```

## License

MIT — see [LICENSE](./LICENSE).
