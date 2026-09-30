# Requirements Document

## Introduction

`avatar-video` is the only skill in the set that depends on a hosted provider
(HeyGen) to generate a presenter. This feature adds an **optional, fully local
talking-head backend** so that a machine with a capable GPU can generate a
presenter without any hosted service, API key, subscription, or network call at
generation time. The host is *probed* for its operating system and GPU; when it
meets the thresholds (NVIDIA CUDA with ≥ 6 GiB VRAM, or macOS Apple Silicon with
≥ 24 GiB unified memory) the skill **offers** to install only the models that are
compatible with that accelerator, surfaced as a consent prompt. The user installs,
then generation runs locally. When the host is ineligible or the user declines,
the existing honest fallback (script + local Kokoro voice + storyboard) and the
existing optional HeyGen path both remain.

---

## Glossary

- **Avatar Video**: The `avatar-video` skill; generates a presenter video from a script when no camera or footage exists.
- **Presenter**: The on-screen person who speaks the script (AI avatar, animated still photo, or dubbed existing clip).
- **Mode**: One of `avatar` (public AI presenter), `photo` (still photo animated into a talking clip), `dub` (existing clip translated and re-lip-synced).
- **Local backend**: An offline, self-hosted lip-sync/presenter model that runs on the user's own GPU with no hosted provider.
- **Provider**: The thing that produces the presenter clip. May be `local` (this feature), `heygen` (hosted), or `fallback` (script + voice + storyboard only).
- **Accelerator**: The GPU/compute unit used by a local backend. One of `cuda` (NVIDIA), `mps` (Apple Metal), `rocm` (AMD), `directml`, `cpu`.
- **Unified memory**: Apple Silicon memory shared by CPU and GPU (there is no dedicated VRAM). "≥ 24 GiB" means total `hw.memsize`, not a discrete VRAM pool.
- **VRAM**: Dedicated GPU memory reported by `nvidia-smi` (`memory.total`), in MiB.
- **Capability probe**: A read-only, network-free scan that reports OS, architecture, accelerator, memory, and eligibility.
- **Eligibility gate**: The threshold check that decides whether the local offer may be shown.
- **Consent prompt**: The user-facing ask (verbatim model list, download size, disk, licences) that MUST precede any model download.
- **Model pack**: The pinned files (weights + configs) a backend needs, with size and SHA-256.
- **Backend manifest**: `avatar_models.json`, the single source pinning backends, files, sizes, hashes, licences, accelerator support, and memory floors.
- **Private runtime**: A user-data directory (`skill-bank/avatar`) holding `uv`, a virtual environment, and verified models; never global installs.
- **Packaging**: The existing local pipeline that treats a generated clip as footage and captions/renders it (HyperFrames).
- **Job contract**: The JSON request/result/progress shape shared by `tools/run_video_job.py` and desktop hosts.
- **Route / Renderer**: Terms from `runtime_requirements.json` (`avatar-video` route; `hyperframes` renderer).
- **skills-src / manifest / generator**: The single-source authoring flow: `skills-src/<cap>/skill.md` + `skills-src/manifest.yaml` → generated `SKILL.md` targets via `scripts/gen_skills.py`.
- **Short clip**: A generated presenter clip whose spoken audio is within the backend's recommended duration (see Req 13).

---

## Requirements

### Requirement 1: Capability and OS detection

**User Story:** As a desktop user, I want the skill to know my operating system and GPU, so that it only offers a local backend my machine can actually run.

#### Acceptance Criteria

