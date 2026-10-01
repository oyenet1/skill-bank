# Object Library

A reusable vocabulary of scene objects. Reach for these before hand-building a
visual. Every object must be resolvable in one of three ways, in this order:

## Resolution order

Resolve every object in this order. Never leave a gap because something was
missing — go online, then generate.

1. **Use what the requester supplied.** Always first, always preferred.
2. **Use the asset bank** — the bundled 580 SVGs (`course-creator/assets/` when
   the bundle is installed) plus the project's own assets: icons, logos,
   technology marks, existing diagrams.
   For device objects, read `assets/device-objects/CATALOG.md` in the installed
   `visual-assets` skill (or the bundle's `course-creator-assets` subskill).
   It ships reviewed devmock phones, laptops, tablets, monitors and workstations,
   with provenance in `manifest.json`. Copy suitable objects into the project;
   inspect screen placeholders, backgrounds and dimensions before use.
   Watermarked images and visible provider-credit previews are excluded.
   Do not remove or obscure watermarks to make a source usable.
3. **Go online.** Find a reusable image or asset and record its source URL,
   licence and retrieval date in `assets/manifest.json` before use. Verify the
   terms before anything is published.
4. **Generate or draw it** — only when it cannot be found online, or when the
   asset must be original or animated. Prefer an editable SVG or a Vue component
   built in the project, since it inherits `v-motion` and `v-click`. Fall back to
   AI image generation last, and **label generated art as generated**.

Do not replace a genuine product screen or a real photograph with a generated
imitation. Generation is for illustration the requester never had and that does
not exist online — not for faking evidence.

## Arrows and connectors

`arrow-straight` · `arrow-curved` · `arrow-elbow` · `arrow-dashed` ·
`arrow-bidirectional` · `arrow-labelled` · `connector-dot` · `connector-anchor` ·
`bracket` · `brace` · `brace-map` · `callout-tail` · `leader-line` ·
`flow-line` · `branch-split` · `branch-merge` · `loop-back` · `dependency-arrow`

Match the connector to the meaning: solid for flow, dashed for optional or async,
bidirectional for a relationship, labelled for a named edge.

## Diagrams and architecture

Prefer a **diagram** over prose whenever the content is structure — systems,
flows, hierarchies, sequences, relationships. In Slidev this is a fenced
` ```mermaid ` block, rendered natively and styled from the brand palette through
`defineMermaidSetup` in `setup/mermaid.ts` (`theme: 'base'` plus `themeVariables`
for node, edge, note and actor colours). Set the diagram colours from
`brand.md` so diagrams match every other slide.

| Need | Mermaid kind |
|---|---|
| architecture, request path, decision flow | `graph TD` / `graph LR` — flowcharts |
| step-by-step interaction, API calls, message order | `sequenceDiagram` |
| entities and their relationships | `erDiagram` |
| type or class structure | `classDiagram` |
| state machine, lifecycle, status transitions | `stateDiagram-v2` |
| schedule, roadmap, phases | `gantt` |
| proportions of a whole | `pie` |
| branching history | `gitGraph` |
| user journey, experience stages | `journey` |

Rules for diagrams:

- **Reveal, then annotate.** Show the whole diagram first so the viewer has the
  map, then `v-click` highlight one node or edge at a time as narration reaches
  it. Never animate a diagram in node-by-node from nothing — the viewer loses the
  shape.
- Colour the active node with the brand accent and dim the rest
  (`dim-others`). One active element per step.
- Label edges when the relationship has a name. An unlabelled arrow is a guess.
- Keep node labels to 2–4 words. Put detail beside the diagram, not inside it.
- For architectural drawings, draw the real boundary — the client, the service,
  the datastore, the third party — and do not invent a component that does not
  exist in the system being described.
- A hand-drawn `svg-diagram` is better than Mermaid when the layout must be
  non-standard or the diagram itself must morph.

## Attention and emphasis

`arrow` · `callout-box` · `spotlight` · `magnifier` · `underline-sweep` ·
`highlight-box` · `pointer-cursor` · `focus-ring` · `dim-others` ·
`numbered-badge` · `progress-dots`

## Type and hook

`kinetic-headline` · `word-by-word-reveal` · `typewriter` · `counter-ticker` ·
`stat-callout` · `quote-card` · `subtitle-strip` · `lower-third` ·
`keyword-highlight` · `text-highlight-sweep` · `rotating-word` ·
`outline-to-fill`

## Layout and framing

`card` · `panel` · `glass-panel` · `split-screen` · `bento-cell` ·
`browser-chrome` · `phone-frame` · `laptop-frame` · `window-frame` ·
`picture-in-picture` · `broll-frame` · `safe-area-guide`

## UI and product

`button` · `input-field` · `form-field` · `checkbox` · `toggle` · `dropdown` ·
`search-bar` · `tooltip` · `toast` · `badge` · `tag` · `avatar` ·
`table-row` · `skeleton-loader` · `loading-spinner` · `notification-card`

## Data and process

`bar-chart` · `line-chart` · `pie-chart` · `sparkline` · `progress-bar` ·
`meter` · `stat-tile` · `timeline` · `step-indicator` · `pipeline` ·
`node-graph` · `flow-arrow` · `checklist` · `comparison-table`

## Code and terminal

`code-block` · `terminal-window` · `diff-view` · `command-typing` ·
`file-tree` · `diff-badge` · `syntax-highlight`

## Texture and atmosphere

`gradient-mesh` · `noise-overlay` · `grid-pattern` · `dot-grid` · `blob` ·
`particle-field` · `light-sweep` · `vignette` · `grain` · `glow` ·
`parallax-layer`

## Transition primitives

`wipe` · `slide` · `zoom` · `fade` · `morph` · `mask-reveal` · `page-turn` ·
`whip-pan` · `glitch-cut` · `dissolve`

## Selection rules

- Pick the object that **explains**, not the one that decorates. Every object
  needs a reason to be on screen.
- One idea per frame. If two ideas are present, split the scene.
- Effects must clarify a cause, a sequence, a contrast or an attention shift.
  Do not invent an effect just to fill the effects bible.
- Keep named effects consistent across Slidev scenes, Remotion scenes and any
  CapCut handoff so the same move means the same thing everywhere.
- Respect `brand.md` → `Accessibility` → `Reduced motion`: when reduced motion is
  required, the idea must stay clear with fades and static layouts only.
