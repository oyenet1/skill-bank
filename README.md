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

Installing `course-creator` includes its [eight focused subskills](./course-creator/SKILL.md): course mapping, content authoring, assets, Slidev decks, Remotion lesson video, Kokoro voice narration, sales copy, and Remotion product launch. The parent chooses only the subskills needed for the teacher's request. They can work alone or share the same course map and assets.

Independent actions include lesson writing; notes as PDF or an online page; optional exercises; publishable assignments, quizzes, and rubrics; lesson-by-lesson Slidev decks; optional local Kokoro voice narration; Remotion videos using supplied text, audio, or teacher footage; and a timecoded CapCut Desktop handoff. Written material, decks, narration, and video can be produced separately or combined. Visual outputs can use the 580 bundled SVG images and icons. Videos use a shared course style and a per-video `style.md`.

For separate installation or invocation outside the parent, use [curriculum-map](./curriculum-map/SKILL.md), [content-authoring](./content-authoring/SKILL.md), [visual-assets](./visual-assets/SKILL.md), [slide-decks](./slide-decks/SKILL.md), [explainer-video](./explainer-video/SKILL.md), [voice-narration](./voice-narration/SKILL.md), [sales-copy](./sales-copy/SKILL.md), or [product-launch-video](./product-launch-video/SKILL.md). Each accepts a standalone brief or existing files, and each is craft-first: it leads with the artifact it produces and treats course work as one optional branch rather than a requirement. The sales-copy skill draws from the LodgeStatus campaign notes to write credible hooks and sales copy for skills and courses.

The [product-launch-video](./product-launch-video/SKILL.md) skill is also included as a subskill in `course-creator`. It turns supplied screenshots and product information into a motion ad or screenshot-based demo, using genuine screens as evidence. It writes a per-video `style.md` and delivers editable Remotion source plus an MP4 when rendering is available.

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
npx skills add oyenet1/agent-skills@voice-narration -g

# Install screenshot-driven Remotion product ads independently
npx skills add oyenet1/agent-skills@product-launch-video -g

# Install the standalone planning and visual-sourcing skills
npx skills add oyenet1/agent-skills@curriculum-map -g
npx skills add oyenet1/agent-skills@visual-assets -g

# Install all skills from this repo
npx skills add oyenet1/agent-skills --all
```

## Editing Skills

Skills are generated. The source of truth is [`skills-src/`](./skills-src/); the
`course-creator/subskills/` folders and the top-level skills are build output.
**Do not edit generated folders by hand** — the next build overwrites them.

| Path | What it holds |
|---|---|
| `skills-src/manifest.yaml` | which capabilities exist, their names, and which shared modules each ships |
| `skills-src/<capability>/skill.md` | one capability — frontmatter for both targets, shared craft, `{{mode:…}}` blocks for target-specific text |
| `skills-src/_shared/` | the intake modules: `intake`, `brand`, `video`, `voice`, `preflight`, `objects` |
| `skills-src/_shared/prompts/<category>/` | script and storyboard patterns, one file per pattern |
| `skills-src/<capability>/files/` | extra files a target ships (e.g. the product launch workflow) |

One capability emits two install targets: the `course-creator` bundle subskill
(`course-creator-<id>`) and the standalone skill (`<id>`). Tokens in a
`skill.md` resolve per target — `{{ref:brand}}` links the shared module,
`{{doc:narration.md}}` links a `course-creator` reference, `{{sibling:voice-narration}}`
links another capability, and `{{asset:tools/kokoro/README.md}}` resolves a
shipped path at the right depth.

```bash
# regenerate every target (requires pyyaml)
python scripts/gen_skills.py

# verify committed output matches the source — run before committing
python scripts/gen_skills.py --check

# behaviour tests
cd scripts && python -m unittest
```

The tool trees follow the same rule: `course-creator/tools/kokoro/` is canonical
and `voice-narration/tools/kokoro/` is generated from it, so the standalone
install works alone.

## Intake

Every producing skill runs the same intake protocol before it makes anything.
See [`skills-src/_shared/intake.md`](./skills-src/_shared/intake.md): present
inputs are used, inferable inputs get a stated default recorded with a reason,
and missing inputs that would change the deliverable are asked in **one batched
block with options and a recommended pick**. Brand values and evidence are never
invented.

Brand identity lives in a `brand.md` that skills read and write — colour, type,
tone, vertical, claims and accessibility all inherit from it, and each per-video
`style.md` records only its deltas. A local project can be read with
`python scripts/extract_brand.py <path>`; secrets and dotfiles are never read.

## License

MIT — see [LICENSE](./LICENSE).
