# Desktop video platform support

The skill installer and job tools use the operating system and CPU architecture
at runtime. No Linux distribution package manager is required by the Python
bootstrap. User data locations keep downloaded runtimes outside read-only
application resources, including AppImage mounts.

| Target | Managed Node archive | Kokoro data location | Local voice setup |
|---|---|---|---|
| Windows x64/arm64 | `win-x64` / `win-arm64` zip | `%LOCALAPPDATA%/skill-bank/kokoro` | Python entry point; PowerShell installs private uv if absent |
| macOS x64/arm64 | `darwin-x64` / `darwin-arm64` tar.xz | `~/Library/Application Support/skill-bank/kokoro` | Python entry point; `sh` installs private uv if absent |
| Linux x64/arm64 | `linux-x64` / `linux-arm64` tar.xz | `${XDG_DATA_HOME:-~/.local/share}/skill-bank/kokoro` | Python entry point; `sh` installs private uv if absent |

Debian, Arch, Fedora, RPM installations, and AppImage use the Linux path. The
app's FFmpeg and rendering binaries still need per-platform desktop testing;
this source check has only executed on Linux. A first-use download also needs
network access. The installer reports unsupported OS/CPU combinations and
failed binary verification explicitly. Hosted avatar jobs still require a
HeyGen account; on Windows the installer checks a native CLI first, then WSL.

## First-use bootstrap

Each runtime-backed skill ships one cross-platform entry point, so an install
made by any skill manager can finish its own setup. The launcher detects the OS
and CPU, then runs `tools/bootstrap.py`, which reads the generated
`tools/dependencies.json`:

| OS | Launcher |
|---|---|
| Linux, macOS | `sh tools/setup.sh` |
| Windows (PowerShell) | `powershell -ExecutionPolicy Bypass -File tools\setup.ps1` |
| Windows (Command Prompt) | `tools\setup.cmd` |

`bootstrap.py` verifies the host against the same `x64`/`arm64` table as
`ensure_video_runtime.py`, prepares the private runtime (Node, FFmpeg/FFprobe,
the selected renderers, Chromium, and Kokoro or speech models where the skill
needs them), then installs the associated standalone skills and indirect dependencies missing from
the skills directory:

| Skill | Direct associated skills (indirect dependencies are also installed) |
|---|---|
| `slide-decks` | `visual-assets`, `explainer-video` |
| `explainer-video` | `voice-narration`, `product-launch-video`, `slide-decks`, `visual-assets` |
| `product-launch-video` | `explainer-video`, `voice-narration` |
| `talking-head-video` | `avatar-video`, `explainer-video`, `product-launch-video` |
| `avatar-video` | `talking-head-video`, `voice-narration` |
| `voice-narration` | `explainer-video`, `product-launch-video` |

A sibling is installed from the generated `tools/sibling_skills.json` snapshot
using the bundled Python installer. No system npx, Git, remote clone or agent
configuration override is needed. `--target` selects the exact root; existing
skills are preserved, incomplete destinations are refused, and a failed sibling
installation prevents setup from claiming readiness. Each installed sibling
receives the same snapshot so its future first-use setup can prepare its own
associated skills. The snapshot excludes model files, virtual environments,
binary runtime caches and recursive copies of itself. Cyclic associations are
visited once. Existing direct dependencies still have their indirect dependencies
checked. Bundle subskills do not install siblings because the bundle ships them.
The parent `course-creator/tools/setup` launcher prepares renderer, narration and
transcription; narration-dependent subskills use that launcher automatically.
Visual assets also ship a launcher. `--check` verifies cached tools, imports,
models and missing siblings without installation; it fails when a required
dependency is absent. `--yes` skips the prompt, and `--no-skills`
prepares runtimes only.

The shared `tools/ensure_video_runtime.py` and Kokoro `tools/kokoro/start.py`
can be called from a Tauri command and their standard-error JSON progress is
relayed to a frontend channel. The Tauri source now wires the Python job
runner and subtitle review into Video Studio; native execution is still unverified.

## Local photo presenter capability gate

