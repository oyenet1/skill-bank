# Design Document: Local Avatar (Talking-Head) Backend

## Overview

Add an optional, fully local presenter backend to `avatar-video`. A network-free
probe reads the host OS and accelerator; an eligibility gate decides whether the
machine may be offered a local model; a consent prompt precedes any download; a
private, SHA-256-verified runtime installs only accelerator-compatible models;
and a generator produces a `photo`-mode talking-head clip that flows through the
existing local captioning/rendering pipeline. HeyGen remains the optional hosted
provider, and the script + Kokoro voice + storyboard fallback is unchanged.
Everything is authored in `skills-src/_shared/tools/`, declared once in
`manifest.yaml`, and generated into both targets (Req 11).

---

## Architecture

### High-Level Structure

```
                      skills-src/_shared/tools/            (single source, Req 11)
                      ├── avatar_probe.py        probe OS/GPU      (Req 1,2)
                      ├── avatar_models.json     pins + thresholds (Req 4,13,18)
                      ├── avatar_ensure.py       consent + install (Req 3,5,12)
                      ├── avatar_generate.py     local clip        (Req 6,13)
                      └── avatar_provider.py     dispatch          (Req 7,9)
                                   │
                 scripts/gen_skills.py  ──► avatar-video/tools/*
                                   │       course-creator/subskills/course-creator-avatar-video/tools/*
                                   ▼
┌──────────────────────────── avatar-video SKILL.md ────────────────────────────┐
│ Preflight (Req 11)                                                            │
│   avatar_probe.py ─► eligible?                                                │
│        │no                         │yes                                       │
│        ▼                           ▼                                          │
│   provider dispatch        consent prompt (Req 3) ──► user says yes           │
│        │                           ▼                                          │
│        │                    avatar_ensure.py ──► private runtime (Req 5)      │
│        │                           ▼                                          │
│        │                    avatar_provider.py ─► avatar_generate.py (Req 6)  │
│        ▼                           ▼                                          │
│   fallback (script+kokoro)   generated footage ─► existing packaging (Req 8)  │
└───────────────────────────────────────────────────────────────────────────────┘
         │                                                   │
         ▼                                                   ▼
  HeyGen CLI (optional hosted)                 HyperFrames render + captions
```

### Component Relationships

- `avatar_probe.py` is **read-only and network-free** (Req 1.5); it is the only
  component that inspects hardware.
- `avatar_ensure.py` consumes the probe result and `avatar_models.json`; it is
  the only component that writes to the private runtime (Req 5).
- `avatar_generate.py` consumes an installed backend and local media; it is the
  only component that invokes model inference (Req 6).
- `avatar_provider.py` is the single decision point for `local | heygen |
  fallback` (Req 7) and is the only place the order is encoded.
- Packaging is unchanged: the generated MP4 is footage to the existing tools
  (Req 8).

---

## Components and Interfaces

### 1. `avatar_probe.py` — capability probe

Responsibilities:
- Detect `os`/`arch`, accelerator, memory, and source (Req 1.1).
- Apply thresholds and report `eligible` + `reason` (Req 2).
- Never raise; always emit JSON (Req 1.4, 17.3).

Key interfaces:
```typescript
interface ProbeResult {
  schemaVersion: 1
  os: "Windows" | "Darwin" | "Linux"
  arch: "x64" | "arm64"
  accelerator: {
    kind: "cuda" | "mps" | "rocm" | "cpu" | "unknown"
    name: string | null
    memoryBytes: number | null
    source: string          // "nvidia-smi" | "sysctl:hw.memsize" | ...
  }
  thresholdBytes: number | null
  eligible: boolean
  reason: string
  candidates: string[]      // compatible backend ids (Req 4.2)
}
```

Key behaviors:
- CUDA via `nvidia-smi`; pick max `memory.total` when several GPUs (Req 1.7).
- macOS: Darwin + `arm64` → `mps`, memory from `sysctl -n hw.memsize` (Req 1.3).
- `rocm`/`cpu`/unknown → ineligible with accelerator named (Req 2.4, 14.2).
- Thresholds loaded from `avatar_models.json` (Req 2.3, 18.1).

