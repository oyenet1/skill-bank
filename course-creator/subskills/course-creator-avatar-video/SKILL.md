---
name: course-creator-avatar-video
description: Generate an AI presenter, talking-photo or dubbed clip for a course from a script inside the course-creator bundle, then caption it locally. Delivers the video, the audio and the voiceover text.
---

# Avatar Video

Generate a presenter video from a script when there is no camera and no footage
to supply.

| Mode | What it produces |
|---|---|
| `avatar` (default) | a public AI presenter reads the script, lip-synced |
| `photo` | a still photo of a person is animated into a lip-synced talking clip |
| `dub` | an existing clip is translated and lip-synced into another language |

This is the **one skill in the set that depends on a hosted provider** — HeyGen —
for the presenter itself. Transcription, captioning and packaging stay local.
Be honest about the dependency: if the provider is unavailable or
unauthenticated, deliver the script, the voice and the storyboard, and say what
is blocked. **Never fabricate a presenter video.**

To package footage the requester already has, use [course-creator-talking-head-video](../course-creator-talking-head-video/SKILL.md)
instead — that path is local end to end.

## 1. Intake

Read [intake](references/intake.md). Resolve `brand.md` ([brand](references/brand.md)) for the on-screen framing,
then settle these in order:

1. **Mode** — `avatar` / `photo` / `dub` (see the table). Ask when unclear;
   `avatar` is the default when no photo and no existing clip is supplied.
2. **Script** — the words the presenter says. Write it for the ear, one idea per
   sentence. For `dub`, the input is the existing clip plus the target language
   rather than a script.
3. **Voice and language** — resolve through [voice](references/voice.md): language first, then
   voice. The provider needs a `voice_id`; the local fallback uses Kokoro.
4. **Presenter** — for `avatar`, choose a public avatar (name it in the brief);
   for `photo`, the still of a person, with rights to use their image confirmed
   before generating.
5. **Platform** — ask once; it derives aspect and resolution ([video](references/video.md) §2).
   The provider accepts 720p, 1080p or 4K output.
6. **Ending** — a closing card or the presenter's own sign-off. Only add a CTA
   the request asked for.

## 2. Preflight — provider auth gate

Read [preflight](references/preflight.md).

- Run `python3 tools/ensure_video_runtime.py avatar-video` from this skill
  directory for the local packaging toolchain (HyperFrames, FFmpeg) — the
  captioning and render of the result.
- Check the **provider**: the HeyGen CLI must be installed and authenticated.
  Run its status command, then `heygen auth login --oauth` to sign in when it is
  not. OAuth rides the free-usage allowance; an API key bills API credits.
  Report the status **verbatim** before spending anything.

**On a provider gap**, do not stop silently and do not fake the output. Report
the exact missing step and offer the offline fallback: produce the finished
**script**, the **local Kokoro voice** and the **storyboard**, and state that the
presenter render is blocked until the provider is authenticated. Keep the script
so the render can resume once auth lands.

**Confirm the current request body against the installed CLI** — read
`heygen video create --request-schema` rather than trusting a remembered field
list, since the body is a discriminated union that changes between releases.

## 3. Script and voice

Write `script.md` first: the spoken text, beat by beat, with the on-screen
framing each beat needs. This is the timing master — scene and caption timing
align to the spoken audio, not to an estimate.

Resolve the voice through [voice](references/voice.md). Generate and verify the local WAV (and
its MP3) before generating the presenter, so a provider failure still leaves a
usable audio deliverable. Identify names and technical terms that the synthetic
voice mispronounces and fix them in the script.

## 4. Generate the presenter

Drive the HeyGen CLI for the chosen mode. Discovery is read-only and needs no
spend; confirm the avatar and voice before creating:

```bash
heygen avatar list --ownership public --limit 5
heygen voice list --engine starfish --limit 5

# avatar — script-driven AI presenter
heygen video create --wait -d '{
  "type": "avatar",
  "avatar_id": "<avatar-id>",
  "script": "Your narration here.",
  "voice_id": "<voice-id>"
}'

# photo — animate a still of a person into a talking clip
heygen video create --wait -d '{
  "type": "image",
  "image": { "type": "url", "url": "<person image>" },
  "script": "Your narration here.",
  "voice_id": "<voice-id>"
}'
```

For `dub`, translate and lip-sync the supplied clip through the provider's
translate/lipsync command instead of creating from a script.

Read the created clip back and verify it before packaging: correct avatar or
photo, correct voice and language, full script spoken, no artefacts. Ledger the
result as a project asset. If the provider returns a failure, report its message
and fall back per §2 — do not retry blindly.

## 5. Caption and package

Treat the generated clip as footage and package it locally:

- `python3 tools/transcribe_captions.py <clip> --out <project-dir> --language <code>`
  for a local word-level transcript and timed SRT/VTT/JSON. Review the words
  against the approved script before using them as caption timing.
- Composite a clean caption rail, in the brand type, inside the safe area,
  synced to the transcript — the same rules as
  [course-creator-talking-head-video](../course-creator-talking-head-video/SKILL.md) §4. Optionally add a designed opening card.
- Keep the presenter's own audio as the bed; any added music ducks under the
  speech.
- Render at the master resolution from [video](references/video.md) §2, then downscale.

## 6. Deliver — three outputs

Per [video](references/video.md) §14: the **video** (MP4 — the presenter clip, captioned, master
rendered then downscaled), the **audio** (the spoken track as MP3), and the
**voiceover text** (the transcript as timed SRT, or plain TXT). Also keep
`script.md`, the provider job details (avatar, voice, mode) so the result can be
reproduced, and the caption files.

Report the mode, provider status, platform, resolutions, avatar and voice used,
output paths, and any unverified claim or provider limitation.





## Course integration

Read the [video style template](../../references/video-style-template.md) and keep the
presenter framing aligned with the course visual identity and the per-video
`style.md`. Register the generated clip, its transcript and caption files under
the lesson's `artifacts`, and mark affected outputs in `staleArtifacts` after the
script changes. If TTS is requested, also read the [course-creator-voice-narration](../course-creator-voice-narration/SKILL.md)
subskill. Store output under the lesson folder.
