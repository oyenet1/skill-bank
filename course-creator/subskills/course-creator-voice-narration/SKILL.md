---
name: course-creator-voice-narration
description: Produce optional Kokoro WAV narration from a teacher script or selected course lesson within the course-creator bundle.
---

# Course TTS

Read the [narration workflow](../../references/narration.md) and [bundled Kokoro tool guide](../../tools/kokoro/README.md). Accept a supplied script or write one when requested. Keep editable UTF-8 text, run Kokoro only when synthetic speech was requested, and inspect the actual WAV for duration, silence, clipping, and pronunciation. Prefer short scene tracks when later timing edits matter.

Register `narrationText` and `narrationAudio` under the lesson's artifacts, with `artifactSources.narrationAudio` pointing to `narrationText`. Mark any video using changed audio stale. A TTS request does not create slides or video; supplied teacher audio takes priority when the teacher wants that recording used.
