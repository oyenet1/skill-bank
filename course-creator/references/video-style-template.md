# Video `style.md` Template

Use this as the shape of each requested video's `style.md`. Replace every placeholder with a real decision before production. The course-level `style.md` supplies defaults; copy the resolved values into the video file and state lesson-specific changes.

```markdown
# Style: {lesson or concept title}

## Teaching intent
- Audience and prior knowledge: {who this is for}
- Single takeaway: {what the learner will understand or do}
- Story beat: {teacher-supplied or generated scene and its role}
- Tone and pace: {concrete words, for example patient, playful, measured}

## Visual identity
| Token | Value | Use |
|---|---|---|
| Background | {hex} | {where} |
| Primary text | {hex} | {where} |
| Accent | {hex} | {what it highlights} |
| Display font | {family, weight, size} | {titles} |
| Body font | {family, weight, size} | {explanations} |
| Caption font | {family, weight, size} | {captions} |

## Frame system
- Canvas and frame rate: {width × height, fps}
- Safe areas and minimum text size: {values}
- Standard layouts: {full visual, teacher inset, teacher beside visual, full-screen teacher}
- Image treatment and diagram rules: {crop, border, label, source-credit placement}
- Representative frames: {links or descriptions for opening, explanation, demo, final takeaway}

## Effects bible
| Effect ID | Teaching purpose | Applies to | Entrance | Hold/change | Exit | Duration/easing | CapCut equivalent |
|---|---|---|---|---|---|---|---|
| {id} | {why the motion helps} | {elements} | {how it appears} | {what changes} | {how it disappears} | {seconds or frames} | {manual edit recipe} |

## Sound and captions
- Narration source: {teacher video, teacher audio, text-only, requested TTS}
- Caption appearance and placement: {style and safe area}
- Music and sound cues: {if requested, with levels and purpose}
- Timing master and sync points: {media source and scene/caption cues}

## Accessibility and review
- Readable final state for each explanation: {what remains visible}
- Reduced-motion treatment: {how the idea stays clear with less movement}
- Checks: {contrast, spelling, no overlap, audio sync, sources, asset availability}
```

Effects should clarify a cause, sequence, contrast, or attention shift. Keep the named effects consistent across Slidev, Remotion, and CapCut instructions; do not invent an effect to fill the table.
