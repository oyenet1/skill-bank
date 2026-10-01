# Video Intake

Run after the brand profile is resolved. Ask only what the request does not
already state, and batch the rest per [intake](intake.md).

## 1. Category — ask the purpose

One question, or skip it when the request already carries the purpose.

| Purpose | Category |
|---|---|
| teach a concept · summarize/recap · announce | **`motion-graphic`** (default) |
| sell / promote | `launch-ad` |
| demonstrate a workflow · onboard | `screencast-demo` |
| document existing footage | `footage-overlay` |
| longer lesson with a learning outcome | `explainer-lesson` |
| images on a beat | `slideshow-montage` |

**When the purpose is unclear, ask and wait.** A default category is a
recommendation, not an answer; use it only when the requester delegates the choice.

| Category | What it is |
|---|---|
| `motion-graphic` | kinetic typography, data callouts, abstract animated scenes. No footage needed. |
| `explainer-lesson` | teaching scenes, concept beats, slide-derived. |
| `screencast-demo` | real product or UI screens, annotated. |
| `footage-overlay` | supplied video with graphic overlays and captions. |
| `launch-ad` | product proof, one story, one verified CTA. |
| `slideshow-montage` | images cut on a beat grid. |

## 2. Platform — ask once, derive the rest

| Platform | Aspect | Master | Delivery |
|---|---|---|---|
| YouTube (long) | 16:9 | 3840×2160 | 3840×2160 or 1920×1080 |
| YouTube Shorts · TikTok · Instagram Reels | 9:16 | 2160×3840 | 1080×1920 |
| Instagram feed | 4:5 | 2160×2700 | 1080×1350 |
| LinkedIn | 1:1 or 16:9 | 2160×2160 / 3840×2160 | 1080×1080 / 1920×1080 |
| X / Twitter | 16:9 or 1:1 | 3840×2160 / 2160×2160 | 1920×1080 / 1080×1080 |
| Facebook | 16:9 or 1:1 | 3840×2160 / 2160×2160 | 1920×1080 / 1080×1080 |
| Website embed | 16:9 | 3840×2160 | 1920×1080 |
| Presentation / projector | 16:9 | 3840×2160 | 1920×1080 |

**Export policy.** The resolution ladder is **4K master** — rendered whenever the
platform accepts it, then downscaled — → **1080p delivery (the default)** →
**720p delivery (the smallest accepted)**. Use 720p only when file size or
bandwidth demands it; **never deliver below 720p**. Frame rate 30fps unless the
requester asks otherwise; 60fps for fast motion or screen recordings that must
stay legible.

Record the resolved `Category`, `Platform`, `Aspect`, `Master`, `Delivery`,
`Renderer`, `fps` and `Watermark` in the `## Delivery` block of `style.md`.

## 3. Audio mode — ask which of these

| Mode | Meaning | Consequences |
|---|---|---|
| `silent` | on-screen text carries the meaning | captions mandatory, no TTS, no music |
| `voiceover` | narration only | [voice](voice.md) runs, captions optional |
| `music` | instrumental bed only | source BGM, no TTS |
| `full` | voiceover + music + SFX | [voice](voice.md) + BGM + level the bed under speech |

Then ask for a **voiceover** *(optional)*: a recorded voiceover supplied by the
requester. If supplied, it is the **timing master** — scenes and captions align
to it. If not, [voice](voice.md) generates one. If neither, fall back to `silent`.

## 4. Ending — ask what it closes on

| Ending | Use when |
|---|---|
| **Main CTA** (recommended) | there is one next action: visit, buy, enrol, sign up |
| Logo sting | brand recall, no action required |
| Takeaway recap | teaching content, the point must land |
| QR code | offline or mobile handoff |
| Contact | services, agency, local business |
| Next video pointer | part of a series |

A CTA needs a **verified destination** — a real URL, enrolment page or waitlist.
Never invent one. Keep exactly **one** CTA visible at the end.

## 5. Assets — ask what they can supply

Collect these up front so production does not stall mid-build.

| Asset | Needed for | If missing |
|---|---|---|
| Logo (lockup + mark + mono) | all | ask; else no logo, output marked `unbranded` |
| Brand SVGs / icons | all | fall back to the bundled 580-SVG library |
| Screenshots | `screencast-demo`, `launch-ad` | **required** — cannot invent UI |
| Screen recording | `screencast-demo` | stills + described result |
| Product / lifestyle stills | `launch-ad`, `slideshow-montage` | ask |
| Footage | `footage-overlay` | **required** for this category |
| Charts / data | `motion-graphic` | draw an editable SVG diagram |
| Custom fonts | all | ask; else system-safe stack |

