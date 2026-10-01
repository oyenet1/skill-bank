---
name: course-creator-motion-graphics-video
description: Create animated lesson diagrams, process flows, chapter titles and concept explanations within course-creator, sharing course style and lesson IDs.
---

# Motion Graphics Video

## Automatic first-use setup

Before production, run the bundled launcher with `--yes`; it detects the host, prepares private runtimes, and installs the declared sibling dependency graph. Do not ask the requester to install packages manually.

- Linux/macOS: `sh ../../tools/setup.sh --yes`
- Windows: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ../../tools/setup.ps1 --yes`

Use `--check` for a read-only readiness check. If prerequisites are missing, rerun setup. Follow the returned `pythonExecutable` and runtime paths for later commands. Model-license acceptance, image rights and account credentials remain explicit inputs.

Turn a brief, script or verified data into an animation-led video. Motion should
explain relationships, sequence, emphasis or change. Deliver an actual rendered
MP4 and editable source when the runtime works; report failures explicitly.

## Social media output

Read [social-media](references/social-media.md) before producing audience-facing text or video.
Resolve the publishing platform and audience, keep the hook and payoff clear,
and verify mobile readability, captions and the chosen channel's format.
Ask for missing material choices at intake. Aim for shareability without
claiming guaranteed viral performance; preserve the requested teaching depth.

## Short prompt alias

When a submitted request begins with `/motion-graphics`, treat the following text as the
brief for this skill. Follow the clarification breakpoint below before dependent
production. A host may require a native command adapter to deliver slash input.

## Clarify before production

Read [intake](references/intake.md) before starting. If missing or ambiguous inputs would change
the result, ask a concise batch of questions and wait for answers. Offer
recommended choices; apply them only when the requester selects them or
explicitly asks you to choose. Use details already supplied rather than asking
again. Continue directly when the brief is complete.

## Resolve the brief

Read [intake](references/intake.md) and [brand](references/brand.md). Capture purpose, audience, platform,
duration, aspect ratio, key message and audio mode. Ask for missing deliverable-changing details and wait for answers before
planning or production, unless the requester delegates those choices. For a course segment,
inherit the lesson audience, learning objective and course style. For a standalone
brief, no course map is required. Do not invent brand details or data.

## Plan visual motion

Read [video](references/video.md) for delivery and audio guidance. Create `style.md`, `script.md`
and `storyboard.md` before authoring. Each beat records duration, copy, visual
source, motion purpose, entrance, readable hold, exit and transition.

Choose a useful treatment: typography for a headline; an animated diagram for
relationships; progressive steps for a process; an accurately scaled chart for
verified data; or a title/logo reveal using supplied brand assets. For education,
introduce one concept at a time, label moving parts, and pause long enough to
read the completed diagram. Keep illustrative examples explicitly labelled.
Use [objects](references/objects.md) for assets and [generated-assets](references/generated-assets.md) only when supporting
illustrations help. Real product UI stays in [course-creator-product-launch-video](../course-creator-product-launch-video/SKILL.md);
an extended lesson walkthrough can use [course-creator-explainer-video](../course-creator-explainer-video/SKILL.md).

## Author and render

Default to Remotion; use HyperFrames when requested or when HTML source better
fits the handoff. Reuse the existing renderer tools and runtime; there is no new
rendering engine. Read [preflight](references/preflight.md) and run the OS first-use launcher if
needed, then use the verified Python/executable paths:

```sh
python3 tools/ensure_video_runtime.py explainer-video --renderer remotion
```

For HyperFrames, use `--renderer hyperframes`. Author an editable timed
composition with deterministic frame-based motion or a seekable timeline.
Avoid random motion that changes between renders. Keep text within safe areas,
preserve chart scales, and use readable holds rather than constant movement.

Use the existing assembly timing contract in `tools/assemble_video.py`.
A one-scene example (the source composition owns its internal beats):

```json
{"title":"Motion graphics","aspect":"16:9","fps":30,"scenes":[{"id":"motion","duration_sec":15}]}
```

Check the tool's plan schema before rendering; add supplied narration/audio and
caption fields using that contract. Render and package with one of:

```sh
python3 tools/render_remotion_video.py src/index.ts MotionGraphics timing.json --out output
python3 tools/render_hyperframes_video.py index.html timing.json --out output
```

Read [voice](references/voice.md) only when narration is needed. Standalone narration uses the
bundled `tools/kokoro/start.py`; the course bundle uses its parent Kokoro tools.
Keep a supplied recording as the timing master. For spoken videos, transcribe
the finished mix with `tools/transcribe_captions.py` and review caption timing.
Silent graphics do not require speech captions.

## Review and deliver

Inspect the opening, midpoints and ending plus the complete video for clipping,
readability, timing, diagram meaning, accurate chart values and audio balance.
Verify the MP4 has the intended duration, dimensions and any requested audio.
Deliver the MP4, editable source and selected local assets, style, script,
storyboard and provenance; include narration and captions when requested.

Use the same stable lesson IDs and course style as the other course subskills.
Register the actual video/source paths in the lesson's course map artifact fields;
reuse approved text, diagrams and narration. Do not regenerate unrelated lessons.
