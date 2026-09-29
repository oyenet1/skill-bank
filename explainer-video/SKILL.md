---
name: explainer-video
description: Produce an explainer, lesson or motion-graphics video from any brief, script, slides, audio, narration or footage. Asks for the video category, platform, audio mode and ending, resolves the brand profile, builds the visuals in Slidev or Remotion, layers sound effects, and renders at 1080p or above. Use for video work that does not require a full course.
---

# Explainer Video

Produce the requested video and nothing else. Start from the supplied brief and
actual existing assets — a Slidev deck can guide the design but is not required.
Work from real material; never invent a UI state, a metric, a testimonial or a
click result.

## 1. Intake

Read [intake](references/intake.md), then [video](references/video.md) for the full decision list. The order
matters:

1. **Brand** — resolve `brand.md` ([brand](references/brand.md)). Interview to create it if
   absent; never invent palette, fonts or logo.
2. **Category** — ask the purpose. Six categories; **`motion-graphic` is the
   default when the purpose is unclear.**
3. **Platform** — ask once. It derives aspect ratio and resolution.
4. **Audio mode** — `silent` / `voiceover` / `music` / `full`.
5. **Voiceover** *(optional)* — a supplied recording is the timing master;
   otherwise generate with [voice](references/voice.md).
6. **Ending** — main CTA, logo sting, takeaway, QR, contact, or next video.
7. **Assets** — logo, SVGs, screenshots, footage, charts. Collect up front.
8. **Per-category inputs** — headline and key points, or topic and learning
   outcome, or screenshots and supported claims.

Missing deliverable-changing inputs go into **one batched block** with options and
a recommended pick each. Do not re-ask what the request already states.

## 2. Preflight

Read [preflight](references/preflight.md) and confirm the toolchain before promising a render.
Report gaps up front. Never claim an output exists if the tool that makes it is
missing.

## 3. Write before you build

Create `style.md` first. It carries palette, fonts, tone, canvas and safe areas,
representative frames, and an **effects bible**: each effect's purpose, entrance,
hold, exit, duration, easing and use conditions. Then `script.md`, then
`storyboard.md` with stable beat IDs — each beat records narration or on-screen
copy, visual source, motion direction, duration and transition.

**Every video opens on a hook cover** — see [video](references/video.md) §11. Beat 1 is a single
designed frame carrying the hook phrase as payoff or tension, legible at thumbnail
size and held 1.5–3 seconds. It is the first frame, the cover and the thumbnail at
once, so write it deliberately rather than letting the first scene double as it.
Record the cover line in `style.md`.

Resolve `## Delivery` in `style.md` from §2 of [video](references/video.md): category, platform,
aspect, master resolution, delivery resolution and fps. **Export floor is 1080p;
render a 4K master whenever the platform accepts it and downscale for delivery.**

## 4. Build

| Category | Build in |
|---|---|
| `motion-graphic`, `explainer-lesson`, `slideshow-montage` | **Slidev** — see §5 |
| `screencast-demo`, `launch-ad` | **Remotion** — real screens, animated crops and callouts |
| `footage-overlay` | Remotion or a compositor over the supplied footage |

Draw from the object library in [objects](references/objects.md) before hand-building a visual.
Download or draw anything missing — never leave a gap. Copy selected assets into
the project and record provenance and alt text in `assets/manifest.json`.

### 5. Motion graphics in Slidev

Slidev gives real animation primitives: `v-click` (`.up`, `.fade-in`,
`.fade.right.scale`), `v-motion` (`:initial` → `:enter` → `:leave`, plus
`:click-1`), `v-mark` for annotations, and named `transition` frontmatter. The
full rack — layouts, built-in components, code highlighting, diagrams, UnoCSS,
global layers, presenter tools — is in [slidev](references/slidev.md). Use what exists before
building a component. Keep `--with-clicks` steps aligned to storyboard beat IDs.

Edit through the **Slidev MCP server** (always enabled — see [slidev](references/slidev.md) and
[preflight](references/preflight.md)) rather than rewriting the file, and `slidev-goto-slide` to
inspect each rendered scene at delivery size.

**For structure, draw a diagram.** Architecture, request paths, sequences,
entities, state and schedules render natively from a ` ```mermaid ` block, themed
from the brand palette via `defineMermaidSetup` in `setup/mermaid.ts`. Show the
whole diagram first, then `v-click` one node or edge at a time — colour the active
element with the accent and dim the rest. Pick the diagram kind and follow the
connector rules in [objects](references/objects.md). Never invent an architectural component that
is not in the system being described.

**Code on screen must be lint-clean and actually run** — see [code](references/code.md). Lint
it before it goes into the video, and use step highlighting or `{monaco}` so the
change is visible.

**Slidev has no native MP4 export.** Assemble video either by exporting the
stepped PNG sequence (`slidev export --with-clicks --format png`) and building it
with `ffmpeg` at the storyboard's per-step durations, or by driving the deck with
Playwright on a timing schedule and recording it when `v-motion` easing must
survive. Render at the master resolution, not the export default.

### 6. Sound

Plan it in `style.md`. Use a small named SFX set — `typing`, `click`, `alert`,
`success`, `whoosh`, `pop`, `shutter`, `hover`, `ambient` — and use it
consistently. Duck music and ambient beds roughly 12–18 LUFS under speech. A
`silent` video gets no SFX and no music. Check the result **when muted**: the
picture must still communicate.

### 7. Screen conventions

- **Highlight hooks** as they appear — word-by-word reveal, highlight sweep or
  accent-colour treatment. The single most important phrase never arrives as
  undifferentiated body text.
- **Zoom in** on form filling and typing, keep the cursor visible, and pair it
  with `typing` / `click` / `alert` / `success` SFX at the matching moments.
- **One concept per scene.** A new concept gets a new slide, a broll cut or a
  layout change.
- Never rely on narration alone to deliver the point.

## 8. Produce and inspect

Generate the voice track early and let it run in the background while visuals are
authored — it is the timing master. Render, then inspect the actual output:
opening frame, each scene, transitions, final CTA, captions against final audio,
audio sync, legibility at delivery size, and that every referenced asset exists.

## 9. Report

State the category, platform, resolutions, renderer, output paths, the voice and
SFX used, and every render limitation or unverified claim you left out.

## Standalone output

Work from the brief and whatever assets exist. If a `course-plan.json` is
present and the requester points at a mapped lesson, register the video source
and MP4 under that lesson's `artifacts` and use `artifactSources` /
`staleArtifacts` as usual; otherwise use the output directory the requester
names.

For a product launch ad or a screenshot-based product demo, use the
`product-launch-video` skill when it is installed — this skill handles
explainer and lesson video.
