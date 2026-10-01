---
standalone:
  name: voice-narration
  description: >-
    Handles /narration prompts delivered by the host.
    Generate clean WAV narration from any supplied script using local Kokoro TTS.
    Works for courses, podcasts, ads, walkthroughs, or any text. Accepts a script
    or writes one from a brief, asks for language, accent and voice, and verifies
    the audio before claiming it exists. Use when the deliverable is synthetic
    speech rather than slides or video.
bundle:
  name: course-creator-voice-narration
  description: >-
    Produce optional Kokoro WAV narration from a teacher script or a selected
    course lesson inside the course-creator bundle. Registers the script and
    audio as lesson artifacts and marks dependent outputs stale after an edit.
---

# Voice Narration

Turn any supplied script into editable UTF-8 text and one WAV. Accept a script
as given, or write one from a brief when asked. A supplied recording always wins
when the request is to use that recording. Narration stands alone: never produce
slides, captions or video as a side effect.

## Short prompt alias

When a submitted request begins with `/narration`, treat the following text as the
brief for this skill. Follow the clarification breakpoint below before dependent
production. A host may require a native command adapter to deliver slash input.

## Clarify before production

Read {{ref:intake}} before starting. If missing or ambiguous inputs would change
the result, ask a concise batch of questions and wait for answers. Offer
recommended choices; apply them only when the requester selects them or
explicitly asks you to choose. Use details already supplied rather than asking
again. Continue directly when the brief is complete.

## 1. Intake

Read {{ref:intake}} first. Then resolve the voice in this order — language
first, because it constrains everything after it. Full rules in {{ref:voice}}.

1. **Language** — ask, or take it from the script. Confirm the language has a
   Kokoro voice before promising it.
2. **Accent** — ask only when the language is English: American or British.
3. **Voice** — female, male, or the requester's own recording. If they have a
   recorded voiceover, **do not synthesise** — use it as the timing master.

Default voice comes from {{ref:brand}} → `Voice and tone` → `Preferred TTS voice`
when a `brand.md` exists. Always name the chosen voice in the working brief so
the result is reproducible.

## 2. Generate

Read the bundled tool guide at {{asset:tools/kokoro/README.md}} and run its local
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

{{mode:bundle}}
## Course integration

Read the {{doc:narration.md|narration workflow}} for beat splitting and
timing conventions. Save under `lessons/{lesson-id}/audio/`. Register
`narrationText` and `narrationAudio` in that lesson's `artifacts`, with
`artifactSources.narrationAudio` set to `["narrationText"]`.

After a script edit, mark its audio stale — and mark a video stale only if that
video uses the audio. Keep teacher-written material intact.
{{/mode}}

{{mode:standalone}}
## Output location

Use the directory the requester names. With no preference, write beside the
source script. If a `course-plan.json` is present and the requester points at a
mapped lesson, register `narrationText` and `narrationAudio` under that lesson's
`artifacts` and set `artifactSources.narrationAudio` to `["narrationText"]`;
 otherwise use a plain output folder.
{{/mode}}
