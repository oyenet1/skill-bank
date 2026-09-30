# Video skills and desktop integration audit

This describes the current worktree, including the sibling Tauri app at
`/home/fade/Projects/js/devmock`. The app now has one real local render route;
the broader skill execution pipeline remains unfinished.

## Current skill workflow

1. Select `explainer-video` for an authored lesson, `product-launch-video` for
   an ad, `talking-head-video` for existing footage, or `avatar-video` for a
   provider-generated presenter. `course-creator` selects these as nested
   subskills when a course needs them.
2. Shared intake resolves brand, video category, platform, aspect, audio mode,
   ending, and required assets. A real product demo needs real screens.
3. Preflight calls the bundled `tools/ensure_video_runtime.py` for Slidev,
   Remotion or HyperFrames, Chromium, Node, FFmpeg and FFprobe. It installs missing tools in a
   private user data directory and returns executable paths as JSON. Kokoro's
   cross-platform `start.py` installs missing `uv` locally, creates a Python environment,
   installs packages, and verifies model files.
4. The agent writes `style.md`, `script.md`, and a timed `storyboard.md`.
5. `explainer-video` uses Slidev for motion graphics and lessons; screenshot
   demos and launch ads use Remotion or HyperFrames. The explainer skill now
   ships `tools/render_slidev_video.py` to export and time Slidev click states;
   continuous motion still needs browser recording. The shipped
   `tools/assemble_video.py` joins rendered scene files, narration or source
   footage audio, optional background music, and reviewed captions into a
   portable MP4 package.
6. Voice is generated or supplied, then visuals and sound are assembled into
   MP4. `tools/run_video_job.py` now gives the desktop host one request command
   with JSON progress, verification, cancellation and retry; the app has not
   yet invoked it. The final audio and picture are inspected.
7. The video skills require `captions.json`, `captions.srt`, and
   `captions.vtt`. `tools/write_subtitles.py` validates measured cues;
   `tools/transcribe_captions.py` uses local HyperFrames ASR on final media,
   groups measured words, and writes all caption files for review.

## Gaps found in this worktree

| Area | Current evidence | Required implementation |
|---|---|---|
| Skill install | Each video route ships `runtime_requirements.json` and `ensure_video_runtime.py`; `scripts/install_video_skill.py` copies and prepares a skill immediately and can resume failed setup with `--resume`. Every route declared to use Kokoro now ships its bootstrap files. `npx skills add` itself has no install hook. | Call setup on first use for installs made through generic skill managers, and from the desktop app's setup phase. |
| Preflight | The bundled setup reports JSON status and executable paths and now checks the installed Remotion/HyperFrames browser instead of trusting a marker. The desktop app has a native Tauri setup command with progress and cancellation, but uses its own older manifest and checks. | Bring the desktop runtime setup into parity and verify managed Node/browser installation on every supported platform. |
| Voice | Kokoro's Python entry point now bootstraps `uv`/Python/packages and verifies pinned model files on Windows, macOS, and Linux; voice skill asks for WAV. | Show model download progress in the desktop UI and handle unsupported languages before job start. |
| Hosted avatar provider | The avatar installer checks native HeyGen CLI first, then WSL on Windows, and verifies authentication after local setup; the CLI is absent on this machine. | Provide an attended install/auth step in the desktop host, and keep the local script/voice/storyboard fallback available. |
| Subtitle timing | Final-media local ASR now produces word-timed cues and SRT/VTT/JSON with a review flag. The bridge and cue grouping are tested with an encoded audio file; live ASR model download and recognition are not verified in this sandbox. | Add supplied-script forced alignment and a desktop review/editor flow; verify first-use ASR model setup on supported systems. |
| Rendering | A deterministic FFmpeg scene assembler and Slidev/Remotion/HyperFrames adapters ship with the video skills. A job runner now stages output, relays JSON progress, verifies media, stops active child processes on cancellation, and resumes after subtitle failures. | Run live end-to-end renderer checks in the desktop host and wire its cancel control to the runner. |
| Desktop | `devmock/src-tauri/src/video_project.rs` writes MP4 projects; Video Studio can use a provider model or a local template for script/storyboard drafting | Add full Slidev/Remotion or HyperFrames render adapters and model output review beyond scene editing. |
| Existing native tooling | `devmock/src-tauri/src/lib.rs` exposes FFmpeg and Kokoro model status/install | The first route automatically installs missing FFmpeg and voice model on Run; add a common dependency manifest for all skill routes. |
| Assets | The form accepts PNG/JPEG/WebP images, per-scene narration, and MP4/WebM/MOV footage; originals are preserved. Each storyboard scene now chooses an uploaded image or a text card, and the project records that source index. | Add source URL/licence review where assets are fetched online, plus visual inspection of every composed scene. |
| Timing | The first desktop route times each caption to a synthesized scene WAV or a silent scene; skill-level ASR can re-caption final media. | Wire final-media transcription and transcript review into the desktop job. |