### 2. `avatar_models.json` — declarative manifest

Responsibilities:
- Pin thresholds, accelerator support, model files, licences, and performance
  bands (Req 4.1, 13.1, 18.1).

Key interfaces:
```typescript
interface BackendManifest {
  schemaVersion: 1
  thresholds: { cudaBytes: number; mpsBytes: number }   // Req 2.1,2.2
  defaults: { cuda: string; mps: string }                // Req 4.5
  backends: Backend[]
}
interface Backend {
  id: string
  displayName: string
  modes: ("photo" | "avatar" | "dub")[]                  // Req 4.1, 6.3,6.4
  accel: ("cuda" | "mps")[]
  minAccelMemoryBytes: number
  qualityTier: number
  license: string
  licenseClass: "permissive" | "restricted" | "research-only"   // Req 4.8, 12.6
  sourceUrl: string
  revision: string                                       // pinned commit / HF revision
  pythonVersion: string
  recommendedMaxSeconds: number                          // Req 13.1
  estimatedSecondsPerSecond: [number, number]
  files: { name: string; bytes: number; sha256: string; url: string }[]
}
```

Key behaviors:
- Only rows whose `accel` includes the detected accelerator and whose
  `minAccelMemoryBytes` fits are candidates (Req 4.2).
- Update a pin by editing this file only (Req 18.2).

### 3. `avatar_ensure.py` — consent-gated installer

Responsibilities:
- Emit the consent payload and refuse to download before consent (Req 3.1,3.2).
- Build the private runtime and verify every file (Req 5, 12.1).
- Report disk needs and refuse on insufficient space (Req 12.5).

Key interfaces:
```typescript
interface ConsentPayload {
  phase: "consent-required"
  message: string
  accelerator: "cuda" | "mps"
  candidates: {
    id: string; displayName: string; qualityTier: number
    license: string; downloadBytes: number; diskBytes: number
    recommendedMaxSeconds: number
  }[]
  installCommand: string     // "python3 tools/avatar_ensure.py avatar-video --backend <id>"
}
```

Key behaviors:
- `--check` reports readiness without installing (Req 3.5).
- Idempotent when satisfied (Req 3.6).
- Resumable `.part` downloads with size + SHA-256 (Req 3.7, 12.1).
- Reuses/privately installs `uv`; no global changes (Req 5.3).
- Phases `uv → python → packages → model → verify → complete` (Req 5.6, 15.2).

### 4. `avatar_generate.py` — local generation

Responsibilities:
- Produce a `photo`-mode lip-synced clip; report unsupported modes honestly
  (Req 6.1–6.4).
- Verify the MP4 and support cancellation (Req 6.6, 6.7).

Key interfaces:
```typescript
interface GenerateResult {
  ready: boolean
  backend: string
  mode: "photo" | "avatar" | "dub"
  video: string | null
  durationSec: number | null
  elapsedSec: number
  unsupportedReason?: "local-avatar-mode-unsupported" | "local-dub-mode-unsupported"
  error?: string
}
```

Key behaviors:
- `avatar`/`dub` → `ready:false` + reason, never fabricate (Req 6.3, 6.4, 9.1).
- SIGTERM cancels; failed work stays in `.work-<id>` (Req 6.6, 15.3).
- Warns past `recommendedMaxSeconds` (Req 6.8, 13.2).

### 5. `avatar_provider.py` — dispatch

Responsibilities:
- Resolve `local → heygen → fallback` unless overridden (Req 7.1, 7.2).
- Report provider and reason (Req 7.3, 9.2).

Key interfaces:
```typescript
interface ProviderDecision {
  provider: "local" | "heygen" | "fallback"
  backend?: string
  reason: string
  blocked?: string            // exact missing step when fallback (Req 9.2)
  retryCommand?: string
}
```

Key behaviors:
- Explicit `--provider` / `SKILL_BANK_AVATAR_PROVIDER` fails loudly if it cannot
  run (Req 7.2).
