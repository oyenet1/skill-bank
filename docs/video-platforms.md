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
be relayed to a frontend channel. The Tauri app has not yet wired the Python
job runner or subtitle review into its production render action.