1. THE probe SHALL report `schemaVersion`, `os` (`Windows` | `Darwin` | `Linux`), `arch` (`x64` | `arm64`), `accelerator.kind`, `accelerator.name`, `accelerator.memoryBytes`, `accelerator.source`, and `eligible` as JSON on stdout, with progress JSON on stderr.
2. WHEN the OS is Linux or Windows, THE probe SHALL query `nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits` and SHALL classify the accelerator as `cuda` with `memoryBytes = memory.total MiB × 1,048,576` when the command succeeds.
3. WHEN the OS is Darwin and `platform.machine()` is `arm64`, THE probe SHALL read total unified memory from `sysctl -n hw.memsize` and SHALL classify the accelerator as `mps`.
4. WHEN no supported accelerator is found, THE probe SHALL return `eligible: false` with a machine-readable `reason` and SHALL exit 0 (a probe failure is not a crash).
5. THE probe SHALL NOT make any network request and SHALL NOT install anything.
6. IF an external command (`nvidia-smi`, `sysctl`, `system_profiler`) is missing, times out, or returns unparseable output, THEN THE probe SHALL degrade to the next detection step and record the failed `source` without raising.
7. WHEN `nvidia-smi` reports multiple GPUs, THE probe SHALL select the GPU with the greatest `memory.total` and SHALL report it as `accelerator.name`.

---

### Requirement 2: Eligibility thresholds

**User Story:** As the product owner, I want a clear, configurable capability gate, so that only machines that can realistically run the models are offered the download.

#### Acceptance Criteria

1. WHEN the accelerator is `cuda`, THE gate SHALL mark the host eligible iff VRAM ≥ 6 GiB (6 × 1024³ bytes).
2. WHEN the accelerator is `mps`, THE gate SHALL mark the host eligible iff total unified memory ≥ 24 GiB.
3. THE thresholds SHALL be read from a single declarative source so they can be tuned without editing probe logic.
4. WHEN the accelerator is `rocm`, `directml`, `cpu`, or unknown, THE gate SHALL mark the host ineligible in this version and SHALL name the accelerator in `reason`.
5. THE probe SHALL report the measured value, the threshold, and a boolean `eligible` in the same document so a desktop host can render an explanation without recomputing.

---

### Requirement 3: Consent-gated install

**User Story:** As a user, I want to be asked before anything large is downloaded, so that I stay in control of disk, bandwidth, and licences.

#### Acceptance Criteria

1. WHEN the host is eligible and no compatible backend is installed, THE skill SHALL present a consent prompt listing each candidate backend with its `displayName`, `qualityTier`, `downloadBytes`, `diskBytes`, `accelerator`, and `license`.
2. THE installer SHALL NOT download any model file and SHALL NOT create a Python environment until the user has explicitly consented to that backend.
3. WHEN the user consents, THE skill SHALL run `python3 tools/avatar_ensure.py avatar-video --backend <id>` and SHALL report its JSON result verbatim.
4. WHEN the user declines, THE skill SHALL record the decline for the run, SHALL continue with the provider dispatch order (Req 7), and SHALL NOT re-prompt in the same run.
5. `avatar_ensure.py --check` SHALL report eligibility, installed backends, and readiness without installing and without network access beyond a version check.
6. THE installer SHALL be idempotent: a second run with a satisfied backend SHALL perform no download and SHALL return `ready: true`.
7. Downloads SHALL be resumable via a `<file>.part` temp and SHALL verify size and SHA-256 before use (mirroring the Kokoro downloader).
8. THE consent prompt SHALL be emitted as one JSON line on stderr with `phase: "consent-required"` so an agent or desktop host can render it.

---

### Requirement 4: Compatibility matrix and best-on-accelerator selection

**User Story:** As a user, I want only the models that actually work on my GPU installed, so that setup succeeds and generation works normally.

#### Acceptance Criteria

1. THE backend manifest SHALL pin, per backend: `id`, `displayName`, `modes`
   (`photo` at minimum), `accel` (list of supported accelerators),
   `minAccelMemoryBytes`, `qualityTier`, `license`, `licenseClass`, `sourceUrl`,
   `revision`, `files[]` (`name`, `bytes`, `sha256`, `url`), and `pythonVersion`.
