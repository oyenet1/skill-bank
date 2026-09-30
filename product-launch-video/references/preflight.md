# Preflight

Before production, run the bundled setup for the requested deliverable. It
checks the local toolchain, installs supported missing tools in a private user
data directory, verifies them, and prints machine-readable JSON with exact
executable paths. Use those paths for subsequent commands. It does not change
global npm packages or the user's shell profile.

## Check per deliverable

| Deliverable | Requires | Check |
|---|---|---|
| `voice-narration` | Python 3.10+ · disk space for Python and Kokoro models | Run `python3 tools/kokoro/start.py` (`py -3 tools/kokoro/start.py` on Windows); it installs missing `uv` locally, creates Python 3.12, installs packages, and verifies model downloads. |
| `slide-decks` | Node · Slidev · Chromium · FFmpeg | `python3 tools/ensure_video_runtime.py slide-decks` |
| `explainer-video` | Node · Slidev · Remotion · HyperFrames · Chromium · FFmpeg | `python3 tools/ensure_video_runtime.py explainer-video` |
| `product-launch-video` | Node · Remotion · HyperFrames · Chromium · FFmpeg | `python3 tools/ensure_video_runtime.py product-launch-video` |
| `content-authoring`, `marketing-copy` | none | — |
| Generated scene illustration | Python 3.10+ · OpenAI image API key/model access | Read the generated-assets reference; desktop prepares private Python on first use. |
| Brand extraction from a URL | web fetch tooling | the environment's web fetch capability |
| asset/object downloads | network | reachable asset source |

Run from the installed skill directory, or give the absolute path to its bundled
`tools/ensure_video_runtime.py`. `--check` reports status without installing.
The setup needs Python 3.10+ and a network connection on first install. Confirm
`bun` separately if a supplied project requires it.

**When the route offers a renderer choice** — the demo and ad categories build
in either Remotion or HyperFrames — pass `--renderer remotion` or
`--renderer hyperframes` so only the chosen engine is installed. Preparing both
is wasteful. Without the flag the route's full set is prepared.

For local narration in a standalone video skill, run its
`python3 tools/kokoro/start.py` before generating speech (`py -3` on Windows).
In the course bundle use `course-creator/tools/kokoro/start.py`. The
voice-narration skill has the same setup path. On Unix, `start.sh` remains a
terminal convenience wrapper.

## Local speech recognition

For captioned video, run `python3 tools/ensure_python_runtime.py
--prepare-transcription` (use `py -3` on Windows). This prepares a private
Python environment, pinned speech packages and the English model. Pass
`--model small` for multilingual speech. The video installer prepares this
step automatically; final-media transcription also prepares it on first use.

`tools/transcribe_captions.py` reuses installed native Whisper when available,
or selects managed CPU speech recognition without a compiler. Use
`--engine faster-whisper` to choose the managed backend explicitly. Unknown
languages use a multilingual model; English-only models reject non-English
language requests. The decoder version is pinned, with an older compatible
wheel selected on macOS before version 14. First use needs network access and
space for model downloads. Recognition emits progress and keeps its log.
Review the generated word timing and caption text before delivery.

## Report shape

Summarize the setup JSON, then continue when `ready` is true.

```
{"ready": true, "route": "slide-decks", "paths": {"node": "...", "slidev": "...", "ffmpeg": "..."}, "missing": []}
```

## Behaviour on a gap

- **Never claim an output exists** if the tool that makes it is missing.
- For Kokoro, run the bundled setup path before reporting a missing tool. It
  installs uv, Python, packages and models without a global package install.
- If setup fails, report its `error` or `missing` values and the exact retry
  command. Keep editable source when only rendering is blocked.
- Offer the downgrade path: e.g. without Playwright, produce the Slidev deck and
  the `--with-clicks` PNG sequence and stop there, rather than a broken video.
- If only the render step is blocked, deliver editable source and state the
  specific render blocker.

## MCP / environment

If the environment exposes MCP servers used for web fetch, search or media,
confirm they respond before promising a live URL extraction or an asset
download. If they do not, fall back to asking the requester for the values.

**The Slidev MCP server is always set up before any Slidev work.** Do not begin
editing a deck until it is registered, and never disable it with `mcp: false`.

| Mode | Setup |
|---|---|
| Dev server running | register `http://localhost:<port>/__mcp` (streamable HTTP) with the agent |
| No dev server | `npx slidev mcp slides.md` over stdio |

```bash
claude mcp add --transport http slidev http://localhost:3030/__mcp
```

Confirm it responds (`slidev-get-info` returning the entry file and slide count)
before relying on it. If it cannot be registered, say so and fall back to plain
file edits — but report that the structured workflow and live verification were
unavailable.

## Linters

When the deliverable contains code, confirm a linter or formatter is available
for each language used — see the code-quality module where it ships with this
skill. Report missing tooling before producing code the reader is expected to
trust.
