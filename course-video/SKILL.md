---
name: course-video
description: Produce an educational Remotion video or a CapCut Desktop editing handoff from a teacher brief, slides, script, audio, or teacher footage. Use for video work without requiring a full course.
---

# Course Video

Work from the supplied brief or actual existing assets. A Slidev deck can guide the design but is not required. Produce only the requested video and handoff assets. For any video request, read the installed mandatory video entrypoint skill first and then relevant Remotion, caption, audio, or editing skills. Check current library documentation for APIs and commands.

For a product launch ad or screenshot-based product demo, use the separate `product-launch-remotion` workflow when it is installed; this skill handles educational lesson videos.

Before scenes, write a concrete `style.md` for this video. Include palette, fonts, tone, frame size and safe area, presenter layout, representative frames, and an effects bible with purpose, entrance, exit, duration, easing, and use conditions. Keep concept and storyboard beat IDs when supplied. Use relevant course-local images and icons; when the `course-creator` bundle is present, inspect its asset library and copy selected visuals into the course folder. Align scene and caption timing to actual teacher footage or audio; text alone is a script until timed or recorded. Create editable Remotion source and render an MP4 when rendering works. Inspect key frames, audio, captions, transitions, and asset paths.

For a requested CapCut Desktop handoff, provide separate scene clips and reusable media plus a timecoded guide covering layers, placement, effects, keyframes, entrance, exit, captions, and audio cues. Check current CapCut controls before giving precise interface directions.

If a course map exists, register the video source, MP4, and actual inputs under the lesson's `artifacts`; record dependencies in `artifactSources` and mark affected outputs in `staleArtifacts` after input changes. Use a supplied recording when available; synthetic speech is a separate request. This skill also works for a standalone educational video.
