# Optional Kokoro Narration

Text, slides, TTS audio, and video can each be requested alone or combined. Use this reference only when the teacher asks for synthetic narration or specifically chooses Kokoro. A supplied teacher recording takes priority and requires no TTS generation.

## Inputs and output

- Accept a teacher-supplied plain-text script, or write a short narration script from the selected lesson or concept when asked. Keep the script as editable UTF-8 text and check names, technical terms, and pronunciation before synthesis.
- If a course exists, store script and WAV under `lessons/{lesson-id}/audio/`; for a standalone request, use the teacher's chosen output folder. Register course files as `narrationText` and `narrationAudio` artifacts in `course-plan.json`, with `artifactSources.narrationAudio` set to `["narrationText"]`. If the script changes, mark `narrationAudio` stale; mark a video stale too when it actually uses that audio.
- Prefer one file per storyboard beat or short scene when precise timing or later edits matter. Whole-lesson narration is acceptable when the teacher wants a single track. Keep the same beat IDs in the script list, Slidev storyboard, Remotion scene, and CapCut guide.

## Generate with the bundled tool

Read the [bundled Kokoro guide](../tools/kokoro/README.md) before use. The bundled `start.sh` prepares a local environment and models when missing; its native path runs on CPU. Use `--text-file`, `--out`, and an available `--voice` rather than passing a long script on the shell command line. For example, from `tools/kokoro/`:

```bash
./start.sh --text-file /absolute/path/to/narration.txt --out /absolute/path/to/narration.wav --voice af_bella
```

The local `kokoro-onnx` API accepts voice, speed, and language and writes WAV samples; check the [official Kokoro ONNX API](https://github.com/thewh1teagle/kokoro-onnx) for current behavior. After synthesis, listen to the actual WAV, check duration, silence, pronunciation, and clipping, and regenerate only the affected beat if needed. Derive scene and caption timings from the resulting audio; a text script by itself has no exact timestamps.

If setup or synthesis fails, keep the script and report the specific missing dependency or model. Do not claim an audio file or synchronized captions exist unless verified. Do not start model downloads or TTS for text-only lessons, slide-only requests, or videos using teacher-supplied audio.
