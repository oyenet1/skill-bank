# Slidev Capability Rack

Use the framework properly instead of reimplementing it. Almost every "I need a
component for this" is already a built-in or one `addons:` entry away.

## Headmatter (first slide)

```yaml
---
theme: default          # official, community (omit the slidev-theme- prefix), or local
addons: []              # package names or local paths; installs prompts on start
title: ''
titleTemplate: '%s — Deck'
info: false
author: ''
keywords: ''
presenter: true         # presenter mode
browserExporter: dev
download: false         # PDF download button in the SPA build
exportFilename: ''
transition: slide-left  # default transition for the deck
layout: cover
class: ''
---
```

Per-slide frontmatter additionally takes `layout`, `transition`, `class`,
`clicks`, `hideInToc`, `level`, `background`, `image`, `disabled`.

## Layouts

`default` · `cover` · `center` · `section` · `quote` · `fact` · `statement` ·
`intro` · `end` · `none` · `two-cols` · `two-cols-header` · `image-left` ·
`image-right` · `iframe-left` · `iframe-right` · `iframe`

Use `::left::` / `::right::` to fill the two-column layouts, and
`<template #right>` where a layout exposes named slots.

## Built-in components

`Arrow` · `AutoFitText` · `LightOrDark` · `Link` · `RenderWhen` · `SlideCurrentNo`
· `SlidesTotal` · `Titles` · `Toc` · `Transform` · `VClick` · `VAfter` · `VSwitch`
· `VDrag` · `VMark` · `VClips` · `Demo` · `Tweet` · `Youtube` ·
`PoweredBySlidev`

`Transform` gives scale/rotate/translate; `AutoFitText` fits a long headline;
`LightOrDark` swaps assets between themes; `RenderWhen` swaps rendered output
between dev, build and export.

## Animation

| Need | Primitive |
|---|---|
| reveal in order | `v-click` · `v-clicks` on a list |
| reveal without a new step | `v-after` |
| hide after a step | `v-click-hide` |
| sequences and loops | `v-switch` |
| continuous motion | `v-motion` — `:initial` · `:enter` · `:leave` · `:click-N` |
| annotate a phrase | `v-mark` — `underline` · `circle` · `box` · `highlight` · `strike-through` · `crossed-off` |
| drag to position | `v-drag` |
| step-only element | `VClick` / `VAfter` components |
| count steps | `$clicks` in the template |
| per-slide default | frontmatter `clicks:` |
| enter/leave | frontmatter `transition:`; `a \| b` for different forward/back; custom CSS `.<name>-enter-active` etc. |

`v-click` modifiers: `.up` `.down` `.left` `.right` `.fade-in` `.fade` `.scale`
plus compositions like `.fade.right.scale`, and `.none` to disable.

## Code

Fenced blocks are highlighted by **Shiki**; a language identifier is required.

| Need | Syntax |
|---|---|
| highlight lines | ` ```ts {1,3-5} ` |
| highlight in steps | ` ```ts {1\|3\|all} ` — magic move across clicks |
| dim, keep code visible | ` ```ts {*}\|{1,3} ` |
| live editor | ` ```ts {monaco} ` |
| runnable editor | ` ```ts {monaco-run} ` |
| diff view | ` ```ts {monaco-diff} ` |
| hide / show only | `{hide}` · `{hide|show}` · `{none}` |
| line numbers | `{lines:true}` |
| start line | `{startLine:5}` |
| max height + scroll | `{maxHeight:'200px'}` |

Monaco and magic-move are the two that most improve a teaching deck: magic-move
shows the *change* between two states, Monaco lets the viewer edit.

## Diagrams and math