The local avatar source implementation provides conditional hardware/model selection.
The following table describes eligibility; actual GPU inference still needs native-host verification.

| Host | Accelerator | Memory gate | Probe outcome |
|---|---|---|---|
| Windows x64 | NVIDIA CUDA | 6 GiB VRAM | Compatible CUDA models are listed |
| Linux x64 (Debian, Arch, Fedora; RPM/AppImage hosts) | NVIDIA CUDA | 6 GiB VRAM | Compatible CUDA models are listed |
| macOS 14+ arm64 | Apple Silicon MPS | 24 GiB unified memory | MuseTalk MPS; actual inference smoke gate required. SadTalker compatibility is disabled pending licensed model data |
| Any host | AMD/ROCm, CPU, integrated/unsupported GPU | Unsupported in this release | Editable script/local voice/storyboard fallback remains available |
| Other OS/architecture | Any | Unsupported in this release | Explicit platform reason, no model offer |

Run `python3 tools/avatar_probe.py` (`py -3` on Windows). The command installs
nothing and needs no network. `avatar_models.json` is the source for thresholds,
accelerator support, pinned sources, licences, and clip guidance. When updating
a pin, edit that manifest, run `python3 tools/avatar_pin.py --online` to compare
file sizes and SHA-256 values with the pinned source, then regenerate skills.
No backend may be offered with a missing model digest. Model download consent
and image-rights confirmation are separate from checking the hardware.

Accepted installation uses pinned target-compatible PyTorch and binary native
packages, with a small allowlist of pure Python source packages. RPM and AppImage
use the same writable app-data runtime; installation never writes into the bundle
or requires distro package managers. Hardware detection alone does not download
models. No claim of error-free operation on untested operating systems is made.

## Verified download trust

Managed Python download paths use the shared `network_tls.py` helper: Python
default roots on Windows, available CA bundles on Debian/Arch/Fedora, and system
Keychain certificates on macOS. Certificate and hostname verification stay
enabled. Missing optional stores preserve the default trust configuration;
network failures remain visible and retryable. Authenticated image API requests
reject redirects, while public model/runtime downloads may follow CDN redirects.
This is covered by source tests; macOS cold installation still needs a real host.

## Private Python manager fallback

If the standalone UV installer is unavailable, the shared Python/Kokoro helpers
and native desktop runner use the pinned UV 0.12.13 PyPI wheel. The registry in
`uv_wheels.json` records official artifact URL, exact size and SHA-256 for Linux
x86_64 (glibc/musl), Linux ARM64, macOS Intel/Apple Silicon and Windows x64/ARM64.
Only the known executable and its licenses are copied into private app data.
This path requires neither system pip nor package compilation. Unknown platforms
receive an explicit unsupported reason. The private executable is checked before
use. Failed or cancelled installer execution does not override cancellation.

A cold Linux check actually exercised an HTTP 403 installer failure, successful
verified wheel installation, and subsequent private Python 3.12.14 download and
execution. Native Tauri and Windows/macOS execution remain unverified because app
builds are deferred and those test hosts are unavailable.

## Launching without a system Python

The Unix/PowerShell launchers check Python's version before running the bootstrap.
When no suitable interpreter exists, they privately prepare UV and Python 3.12,
then run the same bootstrap. Windows uses native PowerShell HTTPS/ZIP/SHA-256
facilities; Unix uses curl or wget, a SHA-256 verifier and unzip when available,
or the official standalone installer when unzip is absent. The registry supplies
exact wheel hashes and sizes. No global pip or compiler is needed. `--check`
reports missing Python without installing anything. The bootstrap JSON returns
`pythonExecutable` so follow-up tools can use the private interpreter explicitly.

The no-Python Unix path was exercised with Python and UV excluded from PATH. It
installed the verified wheel, downloaded Python 3.12.14 and ran the bootstrap CLI
at `/tmp/skill-bank-no-python-launcher-o564ekfp`. Tests cover read-only checks,
rejecting old Python, argument preservation and exit codes. Windows/PowerShell
and macOS native execution remain unverified on this Linux host.
