---
name: product-launch-video
description: Handles /product-launch prompts delivered by the host. Create a motion-led product launch ad or screenshot-based product demo in Remotion or HyperFrames from supplied screenshots, product details, a website, or a repository. Grounds every claim in real screens, resolves the brand profile, asks for platform, renderer and ending, and delivers the video, the audio and the voiceover text. Use when the deliverable is a promotional product video.
---

# Product Launch Video

## Automatic first-use setup

Before production, run the bundled launcher with `--yes`; it detects the host, prepares private runtimes, and installs the declared sibling dependency graph. Do not ask the requester to install packages manually.

- Linux/macOS: `sh tools/setup.sh --yes`
- Windows: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/setup.ps1 --yes`

Use `--check` for a read-only readiness check. If prerequisites are missing, rerun setup. Follow the returned `pythonExecutable` and runtime paths for later commands. Model-license acceptance, image rights and account credentials remain explicit inputs.

Accept product screenshots as the main input; also use any supplied product
brief, site, repository, brand assets, screen recording or founder footage.
Inspect every selected screenshot before writing a claim. A screenshot-only
request is workable. Ask only for a missing decision that changes the
deliverable; infer ordinary defaults and label unverified details.

Produce the requested video, not an unrelated course or marketing campaign.

Before building, read [preflight](references/preflight.md) and run
`python3 tools/ensure_video_runtime.py product-launch-video --renderer <renderer>`
from this skill directory, where `<renderer>` is `remotion` (default) or
`hyperframes`. Use the verified executable paths in its JSON result for the
chosen renderer and FFmpeg; report any setup failure before promising a render.

## Short prompt alias

When a submitted request begins with `/product-launch`, treat the following text as the
brief for this skill. Follow the clarification breakpoint below before dependent
production. A host may require a native command adapter to deliver slash input.

## Clarify before production

Read [intake](references/intake.md) before starting. If missing or ambiguous inputs would change
the result, ask a concise batch of questions and wait for answers. Offer
recommended choices; apply them only when the requester selects them or
explicitly asks you to choose. Use details already supplied rather than asking
again. Continue directly when the brief is complete.

## Automatic product screenshots

For product demos and launch ads, read [product-capture](references/product-capture.md). When real
screenshots are missing, capture the identified public or authenticated product
with `tools/capture_product_screens.py`. Choose desktop, mobile, or both from the
product experience and video brief; prefer mobile captures for mobile demos.
Use private environment credentials or an existing session, verify login, mask
private data, and inspect the images before building scenes. Ask for a product
URL or local project when neither is available; never generate substitute UI.

## 1. Establish what is true

Inventory the supplied screenshots and inspect them at readable size. Record each
file, screen name, visible action or feature, cropped or private details,
resolution, and the claim it can support. Read any supplied brief, website,
repository README or product docs. If the product is identifiable and a public
site exists, inspect the current site and verify that its name and branding match
the screenshots before using its claims. Prefer current product source to older
marketing drafts. When sources conflict, use the most direct current evidence and
flag the conflict.

**A screenshot proves a visible screen exists.** It does not prove a later click
works, a process is automatic, or a customer achieved a result. Blur sensitive
data before production. If only one screen is supplied, make a focused feature
reveal or screen tour.

Create a short `product-brief.md`: audience, problem, product promise, actual
features shown, verified evidence, open claims, offer, destination, and any
footage or audio supplied.

## 2. Intake

Read [intake](references/intake.md) and [video](references/video.md). Resolve `brand.md` ([brand](references/brand.md)) —
falling back to colours and type read off the product screenshots when there is
no brand source. Then ask platform (derives aspect and resolution), audio mode,
ending and offer details. The category is `launch-ad` unless the requester wants
a longer walkthrough.

## 3. Tell one product story

Pick one buyer and one useful outcome. Start with a specific recognisable
problem, reveal the relevant product screen early, demonstrate a small real
workflow, show the practical result supported by source material, and end with
**one verified CTA**. Make a short ad when asked for an ad; allow a longer
walkthrough when the screenshots need careful explanation.

Write `script.md` and `storyboard.md` with stable beat IDs. Each beat records
narration or on-screen copy, exact screenshot or recording source, highlighted UI
region, visible claim, motion direction, duration and transition.

**Beat 1 is a hook cover** — a single designed frame carrying the hook phrase as
payoff or tension, legible at thumbnail size and held 1.5–3 seconds. It is the
first frame, cover and thumbnail at once. See [video](references/video.md) §11 and record the
cover line in `style.md`. If an apparent
interaction is essential, use a real screen recording or matching before/after
screenshots. A cursor may guide attention on a still but cannot imply an
unobserved click result.

## 4. Design and build

Write `style.md` before coding: palette and fonts (from `brand.md`), tone, canvas
and safe areas, frame examples, screenshot treatment, caption placement, and an
effects bible. Record `## Delivery`: category, platform, aspect, master
resolution, delivery resolution, renderer and fps. **Render a 4K master when the
platform accepts it, then downscale — 1080p is the default delivery, 720p the
smallest accepted, never below.**

