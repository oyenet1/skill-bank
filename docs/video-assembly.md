# Assemble rendered video scenes

`tools/assemble_video.py` is shipped with `explainer-video` and
`product-launch-video`. It packages scenes already rendered by Slidev, Remotion,
HyperFrames, a screen recorder, or another renderer. It does not author motion,
record a browser, synthesize speech, align words, or verify claims.

Prepare `plan.json` next to the files it names:

```json
{
  "title": "A short explainer",
  "aspect": "16:9",
  "fps": 30,
  "music": {"file": "audio/bed.wav", "volume": 0.12},
  "scenes": [
    {
      "id": "hook",
      "visual": "frames/hook.png",
      "duration_sec": 2.5,
      "narration": "audio/hook.wav",
      "caption": "A better opening"
    },
    {
      "id": "demo",
      "visual": "clips/demo.mp4",
      "audio_from_visual": true,
      "duration_sec": 4,
      "cues": [
        {"start": 0.2, "end": 1.5, "text": "Open the project"},
        {"start": 1.7, "end": 3.6, "text": "Then choose a scene"}
      ]
    }
  ]
}
```

Run from the skill directory:

```bash
python3 tools/ensure_video_runtime.py explainer-video --renderer slidev
python3 tools/assemble_video.py plan.json --out videos/a-short-explainer
```

Use the FFmpeg and FFprobe paths returned by preflight with `--ffmpeg` and
`--ffprobe` when they are not on `PATH`. The output directory must be empty.
Progress is JSON on standard error and the result is JSON on standard output.
The tool writes `video.mp4`, `manifest.json`, `project.json`, `script.md`,
`storyboard.md`, imported `assets/`, `segments/`, `logs/`, and captions in
JSON, SRT and VTT. An MP3 of the final video's audio is written if a scene has
narration, source footage audio, or a music bed. A project with none of these
has no audio stream or MP3 export. The optional music file loops across the
video at the specified linear volume (above 0 and at most 1); set that level by
listening under speech, since this tool does not automatically duck it. This MP3
is the **mixed final track**. Export a separate reusable voiceover MP3 and WAV
from the narration workflow.

`visual` accepts PNG, JPEG, WebP, MP4, MOV, WebM and MKV. Each scene needs a
positive duration, measured narration, or measurable video duration. Narration
and `audio_from_visual` are mutually exclusive. Provide `caption` or reviewed
scene-relative `cues` for every audible scene. A plain `caption` spans its scene
or measured narration duration, so use `cues` when speech has pauses or several
phrases. The assembler offsets those cues against measured encoded segment
durations. Review the final MP4 and captions together before delivery.

Output is H.264 at 1080p delivery size for the selected aspect. If a 4K master
is required, retain the renderer's original master separately; the assembler
does not create a 4K master. Keep the renderer's editable source in the project
alongside the packaged output.

## From a Slidev deck

The explainer skill also ships `tools/render_slidev_video.py`. Write a timing
JSON using the same plan shape, with one `scenes` entry for each PNG that
`slidev export --with-clicks --format png` will produce. Omit `visual` in those
entries; the adapter assigns exported click states in order. Narration paths
and the optional music path are relative to the timing JSON.

```bash
python3 tools/render_slidev_video.py slides.md timing.json --out videos/slidev-explainer
```

The adapter prepares the Slidev runtime on first use, exports PNGs, invokes the
assembler, and copies the deck and its `public/` assets into `source/`. It
checks the exported frame count against the timing plan. Its `*.slidev-export.log`
file remains beside the requested output even if export fails. Click states are
held frames; continuous `v-motion` easing needs a browser recording instead.

## From a Remotion composition

Both video skills ship `tools/render_remotion_video.py`. Give it a Remotion entry
file, a registered composition ID, and a timing JSON with exactly one `scenes`
entry. The composition provides the visual and its measured duration, so omit
`visual` and usually `duration_sec`. Put its transcript in `caption` or timed
`cues` when using the composition's own audio.

```bash
python3 tools/render_remotion_video.py src/index.ts LaunchAd timing.json \
  --out videos/launch-ad --project-root .
```

The adapter prepares the managed Remotion CLI, renders to MP4, then uses the
assembler for delivery video, optional audio, and captions. It copies the
editable project into `source/`, excluding build caches and `node_modules`.
If the rendered composition already contains audio, set
`audio_from_visual: true` with transcript text or supply `narration` to replace it. The adapter
stops when that choice is missing. Pass `--props props.json` for composition
input props. A `*.remotion-render.log` file remains beside the output on
render failure.

## From a HyperFrames composition

Both video skills ship `tools/render_hyperframes_video.py`. Give it an HTML
composition and a timing JSON with exactly one `scenes` entry. The composition
supplies the visual and its measured duration. Pass `--project-root` if its
assets live above the composition's folder.

```bash
python3 tools/render_hyperframes_video.py index.html timing.json \
  --out videos/launch-ad --project-root .
```

The adapter prepares the managed HyperFrames CLI, renders an MP4, packages
optional audio and timed captions, and copies the HTML project into `source/`.
Use `audio_from_visual: true` with transcript text to retain composition audio,
or supply `narration` to replace it. Pass `--variables vars.json` for variable
overrides. A `*.hyperframes-render.log` file remains beside the output if
rendering fails.

## Time captions to final speech

When a project has speech, run the local transcription bridge on its **final**
video after all narration and music edits:

```bash
python3 tools/transcribe_captions.py videos/launch-ad/video.mp4 \
  --out videos/launch-ad --language en
```

It prepares HyperFrames, transcribes audio locally, groups measured word times
into readable cues, and writes `transcript.json`, `captions.json`,
`captions.srt`, and `captions.vtt`. It marks the caption JSON for review because
speech recognition can mishear words. For non-English speech, the bridge chooses
the multilingual `large-v3` model; first use can download several gigabytes.
Correct the transcript and captions against the actual spoken audio before
delivery. Rerun after any final-audio change. Silent and music-only videos do
not need ASR.
