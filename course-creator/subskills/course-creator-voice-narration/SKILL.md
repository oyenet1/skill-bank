---
name: course-creator-voice-narration
description: Produce optional Kokoro WAV narration from a teacher script or a selected course lesson inside the course-creator bundle. Registers the script and audio as lesson artifacts and marks dependent outputs stale after an edit.
---

# Voice Narration

## Automatic first-use setup

Before production, run the bundled launcher with `--yes`; it detects the host, prepares private runtimes, and installs the declared sibling dependency graph. Do not ask the requester to install packages manually.

- Linux/macOS: `sh ../../tools/setup.sh --yes`
- Windows: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ../../tools/setup.ps1 --yes`

Use `--check` for a read-only readiness check. If prerequisites are missing, rerun setup. Follow the returned `pythonExecutable` and runtime paths for later commands. Model-license acceptance, image rights and account credentials remain explicit inputs.

Turn any supplied script into editable UTF-8 text and one WAV. Accept a script
as given, or write one from a brief when asked. A supplied recording always wins
when the request is to use that recording. Narration stands alone: never produce
slides, captions or video as a side effect.

## Short prompt alias

When a submitted request begins with `/narration`, treat the following text as the
brief for this skill. Follow the clarification breakpoint below before dependent
production. A host may require a native command adapter to deliver slash input.

## Clarify before production

Read [intake](references/intake.md) before starting. If missing or ambiguous inputs would change
the result, ask a concise batch of questions and wait for answers. Offer
recommended choices; apply them only when the requester selects them or
explicitly asks you to choose. Use details already supplied rather than asking
again. Continue directly when the brief is complete.

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

Read the bundled tool guide at ../../tools/kokoro/README.md and run its local
`start.py` with `--text-file`, `--out path/to/narration.wav` and an available `--voice`. The first run
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





## Course integration

Read the [narration workflow](../../references/narration.md) for beat splitting and
timing conventions. Save under `lessons/{lesson-id}/audio/`. Register
`narrationText` and `narrationAudio` in that lesson's `artifacts`, with
`artifactSources.narrationAudio` set to `["narrationText"]`.

After a script edit, mark its audio stale — and mark a video stale only if that
video uses the audio. Keep teacher-written material intact.
