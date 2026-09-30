# Video job command for desktop hosts

The four video skills ship `tools/run_video_job.py`. It accepts a request JSON,
prepares the selected renderer, packages a verified MP4, and optionally times
captions from the final audio. Relative paths resolve beside the request file.
The request itself and the editable renderer source are kept with the project.

```json
{
  "schemaVersion": 1,
  "route": "explainer-video",
  "renderer": "scenes",
  "timing": "timing.json",
  "output": "videos/my-explainer",
  "captions": "auto",
  "language": "en"
}
```

`renderer` can be `scenes`, `slidev`, `remotion`, or `hyperframes`, as allowed
by the route's runtime manifest. `timing.json` uses the
[scene assembly plan](video-assembly.md). For `scenes`, the timing plan provides
each scene's `visual`. Other renderers supply those visuals from a source:

| Renderer | Additional request fields | Timing scenes |
|---|---|---|
| `slidev` | `source`: Slidev `.md` deck | One per exported click state |
| `remotion` | `source`: entry TS/TSX; `compositionId`; optional `projectRoot`, `props` | Exactly one for the composition |
| `hyperframes` | `source`: HTML composition; optional `projectRoot`, `variables` | Exactly one for the composition |

Set `captions` to `auto` (default), `plan`, or `transcribe`. `auto` transcribes
when a scene declares narration or footage audio; otherwise it uses the plan's
cues. `transcribe` always uses local ASR on the final MP4. `plan` keeps supplied
cues, including captions for a genuinely silent video. The transcription model
defaults to English `small.en`, or multilingual `large-v3` when `language` is
non-English. `transcriptionModel` overrides that choice. Local ASR may download
its model on first use and always marks the captions for review.

Run the command from an installed video skill:

```bash
python3 tools/run_video_job.py request.json
python3 tools/run_video_job.py request.json --resume
```

Standard error emits one JSON progress object per line with `phase` and
`message`, plus stage details such as `durationSec`. Standard output emits one
JSON result. A successful render with ASR returns `status: "review_required"`;
the desktop UI should open the transcript and captions for review before it
marks the project approved. `status: "complete"` means all automated stages
finished with plan cues. Neither status replaces visual and claim review.

The command writes `<output>.job-state.json` beside the project. Failed render
attempts remain as `<output>.work-<id>` folders, with a render log beside them;
the final output directory is published only after its video and manifest pass
media inspection. If subtitles fail later, `--resume` reuses the verified MP4
and retries subtitles. A completed project is reused without overwriting
reviewed captions. The state stores a SHA-256 hash of the final MP4 to detect
changes that would invalidate timing. Send SIGTERM to cancel; on POSIX the
runner stops the active process group, and on Windows it uses `taskkill /T`.

The Tauri app still needs to spawn this command from its job host, pass its form
and upload paths, relay progress events to Video Studio, and expose transcript
review. The sibling app is outside this repo's writable workspace in the
current session, so this contract is not yet wired into the app.

`tools/run_desktop_video_job.py` now accepts Video Studio's existing form
payload as `{ "schemaVersion": 1, "request": { ... } }`. It imports the
base64 media into safe assigned filenames and invokes the shared runner:

```sh
python3 tools/run_desktop_video_job.py desktop-request.json --workspace projects/job-123
python3 tools/run_desktop_video_job.py desktop-request.json --workspace projects/job-123 --resume
```

The result includes the desktop fields `script`, `storyboard`, `narration`,
`captionsSrt`, `captionsVtt`, `mixedAudio`, `transcript`, `sizeBytes`, and
`reviewRequired`. The prepared [Tauri source patch](../integrations/devmock/README.md)
bundles this tool and its dependencies, prepares Python privately, and connects
it to the existing form. Application and platform verification remain pending.
