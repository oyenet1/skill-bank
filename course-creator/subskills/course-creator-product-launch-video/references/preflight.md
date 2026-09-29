# Preflight

Before production, confirm the toolchain is actually present. Report gaps
up front instead of failing mid-render.

## Check per deliverable

| Deliverable | Requires | Check |
|---|---|---|
| `voice-narration` | `python3` · Kokoro models | `python3 --version` · `voice-narration/tools/kokoro/start.sh` first-run |
| `slide-decks` | `node` · `npx`/`pnpm` | `node --version` · `npx slidev --version` |
| `explainer-video` (motion graphics) | `node` · `ffmpeg` · Playwright | `node --version` · `ffmpeg -version` |
| `product-launch-video` | `node` · `npm`/`bun` · `ffmpeg` · Remotion | `npx remotion versions` · `ffmpeg -version` |
| `content-authoring`, `sales-copy` | none | — |
| Brand extraction from a URL | web fetch tooling | the environment's web fetch capability |
| asset/object downloads | network | reachable asset source |

Also confirm `bun` if the project uses it as its runtime or package manager.

## Report shape

Print a short table, then continue with what is available.

```
✓ node     v22.11.0
✓ ffmpeg   7.1
✓ python3  3.12
✗ playwright   not installed — motion-graphic video export unavailable
```

## Behaviour on a gap

- **Never claim an output exists** if the tool that makes it is missing.
- Name the missing tool and the exact install command.
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
