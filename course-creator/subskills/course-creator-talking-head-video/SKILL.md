---
name: course-creator-talking-head-video
description: Package a teacher's existing talking-head or interview clip with captions or designed graphic overlays inside the course-creator bundle, leaving the footage untouched. Delivers the packaged video, its audio and its transcript.
---

# Talking Head Video

Package an existing talking-head, interview or podcast clip — add captions, or
designed graphic overlays, or both. **The footage plays in full and is never
altered**: no regrade, no scanline, no reframing of the person, and no cut of the
speaker unless the requester explicitly asks for a trim. Everything is composited
on top.

Use this skill when the input already exists as footage. To build a video from
scratch, use [course-creator-explainer-video](../course-creator-explainer-video/SKILL.md) or [course-creator-product-launch-video](../course-creator-product-launch-video/SKILL.md). To
generate the presenter itself, use [course-creator-avatar-video](../course-creator-avatar-video/SKILL.md).

## 1. Intake

Read [intake](references/intake.md). Resolve `brand.md` ([brand](references/brand.md)) first — captions and
overlays must use its palette and type. Then settle these, in order:

1. **Input clip** — the footage file. Required; there is no video without it.
   Inspect it at readable size: duration, resolution, fps, single or multi-shot,
   whether a person is on screen and where.
2. **Mode** — ask which, and allow both:
   - `captions` (default) — the spoken words as readable subtitles (see §4).
   - `overlays` — designed graphic cards: kinetic titles, lower-thirds, data
     callouts, quotes, side panels, picture-in-picture, timed to what is said.
3. **Platform** — ask once; it derives aspect and resolution ([video](references/video.md) §2).
   The footage is untouched, so an aspect change is a **framing decision**:
   either letterbox to keep the whole frame, or reframe with stated intent.
   Never crop a speaker's face by accident.
4. **Style** — for `captions`, a clean verbatim lower-third rail by default, or
   the cinematic option that composites the peak word **behind** the subject
   (needs a matte; §4). For `overlays`, pick 2–3 card types, not a catalogue.
5. **Ending** — a closing card, or the footage's own close. Do not add a CTA the
   request did not ask for.
6. **Transcript** — if one is supplied, use it and skip transcription.

Never invent a spoken line that is not in the transcript, and never ask for
footage the request already supplies.

## 2. Preflight

Read [preflight](references/preflight.md) and run
`python3 tools/ensure_video_runtime.py talking-head-video` from this skill
directory. Use the verified paths for HyperFrames, FFmpeg and FFprobe. This
workflow runs on the HyperFrames CLI end to end — transcription, the composition
and the render are all local, with no third-party service and no API key.

Confirm `hyperframes doctor` reports FFmpeg/FFprobe and a browser before
promising a render. Report a setup failure up front; never claim an output
exists if the tool that makes it is missing.

## 3. Transcribe locally

`hyperframes transcribe <clip>` produces a word-level transcript using a local
model (Whisper by default, Parakeet when installed) — no key, no rate limit.
Pass `--language` when the speech is not English. The transcript is the **single
source** for both captions and overlay timing; storyboard or guessed timing is
not speech alignment.

Read the transcript before designing anything. Drop filler and false starts from
display, but never rewrite what was actually said — captions are verbatim.

## 4. Build in HyperFrames

Author a HyperFrames composition that places the footage and composites the
captions and cards on top. **The footage element is never styled beyond
placement** — no filter, no grade, no speed change unless asked.

- **Captions** — a clean lower-third rail carries the spoken text, verbatim,
  inside the safe area, legible at delivery size and synced to the transcript.
- **Cinematic captions** — composite the peak word **behind** the subject with a
  matte so the subject occludes it. This is the earned accent, not the default
  for every line.
- **Overlays** — each card is a reusable component with an entrance, a hold and
  an exit, timed to the line it belongs to. Draw from [objects](references/objects.md) before
  hand-building a graphic. When overlays are used, **the opening card is the hook
  cover** — one idea, phrased as payoff or tension, legible at thumbnail size
  ([video](references/video.md) §11).
- **Sound** — the clip's own audio is the bed; any added SFX stay below the
  speech. Re-voice only when the requester asks ([voice](references/voice.md)).
- **Trim** only on request, with `data-media-start` / `data-duration` on the
  footage clip, keeping the captions aligned to the trimmed timeline.

Render at the master resolution from [video](references/video.md) §2, then downscale.

## 5. Review the real output

Inspect the actual render: the opening, each caption and card at the moment it
appears, the safe areas, and the close. Confirm the transcript matches what is
spoken, no line is cut off mid-word, no card covers the speaker's face or a
caption, the footage is unaltered, and the piece still communicates when muted.
Check captions against the final audio, not an estimate.

Export `captions.srt`, `captions.vtt` and `captions.json` with
`python tools/write_subtitles.py captions.json --out captions`, timed to the
final video. Keep the composition source and the transcript with them.
When captions need to be regenerated from final speech, run
`python3 tools/transcribe_captions.py <final-video.mp4> --out <project-dir> --language <code>`.
It writes word-level `transcript.json` and reviewable timed captions. Correct
recognition errors and check the cues against the final video.

## 6. Deliver — three outputs

Per [video](references/video.md) §14: the **video** (MP4, master rendered then downscaled), the
**audio** (the clip's audio as MP3, from a verified extraction), and the
**voiceover text** (the transcript as timed SRT, or plain TXT). Report the mode,
platform, resolutions, the caption/overlay style used, the output paths, and
every limitation — including any trim or reframing made to fit the platform.





## Optional generated illustrations

Read [generated-assets](references/generated-assets.md) when generating supporting scene images. Keep the
verified image and its provider/model/prompt metadata with the editable project.

## Course integration

Read the [video style template](../../references/video-style-template.md). Keep the clip's
captions and cards aligned with the course visual identity and the per-video
`style.md`. Register the packaged video, its transcript and its caption files
under the lesson's `artifacts`, and mark affected outputs in `staleArtifacts`
after the source footage changes. Store output under the lesson folder.
