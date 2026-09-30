# Implementation Tasks

## Task List

- [ ] 1. Foundation — declarative config and capability probe
  - [x] 1.1 Create `skills-src/_shared/tools/avatar_models.json` with `schemaVersion`, `thresholds` (`cudaBytes` = 6 GiB, `mpsBytes` = 24 GiB), `defaults` (`cuda`, `mps`), and a `backends[]` skeleton carrying the full row shape (`id`, `displayName`, `modes`, `accel`, `minAccelMemoryBytes`, `qualityTier`, `license`, `sourceUrl`, `pythonVersion`, `recommendedMaxSeconds`, `estimatedSecondsPerSecond`, `files[]`) (Req 2.3, 4.1, 13.1, 18.1)
  - [ ] 1.2 Populate the registry from design Appendix A: `musetalk-15` (cuda default), `latentsync-15` (restricted, opt-in), `sadtalker` (cuda+mps compatibility), `musetalk-mps` (mps default), each with `license`, `licenseClass`, `revision`, and `files[]` carrying the pinned `bytes` + `sha256`; include `defaults: {cuda, mps}`; exclude Wav2Lip (Req 4.1, 4.3, 4.8, 12.6, D1)
  - [x] 1.3 Implement `skills-src/_shared/tools/avatar_probe.py`: `platform` OS/arch detection; CUDA via `nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits`; macOS `sysctl -n hw.memsize` on `arm64`; max-GPU selection; JSON stdout + stderr progress; never raises; no network (Req 1.1–1.7, 15.1, 17.3)
  - [x] 1.4 Implement the eligibility gate and candidate filter inside the probe using `avatar_models.json` (compatible `accel` ∧ `minAccelMemoryBytes ≤ memoryBytes`), ordered by `qualityTier` desc then `downloadBytes` asc (Req 2.1–2.5, 4.2, 4.3, 14.2)
  - [x] 1.5 Write `scripts/test_avatar_probe.py` covering: cuda at exactly 6 GiB (eligible), cuda below 6 GiB (ineligible), mps at 24 GiB, mps below 24 GiB, multi-GPU max selection, missing-binary degradation, `cpu`/`rocm` ineligible, and incompatible-backend rejection (Req 16.1, 16.2)
  - [x] 1.6 Add the manifest-build digest rule: a `tools/avatar_pin.py` (or build check) that resolves each file's `sha256` from the source repo's HuggingFace LFS `oid` and FAILS if any file lacks a digest (Req 4.9, 12.1, Appendix A)

- [ ] 2. Installer — consent, private runtime, verification
  - [x] 2.1 Implement `skills-src/_shared/tools/avatar_ensure.py` argument surface (`avatar-video`, `--backend`, `--check`) and the `consent-required` stderr payload with `displayName`, `qualityTier`, `license`, `downloadBytes`, `diskBytes`, `recommendedMaxSeconds`, and `installCommand` (Req 3.1, 3.8, 12.2)
  - [x] 2.2 Enforce consent: no model download and no environment creation before explicit consent; `--check` reports readiness without installing (Req 3.2, 3.5)
  - [x] 2.3 Add the disk-space precheck (sum `downloadBytes` + `diskBytes`) with a clear refusal error (Req 12.5)
  - [x] 2.4 Implement the private runtime under `<user-data>/skill-bank/avatar/` with `SKILL_BANK_AVATAR_HOME` override; reuse/privately install `uv` (PowerShell on Windows, `sh` otherwise); private venv at the backend `pythonVersion`; requirements hash marker (mirror `tools/kokoro/start.py` patterns) (Req 5.1–5.4, 5.6)
  - [x] 2.5 Implement resumable model downloads to `<runtime>/models/<backend>/` with `<file>.part`, size + SHA-256 verification, and idempotent re-run (`ready:true`, no download) (Req 3.6, 3.7, 5.5, 12.1, 17.2)
  - [x] 2.6 Emit JSON result `{ready, route, backend, paths, missing, error?}` and stderr phases `uv → python → packages → model → verify → complete` (Req 5.6, 15.1, 15.2, 17.1)
  - [x] 2.7 Write `scripts/test_avatar_ensure.py` covering: no download before consent, `--check` non-mutating, resumable/verification behavior with a stubbed server or pre-seeded files, idempotency, disk-refusal, and unchanged `PATH`/profile (Req 16.3)
  - [ ] 2.8 Implement the MPS smoke gate: a bundled portrait+WAV fixture run through `musetalk-mps`, marking it ready only on a valid MP4 and otherwise offering `sadtalker`; embed the port at commit `7fd019315127d7f31e2e7f9853547ddceabbeb6e` (Req 4.10, D2)