2. WHEN selecting a backend, THE selector SHALL consider only backends whose `accel` includes the detected accelerator and whose `minAccelMemoryBytes` ≤ detected `memoryBytes`.
3. THE selector SHALL choose the compatible backend with the highest `qualityTier`, breaking ties by lowest `downloadBytes`, EXCEPT that a `defaults` entry for the detected accelerator (`defaults.cuda` / `defaults.mps`) SHALL override tier ordering when present (D1).
4. THE selector SHALL NOT install or offer a backend that fails the compatibility filter, even if the user names it.
5. WHEN the accelerator is `mps`, THE selector SHALL consider only backends validated for Metal and SHALL designate exactly one as the MPS default.
6. THE chosen backend `id` SHALL be written to the project manifest and job state so a result is reproducible.
7. IF no compatible backend exists for a detected accelerator, THEN THE selector SHALL return `eligible: false` with the accelerator named, and SHALL NOT recommend a hosted provider as a substitute in the same field.
8. THE selector SHALL prefer `permissive` backends; a `restricted` backend SHALL be offered only as an explicit opt-in, and a `research-only` backend SHALL NOT be selectable automatically.
9. THE selector SHALL NOT include a backend whose files lack a non-null `sha256`.
10. WHEN the accelerator is `mps`, THE installer SHALL gate the MPS default behind an on-device smoke inference (a bundled portrait + WAV fixture producing a valid MP4) and SHALL fall back to the verified `sadtalker` backend when the gate fails (D2).

---

### Requirement 5: Private, reproducible runtime

**User Story:** As a user, I want the models and tools isolated from my system, so nothing global is changed and uninstalling is trivial.

#### Acceptance Criteria

1. THE runtime SHALL live under `<user-data>/skill-bank/avatar/` (`LOCALAPPDATA`, `~/Library/Application Support`, or `XDG_DATA_HOME`).
2. `SKILL_BANK_AVATAR_HOME` SHALL override the runtime directory, so the skill can run from a read-only resource directory.
3. THE installer SHALL reuse or privately install `uv` (Windows via PowerShell, macOS/Linux via `sh`) and SHALL NOT modify `PATH`, shell profiles, or global packages.
4. THE installer SHALL create a private virtual environment at the pinned Python version and SHALL record a requirements hash marker so package changes trigger a reinstall.
5. Model files SHALL live under `<runtime>/models/<backend>/` and SHALL be gitignored.
6. THE installer SHALL emit newline-delimited JSON progress on stderr with phases `uv`, `python`, `packages`, `model`, `verify`, `complete`.

---

### Requirement 6: Local presenter generation

**User Story:** As a user with a capable GPU, I want to generate the talking-head clip on my own machine, so I do not pay a hosted provider.

#### Acceptance Criteria