| Need | Feature |
|---|---|
| flowcharts, sequences, ER, class, state, gantt, pie, git, journey | Mermaid — ` ```mermaid ` |
| UML from text against a PlantUML server | PlantUML — ` ```plantuml ` |
| maths | LaTeX/KaTeX — `$inline$` and `$$block$$`, with `{1\|2\|all}` step highlighting |
| mathematical figures | TikZ — ` ```tikz ` with a `TikZ` addon |

Style Mermaid from the brand palette with `defineMermaidSetup` in
`setup/mermaid.ts`: `theme: 'base'` plus `themeVariables` for node, edge, note
and actor colours. See [objects](objects.md) for which diagram kind to pick.

## Styling

- **UnoCSS** is built in — utility classes work in any slide.
- `<style>` is global; `<style scoped>` is per-slide.
- `@iconify-json/*` collections give `i-carbon-*`, `i-logos-*` and similar icon
  classes with no download step.
- Global layers: `global-top.vue` and `global-bottom.vue` render on every slide —
  use them for a persistent logo, progress bar or watermark.

## Presenter, recording and export

| Action | Command / flag |
|---|---|
| presenter mode | `--presenter` or press `p`; notes from a trailing HTML comment |
| recording (camera + mic) | `--record`; output under `.slidev/recordings` |
| browser exporter | `browserExporter` headmatter, or `slidev export` |
| PDF (default) | `slidev export` |
| PNG per slide | `slidev export --format png` |
| PNG per click state | `slidev export --with-clicks --format png` |
| transparent PNG | `--omit-background` |
| PPTX | `slidev export --format pptx` |
| Markdown | `slidev export --format md` |
| dark | `--dark` |
| range | `--range 1,6-8,10` |
| longer timeout | `--timeout 60000` |
| SPA build | `slidev build` |
| build with PDF | `slidev build --download` |

**There is no native MP4 export.** For video, take the `--with-clicks` PNG
sequence into `ffmpeg`, or drive the running deck with Playwright on a timing
schedule and record the browser when `v-motion` easing must survive.

## MCP server — always enabled

Slidev ships a built-in MCP server (v52.17.0+). **Leave it on.** Never set
`mcp: false` in the headmatter, and register the server before editing a deck.
It turns slide work from raw text edits into structured, verifiable operations.

**Via the dev server** (preferred — gives live navigation):

```
http://localhost:<port>/__mcp
```

```bash
# Claude Code
claude mcp add --transport http slidev http://localhost:3030/__mcp
```

```json
{ "mcpServers": { "slidev": { "type": "http", "url": "http://localhost:3030/__mcp" } } }
```

**Via stdio** (no dev server needed):

```json
{ "mcpServers": { "slidev": { "command": "npx", "args": ["slidev", "mcp", "slides.md"] } } }
```

| Tool | Use |
|---|---|
| `slidev-get-info` | deck overview: entry, title, slide count, files, dev URL, position |
| `slidev-list-slides` | every slide with number, title, layout, source file |
| `slidev-get-slide` | one slide's full source: frontmatter, content, note |
| `slidev-update-slide` | update content, note and/or frontmatter |
| `slidev-insert-slide` | insert after an existing slide |
| `slidev-remove-slide` | remove a slide |
| `slidev-move-slide` | reorder before/after another slide |
| `slidev-goto-slide` | navigate the live presentation (dev server only) |

Slides are addressed by their **1-based rendered number**. Edits write back to
the markdown files and hot-reload instantly.

**Workflow.** List the slides to establish numbering, edit through the MCP tools
rather than rewriting the file, then `slidev-goto-slide` and inspect the rendered
result at the delivery size before moving on. Verify every slide you touch this
way — a structured edit still needs a visual check.

## Extending

- Custom Vue components go in `components/` and are auto-imported.
- Composables come from `@slidev/client`; `useSlideContext()` exposes the current
  slide, `$frontmatter`, `$clicks` and `$page`.
- `setup/` holds config factories such as `mermaid.ts`, `shiki.ts`, `unocss.ts`.
- Import external decks with `src:` on a slide.
- Themes and addons install from the official gallery or the community; add them
  under `addons:` and Slidev offers to install on start.

**Before promising a diagram, editor or addon works, confirm it is installed.**
Read the current Slidev docs for exact syntax when a feature is load-bearing.
