# Video workflow completion audit

Checked against the original install → form inputs/uploads → script/assets/audio →
video → timed subtitles → finished editable project goal on 2026-09-30.
App builds remain disabled at the requester's instruction.

| Requirement | Authoritative evidence | Status |
|---|---|---|
| Explain skill workflow and duration guidance | `video-desktop-integration.md`, generated skill intake/preflight/generation instructions | Documented. Initial target: 30 seconds–3 minutes; longer teaching material in 5–10 minute chapters. 30 minutes is a limit, not a benchmark. |
| Automatically prepare missing tools | Shared runtime manifest/installers, cross-platform `bootstrap.py` launchers (`setup.sh`/`.cmd`/`.ps1`), Kokoro bootstrap, managed ASR first use, desktop host provisioning | Implemented; the bootstrap detects OS/arch, prepares the runtime, and installs missing associated sibling skills from the bundled snapshot, with `--check` for a read-only plan. Managed ASR and authored renderer setup exercised on Linux. Generic skill managers have no install hook, so the first-use launcher performs setup. |
| Script and editable storyboard | Desktop template draft, configured AI writer, `videoAi.test.ts`, importer/exported project | Implemented. Provider planning requires configured credentials/local service; no live provider planning claim is made from parser tests. |
| User form/media input | Video Studio with searchable menus, uploaded source images, narration and footage; importer tests | Implemented and source-checked. Native form interactions require a built host to verify. |
| Generate supporting visual assets | Shared `generate_image_asset.py`, native command, VideoAssetPanel, frontend and PNG/provider tests | Implemented with cached PNGs and provenance. No paid OpenAI request was made; account/model access remains unverified. Real product/portrait inputs remain required. |
| Generate narration and export audio | Managed Kokoro, native synthesis, per-scene audio import, assembler | Local spoken render previously produced actual audio/video and timed subtitles. Other native OSes remain unverified. |
| Full rendered video and source | Authored HyperFrames/Remotion/Slidev adapters and FFmpeg assembly; live Linux smoke artifacts | Actual outputs exist for all three engines. Native Tauri execution and other OSes remain unverified. |
| Timed SRT/VTT and review | Managed recognition on final media, word cues, caption editor and round-trip tests | Actual JSON/SRT/VTT exist for a spoken sample. Source review/export checks pass. Forced alignment to a supplied script is a remaining enhancement. |
| Progress, cancellation and retry | Host channels, job state, process-group handling, real cancellation test, native cache and frontend tests | Implemented. Tested outside the built native UI; hosted cancellation stops local waiting and may not stop provider processing. |
| Local photo presenter PRD | Pinned registry, consent/runtime/generator/dispatcher tools, Tauri form and pre-generation contract, tests | Source integrated. This AMD/ROCm host is ineligible; real Windows/Linux NVIDIA and Apple Silicon inference remain unverified. SadTalker compatibility is disabled due to Basel model terms. |
| All desktop OS targets | Conditional runtime paths/installers, model eligibility, wheel resolution; bundle target `all` | Source targets Windows/macOS/Linux including Debian/Arch/Fedora and RPM/AppImage. No native cross-platform certification is claimed. |
| Complete distributable integration | Canonical patch with registered native modules, resources, UI and tests | Patch applies to app Git HEAD and reverse-checks against the integrated checkout. Native compilation was not run. |

## Verification completed

- 136 Python tests pass, including OS/arch bootstrap planning and launcher
  emission, actual media importer/renderer handoff, and process-tree
  cancellation; provider/image inference tests use explicit stubs.
- Seven frontend tests pass for storyboard parsing, image generation/cancellation,
  and actual storyboard store actions.
- Both full Vue checking and the configured type check pass. The configured check
  now includes Vue and TSX, preventing previously missed component errors.
- All 515 generated skill files match their sources.
- Shared download TLS loads distro CA bundles and macOS system Keychain roots
  for managed Python. Tests retain certificate/hostname verification and tolerate
  missing optional stores. A live Hugging Face HTTPS request passed on Linux.
- A forced cold setup with system UV hidden reproduced HTTP 403 at the standalone
  installer. The new hash-pinned PyPI wheel fallback installed and executed UV
  0.12.13, then downloaded and executed private Python 3.12.14 successfully at
  `/tmp/skill-bank-cold-runtime-fixed-wgw8qo_7`. This proves this Linux bootstrap
  path; it does not prove native Windows/macOS execution.
- A Unix launcher test with Python and UV excluded from PATH actually provisioned
  UV and Python 3.12.14 and ran the bootstrap CLI. Source tests also prove old
  Python rejection, read-only missing-Python checks, argument preservation and
  propagated exit codes. PowerShell execution remains unverified.
- The generated sibling source snapshot installed four associated skills into
  an exact target containing spaces without npx, Git or a remote clone. Tests
  cover preserving user edits, incomplete destinations, symlinks, unsafe archive
  paths, digest failures and propagation of the original source snapshot. Both
  first-use bootstrap and the explicit installer prepare these associated skills.
- A previously rendered spoken MP4 still probes as 5.421354 seconds with video and
  audio streams; live font/source renderer smoke artifacts remain present.
- The complete patch was applied to a temporary copy of the app baseline and
  every registered native module was found. The user's app was not overwritten.

## Remaining evidence needed

The goal is not marked complete: native desktop execution, actual supported GPU
inference, Windows/macOS first-use installation, and live hosted-account access
cannot be proved by source checks or mocked tests. Builds remain deferred by the
requester. A supported GPU host is needed for the PRD inference gates; a compatible
licensed replacement is needed for its SadTalker fallback requirement.

## Current host verification gate (2026-09-30)

The available release binary/AppImage is dated 2026-09-29 and predates the
current native integration. The executable at
`/home/fade/Projects/js/devmock/src-tauri/target/release/progravity` does not
contain any of the registered `video_skill_run`, `video_skill_avatar_probe`,
`video_skill_avatar_install`, or `video_skill_generate_image` command names.
It cannot exercise the new bridge, so launching that old release would not
verify the current source. Building a replacement remains explicitly deferred.

A fresh read-only avatar check reports `unsupported-accelerator:rocm`, with no
installed backends or eligible candidates. This host cannot supply the required
NVIDIA or Apple Silicon inference evidence. The four existing Linux render
artifacts still probe successfully: spoken video/audio 5.421354 seconds and
HyperFrames/Remotion/Slidev visual smoke clips 0.5 seconds each. Those media
artifacts prove their recorded renderer checks, not the new native bridge.

The remaining gates require external state: a current native host when builds
are allowed, eligible NVIDIA/Apple Silicon machines, and configured hosted
account access for live provider checks. The existing model-license deviation
also remains unresolved. These gates prevent declaring the full goal complete.