1. THE generator SHALL accept `--mode photo|avatar|dub`, `--backend <id>`, an input image (`--image`) for `photo`, a verified WAV/narration (`--audio`), and `--out <dir>`, and SHALL write `video.mp4` plus `manifest.json` (mirroring the renderer output contract).
2. WHEN `--mode photo` and a compatible backend is installed, THE generator SHALL produce a lip-synced clip from the still image and the audio.
3. WHEN `--mode avatar` is requested on the local backend, THE generator SHALL return `ready: false`, `reason: "local-avatar-mode-unsupported"`, and SHALL NOT fabricate a presenter (the local backend animates the user's own image, it cannot invent a stock presenter).
4. WHEN `--mode dub` is requested on the local backend, THE generator SHALL return `ready: false` with the unsupported reason in this version.
5. THE generator SHALL print one JSON result on stdout: `{ready, backend, mode, video, durationSec, elapsedSec}` and JSON progress on stderr.
6. THE generator SHALL be cancellable by SIGTERM and SHALL leave no partial `video.mp4` in the output directory on failure (failed work stays in a `.work-<id>` folder).
7. THE generator SHALL verify the produced MP4 with FFprobe (non-zero duration, video stream present) before reporting success.
8. IF the generated clip exceeds the backend's recommended duration, THEN THE generator SHALL warn on stderr and continue.

---

### Requirement 7: Provider dispatch order

**User Story:** As a user, I want the skill to prefer free/local when possible and fall back predictably, so behavior is never surprising.

#### Acceptance Criteria

1. THE dispatcher SHALL resolve a provider in this order unless overridden: `local` (eligible and installed) → `heygen` (CLI installed and authenticated) → `fallback` (script + Kokoro voice + storyboard).
2. WHEN `--provider local|heygen|auto` is supplied, or `SKILL_BANK_AVATAR_PROVIDER` is set, THE dispatcher SHALL honor the explicit choice and SHALL fail loudly if that provider cannot run.
3. THE dispatcher SHALL report the chosen provider and the reason for the choice in the result JSON and in the run summary.
4. WHEN the dispatcher chooses `fallback`, THE skill SHALL deliver `script.md`, a verified local Kokoro WAV and MP3, and the storyboard, and SHALL state the exact blocked step and retry command.
5. THE dispatcher SHALL NOT require HeyGen to be installed when a local backend is ready, and SHALL NOT require a local backend when HeyGen is authenticated.

---

### Requirement 8: Reuse of local packaging

**User Story:** As a maintainer, I want the generated clip to flow through the existing captioning/rendering path, so there is one packaging pipeline.

#### Acceptance Criteria

1. THE skill SHALL treat the locally generated clip as footage and SHALL package it with the existing `transcribe_captions.py` → caption rail → HyperFrames render path, unchanged.
2. THE job contract SHALL gain an avatar route input for the pre-generation step (image, provider, mode, backend) without changing existing renderer semantics.
3. THE generated clip, its transcript, and `captions.{json,srt,vtt}` SHALL be recorded together in the project manifest.

---

### Requirement 9: Honest fallback and no fabrication

**User Story:** As a user, I never want a fake or silently broken presenter, so I can trust the output.

#### Acceptance Criteria

1. THE skill SHALL NOT claim a presenter video exists unless a real MP4 passed media inspection.
2. WHEN generation is blocked (ineligible host, declined consent, missing model, provider failure), THE skill SHALL report the missing step, the measured values, and the exact retry command.
3. THE skill SHALL keep editable source (script, storyboard, voice files) when only generation is blocked.

---

### Requirement 10: Desktop integration and installer behavior

**User Story:** As a desktop host, I want to surface the offer and progress, so the user can install and start work from the UI.

#### Acceptance Criteria

1. `scripts/install_video_skill.py avatar-video` SHALL NOT hard-fail when HeyGen is absent; it SHALL probe the host, emit the eligibility/consent payload, and succeed when a local backend is available or the fallback is viable.
2. THE desktop docs (`docs/video-desktop-integration.md`, `docs/video-platforms.md`) SHALL document the probe, thresholds, consent event, install command, and per-OS support table.
3. THE probe and installer SHALL be callable from a Tauri command, relaying stderr JSON progress to a frontend channel.

---

### Requirement 11: Single-source generation wiring

**User Story:** As a maintainer, I want the new tools declared once, so bundle and standalone targets stay identical.

#### Acceptance Criteria

1. THE new tools SHALL be authored under `skills-src/_shared/tools/` and declared in `skills-src/manifest.yaml` for the `avatar-video` capability `shared_tools`.
2. `python scripts/gen_skills.py` SHALL emit the tools into both `avatar-video/tools/` and `course-creator/subskills/course-creator-avatar-video/tools/`.
3. `python scripts/gen_skills.py --check` SHALL pass after generation (no stale output).
4. THE `skills-src/avatar-video/skill.md` preflight and generation sections SHALL describe the probe, consent prompt, local provider, and dispatch order, and SHALL regenerate both targets.
5. `.gitignore` SHALL exclude `**/tools/avatar/models/`, `.venv/`, and `.tooling/` under the avatar tree.

---

### Requirement 12: Security, licensing, and privacy

**User Story:** As a user, I want downloads verified and licences respected, so I am not exposed legally or to tampered files.

#### Acceptance Criteria

1. EVERY model file SHALL be verified by size and SHA-256 before use; a mismatch SHALL abort with a clear error and keep the partial for retry.
2. THE consent prompt SHALL display each model's `license`, including non-commercial restrictions, and SHALL NOT auto-accept.
3. THE local backend SHALL treat all input media (photo, audio, footage) as local-only and SHALL NOT upload it.
4. THE skill SHALL require the user to confirm rights to any person's image before `photo` mode generation.
5. THE installer SHALL report total `downloadBytes` and `diskBytes` before starting and SHALL refuse to start if free disk is insufficient.
6. THE consent prompt SHALL show each backend's `licenseClass` and its component licences (the union of every file's source-repo licence), and the backend class SHALL be the worst class across its files.
7. THE manifest SHALL NOT ship a `research-only` backend in the default set; Wav2Lip is excluded unless explicitly re-enabled as opt-in (D1).

