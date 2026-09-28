# Visuals, Slidev, Video, and CapCut

Use only the section for the requested action. Media outputs are independent: creating slides does not automatically render PDF or video, and creating a video does not automatically create a CapCut package.

## Resolve one teaching visual

Use a visual when it makes a concept easier to recognize, compare, or follow. Search in this order:

1. The teacher's course folder and supplied media; then the skill's [bundled image and icon library](bundled-assets.md). Search it for relevant files and inspect the actual candidate rather than selecting by filename alone. Include a suitable local icon or image in the requested teaching output when it clarifies the concept, and copy it into the course folder. The bundled icons have no blanket usage license recorded here; check the selected file's provenance and public reuse terms before publication. Preserve existing files.
2. Search online for a suitable reusable image. Download only when reuse terms are clear; record source URL, creator, license or usage terms, and retrieval date. Use the teacher's preferred sources if supplied.
3. If search fails or a custom scene is needed, use an available image generation skill/tool for a bitmap illustration. Inspect the result for factual accuracy, labels, and consistency with the lesson. Save a selected asset into the course folder.
4. If generation is unavailable or unsuitable, draw an editable Mermaid, SVG, or Slidev-shape diagram. For a concept that cannot be shown accurately this way, provide a clear written visual explanation.

Register the selected asset in `assets/manifest.json` with ID, local path, source method, provenance, permitted use or pending verification, concept IDs, alt text, and caption. Keep source links in learner materials where attribution is required. Do not leave bundled, generated, or downloaded assets only in the skill or a temporary tool location. Reuse the same course-local asset in notes, slides, PDF, and video where it helps continuity. Choose the number of images by teaching value.

Store records in a top-level `{ "assets": [...] }` array. Use `course-folder`, `bundled`, `web`, `generated`, or `drawn` for `sourceMethod`. The `sourceUrl`, `creator`, and `license` fields may be `null` for teacher-supplied or generated media when they do not apply:

```json
{
  "id": "computer-parts-photo",
  "path": "assets/computer-parts.jpg",
  "sourceMethod": "course-folder",
  "sourcePath": null,
  "sourceUrl": null,
  "creator": null,
  "license": null,
  "verificationNote": "Supplied by the teacher; confirm publication rights if needed",
  "conceptIds": ["hardware"],
  "alt": "A computer monitor, keyboard, and mouse on a desk",
  "caption": "These physical parts are examples of hardware."
}
```

For a bundled icon, set `sourceMethod` to `bundled` and `sourcePath` to its path under the skill's `assets/` folder; `path` still points to the copy inside the course. Record the original icon's source and license when verified, or leave `license` null and explain the pending check in `verificationNote`.

## Slidev deck for one lesson

Load any mandatory animation or deck entrypoint skill installed in the environment before authoring motion; the teacher's explicit Slidev choice remains the output framework. Create `lessons/{lesson-id}/slides/slides.md` and a short `storyboard.json` in the same folder. The deck covers the lesson's story, each concept's What/Why/Where/When/How, the visual explanation, demonstration, and learner check. Map every slide or reveal beat to a concept ID. Use click reveals and motion to show one causal step at a time; leave a complete readable state after each sequence. Place presenter notes and source credits where appropriate. Avoid motion that is essential to understand but disappears from a PDF.

Each storyboard beat records `id`, `conceptId`, `slide`, `visibleContent`, `assetIds`, `caption`, `estimatedSeconds`, and `effectId` (or `null`). Video production may add actual `startSeconds` and `durationSeconds` after aligning to supplied audio or footage. Keep beat IDs stable when timing changes; these are the bridge between Slidev reveal states, Remotion scenes, and CapCut directions.

Use the course visual identity when present and keep assets local to the course. Confirm syntax and export options with current [Slidev documentation](https://sli.dev/guide/animations.html). On a separate PDF request, export the deck with click states when they clarify the lesson; verify the static pages and links. A Slidev PDF is not the lesson-notes PDF.

Register the deck and storyboard as separate artifacts. When a deck follows the written lesson, record that source relationship; a deck built directly from a teacher brief can stand alone. A slide PDF sourced from the deck records that dependency and becomes stale if the deck changes.

## Video style and storyboard

Before building any educational video, load the relevant installed video skills. If a video entrypoint is mandatory in the environment, use it; for a Remotion deliverable load `remotion-best-practices` and its specific creation, markup, narration, caption, and rendering references as needed. Read only the skills needed for the chosen footage, narration, captions, animation, and rendering. Use current official documentation for APIs.

Create or reuse `{course-root}/style.md` for the shared course identity. Create `lessons/{lesson-id}/video/style.md` for every lesson video, or `video/style.md` for a standalone educational video. The per-video file must be concrete and reviewable, with:

- Audience, teaching tone, story relationship, and the takeaway.
- Palette with color values, font families/weights/sizes, contrast, background treatment, and image treatment.
- Canvas size, safe areas, frame composition patterns, presenter inset/side-by-side/full-screen rules, and representative frame descriptions or reference frames.
- An **effects bible**: named animation/effect, why it is used, which elements may use it, entrance and exit behavior, duration/easing, transition rules, and restrained use conditions.
- Narration/caption style, pacing, audio cues, and accessibility rules such as readable final states and reduced-motion alternatives where appropriate.

Use the [video style template](video-style-template.md) to make these decisions explicit before authoring scenes.

Use a storyboard with scene IDs, concept IDs, source-slide or asset IDs, visible content, narration/caption text, intended duration, and effect references. A supplied teacher recording or narration is the timing master. If text is supplied without audio, create a timed caption and narration script; synthesize speech only when requested. Align scenes and captions to real media, inspect timing, and correct mismatches before delivery.

Build editable Remotion scenes using the Slidev deck's visual sequence when a deck exists. Otherwise use the teacher's brief, script, storyboard, and supplied media to establish the sequence. Apply the shared assets and style rules in either case. Register each substantial scene as a standalone composition as well as part of the full lesson composition when separate clips are requested for CapCut. Support teacher footage as an inset, beside the teaching visual, or full screen at selected beats. Render an MP4 when the environment supports rendering; otherwise provide source and state the missing render capability. Compare key video frames with the deck when one exists, check that no visual element obscures a caption or presenter, and verify audio levels and transitions.

Register the video source, rendered MP4, and actual inputs under the lesson's `artifacts`. Record dependencies in `artifactSources`: a video may use `slides`, `storyboard`, `narrationAudio`, or `teacherAudio`, but list only inputs it really uses. Mark the rendered MP4 stale when its source or an input changes; mark the CapCut guide and clips stale when their timing changes. A standalone video from a teacher brief needs no Slidev dependency.

For synthetic narration, follow [optional Kokoro narration](narration.md). It is a separate action that may feed the video timeline. Do not synthesize speech during a text-only or supplied-audio request. Time captions from the actual resulting audio.

## CapCut Desktop handoff

On request, package the finished MP4 plus separate scene clips and the images, audio, captions, and other reusable media needed for manual changes. Write a `capcut-edit-guide.md` with an asset inventory and a timecoded timeline table. For each scene, specify track/layer, source file, start/end time, crop or placement, text, effect and parameter values, keyframes, entrance and exit, transition, audio/caption cue, and what the learner should notice. Include steps to import, assemble, preview, and export in CapCut Desktop. Verify current CapCut Desktop controls and names before writing click-by-click UI instructions; keep the timecoded creative directions usable if the UI differs.
