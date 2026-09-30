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
defaults to English `small.en`, or multilingual `small` when `language` is
non-English or unspecified. `transcriptionModel` overrides that choice. Local ASR may download
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

The Tauri source now spawns this command through its job host, passes form and
uploaded media, relays progress to Video Studio, and exposes caption review.
Native desktop execution still needs verification; no app build has been run.

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

## Local presenter pre-generation

For `route: "avatar-video"`, a scene or authored storyboard job may add:

```json
{
  "avatar": {
    "provider": "local",
    "mode": "photo",
    "backend": "musetalk-15",
    "image": "inputs/portrait.png",
    "rightsConfirmed": true
  }
}
```

The portrait path is relative to the job request. Each timing scene must include
narration and transcript. This stage installs nothing: prepare and explicitly
accept a compatible backend using `avatar_ensure.py` first. `SKILL_BANK_AVATAR_HOME`
selects the shared avatar runtime. Local avatar/dub modes are explicitly unsupported.

Before generation, `inputs/avatar-fallback/` receives actual script, verified WAV
and MP3, and storyboard. Failed/cancelled inference retains these plus work logs;
there is no fabricated presenter MP4. Successful clips replace scene visuals while
narration stays separate and generated footage audio is muted. Authored projects
are refreshed with real footage; the original source is retained. Rendering and
final caption review use their established contracts.

State and final manifest `avatar` entries record provider, backend, accelerator,
revision, manifest hash, licence consent, image-rights confirmation, input hash,
verified video hash and elapsed time. Original request resume reuses verified
clips. Backend errors report the blocked step, fallback directory and retry path.

## Optional generated scene illustrations

Devmock can call `video_skill_generate_image` before preparing scene cards and
narration. This command runs `generate_image_asset.py` in managed Python and
returns a verified PNG plus public provenance. Prompts use the explicitly selected
OpenAI image model and quality. The credential is an IPC argument/private child
environment value; it is never saved in asset requests, provenance, or projects.
The hosted provider may keep processing after local cancellation.

Images are cached by model, quality, size and prompt under `<app-data>/asset-jobs`.
Matching verified results are reused before another network request. Generated
images enter `sourceAssets` as normal PNGs with `provenance` containing provider,
model, prompt, size, quality, creation time, SHA-256 and terms URL. The importer
verifies that checksum and exports a public-field allowlist. The final manifest
has `assetSources` and `assetReviewRequired`; caption approval does not clear the
separate image/rights review requirement. Product screens and presenter portraits
must come from the requester.