---

### Requirement 13: Performance envelope for short clips

**User Story:** As a user, I want realistic expectations, so I do not wait hours for a short result.

#### Acceptance Criteria

1. THE backend manifest SHALL declare `recommendedMaxSeconds` and `estimatedSecondsPerSecond` (or a coarse band) per backend.
2. WHEN the narration length exceeds `recommendedMaxSeconds`, THE skill SHALL warn and SHALL offer to split the script into segments and stitch (per Requirement 6).
3. THE skill SHALL state that resolution and accelerator tier dominate memory/time more than clip length, and SHALL surface the expected render time before starting.

---

### Requirement 14: Platform support boundaries

**User Story:** As a maintainer, I want explicit supported/unsupported platforms, so unsupported hosts fail clearly rather than half-working.

#### Acceptance Criteria

1. Supported local acceleration in this version SHALL be `cuda` (Windows/Linux, NVIDIA, ≥ 6 GiB VRAM) and `mps` (macOS arm64, ≥ 24 GiB unified memory).
2. AMD (`rocm`) and integrated/`cpu` hosts SHALL be reported ineligible with a reason and SHALL still have the fallback path; a future ROCm backend is out of scope.
3. WHEN the OS/arch combination cannot host the private runtime, THE installer SHALL report an unsupported-platform error and the exact reason.

---

### Requirement 15: Observability and resume

**User Story:** As an operator, I want machine-readable phases, so progress and failures are debuggable.

#### Acceptance Criteria

1. ALL new tools SHALL emit newline-delimited JSON on stderr with `phase` and `message`, and one JSON document on stdout, matching existing tool conventions.
2. Phase names SHALL align with the desktop contract: `probe → eligible → consent → download → verify → env → generate → package → complete`.
3. A failed generation SHALL keep its work directory and log; the job SHALL be resumable without re-downloading verified models.

---

### Requirement 16: Testing

**User Story:** As a maintainer, I want deterministic tests that run without a GPU, so CI stays green.

#### Acceptance Criteria

1. Unit tests SHALL cover the probe and selector using stubbed `nvidia-smi`/`sysctl` output and SHALL NOT require a GPU or network.
2. Tests SHALL cover: eligible cuda at exactly 6 GiB, ineligible cuda below 6 GiB, eligible mps at 24 GiB, ineligible mps below 24 GiB, multi-GPU selection, missing-tool degradation, and incompatible-backend rejection.
3. Tests SHALL cover consent gating (no download before consent), resumable download verification, and the unsupported `avatar`/`dub` mode responses.
4. Tests SHALL follow the existing `scripts/test_*.py` unittest style and SHALL be runnable via the existing test invocation.
5. `python scripts/gen_skills.py --check` and the new tests SHALL pass together.

---

## Non-Functional Requirements (cross-cutting)

### Requirement 17: Reliability and graceful degradation

**User Story:** As a user, I want setup failures to be recoverable, so I can resume instead of starting over.

#### Acceptance Criteria

1. IF a download, environment build, or generation step fails, THEN THE tool SHALL return `ready: false` with an `error` string and a retry command, and SHALL keep resumable state.
2. THE installer SHALL tolerate a re-run after partial failure (`--resume` equivalent) without re-downloading verified artifacts.
3. THE probe SHALL never raise on unsupported hosts; it SHALL always emit a parseable JSON document.

---

### Requirement 18: Observability and maintainability of config

**User Story:** As a maintainer, I want thresholds and model pins in data, not code, so updates are one-place edits.

#### Acceptance Criteria

1. THE thresholds, accelerator support, and model pins SHALL live in declarative JSON next to the tools.
2. UPDATING a model pin SHALL require editing only the manifest (no code change).
3. THE generated `SKILL.md` targets SHALL remain the only user-facing instructions; tool internals SHALL NOT be duplicated in prose.