- [ ] 3. Generator — local photo-mode clip
  - [x] 3.1 Implement `skills-src/_shared/tools/avatar_generate.py` CLI (`--mode`, `--backend`, `--image`, `--audio`, `--out`) writing `video.mp4` + `manifest.json` (Req 6.1)
  - [x] 3.2 Wire the `photo` inference path for the selected backend (config-driven entrypoint per backend), invoked only from the private venv (Req 6.2, 5.4)
  - [x] 3.3 Return `ready:false` with `local-avatar-mode-unsupported` / `local-dub-mode-unsupported` for `avatar`/`dub`; never fabricate output (Req 6.3, 6.4, 9.1)
  - [x] 3.4 Add SIGTERM cancellation, `.work-<id>` staging, and no partial `video.mp4` on failure (Req 6.6, 15.3)
  - [x] 3.5 Verify the produced MP4 with FFprobe (video stream + non-zero duration) before success; warn past `recommendedMaxSeconds` (Req 6.7, 6.8, 13.2)
  - [x] 3.6 Emit stdout `{ready, backend, mode, video, durationSec, elapsedSec, unsupportedReason?, error?}` and stderr progress (Req 6.5, 15.1)
  - [x] 3.7 Write `scripts/test_avatar_generate.py` covering unsupported-mode responses, FFprobe verification gate, cancellation cleanup, and duration warning (Req 16.3)

- [ ] 4. Dispatcher — provider order and fallback
  - [x] 4.1 Implement `skills-src/_shared/tools/avatar_provider.py` resolving `local → heygen → fallback`, honoring `--provider` and `SKILL_BANK_AVATAR_PROVIDER` (Req 7.1, 7.2)
  - [x] 4.2 Emit `{provider, backend?, reason, blocked?, retryCommand?}`; local never requires HeyGen, HeyGen never requires a local backend (Req 7.3, 7.5, 9.2)
  - [x] 4.3 Verify the fallback delivers `script.md` + verified Kokoro WAV/MP3 + storyboard and states the blocked step + retry command (Req 7.4, 9.2, 9.3)
  - [x] 4.4 Write `scripts/test_avatar_provider.py` covering order resolution, explicit-override failure, and fallback payload (Req 16.3)

- [ ] 5. Single-source wiring and regeneration
  - [x] 5.1 Add the four tools to `skills-src/manifest.yaml` under `avatar-video.shared_tools` (and confirm they land for the bundle target) (Req 11.1)
  - [x] 5.2 Update `skills-src/avatar-video/skill.md` preflight + generation sections to describe probe → consent prompt → local provider → dispatch order, and the honest fallback (Req 11.4, 7, 9)
  - [x] 5.3 Run `python scripts/gen_skills.py` and confirm `avatar-video/tools/` and `course-creator/subskills/course-creator-avatar-video/tools/` both receive the tools (Req 11.2)
  - [x] 5.4 Run `python scripts/gen_skills.py --check` and fix until clean (Req 11.3, 16.5)
  - [x] 5.5 Extend `.gitignore` for the avatar model/venv/tooling trees under generated targets (Req 11.5)

