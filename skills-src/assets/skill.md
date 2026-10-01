---
standalone:
  name: visual-assets
  description: >-
    Find, inspect, copy, draw or generate an illustration, icon or diagram with
    recorded provenance, licence and alt text. Sources from supplied files, the
    asset bank, or online, and generates only what cannot be found. Use when a
    visual is needed and nothing suitable exists yet.
bundle:
  name: course-creator-assets
  description: >-
    Find, inspect, copy, generate, or draw a teaching image or icon for a course
    lesson, with provenance and accessible description. Falls back to the bundled
    580-SVG library, then downloads or draws what is missing.
---

# Visual Assets

Resolve the object or image the work needs, place it where the project can use it,
and record where it came from. The object vocabulary is in {{ref:objects}}.

## Social media output

Read {{ref:social-media}} before producing audience-facing text or video.
Resolve the publishing platform and audience, keep the hook and payoff clear,
and verify mobile readability, captions and the chosen channel's format.
Ask for missing material choices at intake. Aim for shareability without
claiming guaranteed viral performance; preserve the requested teaching depth.

## Clarify before production

Read {{ref:intake}} before starting. If missing or ambiguous inputs would change
the result, ask a concise batch of questions and wait for answers. Offer
recommended choices; apply them only when the requester selects them or
explicitly asks you to choose. Use details already supplied rather than asking
again. Continue directly when the brief is complete.

## 1. Source in this order

1. **Requester-supplied files** — inspect them first and at readable size.
2. **The asset bank** — the project's own assets, plus the bundled library when
   the course-creator bundle is installed.
3. **Go online** — find a reusable source and record its URL, licence and
   retrieval date. Verify the terms before publication.
4. **Generate or draw it** — only when it cannot be found online, or when it must
   be original or animated. Prefer an editable SVG or diagram; use AI image
   generation last, and **label generated art as generated**.

Never leave a gap because an object was missing. Go online, then generate.

Choose visuals that explain the exact concept rather than decorate it. An icon
alone is never proof of a process, and a product logo never implies endorsement.
Do not replace a genuine product screen or a real photograph with a generated
imitation.

## 2. Record and place

Copy selected media into the project's assets folder so notes, slides, PDFs and
video all use the same portable file. Add a record to `assets/manifest.json`:

- source — original bundled path, URL, or "generated"
- known use terms, or a pending-verification note
- the concepts or sections it supports
- caption and alt text
- retrieval date for anything downloaded

Do not claim a blanket licence for a shared collection. Verify a selected logo or
icon's origin and allowed public use when publishing, and record `license: null`
with a verification note when unknown. Respect trademark names.

## 3. Check the result

Inspect the visual at its intended size and against its intended background.
Confirm contrast, legibility of any label, and that the alt text describes what a
sighted reader would get from the image.

{{ref:brand}} governs imagery style: photographic, illustrated, ui-only or mixed,
plus icon and illustration rules. Follow it when one exists.

{{mode:bundle}}
## Course integration

Read the {{doc:bundled-assets.md|bundled asset guide}} and the visual-sourcing
section of the {{doc:visual-media.md|media workflow}}. Inspect the 580 bundled
SVGs before going online — they cover most icons, logos and technology marks.

Copy each selected file into the course `assets/` folder and reference that
course-local copy from lesson notes, Slidev, PDFs and video, so exported material
still works if the skill is moved or uninstalled. Record the bundled path, the
local copy, concept IDs, caption and alt text in the course `assets/manifest.json`.
{{/mode}}

{{mode:standalone}}
## Standalone output

Use the project's `assets/` folder when one exists, otherwise the directory the
requester names, and keep the manifest beside the files. If a `course-plan.json`
is present and the requester points at a mapped lesson, record the asset against
that lesson's artifacts as well.
{{/mode}}

## Optional generated illustrations

Read {{ref:generated-assets}} when generating supporting scene images. Keep the
verified image and its provider/model/prompt metadata with the editable project.

## Bundled device objects

Inspect `assets/device-objects/CATALOG.md` and `assets/device-objects/manifest.json`
in this installed skill before sourcing a phone, laptop, tablet, monitor or
workstation illustration. This bank contains manually reviewed devmock images
without visible stock watermarks or provider credits. Preserve the provenance
when copying a chosen object into the output project. These are illustrative
raster images; some include screen placeholders or baked-in backgrounds.
Do not imply that a mockup shows a real product or assume a PNG is transparent.
Never use watermarked previews or remove a watermark to make a file eligible.
