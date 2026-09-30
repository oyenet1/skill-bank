---
name: motion-graphics-video
description: 'Generate editable motion graphics videos: kinetic typography, animated diagrams, charts, process flows, logo reveals, titles and visual concept explanations. Use for animation-led videos from a brief or script, with optional narration.'
---

# Motion Graphics Video

## Automatic first-use setup

Before production, run the bundled launcher with `--yes`; it detects the host, prepares private runtimes, and installs the declared sibling dependency graph. Do not ask the requester to install packages manually.

- Linux/macOS: `sh tools/setup.sh --yes`
- Windows: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/setup.ps1 --yes`

Use `--check` for a read-only readiness check. If prerequisites are missing, rerun setup. Follow the returned `pythonExecutable` and runtime paths for later commands. Model-license acceptance, image rights and account credentials remain explicit inputs.

Turn a brief, script or verified data into an animation-led video. Motion should
explain relationships, sequence, emphasis or change. Deliver an actual rendered
MP4 and editable source when the runtime works; report failures explicitly.

## Resolve the brief

Read [intake](references/intake.md) and [brand](references/brand.md). Capture purpose, audience, platform,
duration, aspect ratio, key message and audio mode. Use the shared 30-second
fallback for optional choices when the host supports it. For a course segment,
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
illustrations help. Real product UI stays in `product-launch-video`;
an extended lesson walkthrough can use `explainer-video`.

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