Ask once: **Remotion or HyperFrames?** Remotion (default) is a React project with
the larger ecosystem and the more mature Lambda path. HyperFrames is the
Apache-2.0 alternative — plain HTML + CSS + GSAP, no build step, no per-seat or
per-render licence — choose it when the deliverable must ship without a
source-available licence review or the handover must be editable by a
non-developer. Both render the same screens, crops and callouts — see
[video](references/video.md) §9. Record the choice as `Renderer:` in `style.md`.

**Remotion** — build an editable Remotion project. Put screenshots and brand
assets in its public folder and reference them through current Remotion asset
APIs. Keep shots as reusable components, and keep timing in data where practical.
Confirm current syntax and rendering options against installed guidance and
official docs before implementing.

Write a one-scene timing plan and run
`python3 tools/render_remotion_video.py src/index.ts <composition-id> timing.json --out <project-dir>`
from the Remotion project. The adapter prepares Remotion and FFmpeg, renders the
composition, packages timed captions and audio, and copies editable source.
If the composition already has audio, choose `audio_from_visual: true` with its
transcript or supply `narration` to replace it; the adapter rejects an
unspecified audio source instead of silently discarding it.

**HyperFrames** — build a plain-HTML composition instead. Screenshots are plain
`<img>` elements; zoom, pan and callouts are GSAP tweens on a timeline created
paused and registered on `window.__timelines["<composition-id>"]`; timing lives
in `data-start` / `data-duration` / `data-track-index` on slots that carry
`class="clip"`. Keep to the determinism rules — no wall clocks, no unseeded
randomness, no render-time network fetches. Preview and render through the
HyperFrames CLI.

Write a one-scene timing plan and run
`python3 tools/render_hyperframes_video.py index.html timing.json --out <project-dir>`.
The adapter prepares HyperFrames and FFmpeg, renders the HTML composition,
packages captions and audio, and copies source assets. Set
`audio_from_visual: true` with a transcript for embedded audio, or supply
`narration` to replace it.

Draw from [objects](references/objects.md). **Zoom in on form filling and typing**, keep the
cursor visible, and pair the moment with `typing`, `click`, `alert` and `success`
SFX. Highlight the hook phrase as it appears. One concept per scene. Generate any
narration with [voice](references/voice.md) and let it run in the background while the visuals
are built — it is the timing master. The standalone skill ships
`tools/kokoro/start.py` for local narration.

With stills alone, describe the result as a **screenshot-based product demo**
rather than live captured interaction.

## 5. Review the real output

Inspect the opening, each product screen, transitions and the final CTA at the
target size. Confirm every claim matches the brief, every screenshot is genuine
and readable, private information is hidden, captions match final audio, music
does not mask speech, and the video still communicates when muted. Check logo,
URL, offer and brand consistency. Record any unverified claim left out and any
render limitation. Keep source screenshot filenames and their use in the asset
manifest so the owner can replace a screen later.

Export `captions.srt` and `captions.vtt` from final audio or reviewed video
timing. Save measured absolute-time cues as `captions.json` with
`duration_sec` (final video duration) and a `cues` array of `{ "start": seconds, "end": seconds,
"text": string }`, then run
`python tools/write_subtitles.py captions.json --out captions`. Check both
subtitle files against the final MP4 after any timing edit. Do not use estimated
storyboard durations as proof of speech alignment.
For spoken audio without reviewed word cues, run
`python3 tools/transcribe_captions.py <project-dir>/video.mp4 --out <project-dir> --language <code>`
after the final mix. Review its word-level transcript against the actual speech
and revise wrong words before delivery; rerun after audio changes.

If the renderer produces separate scene files, write a scene plan and run
`python3 tools/assemble_video.py plan.json --out <project-dir>`. Point each
`visual` to a rendered image or clip; supply `narration` and transcript text in
`caption`, or set `audio_from_visual: true` with a transcript for footage sound.
Use reviewed scene-relative `cues` where one caption per scene is too coarse.
The assembler exports a 1080p delivery MP4, optional mixed-audio MP3, imported
assets, and timed captions; review the final picture and timing before delivery.
Retain a separate 4K master when required and export the reusable voiceover
MP3/WAV through [voice](references/voice.md). Keep the renderer's editable source project
alongside this package.
For a music bed, add plan-level `music: {"file": "audio/bed.wav", "volume": 0.12}`
and listen to the final mix under speech; the assembler does not auto-duck it.

**Deliver three outputs** — see [video](references/video.md) §14. The **video** (MP4 at the master
resolution, downscaled to delivery), the **audio** (the voiceover as MP3,
converted from the verified WAV), and the **voiceover text** (timed SRT, or plain
TXT when only the read is needed).

Keep `product-brief.md`, `script.md`, `storyboard.md`, `style.md`,
`assets/manifest.json`, `captions.json`, `captions.srt`, `captions.vtt`, the MP3
and voiceover text, the renderer's editable source project and the rendered MP4
together so later edits can be made selectively.





## Optional generated illustrations

Read [generated-assets](references/generated-assets.md) when generating supporting scene images. Keep the
verified image and its provider/model/prompt metadata with the editable project.

## Standalone output

Keep the project in a named `videos/{product-slug}/` folder, or the location the
requester chose. Preserve original screenshots separately from redacted or
cropped working copies so edits remain reversible. Read the sibling
[workflow](references/workflow.md) for the full production sequence.
