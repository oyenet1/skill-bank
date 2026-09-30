# Video Studio desktop integration

The video job runner is now connected to the writable `devmock` checkout in
`/home/fade/Projects/js/devmock`. Video Studio sends its storyboard, uploaded
assets, narration, and selected skill route to the bundled Python runner. The
Tauri host installs or reuses a private Python runtime and routes progress and
cancellation. Runtime files, projects, downloads, and logs live in app data.

## Parallel dependency setup

**Prepare tools** resolves and verifies Node/npm first. Renderer profiles and
FFmpeg/FFprobe then install concurrently, with at most four workers. Each profile
prepares its packages before its browser, and duplicate profiles are visited
once. Existing ready packages and browsers are reused; missing browsers are
repaired and verified, including Remotion's Chrome Headless Shell. Media binaries
must execute successfully before setup reports ready.

Progress events from workers share the existing setup channel. All active
workers finish before the app reports failure or readiness. Renderer workers
share the existing cancellation flag; the native FFmpeg downloader retains its
existing behavior of returning from the download before cancellation completes.
No new package dependency was added for scheduling.

Standalone skills separately use their shared parallel bootstrap: renderer,
transcription, narration and sibling-copy branches overlap, while operations
that share renderer directories or overlapping sibling graphs stay sequential.
See the repository README for dependency layers and exact manifest/lock paths.

Spoken audio is transcribed from the final media. `VideoCaptionEditor.vue`
previews that MP4 and lets users review cue text and timing before saving SRT,
VTT, JSON, and the reviewed transcript. Caption edits are checked against the
video and caption hashes before they are committed. The asset protocol is
scoped to project files under app data.

`docs/patches/devmock-video-job.patch` exports the complete current source
integration, including the caption editor, renderer manifest, and Windows
launcher fixes. Regenerate it from the integrated app checkout with:

```sh
python3 scripts/prepare_devmock_video_patch.py --app /path/to/devmock --from-worktree
```

The patch is relative to that app repository's Git HEAD. It passes a reverse
apply check against the current integrated checkout; this confirms the patch
matches the exported files and does not establish runtime correctness.

## Authored visual workflows

The form offers HyperFrames HTML, Remotion React, Slidev slides, and the original
scene-card route through a searchable `USelectMenu`. Each authored scene keeps
its editable source, local uploaded assets, frame-based timing, and renderer
package requirements. Scene timing expands to measured narration length. The
final assembler retains the original narration or footage audio once and
writes the script, storyboard, MP4, MP3 when audio exists, SRT, and VTT.

The storyboard now has an **On-screen text** field. Visual direction remains
production metadata. Selected brand fonts are downloaded from pinned, integrity-checked Fontsource
packages and preserved with their licences in the editable source. Slidev is hidden when footage is
uploaded because its PNG exporter produces still slides.

## Verification and limits

Real generated-source renders succeeded locally for HyperFrames, Remotion,
and Slidev. A two-scene HyperFrames render retained both uploaded narration and
footage audio. A separate spoken sample completed managed Python/package/model setup and
recognition from the final rendered MP4, producing word timing and JSON/SRT/VTT
with a review flag. This short English sample does not establish accuracy for
other languages, speakers, or long recordings. Source type checking
passed, and focused Python tests exercise source generation, upload preservation,
caption handoff, and resume behavior.

No app build was run. Caption editor use inside the desktop host, native macOS and Windows
execution, provider-backed asset
and avatar generation, and packaging still need verification or integration.
The prepared source patch reflects the latest app files.

## Local presenter implementation

The talking-head panel now includes a searchable backend menu, an explicit
licence/download consent checkbox, install/cancel/retry progress, portrait upload
and image-rights confirmation. The hardware check uses existing Python or a native
read-only fallback; clean hosts can prepare private Python after model consent.
Both avatar commands share the existing video-operation cancellation guard.

Bundled tools implement verified resumable downloads, pinned private environments,
MPS inference smoke gating, offline photo inference, provider dispatch, and
presenter pre-generation through the existing scene renderer. Failed inference
retains real script, narration WAV/MP3, storyboard, logs and staging. The final
project includes original inputs and presenter provenance.

SadTalker remains disabled due to Basel Face Model licensing. This host has no
supported accelerator, so live GPU inference and native UI execution still need
Windows/Linux NVIDIA and macOS Apple Silicon verification. No app build was run.
See `docs/video-desktop-integration.md` for commands and the PRD deviation.

## Generated scene images

`VideoAssetPanel` exposes optional OpenAI image generation. The host command
`video_skill_generate_image` prepares private Python, runs the shared adapter,
relays progress and returns image data/public provenance. Verified images are
cached for retry, and keys never enter project files. Scene sources retain their
metadata and require image/rights review separately from subtitle approval.
The integration patch includes its frontend regression tests. Provider tests use
stubbed responses; no paid request or app build was run.

The exported patch keeps the checkout's existing native audio/speech module and
matching Cargo configuration because the current host registers those commands.
It does not remove that work. Default patch preparation now verifies the complete
canonical patch against the destination, avoiding the obsolete initial template
that omitted later commands and UI features.
