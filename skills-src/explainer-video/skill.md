---
standalone:
  name: explainer-video
  description: >-
    Produce an explainer, lesson or motion-graphics video from any brief, script,
    slides, audio, narration or footage. Asks for the video category, platform,
    audio mode and ending, resolves the brand profile, builds the visuals in
    Slidev, Remotion or HyperFrames, layers sound effects, and delivers the video,
    the audio and the voiceover text. Use for video work that does not require a
    full course.
bundle:
  name: course-creator-explainer-video
  description: >-
    Create an educational Remotion lesson video or a CapCut Desktop editing
    handoff from slides, a brief, script, narration, or teacher footage inside the
    course-creator bundle. Registers video artifacts under the lesson and keeps
    them aligned with the course style.
---

# Explainer Video

Produce the requested video and nothing else. Start from the supplied brief and
actual existing assets — a Slidev deck can guide the design but is not required.
Work from real material; never invent a UI state, a metric, a testimonial or a
click result.

## 1. Intake

Read {{ref:intake}}, then {{ref:video}} for the full decision list. The order
matters:

1. **Brand** — resolve `brand.md` ({{ref:brand}}). Interview to create it if
   absent; never invent palette, fonts or logo.
2. **Category** — ask the purpose. Six categories; **`motion-graphic` is the
   default when the purpose is unclear.**
3. **Platform** — ask once. It derives aspect ratio and resolution.
4. **Audio mode** — `silent` / `voiceover` / `music` / `full`.
5. **Voiceover** *(optional)* — a supplied recording is the timing master;
   otherwise generate with {{ref:voice}}. The standalone skill ships
   `tools/kokoro/start.py` for local narration.
6. **Ending** — main CTA, logo sting, takeaway, QR, contact, or next video.
7. **Assets** — logo, SVGs, screenshots, footage, charts. Collect up front.
8. **Per-category inputs** — headline and key points, or topic and learning
   outcome, or screenshots and supported claims.

Missing deliverable-changing inputs go into **one batched block** with options and
a recommended pick each. Do not re-ask what the request already states.

## 2. Preflight

Read {{ref:preflight}} and run
`python3 tools/ensure_video_runtime.py explainer-video` from this skill
directory. Choose the renderer first (§4) and pass `--renderer remotion` or
`--renderer hyperframes` when the category is a demo or an ad. Use the verified
executable paths in its JSON result for Slidev, Remotion, HyperFrames and FFmpeg.
Report setup failures up front. Never claim an output exists if the tool that
makes it is missing.

## 3. Write before you build

Create `style.md` first. It carries palette, fonts, tone, canvas and safe areas,
representative frames, and an **effects bible**: each effect's purpose, entrance,
hold, exit, duration, easing and use conditions. Then `script.md`, then
`storyboard.md` with stable beat IDs — each beat records narration or on-screen
copy, visual source, motion direction, duration and transition.

**Every video opens on a hook cover** — see {{ref:video}} §11. Beat 1 is a single
designed frame carrying the hook phrase as payoff or tension, legible at thumbnail
size and held 1.5–3 seconds. It is the first frame, the cover and the thumbnail at
once, so write it deliberately rather than letting the first scene double as it.
Record the cover line in `style.md`.

Resolve `## Delivery` in `style.md` from §2 of {{ref:video}}: category, platform,
aspect, master resolution, delivery resolution, renderer and fps. **Render a 4K
master whenever the platform accepts it, then downscale — 1080p is the default
delivery, 720p the smallest accepted, never below.**

## 4. Build

| Category | Build in |
|---|---|
| `motion-graphic`, `explainer-lesson`, `slideshow-montage` | **Slidev** — see §5 |
| `screencast-demo`, `launch-ad` | **Remotion** (default) or **HyperFrames** — real screens, animated crops and callouts |
| `footage-overlay` | **Remotion** (default) or **HyperFrames**, or a compositor over the supplied footage |

Ask once, and only for a demo or an ad: **Remotion or HyperFrames?** Both render
video from web code with headless Chrome and FFmpeg. Remotion is the default — a
React project with the larger ecosystem and the more mature Lambda path.
HyperFrames is the Apache-2.0 alternative — plain HTML + CSS + GSAP, no build
step, no per-seat or per-render licence — for a deliverable that must ship
without a source-available licence review or a handover a non-developer can edit.
See {{ref:video}} §9. Record the choice as `Renderer:` in `style.md` → `## Delivery`.

For a Remotion composition, write a one-scene timing plan and run
`python3 tools/render_remotion_video.py src/index.ts <composition-id> timing.json --out <project-dir>`.
It prepares the renderer, renders the composition, packages the MP4 and timed
captions, and copies the editable project source. Set `audio_from_visual: true`
with a transcript to keep audio already rendered by Remotion, or provide
`narration` to replace it. Review the final mix and captions.
For HyperFrames, use the same one-scene plan with
`python3 tools/render_hyperframes_video.py index.html timing.json --out <project-dir>`.
This retains the HTML composition and its local assets with the finished video.

Draw from the object library in {{ref:objects}} before hand-building a visual.
Download or draw anything missing — never leave a gap. Copy selected assets into
the project and record provenance and alt text in `assets/manifest.json`.

### 5. Motion graphics in Slidev

Slidev gives real animation primitives: `v-click` (`.up`, `.fade-in`,
`.fade.right.scale`), `v-motion` (`:initial` → `:enter` → `:leave`, plus
`:click-1`), `v-mark` for annotations, and named `transition` frontmatter. The
full rack — layouts, built-in components, code highlighting, diagrams, UnoCSS,
global layers, presenter tools — is in {{ref:slidev}}. Use what exists before
building a component. Keep `--with-clicks` steps aligned to storyboard beat IDs.