- Local path never requires HeyGen; HeyGen path never requires a local backend
  (Req 7.5).

### 6. Skill prose + generation wiring

Responsibilities:
- Describe probe → consent → local generation and dispatch in
  `skills-src/avatar-video/skill.md` (Req 11.4).
- Declare tools in `manifest.yaml` `shared_tools` (Req 11.1).
- Regenerate both targets; `--check` clean (Req 11.2, 11.3).
- Extend `.gitignore` for avatar model/venv dirs (Req 11.5).

### 7. Job contract + desktop

Responsibilities:
- Add an avatar pre-generation input (image, provider, mode, backend) without
  changing renderer semantics (Req 8.2).
- Make `install_video_skill.py` probe + offer instead of hard-failing on
  missing HeyGen (Req 10.1).
- Document probe, thresholds, consent event, install command, per-OS table
  (Req 10.2, 14.1, 14.2).

---

## Data Model

### Backend row (`avatar_models.json` → `backends[]`)

| Column | Type | Constraints | Notes |
|---|---|---|---|
| id | string | PK, kebab-case | `musetalk-15`, `latentsync-15`, `sadtalker`, `musetalk-mps` (D1) |
| displayName | string | NOT NULL | Shown in consent |
| modes | string[] | NOT NULL, ⊆ {photo,avatar,dub} | `photo` required |
| accel | string[] | NOT NULL, ⊆ {cuda,mps} | Req 4.2 |
| minAccelMemoryBytes | integer | NOT NULL | VRAM/unified floor |
| qualityTier | integer | NOT NULL | Higher = better (Req 4.3) |
| license | string | NOT NULL | Surfaced at consent (Req 12.2) |
| licenseClass | enum | NOT NULL, ⊆ {permissive,restricted,research-only} | Worst across files (Req 4.8, 12.6) |
| sourceUrl | string | NOT NULL | Provenance |
| revision | string | NOT NULL | Pinned commit / HF revision (Appendix A) |
| pythonVersion | string | NOT NULL | e.g. `3.10` |
| recommendedMaxSeconds | integer | NOT NULL | Req 13.1 |
| estimatedSecondsPerSecond | [number, number] | NOT NULL | Req 13.1 |
| files | object[] | NOT NULL | `{name,bytes,sha256,url}` |

Indexes / selection:
- Candidate filter: `accel ∋ detected` ∧ `minAccelMemoryBytes ≤ memoryBytes`.
- Order: `qualityTier` desc, then `downloadBytes` asc (Req 4.3).

### Job state additions (`<output>.job-state.json`)

| Field | Type | Notes |
|---|---|---|
| provider | string | `local`/`heygen`/`fallback` (Req 7.3) |
| backend | string \| null | Chosen model id (Req 4.6) |
| accel | object \| null | Probe snapshot for reproducibility |
| consent | string | `granted`/`declined`/`not-needed` (Req 3.4) |

### Private runtime layout (Req 5.1)

```
<user-data>/skill-bank/avatar/
├── .tooling/uv[.exe]
├── .venv/                      # pinned Python
├── .requirements-<backend>.sha256
└── models/<backend>/<files…>
```

---

## API Contracts

### `avatar_probe.py`

#### `python3 tools/avatar_probe.py avatar-video [--json]`

**Description:** Read-only capability scan (Req 1, 2).

**Response (stdout):**
```json
{
  "schemaVersion": 1,
  "os": "Linux",
  "arch": "x64",
  "accelerator": { "kind": "cuda", "name": "NVIDIA GeForce RTX 3060",
                   "memoryBytes": 12884901888, "source": "nvidia-smi" },
  "thresholdBytes": 6442450944,
  "eligible": true,
  "reason": "cuda-vram-above-threshold",
  "candidates": ["musetalk", "sadtalker", "wav2lip"]
}
```

**Ineligible example:**
```json
{ "schemaVersion": 1, "os": "Linux", "arch": "x64",
  "accelerator": { "kind": "cpu", "name": null, "memoryBytes": null, "source": "none" },
  "thresholdBytes": null, "eligible": false,
  "reason": "unsupported-accelerator:cpu", "candidates": [] }
```

