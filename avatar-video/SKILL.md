---
name: avatar-video
description: Generate a presenter video from a script when there is no camera: an AI avatar reads it, a still photo is animated into a lip-synced talking clip, or an existing clip is translated and dubbed. Uses a verified local photo presenter or an authenticated HeyGen provider with an editable fallback, captions the result locally, and delivers the video, the audio and the voiceover text.
---

# Avatar Video

## Automatic first-use setup

Before production, run the bundled launcher with `--yes`; it detects the host, prepares private runtimes, and installs the declared sibling dependency graph. Do not ask the requester to install packages manually.

- Linux/macOS: `sh tools/setup.sh --yes`
- Windows: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/setup.ps1 --yes`

Use `--check` for a read-only readiness check. If prerequisites are missing, rerun setup. Follow the returned `pythonExecutable` and runtime paths for later commands. Model-license acceptance, image rights and account credentials remain explicit inputs.

Generate a presenter video from a script when there is no camera and no footage
to supply.

| Mode | What it produces |
|---|---|
| `avatar` (default) | a public AI presenter reads the script, lip-synced |
| `photo` | a still photo of a person is animated into a lip-synced talking clip |
| `dub` | an existing clip is translated and lip-synced into another language |

Photo mode supports a verified local backend on compatible NVIDIA or Apple
Silicon hardware. Avatar and dubbing modes use authenticated HeyGen. Automatic
selection prefers an installed compatible local photo backend, then HeyGen,
then an editable script, local narration and storyboard fallback. Never claim
that fallback assets are a presenter video. An explicit provider choice fails
clearly when unavailable instead of silently changing providers.

To package footage the requester already has, use `talking-head-video`
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

## 2. Preflight — hardware, consent and provider

Read [preflight](references/preflight.md).

- Run `python3 tools/avatar_probe.py` (`py -3 tools/avatar_probe.py` on Windows)
  before choosing a local presenter. This is a read-only, network-free hardware
  check. It reports accelerator, measured memory, eligibility, and compatible
  backend metadata. CUDA needs 6 GiB VRAM; Apple Silicon needs 24 GiB unified
  memory. AMD/ROCm, CPU and unsupported architectures retain the voice/script
  fallback. Hardware eligibility alone does not mean a backend is installed.
- Run `python3 tools/avatar_ensure.py avatar-video --check`. It reports installed
  backends and consent offers without creating environments or downloading
  models. Show the selected model's licence, component licences, download size,
  disk allowance and expected runtime band before asking for acceptance.
- Only after explicit model consent, run
  `python3 tools/avatar_ensure.py avatar-video --backend <id> --accept --consent-token <displayed-token>`.
  The private runtime uses `SKILL_BANK_AVATAR_HOME` or the platform's user-data
  `skill-bank/avatar` folder. Verified downloads resume from `.part` files.
  MPS requires an actual three-second inference check before readiness.
  Use `--allow-restricted` only when the requester explicitly opts into the
  displayed restrictions. SadTalker is disabled because its bundled Basel
  Face Model data is not licensed for general commercial use/distribution.
- Resolve `python3 tools/avatar_provider.py --mode photo` (use the actual mode).
  `--provider local|heygen` or `SKILL_BANK_AVATAR_PROVIDER` overrides automatic
  selection. Local never requires HeyGen authentication; hosted never requires
  local models. Keep script, verified Kokoro WAV/MP3 and storyboard when no
  presenter is available, identifying the blocked step and retry command.

- Run `python3 tools/ensure_video_runtime.py avatar-video` from this skill
  directory for the local packaging toolchain (HyperFrames, FFmpeg) — the
  captioning and render of the result.
- For a resolved **HeyGen provider**, check authentication: the HeyGen CLI must be installed and authenticated.
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
usable audio deliverable. If presenter generation is blocked, package those
real assets with `python3 tools/avatar_provider.py --deliver-fallback fallback
--script script.md --audio narration.wav`; inspect its verified artifact paths
and clearly state the blocked presenter step. Identify names and technical terms that the synthetic
voice mispronounces and fix them in the script.

## 4. Generate the presenter

For a resolved local photo backend, confirm image rights and generate using
its private inference environment:

```bash
python3 tools/avatar_generate.py --backend musetalk-15 --mode photo \
  --image portrait.png --audio narration.wav --out presenter --rights-confirmed
```

Use the selected backend ID, not an assumed default. This command installs
nothing, runs inference offline, verifies video and narration duration, and
returns the actual MP4 plus manifest. Failures retain logs and staging without
publishing a partial final MP4. Local `avatar` and `dub` return explicit
unsupported responses. Keep clips around 30 seconds; split longer narration
into scenes. Resolution and accelerator tier dominate memory and runtime.
Pass generated clips into the normal video job as footage, keeping original
narration separate so it is mixed exactly once.

For a resolved hosted provider, drive the HeyGen CLI for the chosen mode. Discovery is read-only and needs no
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
  `talking-head-video` §4. Optionally add a designed opening card.
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





## Optional generated illustrations

Read [generated-assets](references/generated-assets.md) when generating supporting scene images. Keep the
verified image and its provider/model/prompt metadata with the editable project.

## Standalone output

Keep the project in a named `videos/{slug}/` folder, or the location the
requester chose. Preserve the generated clip, the verified WAV/MP3, `script.md`
and the caption files together so a later voice or script change can be
re-rendered without recomposing the rest.
