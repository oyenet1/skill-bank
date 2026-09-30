# Video Studio job runner handoff

`docs/patches/devmock-video-job.patch` connects the existing desktop form to
the shared video job tools. It bundles the Python tools as Tauri resources,
adds a Rust host command, and sends the existing scene cards, uploaded footage,
and local/uploaded narration through `run_desktop_video_job.py`.

The host reuses `uv` when available or installs it privately using the official
installer. `uv run --no-project --python 3.12` prepares Python without requiring
a system Python installation. Downloads, caches, projects, and logs live in
Tauri app data, including when resources are inside an AppImage. Windows uses
PowerShell and cancels the process tree; Unix uses process groups and gives the
Python runner time to stop its renderer. The Python environment uses UTF-8.

The frontend receives progress through a Tauri channel and reports MP4, final
audio, captions, and transcript paths after the runner verifies them. Spoken
audio uses final-media local ASR and returns a caption review flag. Silent
scenes keep the storyboard cues. Original uploads and form metadata are kept
under `source/desktop/` beside the portable delivery project.

## Prepare and apply source changes

From skill-bank, regenerate the patch against the current app:

```sh
python3 scripts/prepare_devmock_video_patch.py --app /path/to/devmock
git -C /path/to/devmock apply --check /path/to/skill-bank/docs/patches/devmock-video-job.patch
```

When that checkout is writable, apply the reviewed patch there:

```sh
git -C /path/to/devmock apply /path/to/skill-bank/docs/patches/devmock-video-job.patch
```

The separate `devmock-hyperframes-runtime.patch` adds HyperFrames to the
existing manual **Prepare tools** command. The job patch uses the bundled
shared runtime manifest for its own automatic setup. Both patches apply to the
current checkout; neither has been applied to the read-only sibling app here.

## Verification and remaining work

The desktop import tests encode and probe a real scene project, reject duplicate
narration sources, preserve uploaded bytes without using uploaded names as
paths, and check resume identity and preservation of reviewed style. Source
checks include `git apply --check`, Rust formatting, and Vue type checking in
an isolated app copy. The latter reports no errors in the patched files;
eight existing diagnostics remain in StoryboardTimeline, TextBlockControls,
ChromaPanel, and JobProgress.

The Rust host has not been compiled or run: the user requested source work
without an app build. Windows and macOS execution, managed Python first-use
downloads, and live ASR still need platform verification. The patch connects
the existing scene/card/footage route. It does not yet author and run Slidev,
Remotion, or HyperFrames source from the form, expose the runner's resume
control, or provide an in-app caption editor. These remain part of the full
desktop workflow objective.