### `avatar_ensure.py`

#### `python3 tools/avatar_ensure.py avatar-video [--backend <id>] [--check]`

**Description:** Consent-gated install/verify (Req 3, 5, 12).

**Consent (stderr, when needed):**
```json
{ "phase": "consent-required", "accelerator": "cuda",
  "candidates": [ { "id": "sadtalker", "qualityTier": 3, "license": "Apache-2.0",
                    "downloadBytes": 2147483648, "diskBytes": 5368709120,
                    "recommendedMaxSeconds": 30 } ],
  "installCommand": "python3 tools/avatar_ensure.py avatar-video --backend sadtalker" }
```

**Response (stdout success):**
```json
{ "ready": true, "route": "avatar-video", "backend": "sadtalker",
  "paths": { "python": "...", "models": "..." }, "missing": [] }
```

**Response (error):**
```json
{ "ready": false, "route": "avatar-video", "missing": ["model:sadtalker"],
  "error": "insufficient disk (need 5 GiB, have 1.2 GiB)" }
```

### `avatar_generate.py`

#### `python3 tools/avatar_generate.py --mode photo --backend <id> --image <path> --audio <wav> --out <dir>`

**Description:** Local presenter generation (Req 6).

**Response (stdout success):**
```json
{ "ready": true, "backend": "sadtalker", "mode": "photo",
  "video": "<dir>/video.mp4", "durationSec": 18.4, "elapsedSec": 212.7 }
```

**Response (unsupported mode):**
```json
{ "ready": false, "backend": "sadtalker", "mode": "avatar",
  "video": null, "durationSec": null, "elapsedSec": 0,
  "unsupportedReason": "local-avatar-mode-unsupported" }
```

### `avatar_provider.py`

#### `python3 tools/avatar_provider.py avatar-video [--provider auto|local|heygen|fallback]`

**Description:** Provider decision (Req 7).

**Response (stdout):**
```json
{ "provider": "local", "backend": "sadtalker",
  "reason": "eligible-cuda-and-installed",
  "blocked": null, "retryCommand": null }
```

**Fallback example:**
```json
{ "provider": "fallback", "reason": "ineligible:unsupported-accelerator:cpu",
  "blocked": "presenter render", "retryCommand": "python3 tools/avatar_ensure.py avatar-video" }
```

---

## Security Considerations

- All downloads size- and SHA-256-verified before use; mismatch aborts and keeps
  the partial (Req 12.1, 3.7).
- Consent is mandatory before download; each backend's `licenseClass` and component
  licences are shown, and `restricted` requires explicit opt-in (Req 3.2, 12.2, 12.6).
- Media stays local; the local path makes no network calls at generation time
  (Req 12.3).
- Image-rights confirmation before `photo` mode (Req 12.4).
- No global `pip`/`npm`/shell-profile changes; everything is in user data
  (Req 5.3).
- Disk precheck before starting (Req 12.5).

---

## Deployment & Infrastructure

- **Runtime**: Python 3.10+ (probe/dispatch), private per-backend Python via
  `uv`, FFmpeg/FFprobe via the existing `ensure_video_runtime.py` (Req 8.1).
- **Environment variables**: `SKILL_BANK_AVATAR_HOME` (runtime override, Req
  5.2), `SKILL_BANK_AVATAR_PROVIDER` (dispatch override, Req 7.2).
- **Supported platforms** (Req 14.1): Windows/Linux + NVIDIA CUDA ≥ 6 GiB;
  macOS arm64 + ≥ 24 GiB unified memory. AMD/integrated → ineligible (Req 14.2).
- **Platform data dirs** (Req 5.1): `%LOCALAPPDATA%`, `~/Library/Application
  Support`, `${XDG_DATA_HOME:-~/.local/share}` under `skill-bank/avatar`.
- **Distribution**: files authored in `skills-src/_shared/tools/`, declared in
  `manifest.yaml`, emitted by `scripts/gen_skills.py` into both targets; no new
  package manager and no install hook beyond the existing first-use installer
  (Req 10, 11).