Edit through the **Slidev MCP server** (always enabled — see {{ref:slidev}} and
{{ref:preflight}}) rather than rewriting the file, and `slidev-goto-slide` to
inspect each rendered scene at delivery size.

**For structure, draw a diagram.** Architecture, request paths, sequences,
entities, state and schedules render natively from a ` ```mermaid ` block, themed
from the brand palette via `defineMermaidSetup` in `setup/mermaid.ts`. Show the
whole diagram first, then `v-click` one node or edge at a time — colour the active
element with the accent and dim the rest. Pick the diagram kind and follow the
connector rules in {{ref:objects}}. Never invent an architectural component that
is not in the system being described.

**Code on screen must be lint-clean and actually run** — see {{ref:code}}. Lint
it before it goes into the video, and use step highlighting or `{monaco}` so the
change is visible.

**Slidev has no native MP4 export.** Assemble video either by exporting the
stepped PNG sequence (`slidev export --with-clicks --format png`) and building it
with `ffmpeg` at the storyboard's per-step durations, or by driving the deck with
Playwright on a timing schedule and recording it when `v-motion` easing must
survive. Render at the master resolution, not the export default.

For the stepped path, write a timing JSON with one scene per exported click
state, then run
`python3 tools/render_slidev_video.py slides.md timing.json --out <project-dir>`.
This prepares Slidev and FFmpeg, exports each click state, joins it with measured
scene audio and captions, and keeps the deck source with the resulting MP4.
The number and order of timing scenes must match the exported frames. Use the
recorded path when continuous motion is essential; PNG states hold each frame
and do not preserve in-between easing.

When scenes are rendered as separate images or clips, write a scene plan and run
`python3 tools/assemble_video.py plan.json --out <project-dir>` to join them
with measured narration or footage audio. Each scene needs `visual` and either
`duration_sec` or a measurable audio/video duration; add `narration` plus its
transcript in `caption`, or `audio_from_visual: true` plus a transcript for
footage sound. Use `cues` for reviewed timing within a scene. The tool writes a
1080p delivery MP4, optional mixed-audio MP3, imported assets, a manifest, and
SRT/VTT/JSON captions. Retain a separate 4K master when required and export the
reusable voiceover MP3/WAV through {{ref:voice}}.
Add a plan-level `music: {"file": "audio/bed.wav", "volume": 0.12}` only when
the chosen audio mode calls for it; listen and adjust its level under speech.
Inspect its finished video and correct any cue that does not follow speech.
Keep the editable Slidev, Remotion or HyperFrames source with the project.

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

Export `captions.srt` and `captions.vtt` with every video, including silent videos
whose on-screen text carries the message. Time cues against the final audio or
reviewed video timeline; storyboard estimates are not speech alignment. Save the
measured cue data as `captions.json` and run
`python tools/write_subtitles.py captions.json --out captions`. The input has
`duration_sec` (the final video duration) and a `cues` array
of `{ "start": seconds, "end": seconds, "text": string }`. Check the exported
files against the final MP4 after any timing edit.
For spoken audio without reviewed word cues, run
`python3 tools/transcribe_captions.py <project-dir>/video.mp4 --out <project-dir> --language <code>`
after the final mix. It transcribes locally, groups measured words into cues,
and replaces the SRT/VTT/JSON exports. Review recognition against the script
and listen through every cue before delivery; rerun after audio changes.

**Deliver three outputs** — see {{ref:video}} §14. The **video** (MP4 at the
master resolution, downscaled to delivery), the **audio** (the voiceover as MP3,
converted from the verified WAV), and the **voiceover text** (timed SRT, or plain
TXT when only the read is needed). Keep the editable source, the WAV, the
captions and the rendered files together.

## 9. Report

State the category, platform, resolutions, renderer, the three outputs (MP4,
MP3 and SRT/TXT), their paths, the voice and SFX used, and every render
limitation or unverified claim you left out.

{{mode:bundle}}
## Course integration

Read the {{doc:video-style-template.md|video style template}} and the
{{doc:visual-media.md|visual media workflow}}. Write a concrete `style.md` for
**each** video; the course-level style supplies defaults and the per-video file
states only the deltas. Keep concept and storyboard beat IDs when supplied. Use
course-local images and icons; copy selected visuals into the course folder.

Align scene and caption timing to actual teacher footage or audio — text alone is
a script until timed or recorded. If TTS is requested, also read the
{{sibling:voice-narration}} subskill. For a CapCut Desktop handoff, provide
separate scene clips and reusable media plus a timecoded guide covering layers,
placement, effects, keyframes, entrance, exit, captions and audio cues.

Register the video source, MP4 and actual inputs under the lesson's `artifacts`;
record dependencies in `artifactSources` and mark affected outputs in
`staleArtifacts` after an input changes. Store output under the lesson folder.
{{/mode}}

{{mode:standalone}}
## Standalone output

Work from the brief and whatever assets exist. If a `course-plan.json` is
present and the requester points at a mapped lesson, register the video source
and MP4 under that lesson's `artifacts` and use `artifactSources` /
`staleArtifacts` as usual; otherwise use the output directory the requester
names.

For a product launch ad or a screenshot-based product demo, use the
{{sibling:product-launch-video}} skill when it is installed — this skill handles
explainer and lesson video.
{{/mode}}

## Optional generated illustrations

Read {{ref:generated-assets}} when generating supporting scene images. Keep the
verified image and its provider/model/prompt metadata with the editable project.