## Desktop parity pending

The skill runtime manifest now includes HyperFrames 0.8.93 as a renderer for
explainer and product launch video. The sibling app's
`src-tauri/src/video_runtime_requirements.json` still lists only Slidev and
Remotion, and `src-tauri/src/video_runtime.rs` has renderer-specific handling
only for those two. The app needs the HyperFrames package, CLI readiness check,
browser setup, and route option wired through its native setup path. Its current
`video_project.rs` route produces static card scenes rather than running
Slidev, Remotion, or HyperFrames source. The skill-level scene assembler is a
separate, verified delivery step and does not close that adapter gap.

A reviewable [HyperFrames runtime patch](patches/devmock-hyperframes-runtime.patch)
applies to the current `devmock` checkout and passes `git apply --check` and
Rust formatting checks. It has not been applied because the sibling checkout is
read-only in this workspace. The patch prepares the additional renderer; it
does not yet connect the Python video job runner to the app's Render action.

The Remotion adapter has a verified render-to-package handoff with an encoded
test clip. A live Remotion CLI smoke test in this workspace reached Chromium,
but Chromium exited with `SIGTRAP` after the sandbox denied a socket operation.
The HyperFrames adapter has the same encoded-clip handoff check; its local CLI
smoke test stopped at browser availability in this sandbox. Both CLI renders
still need smoke tests in the desktop app's normal runtime environment.

## Desktop job contract

The app should store each job under an app data `projects/<job-id>/` directory.
The form writes `request.json` with category, platform, duration, language,
voice/audio mode, branding, claim sources, chosen inputs, and output folder. A
Tauri command starts one job and returns its ID. Progress events should include
`jobId`, `phase`, `step`, `percent`, `message`, and artifact paths only after
those files exist. Use phases in this order:

`validate → setup → import → research/assets → script → storyboard → audio → timing → visuals → render → subtitles → quality-check → complete`

The final manifest should record `script.md`, `style.md`, `storyboard.md`,
asset files and their sources, narration WAV, caption cue JSON, SRT, VTT,
editable renderer source, and MP4. Verify each file, media duration, and stream
before reporting completion. On failure keep the workspace and logs so a job
can resume from the last valid phase. Cancellation must stop child processes.

## Dependency setup boundary

Dependency installation belongs to the desktop host or the bundled first-use
installer, since these skills are instruction files rather than executable
packages. The bundled installer now reads one manifest for the selected route,
checks versions, installs missing runtimes to a private user data directory,
and verifies binaries. The desktop host now has a matching native setup command
and a manual **Prepare tools** action; the renderer adapter still needs to call
setup as part of its job before Run. Keep optional engines separate:
Slidev/Playwright for graphics, Remotion or HyperFrames for product video, Kokoro for local
English speech, and FFmpeg/ffprobe for output inspection and muxing. Setup must
show download size, network progress, license/model requirements, and a clear
error for unsupported OS/architecture. Avoid global `npm`/`pip` installs.

The first local slice now takes a reviewed storyboard, optional uploaded images,
per-scene narration files, per-scene footage, and optional local English/French/Spanish voice. It installs FFmpeg and the voice
pack on demand, writes `project.json`, the script, storyboard, style, original
and rendered assets, per-scene WAV files, timed SRT/VTT, and a real MP4. Rust
tests render and probe a two-scene project. The scene cards are static with cuts,
and the plan can be drafted through the existing AI provider connection or a
local template. The next step is the richer renderer adapters, automated
asset generation, and word-level timing for uploaded audio/video.