---

## Resolved Decisions (was: open items)

### D1 — Backend registry and defaults (Req 4, 12)

| id | accel | min memory | tier | license / class | modes | role |
|---|---|---|---|---|---|---|
| `musetalk-15` | cuda | 6 GiB | 3 | MIT · permissive | photo | **CUDA default** |
| `latentsync-15` | cuda | 8 GiB | 4 | OpenRAIL++ · restricted | photo | premium opt-in |
| `sadtalker` | cuda, mps | 6 GiB / 24 GiB | 2 | Apache-2.0 code, MIT weights · permissive | photo | compatibility floor |
| `musetalk-mps` | mps | 24 GiB | 3 | MIT · permissive | photo | **MPS default** |

- `defaults = { cuda: "musetalk-15", mps: "musetalk-mps" }`. The `defaults` entry
  **wins over `qualityTier` ordering** (amended Req 4.3): MuseTalk is the default
  because it is both permissive and fast enough to fit the 6 GiB floor; LatentSync
  1.5 is offered as the opt-in premium for ≥ 8 GiB hosts.
- **Wav2Lip is excluded from the registry.** Upstream is now research/non-commercial
  (the repository redirects to a paid endpoint and ships no licence). It is not
  offered, so the licence surface stays permissive. It MAY return later behind
  `licenseClass: research-only` and never auto-selected (Req 4, Req 12).
- **LivePortrait is excluded**: it is video-driven, not audio-driven, and its
  InsightFace models carry non-commercial terms.
- Licence rule: `licenseClass` ∈ `permissive` | `restricted` | `research-only`;
  a backend's class is the **worst** class across its files (Req 12); `restricted`
  requires explicit user opt-in; `research-only` is never selected automatically.

### D2 — MPS path (Req 4, 6, 14)

- Default MPS backend is **`musetalk-mps`** = the MuseTalk 1.5 inference weights
  (identical to the CUDA set) driven by the Apple-Silicon MPS port
  `barnent1/musetalk-mac` pinned by commit, with `PYTORCH_ENABLE_MPS_FALLBACK=1`.
  It reuses the repo's existing Python/torch/`uv` stack (no second runtime). The
  MLX variant (`mlx-community/MuseTalk-1.5-fp16`) is recorded as a future option,
  not the default (it would add an MLX runtime).
- **Validation gate (Req 4.10).** The port is community-maintained, so `avatar_ensure.py`
  SHALL run a bundled ~3-second smoke inference (fixture portrait + fixture WAV) and
  SHALL mark `musetalk-mps` ready **only if it produces a valid MP4**. On failure it
  SHALL NOT install it and SHALL offer **`sadtalker`** (official Apache-2.0, runs on
  Apple Silicon with MPS fallback to CPU — slower but verified) as the MPS fallback.
- SadTalker on Mac is honest-but-slow: its `conv3d` falls back to CPU, so the consent
  prompt SHALL show it as `slow` and MuseTalk-MPS as the fast default.

### D3 — Windows CUDA scope (Req 14)

- **Windows CUDA is in the first release, at parity with Linux.** `nvidia-smi` works
  on Windows; the private `uv`/PowerShell, Node, and FFmpeg paths already used by the
  repo cover Windows. In scope: Windows x64 + NVIDIA ≥ 6 GiB, Linux x64 + NVIDIA ≥ 6 GiB,
  macOS arm64 ≥ 24 GiB.
- A native Windows/NVIDIA smoke test is a release gate, not a scoping question
  (see tasks 8.3).

---

## Appendix A — Model pins

Revisions are the upstream defaults verified on 2026-09-30. Every file MUST carry a
non-null `sha256` (Req 12.1); the manifest-build step fails if any source publishes
no digest (it resolves digests from HuggingFace LFS `oid`).

### A.1 MuseTalk 1.5 inference set (used by `musetalk-15` and `musetalk-mps`)

