# Video skills and desktop integration audit

This describes the current worktree, including the sibling Tauri app at
`/home/fade/Projects/js/devmock`. The app now offers authored HyperFrames, Remotion, Slidev and scene-card
render routes, optional generated illustrations, and local photo presenters.
Hosted presenter authentication and native platform verification remain unfinished.

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
   MP4. `tools/run_video_job.py` gives the desktop host one request command with JSON
   progress, verification, cancellation and retry. The `devmock` app now invokes
   its desktop wrapper from Video Studio. The final audio and picture should be inspected.
7. The video skills require `captions.json`, `captions.srt`, and
   `captions.vtt`. `tools/write_subtitles.py` validates measured cues;
   `tools/transcribe_captions.py` reuses installed native Whisper or prepares
   managed CPU recognition on final media,
   groups measured words, and writes all caption files for review.

## Gaps found in this worktree

| Area | Current evidence | Required implementation |
|---|---|---|
| Skill install | Each video route ships `runtime_requirements.json`, `ensure_video_runtime.py`, and a cross-platform `bootstrap.py` with `setup.sh`/`setup.cmd`/`setup.ps1` and a generated `tools/dependencies.json`. The launcher detects OS/arch, prepares the private runtime, and installs missing associated skills from the bundled snapshot. `scripts/install_video_skill.py` copies and prepares one skill immediately and can resume failed setup with `--resume`. Every route declared to use Kokoro now ships its bootstrap files. `npx skills add` itself has no install hook, so first use runs the launcher. | Desktops continue to use their native setup phase; standalone skills use the bundled first-use bootstrap. |
| Preflight | The bundled setup reports JSON status and executable paths and now checks the installed Remotion/HyperFrames browser instead of trusting a marker. The desktop app now uses the shared renderer manifest, includes HyperFrames browser setup, and launches Windows npm tools through Node. | Verify managed Node/browser installation on every supported platform. |
| Voice | Kokoro's Python entry point now bootstraps `uv`/Python/packages and verifies pinned model files on Windows, macOS, and Linux; voice skill asks for WAV. | Show model download progress in the desktop UI and handle unsupported languages before job start. |
| Avatar provider | Dispatcher prefers verified local photo generation, then authenticated native HeyGen/Windows WSL, then editable fallback. Desktop local models require consent. | Verify actual GPU inference and hosted desktop authentication. |
| Subtitle timing | Final-media local ASR produces word-timed cues and SRT/VTT/JSON with a review flag. Video Studio includes an MP4 caption editor with editable cue text and timing; saves verify video and caption hashes. Managed first-use ASR succeeded on Linux with a short spoken sample; editor use is not verified in a built app. | Add supplied-script forced alignment and verify first-use ASR on supported systems. |
| Rendering | A deterministic FFmpeg scene assembler and Slidev/Remotion/HyperFrames adapters ship with the video skills. The desktop job runner stages output, relays JSON progress, verifies media, stops active child processes on cancellation, and resumes after subtitle failures. | Run live end-to-end renderer checks in the desktop host. |
| Desktop | Video Studio invokes the bundled job runner and caption review command; the Rust host provisions a private Python runtime and stores jobs in app data. | Verify the native desktop host and rendering on supported OSes; integrate provider-backed asset and avatar generation. |
| Existing native tooling | The app keeps its native FFmpeg and Kokoro setup paths; the job runner provisions its Python runtime automatically. | Verify first-use model handling and native tool setup on every supported platform. |
| Assets | The form accepts PNG/JPEG/WebP images, per-scene narration, and MP4/WebM/MOV footage; originals are preserved. Each storyboard scene now chooses an uploaded image or a text card, and the project records that source index. | Add source URL/licence review where assets are fetched online, plus visual inspection of every composed scene. |
| Timing | The desktop runner transcribes final media and the caption editor writes reviewed JSON, SRT, VTT, and transcript copies. | Add supplied-script forced alignment and verify editor round trips in the built app. |

## Desktop renderer setup and remaining integration

The native desktop setup now uses the same runtime requirements as the skills,
including HyperFrames for explainer, product, talking-head, and avatar routes.
It installs and checks the HyperFrames browser, launches Windows npm tools
through their declared JavaScript entry points, and stops the active process
tree when setup is cancelled. The shared Python installer and renderer adapters
use the same approach for Windows batch wrappers. Focused runtime checks cover
literal tool arguments with spaces and shell characters. These checks do not
prove native Windows or macOS execution.

Video Studio offers searchable visual workflow choices. The authored path
uses `author_desktop_video.py` to create editable scene source and
`render_desktop_sources.py` to render and assemble it with the original audio.
The source package includes local media and pinned renderer dependencies.
**On-screen text** is reviewed separately from visual production direction.
The final output retains the original uploads and narration alongside the
MP4, script, storyboard, timed captions, and optional MP3.

Live generated-source smoke renders succeeded for all three renderers in this
Linux workspace. An additional two-scene HyperFrames output retained narration
and footage audio. A separate short English spoken sample completed first-use managed ASR
setup and recognition from a rendered MP4, producing timed JSON/SRT/VTT with
a review flag. Other languages, native host use, and macOS/Windows execution
remain unverified. The
app source type check passed. No desktop app build was run.

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
packages. The bundled launcher now detects OS/arch and reads one manifest for
the selected route, checks versions, installs missing runtimes to a private user
data directory, verifies binaries, and installs missing associated sibling skills from the bundled snapshot.
The desktop host now has a matching native setup command and a manual
**Prepare tools** action. The authored renderer runner also
prepares the selected engine before rendering. Keep optional engines separate:
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
local template. Authored renderer adapters and final-media word timing are now connected.
Optional OpenAI scene image generation is connected; supplied-script forced
alignment and live provider/native verification remain to be added.