Record every file in `assets/manifest.json` with source, provenance, alt text and
use terms. Copy selected assets into the project so the output stays portable.

## 6. Optional: watermark

Ask whether a watermark is wanted. It is optional and often omitted — offer it,
do not assume it.

| Ask | Options |
|---|---|
| Watermark | none (recommended) / text / logo / both |
| Opacity | subtle 15–25% (recommended) / medium 40% / strong 70%+ |

- **Text** — the brand or product name from `brand.md`.
- **Logo** — the mark (not the full lockup) from `brand.md` → `Logo`.
- **Both** — mark plus name, mark first.
- Keep it in a **safe corner** — usually bottom-right, inside the safe area, never
  under captions or a CTA.
- Keep it on a consistent position and opacity for the whole video. A watermark
  that moves or changes weight reads as a mistake.
- At `subtle`, it must remain legible when paused; at any opacity it must never
  reduce the legibility of content beneath it.

Record the choice in `style.md` → `## Delivery` as `Watermark: none` or
`Watermark: logo · 20% · bottom-right`.

## 7. Per-category required inputs

| Category | Must have | Ask (options, recommended pick) | Defaults |
|---|---|---|---|
| `motion-graphic` | headline, 1–5 key points or stats | duration 15/30/60s · pace calm/energetic | 30s · energetic |
| `explainer-lesson` | topic, audience level, one learning outcome | duration · narration mode | 60s · voiceover |
| `screencast-demo` | screenshots or recording | which claims are supported · CTA | feature-reveal |
| `footage-overlay` | footage + transcript | overlay moments · caption style | anchor captions |
| `launch-ad` | product, problem, evidence, CTA | duration · offer details | 30s |
| `slideshow-montage` | images | tempo · captions · duration | 30s |

Every category also needs a **hook line** for the cover — see §11. Ask for it with
the rest; if the request already carries one, use it.

## 8. Production order

1. Resolve `brand.md` ([brand](brand.md)).
2. Category → platform → audio mode → ending → assets → optional watermark.
3. Check the toolchain ([preflight](preflight.md)).
4. Pick 2–3 prompt patterns for `category × vertical` from `references/prompts/`.
5. Write `style.md`, then `script.md`, then `storyboard.md`.
6. Write the hook cover first — it is the frame the rest of the video must earn.
7. Start the voice track immediately and let it generate **in the background**
   while the visuals are authored — it is the timing master, so its beat lengths
   drive the scene durations.
8. Choose the renderer for the category — Slidev, Remotion or HyperFrames (see
   §9) — and build the scenes.
9. Layer sound, then render, then inspect.
10. Deliver the three outputs (see §14): the video, the audio and the voiceover
    text.

When a desktop host provides `request.json`, run
`python3 tools/run_video_job.py request.json` from this skill directory after
the source composition or scene plan exists. Relay its JSON progress to the UI;
use `--resume` after a failed stage. A result with `status: "review_required"`
needs transcript and caption review before approval. The request shape and
state files are documented in the repository's `docs/video-job-contract.md`.

## 9. Build the visuals — Slidev, Remotion or HyperFrames

The renderer follows the category. Ask the requester once — "Remotion or
HyperFrames?" — only for a demo or an ad; every other category uses its default.

| Category | Renderer | Why |
|---|---|---|
| `motion-graphic`, `explainer-lesson`, `slideshow-montage` | **Slidev** | real animation primitives (`v-click`, `v-motion`, `v-mark`), Mermaid diagrams, code highlighting |
| `screencast-demo`, `launch-ad` | **Remotion** (default) or **HyperFrames** | real screens, animated crops and callouts |
| `footage-overlay` | **Remotion** (default) or **HyperFrames**, or a compositor | graphic overlays on the supplied footage |

**Remotion vs HyperFrames.** Both render video from web code with headless
Chrome and FFmpeg, frame by frame, and both render locally or on AWS Lambda.

- **Remotion** (default) — a React/TSX project. Pick it for the larger ecosystem
  (charts, Three.js, transitions, captions), and because its local Lambda path is
  the more mature one.
- **HyperFrames** — HTML + CSS + GSAP compositions with no build step. Pick it
  when the deliverable must ship without a source-available license review
  (HyperFrames is Apache-2.0, with no per-seat or per-render cost), when the
  author is an AI agent, or when a plain-HTML composition is easier to hand over
  than a React project.

