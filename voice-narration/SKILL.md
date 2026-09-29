---
name: voice-narration
description: Create optional course narration from an existing or newly requested script using Kokoro TTS. Use when a teacher requests synthetic speech, with or without slides or video.
---

# Course TTS

Accept a teacher script, or write one from a lesson or concept when requested. Produce editable UTF-8 text and a WAV only. A teacher recording takes priority when the request is to use that recording. Narration can stand alone; do not make slides, captions, or video as a side effect.

Read [the bundled Kokoro tool guide](tools/kokoro/README.md) and run its local `start.sh` with `--text-file`, `--out`, and an available `--voice`. The first run prepares its environment and models. Check current official Kokoro ONNX documentation when API behavior matters. Do not claim a WAV exists until generation succeeds; inspect its duration, silence, clipping, and pronunciation. Split a long lesson by storyboard beat when later timing or edits matter.

For a mapped course, save files under `lessons/{lesson-id}/audio/`, register `narrationText` and `narrationAudio` in `artifacts`, and set `artifactSources.narrationAudio` to `["narrationText"]`. After a script edit, mark its audio stale and mark a video stale only if that video uses the audio. For a standalone request, use the output directory chosen by the teacher.
