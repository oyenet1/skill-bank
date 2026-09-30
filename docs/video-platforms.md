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

The shared `tools/ensure_video_runtime.py` and Kokoro `tools/kokoro/start.py`
can be called from a Tauri command and their standard-error JSON progress can
are relayed to a frontend channel. The Tauri source now wires the Python job
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