Only one renderer is installed and used per video. Record the choice as
`Renderer: remotion` or `Renderer: hyperframes` in `style.md` → `## Delivery`.

### 9a. Slidev — motion graphics, lessons, slideshows

For `motion-graphic`, `explainer-lesson` and `slideshow-montage`, author the
visuals as a **Slidev deck**. It gives real animation primitives instead of
hand-rolled keyframes:

| Need | Use |
|---|---|
| element appears | `v-click` with `.up` · `.fade-in` · `.fade.right.scale` |
| sequential reveal | `v-click` ordered, or `v-motion` `:click-1` `:click-2-4` |
| continuous motion | `v-motion` `:initial` → `:enter` → `:leave` with x/y/rotate/scale |
| scene change | frontmatter `transition: <name>`; use `a \| b` for distinct forward/back |
| custom transition | name it in frontmatter, define `.<name>-enter-active` etc. in styles |

Keep the deck's `--with-clicks` steps aligned to storyboard beat IDs so each
click step is one narrative step.

**Slidev has no native MP4 export.** Its CLI exports `pdf` (default), `png`,
`pptx`, `md`. Assemble video with one of these:

| Path | How | Use when |
|---|---|---|
| **Stepped** | `slidev export --with-clicks --format png` → `ffmpeg` image2 sequence at the storyboard's per-step durations → mux the TTS track | deterministic, scriptable, no easing |
| **Recorded** | Playwright drives the deck against a timing schedule and records the browser | real `v-motion` easing and continuous movement must survive |

Always render at the **master** resolution from §2, never at the export default.

### 9b. Remotion — demos and ads

Build an editable Remotion project. Put screenshots, footage and brand assets in
its `public/` folder and reference them through the current asset APIs. Keep each
shot as a reusable component and keep timing in data where practical. Confirm
the syntax and render options against the installed Remotion guidance before
implementing. Render locally for one video; reach for Lambda only when a batch
makes it worthwhile. Retain the source project as a deliverable.

### 9c. HyperFrames — the HTML alternative

Build a HyperFrames composition instead of a React project when the licence or
the handover favours it. A composition is a plain HTML file whose timing lives in
`data-*` attributes and whose motion is a seekable GSAP timeline:

- give every visible slot `class="clip"` with an `id`, `data-start`,
  `data-duration` and `data-track-index`;
- create the timeline **paused** and register it on
  `window.__timelines["<composition-id>"]` under the same id as the root;
- keep to the determinism rules — no wall clocks, no unseeded randomness, no
  render-time network fetches.

Use the same screenshots and copy as the Remotion path. Preview and render
through the CLI (`hyperframes preview`, `hyperframes render --quality looks`) at
the master resolution, and inspect each scene before delivery. The composition
HTML **and** the rendered file are the editable source. When a port from an
existing Remotion project is needed rather than a new build, the
`remotion-to-hyperframes` skill translates roughly 80% mechanically and flags
what it cannot.

## 10. Sound design

Sound is a first-class layer, not an afterthought. Plan it in `style.md` under
`## Sound and captions`.

**SFX palette** — keep a small named set and use it consistently:

| SFX | Use for |
|---|---|
| `typing` | on-screen typing, form filling, command entry |
| `click` / `tap` | button press, selection, toggle |
| `alert` | notification, warning, error state appearing |
| `success` | completed action, checkmark, confirmed state |
| `whoosh` | scene change, element sweep in/out |
| `pop` | object appearing, badge, stat landing |
| `hover` | cursor passing over UI |
| `shutter` | screenshot reveal, freeze frame |
| `ambient` | low bed under a silent or music-only cut |

**Mixing rules**
- Music and ambient beds **duck under speech** — target roughly −12 to −18 LUFS
  below the voiceover, never masking it.
- SFX sit above the bed and below the voice.
- A `silent` video needs no SFX and no music; its captions carry the meaning.
- Check the result when muted: the picture must still communicate.

## 11. Hook cover — every video opens on one

**Every video opens on a hook cover.** No exceptions, for any category. It is a
single designed frame that carries the hook and tells the viewer why to keep
watching — the first frame, the cover art, and the thumbnail are the same frame,
so design it as all three at once.