| Destination path | Source repo @ revision | bytes | sha256 |
|---|---|---|---|
| `musetalkV15/unet.pth` | `TMElyralab/MuseTalk` @ `2bcb936e2fddb4d86db4c62fd45b387d0c061571` | 3400074924 | `7ebf6c98c181e20838e4c0054e96e944ac60d5d692cc01db42839fe11b787007` |
| `sd-vae/diffusion_pytorch_model.bin` | `stabilityai/sd-vae-ft-mse` @ `31f26fdeee1355a5c34592e401dd41e45d25a493` | 334707217 | `1b4889b6b1d4ce7ae320a02dedaeff1780ad77d415ea0d744b476155c6377ddc` |
| `whisper/pytorch_model.bin` | `openai/whisper-tiny` @ `169d4a4341b33bc18d8881c4b69c2e104e1cc0af` | 151095027 | `9607f98a2b22d9e229ae43c52ecea79dcede9e0c5cfae67e8da6eda86d8aac1d` |
| `dwpose/dw-ll_ucoco_384.pth` | `yzd-v/DWPose` @ `1a7144101628d69ee7a3768d1ee3a094070dc388` | 406878486 | `0d9408b13cd863c4e95a149dd31232f88f2a12aa6cf8964ed74d7d97748c7a07` |
| `face-parse-bisent/79999_iter.pth` | `ManyOtherFunctions/face-parse-bisent` @ `0073b233a5a3c4b1377d4dbf49245017938a72b5` | 53289463 | `468e13ca13a9b43cc0881a9f99083a430e9c0a38abd935431d1c28ee94b26567` |
| `face-parse-bisent/resnet18-5c106cde.pth` | `ManyOtherFunctions/face-parse-bisent` @ `0073b233a5a3c4b1377d4dbf49245017938a72b5` | 46827520 | `5c106cde386e87d4033832f2996f5493238eda96ccf559d1d62760c4de0613f8` |

Optional (evaluation only, not required for inference), `licenseClass: restricted`:
`syncnet/latentsync_syncnet.pt` | `ByteDance/LatentSync` @ `405eda8eab9f65c1a6e0c292a5dee5a08089e2ae` | 1488019828 | `38fa63bad3ed2332f647c40a5dc616cb0e233db8579f698f62af4c41965c4da5`.

Small configs (`musetalkV15/musetalk.json`, `config.json`, `preprocessor_config.json`) ship from the
same pinned revisions with their own recorded digests.

### A.2 LatentSync 1.5 set (`latentsync-15`, OpenRAIL++)

All from `ByteDance/LatentSync-1.5` @ `32a20d29aead0498e3e885e90dbbe8027da1b61b`:

| file | bytes | sha256 |
|---|---|---|
| `latentsync_unet.pt` | 5072348184 | `6440b49a7ccceff56cdc001f5f17605216337f5bbd66fa360139768926e23f51` |
| `stable_syncnet.pt` | 1605324224 | `dccc464554b85ed939ae5cf63000e5803d4b21d8c7dae2260544a10aeb1ac483` |
| `whisper/tiny.pt` | 75572083 | `65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9` |
| `auxiliary/2DFAN4-cd938726ad.zip` | 96316515 | `cd938726adb1f15f361263cce2db9cb820c42585fa8796ec72ce19107f369a46` |
| `auxiliary/s3fd-619a316812.pth` | 89843225 | `619a31681264d3f7f7fc7a16a42cbbe8b23f31a256f75a366e5a1bcd59b33543` |
| `auxiliary/sfd_face.pth` | 89844381 | `d54a87c2b7543b64729c9a25eafd188da15fd3f6e02f0ecec76ae1b30d86c491` |
| `auxiliary/i3d_torchscript.pt` | 51235320 | `bec6519f66ea534e953026b4ae2c65553c17bf105611c746d904657e5860a5e2` |
| `auxiliary/vgg16-397923af.pth` | 553433881 | `397923af8e79cdbb6a7127f12361acd7a2f83e06b05044ddf496e83de57a5bf0` |
| `auxiliary/vit_g_hybrid_pt_1200e_ssv2_ft.pth` | 2023804201 | `5a210a92f035dff30c53b46157b612e7a1a5d3c99700e1b2d71da5c399ca7e70` |
| `auxiliary/koniq_pretrained.pkl` | 109768650 | `ff9277bcc68ecc10e77d88b6d0a32825ec3c85562095542734ec6212eaaf6d81` |
| `auxiliary/syncnet_v2.model` | 54573114 | `961e8696f888fce4f3f3a6c3d5b3267cf5b343100b238e79b2659bff2c605442` |

