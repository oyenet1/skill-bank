---
name: course-creator-assets
description: Find, inspect, copy, generate, or draw a teaching image or icon for a course lesson, with provenance and accessible description. Falls back to the bundled 580-SVG library, then downloads or draws what is missing.
---

# Course Assets

Read the [bundled asset guide](../../references/bundled-assets.md) and the
visual-sourcing section of the [media workflow](../../references/visual-media.md), then
the object library in [objects](references/objects.md).

## 1. Source in this order

1. **Requester-supplied files** — inspect them first and at readable size.
2. **The asset bank** — the bundled 580 SVGs plus the project's own assets.
3. **Go online** — find a reusable source and record its URL, licence and
   retrieval date. Verify the terms before publication.
4. **Generate or draw it** — only when it cannot be found online, or when it must
   be original or animated. Prefer an editable SVG or diagram; use AI image
   generation last, and label generated art as generated.

Never leave a gap because an object was missing. Go online, then generate.

Choose visuals that explain the exact concept rather than decorate it. An icon
alone is never proof of a process, and a product logo never implies endorsement.
Do not replace a genuine product screen or a real photograph with a generated
imitation.

## 2. Record and place

Copy selected media into the course `assets/` folder so notes, Slidev, PDF and
video all use the same portable file. Add a record to `assets/manifest.json`:

- source, original bundled path or URL
- known use terms, or a pending-verification note
- concept IDs it supports
- caption and alt text
- retrieval date for anything downloaded

Do not claim a blanket licence for the bundled collection. Verify a selected
logo or icon's origin and allowed public use when publishing, and record
`license: null` with a verification note when unknown. Respect trademark names.

## 3. Check the result

Inspect the visual at its intended size and against its intended background.
Confirm contrast, legibility of any label, and that the alt text describes what
a sighted reader would get from the image.

[brand](references/brand.md) governs imagery style: photographic, illustrated, ui-only or mixed,
plus icon and illustration rules. Follow it when one exists.
