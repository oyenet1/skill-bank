---
name: voice-narration
description: Generate clean WAV narration from any supplied script using local Kokoro TTS. Works for courses, podcasts, ads, walkthroughs, or any text. Accepts a script or writes one from a brief, asks for language, accent and voice, and verifies the audio before claiming it exists. Use when the deliverable is synthetic speech rather than slides or video.
---

# Voice Narration

Turn any supplied script into editable UTF-8 text and one WAV. Accept a script
as given, or write one from a brief when asked. A supplied recording always wins
when the request is to use that recording. Narration stands alone: never produce
slides, captions or video as a side effect.

## 1. Intake

Read [intake](references/intake.md) first. Then resolve the voice in this order — language
first, because it constrains everything after it. Full rules in [voice](references/voice.md).

1. **Language** — ask, or take it from the script. Confirm the language has a
   Kokoro voice before promising it.
2. **Accent** — ask only when the language is English: American or British.
3. **Voice** — female, male, or the requester's own recording. If they have a
   recorded voiceover, **do not synthesise** — use it as the timing master.

Default voice comes from [brand](references/brand.md) → `Voice and tone` → `Preferred TTS voice`
when a `brand.md` exists. Always name the chosen voice in the working brief so
the result is reproducible.

## 2. Generate

Read the bundled tool guide at tools/kokoro/README.md and run its local
`start.sh` with `--text-file`, `--out` and an available `--voice`. The first run
prepares its environment and models. Check current official Kokoro ONNX
documentation when API behaviour matters.

Produce editable UTF-8 text and a WAV. Do not claim a WAV exists until generation
succeeds.

## 3. Verify

Inspect the actual file before reporting it:

- duration matches the intended read length
- no long silence at either end
- no clipping
- names and technical terms pronounced correctly

Split a long read by storyboard beat when later timing or edits matter. When the
output feeds a video, generate the audio **first** and let it run while visuals
are authored — its beat lengths drive scene durations.

## 4. Report

State the voice used, the duration, the output paths, and anything that could
not be verified. If generation failed, say exactly what failed rather than
reporting a partial success.

## Output location

Use the directory the requester names. With no preference, write beside the
source script. If a `course-plan.json` is present and the requester points at a
mapped lesson, register `narrationText` and `narrationAudio` under that lesson's
`artifacts` and set `artifactSources.narrationAudio` to `["narrationText"]`;
 otherwise use a plain output folder.