## Practical duration guidance

As an initial production target, use 30 seconds to 3 minutes for ads and short
explainers. For teaching, split longer material into 5 to 10 minute chapters.
These are workflow recommendations, not performance benchmarks. The current
assembler accepts projects up to 30 minutes; renderer costs, model downloads,
scene count, machine resources, and review effort still need longer-run
measurement before that ceiling can be recommended for regular use.

## Local photo presenter integration

The `prd/local-avatar-talking-head` source implementation is connected to Skill
Bank and devmock. The talking-head form exposes searchable backend selection,
licence/download consent, progress, cancellation, a portrait upload, and separate
image-rights confirmation. `video_skill_avatar_probe` returns installed state
and consent offers; `video_skill_avatar_install` requires the displayed manifest
token and explicit acceptance. A native, network-free probe works without Python;
only accepted installation may prepare private Python on a fresh host.

`avatar_ensure.py avatar-video --check` never installs. Accepted installation
creates a private backend environment, checks accelerator allocation, verifies
source and model hashes, and tests the MPS port with a three-second fixture.
The app's runtime is `<app-data>/avatar`; standalone skills use the platform
user-data `skill-bank/avatar` directory, overridable by `SKILL_BANK_AVATAR_HOME`.
Every generation runs in its pinned private interpreter with networking disabled.

Desktop requests carry `avatar: {provider: "local", mode: "photo", backend,
rightsConfirmed, image: {name, mime, dataBase64}}` and `jobRoute: "avatar-video"`.
Every scene needs local narration or uploaded audio. Pre-generation writes real
script, WAV, MP3 and storyboard fallback assets before inference, imports verified
presenter MP4s as muted footage, and retains original narration for one audio mix.
Existing renderer and caption-review contracts remain in use. Original inputs,
clip manifests, consent, accelerator and backend provenance are exported with the
editable project. Verified clips are reused when resuming the original request.

The standalone dispatcher prefers installed local photo generation, then
explicitly authenticated HeyGen, then editable fallback. Explicit unavailable
providers fail clearly. Hosted avatar/dub creation retains its attended CLI flow.
Use `avatar_provider.py --deliver-fallback OUT --script script.md --audio narration.wav`
to package actual local narration when a presenter cannot be generated.

38 unique model/configuration pins were verified against upstream metadata.
Dependency resolution passed for CUDA MuseTalk on Linux/Windows, its Python 3.11
MPS port on macOS arm64, and LatentSync on Linux/Windows. These checks are not GPU
inference certification. This host is AMD/ROCm and cannot run the supported
models. Real NVIDIA Windows/Linux and Apple Silicon inference and native app
execution still require verification. No desktop build was run.

### PRD licensing deviation

SadTalker is retained in `disabledBackends` because its pinned pack contains
Basel Face Model data restricted to internal noncommercial research/evaluation;
it cannot be advertised as a wholly permissive distributable backend. The MPS
smoke gate therefore reports an unavailable compatibility fallback instead of
installing SadTalker. A licensed replacement is required to close that PRD task.
See [upstream Basel Face Model terms](https://faces.dmi.unibas.ch/bfm/main.php?nav=1-2&id=downloads).

### Maintaining pins

Update model revision, file sizes, SHA-256, code archive digest, environment pins,
component licences and estimates together in `skills-src/_shared/tools/avatar_models.json`.
Run `avatar_pin.py --online`, perform target-platform dependency resolution and
inference checks, regenerate skills, and sync bundled tools into devmock. Changing
any backend metadata invalidates previous installation markers and consent tokens.
Never promote a research-only component via a permissive mirror repository label.

## Generated scene illustrations

Video Studio optionally generates an illustration for each scene without assigned
images or footage. The form exposes image model, searchable quality selection,
one-time OpenAI key or saved-key vault unlock. Render progress includes generation,
then local narration, authored visuals, assembly and subtitles. Product videos
still require real product screenshots/footage. Local portrait animation disables
scene illustration generation so its uploaded portrait remains the input.

The provider adapter publishes a valid PNG and provenance together, checks PNG
chunk checksums/encoding/dimensions, and caches immutable completed requests by
prompt/model/size/quality. It uses platform CA roots with explicit macOS Keychain
and Linux distro support, rejects authenticated redirects, keeps secrets out of
files, and reports failures without publishing a fake asset. Completed images can
be reused after later rendering failures. The exported project retains source
images, provider/model/prompt metadata, terms URL and an image-review flag.

Stubbed provider tests cover malformed responses, cancellation, corruption, cache
reuse and credential exclusion. Actual media tests verify importer/export
provenance. Frontend tests verify generation handoff and cancellation. No paid
provider request or desktop build was run; live account/model access still needs
verification.

## Full frontend source check

The standard type-check configuration now includes Vue and TSX as well as TS.
The full check found missing storyboard Add/Duplicate/Delete store actions and
obsolete Nuxt UI sizes. Those actions now preserve unique IDs, independent slide
settings, contiguous ordering, a valid selection and at least one slide; edits
stop active playback. Invalid indices are ignored. Regression tests cover the
actual store actions. Both full Vue checking and the configured type check pass.
Native execution remains unverified and no app build was run.