- [ ] 6. Job contract and desktop integration
  - [x] 6.1 Extend `run_video_job.py` (via the shared tool) to accept avatar pre-generation inputs (`mode`, `provider`, `backend`, `image`) and record `provider`/`backend`/`accel`/`consent` in job state and manifest, without altering renderer semantics (Req 8.2, 4.6, 7.3)
  - [x] 6.2 Make `scripts/install_video_skill.py avatar-video` probe the host and offer/verify the local backend; stop hard-failing when HeyGen is absent; keep `--resume` (Req 10.1, 17.2)
  - [x] 6.3 Emit the probe/consent JSON so a Tauri command can relay stderr progress to a frontend channel (Req 10.3)
  - [x] 6.4 Update `docs/video-platforms.md` with the per-OS accelerator + memory support table and thresholds (Req 10.2, 14.1, 14.2)
  - [x] 6.5 Update `docs/video-desktop-integration.md` with the local provider row, consent event, install command, and remaining verification work (Req 10.2)
  - [x] 6.6 Update `docs/video-job-contract.md` with the avatar pre-generation request fields and result additions (Req 8.2)

- [ ] 7. Security, licensing, and performance surfacing
  - [x] 7.1 Ensure the consent payload prints each backend's `license` including non-commercial restrictions and requires explicit acceptance (Req 12.2, 3.2)
  - [x] 7.2 Confirm no code path uploads local media; add a check/test asserting the local generator makes no outbound request (Req 12.3)
  - [x] 7.3 Add the image-rights confirmation step to the skill intake for `photo` mode (Req 12.4)
  - [x] 7.4 Surface `recommendedMaxSeconds` and the expected render-time band before generation starts (Req 13.1, 13.3)

- [ ] 8. Verification and documentation closeout
  - [x] 8.1 Run the full test suite (`scripts/test_*.py`) including the new avatar tests (Req 16.4)
  - [x] 8.2 Add a short `skills-src/_shared/tools/avatar_models.json` maintenance note (how to update a pin) in the generated `tools/` README or the skill references (Req 18.2)
  - [ ] 8.3 Run a Linux + NVIDIA end-to-end smoke test: install `musetalk-15` and render a ~10 s photo-mode clip (Req 14.1, D1)
  - [ ] 8.4 Run a macOS arm64 end-to-end smoke test through the MPS gate, confirming the fallback to `sadtalker` when the port fails (Req 4.10, 14.1, D2)
  - [ ] 8.5 [P] Run a Windows + NVIDIA end-to-end smoke test on a real machine before release, covering the PowerShell/`uv` bootstrap (Req 14.1, D3)
  - [ ] 8.6 Confirm no backend file has a null `sha256` and that the registry matches design Appendix A (Req 4.9, 12.1)

## Verification and deviations (2026-09-30)

Source integration is implemented in Skill Bank and devmock, including searchable
backend selection, model/licence consent, native detection without Python,
private environments, offline inference, fallback assets, scene handoff, provenance
and original-request resume. All 136 Python tests passed. Tests include actual media packaging with
stubbed inference and actual Linux process-tree cancellation. The configured
app type check now includes Vue components and passes. Missing storyboard actions
and obsolete component sizes found by the full check were fixed and tested. Native Rust was
formatted/parsed; no desktop build was run, as requested.

Tasks 1.2, 2.8, 8.4 and 8.6 cannot match the Appendix exactly: SadTalker's bundled
Basel Face Model data is research/noncommercial and is kept in disabledBackends.
The MPS smoke gate is implemented, but failed inference never installs that
unlicensed compatibility fallback. A licensed replacement is needed. All 38
unique model/configuration digests were checked against pinned upstream metadata.

Dependency resolution passed on Linux/Windows for CUDA MuseTalk and LatentSync,
and on macOS arm64 with Python 3.11 for MuseTalk MPS. Source package allowlists
cover legacy pure Python dependencies; native dependencies require wheels.
Actual NVIDIA Windows/Linux and Apple Silicon inference tasks remain unchecked:
this host reports AMD/ROCm and is ineligible. No local presenter inference success
is claimed from stubbed tests or dependency resolution.