| Rule | Why |
|---|---|
| **One idea: the hook phrase, plus at most one supporting line** | a cover with a title, a subtitle and a logo competes with itself and reads as nothing |
| **Phrase it as payoff or tension, not as a topic** | "Ship in an afternoon, not a sprint" beats "Introduction to deployment" |
| **Legible at thumbnail size** | at 9:16 and 1:1 it is usually seen far smaller than the frame — check the hook still reads at ~20% |
| **Hold 1.5–3 s, then move** | a cover that lingers reads as a stall; a cover that flashes is missed |
| **Brand mark is a corner element, never the hero** | a logo-only cover says nothing |
| **Say the hook in the narration too** | if there is audio, the first spoken sentence is the cover line |
| **Promise only what the video pays off** | an unkept cover loses the viewer at the second beat |

Every category opens this way — including a **silent** or music-only video, where
the cover carries the meaning on its own. The `slideshow-montage` opening image
and the `footage-overlay` title card are hook covers too: give them a hook line
rather than just a title.

**The first beat of every pattern in the bundled prompt set is the hook cover.**
Treat it as mandatory even when a pattern does not spell it out.

Record the chosen cover line in `style.md` → `## Delivery` as `Hook cover:`.

## 12. Screen conventions

**Hook highlighting.** When a hook or key phrase appears on screen — as headline,
explanation or subtitle — highlight it as it is spoken or read: word-by-word
reveal, a highlight sweep, or an accent-colour treatment from `brand.md`. Never
let the single most important phrase arrive as undifferentiated body text.

**Product demo zoom.** On any form-filling, typing or dense-UI moment, **zoom in**
on the field being used and keep the cursor visible. Pair it with the matching
SFX: `typing` while characters appear, `click` on commit, `alert` on a
notification, `success` on completion. Keep labels and data legible at the
zoomed size.

**Concept rhythm.** Every new concept gets a **new scene** — a new slide, a broll
cut, or a layout change. Never carry two concepts on one static frame. Use broll
when the concept is contextual and the main visual cannot change.

**Still readable when muted.** On-screen text must be sufficient on its own:
never rely on narration alone to deliver the point.

## 13. Product demos — follow how people actually learn

A demo is a lesson, not a feature tour. These rules are not stylistic; each one
exists because viewers abandon or misremember demos that break it.

| Rule | Why |
|---|---|
| **Show the outcome first** | name what the viewer will be able to do before the first click. It tells them what to hold onto. |
| **One action per beat** | two clicks in one step and the viewer loses which caused what. |
| **Always show the state change** | the before and after of the action must both be visible, or causation is invisible. |
| **Narrate *why*, not *what*** | "we lock the record so a failed payment can't double-charge" beats "now I click Save". |
| **Progressive disclosure** | reveal the UI as it is needed. A full dashboard at once teaches nothing. |
| **Zoom to the action** | see §10 — the viewer cannot follow a form on an unzoomed full screen. |
| **Name each screen** | give the viewer a mental map they can reuse later. |
| **Pace for a first-timer** | hold on the state change long enough to be read; never cut on the click. |
| **Recap with the same steps** | a short close repeating the sequence is what actually sticks. |
| **Show real friction** | if a step is slow or has a caveat, show it. A frictionless fake is discovered immediately. |

**When the product demo contains code**, the code must be lint-clean and actually
run — see [code](code.md). Lint it before it goes into the demo, not after.

**When the demo teaches a system**, prefer a real architectural diagram over
prose — see the diagram rules and the Mermaid kinds in [objects](objects.md).

## 14. Outputs — three deliverables

Every video delivers **three outputs**, not one. Keep them together in the
project folder so a later edit stays selective.

| Output | File | Source |
|---|---|---|
| **Video** | `<name>.mp4` | the render, at the master resolution, downscaled to delivery (1080p default, 720p floor) |
| **Audio** | `<name>.mp3` | the voiceover track, exported alongside the working WAV |
| **Voiceover text** | `<name>.srt` **or** `<name>.txt` | the narration: timed cues when it must line up with the audio, plain text otherwise |

- **Audio.** Narration is its own deliverable (see [voice](voice.md)). Export the
  voiceover as **MP3** as well as the working WAV, so it can be reused or re-cut
  without the video. When the video also carries music or SFX, export the mixed
  track as a second MP3.
- **Voiceover text.** Ship the narration as timed **SRT** when the timing matters,
  or as plain **TXT** when only the read is needed. For a narrated video the
  voiceover text and the captions are the same text — use one source.
- **Captions** remain separate and are still required where the audio mode or the
  category calls for them: `captions.srt`, `captions.vtt` and `captions.json`.

A `silent` video still delivers the video and the text; its audio output is the
music or ambient bed as MP3, or it is omitted when the video is genuinely silent.
State the omission rather than inventing an empty track.