### A.3 SadTalker set (`sadtalker`, Apache-2.0 code / MIT weights)

All from `vinthony/SadTalker` @ `4aedd064359e623398a2d73eb8c253ebb2bd516c`:

| file | bytes | sha256 |
|---|---|---|
| `epoch_20.pth` | 288860037 | `6d17a6b23457b521801baae583cb6a58f7238fe6721fc3d65d76407460e9149b` |
| `facevid2vid_00189-model.pth.tar` | 2112619148 | `fbad01d46f0510276dc4521322dde6824a873a4222cd0740c85762e7067ea71d` |
| `auido2exp_00300-model.pth` | 34278319 | `b7608f0e6b477e50e03ca569ac5b04a841b9217f89d502862fc78fda4e46dec4` |
| `auido2pose_00140-model.pth` | 95916155 | `4fba6701852dc57efbed25b1e4276e4ff752941860d69fc4429f08a02326ebce` |
| `mapping_00109-model.pth.tar` | 155779231 | `84a8642468a3fcfdd9ab6be955267043116c2bec2284686a5262f1eaf017f64c` |
| `mapping_00229-model.pth.tar` | 155521183 | `62a1e06006cc963220f6477438518ed86e9788226c62ae382ddc42fbcefb83f1` |
| `BFM_Fitting/01_MorphableModel.mat` | 240875364 | `37b1f0742db356a3b1568a8365a06f5b0fe0ab687ac1c3068c803666cbd4d8e2` |
| `BFM_Fitting/BFM09_model_info.mat` | 127170280 | `db8d00544f0b0182f1b8430a3bb87662b3ff674eb33c84e6f52dbe2971adb81b` |
| `BFM_Fitting/Exp_Pca.bin` | 51086404 | `e7f31380e6cbdaf2aeec698db220bac4f221946e4d551d88c092d47ec49b1726` |
| `hub/checkpoints/2DFAN4-cd938726ad.zip` | 96316515 | `cd938726adb1f15f361263cce2db9cb820c42585fa8796ec72ce19107f369a46` |
| `hub/checkpoints/s3fd-619a316812.pth` | 89843225 | `619a31681264d3f7f7fc7a16a42cbbe8b23f31a256f75a366e5a1bcd59b33543` |
| `shape_predictor_68_face_landmarks.dat` | 99693937 | `fbdc2cb80eb9aa7a758672cbfdda32ba6300efe9b6e6c7a299ff7e736b11b92f` |

**Do NOT download** `wav2lip.pth` from this repo: its provenance is research/non-commercial
and it is not required for SadTalker inference (licence hygiene, D1).

### A.4 Code pins (not weights)

| Component | Repo @ commit |
|---|---|
| MuseTalk inference | `TMElyralab/MuseTalk` @ `0a89dec45a0192b824e3cf4daf96c239440c5ed8` |
| Apple-Silicon MPS port | `barnent1/musetalk-mac` @ `7fd019315127d7f31e2e7f9853547ddceabbeb6e` |
| SadTalker inference | `OpenTalker/SadTalker` @ `cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8` |
| LatentSync inference | `bytedance/LatentSync` @ `main` (pin at first verified download) |

Composite licence note: `musetalk-15`/`musetalk-mps` = MIT code, with MIT (sd-vae, whisper),
Apache-2.0 (DWPose), WTFPL (face-parse-bisent) components; the optional syncnet checkpoint is
OpenRAIL++ and is excluded from the default install. `latentsync-15` = OpenRAIL++ (restricted,
explicit opt-in). `sadtalker` = Apache-2.0 code + MIT-published weights.
