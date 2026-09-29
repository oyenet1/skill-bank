# Video `style.md` Template

Use this as the shape of each requested video's `style.md`. Replace every placeholder with a real decision before production. Resolve identity from `brand.md` when it exists: copy the resolved values into the video file and state only the lesson-specific changes. Without a `brand.md`, record the values as `unbranded` defaults.

```markdown
# Style: {lesson or concept title}

## Delivery
- Category: {motion-graphic | explainer-lesson | screencast-demo | footage-overlay | launch-ad | slideshow-montage}
- Platform: {YouTube | TikTok | Reels | LinkedIn | X | Facebook | website | presentation}
- Aspect ratio: {16:9 | 9:16 | 1:1 | 4:5}
- Master resolution: {e.g. 3840×2160}
- Delivery resolution: {e.g. 1920×1080} — floor is 1080p
- Frame rate: {24 | 30 | 60}
- Renderer: {Slidev → ffmpeg | Remotion | both | CapCut handoff}
- Audio mode: {silent | voiceover | music | full}
- Ending: {main CTA + destination | logo sting | takeaway recap | QR | contact | next video}
- Watermark: {none | text | logo | both} · {opacity % if any} · {position}

## Teaching intent
- Audience and prior knowledge: {who this is for}
- Single takeaway: {what the learner will understand or do}
- Story beat: {teacher-supplied or generated scene and its role}
- Tone and pace: {concrete words, for example patient, playful, measured}

## Visual identity
<!-- Copy from brand.md. State only the deltas. -->
| Token | Value | Use | Source |
|---|---|---|---|
| Background | {hex} | {where} | {brand.md | default} |
| Primary text | {hex} | {where} | |
| Accent | {hex} | {what it highlights} | |
| Display font | {family, weight, size} | {titles} | |
| Body font | {family, weight, size} | {explanations} | |
| Caption font | {family, weight, size} | {captions} | |

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
- Voice: {language · accent · female/male/custom · named Kokoro voice}
- SFX palette: {typing | click | alert | success | whoosh | pop | shutter | hover | ambient — which are used where}
- Music and sound cues: {if requested, with levels and purpose; duck 12–18 LUFS under speech}
- Caption appearance and placement: {style and safe area; mandatory when audio mode is silent}
- Timing master and sync points: {media source and scene/caption cues}

## Accessibility and review
- Readable final state for each explanation: {what remains visible}
- Reduced-motion treatment: {how the idea stays clear with less movement}
- Checks: {contrast, spelling, no overlap, audio sync, sources, asset availability}
```

Effects should clarify a cause, sequence, contrast, or attention shift. Keep the named effects consistent across Slidev, Remotion, and CapCut instructions; do not invent an effect to fill the table.
