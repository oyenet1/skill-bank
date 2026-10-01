# Installation and LodgeStatus video audit

The September 30, 2026 Linux sandbox run finished successfully. A repeat setup and a read-only readiness check both passed. Measurements are recorded in [the audit data](video-installation-audit.json).

| Operation | Measured time | Result |
|---|---:|---|
| Published motion-graphics skill installation with a fresh npm cache | 5m 9.8s | CLI found all 13 skills and installed the requested skill |
| Published installation of all 13 skills with the same warmed CLI cache | 1m 48.2s | All 13 SKILL.md files present |
| Local skill files for the isolated runtime benchmark | 1m 8.4s | Requested skill installed |
| Runtime benchmark execution through successful setup, including failed attempts | 49m 52.4s | All required renderers, speech recognition, narration and associated skill copies ready |
| Entire benchmark elapsed time through final verification | 54m 20.6s | Includes manual storage/path recovery and repeat checks |
| Repeat cached setup | 7.8s | Ready; verified components reused |
| Read-only readiness check | 6.7s | Ready |
| Narration, renderer checks, rendering and assembly | 4m 55.7s | Five scenes, approximately 29.2s video |
| Generation plus measured transcription and caption rendering/revision | 5m 49.4s | Clean and captioned MP4s with editable sources |

These are separate measurements, not promises for another connection or machine. Runtime setup reused compatible system Node/npm, UV and FFmpeg, but installed isolated renderer packages, browsers, Python environments and speech models. No caches from the warm renderer runtime were seeded into the benchmark. The published CLI test and the local runtime test used separate sandboxes.

The first runtime attempt failed after an ASR wheel timeout and a Chromium extraction failure caused by the temporary filesystem's user quota. The ASR retry completed successfully. The same sandbox was moved to disk without discarding successful downloads. A resolved helper path became invalid during relocation; restoring its compatibility path allowed setup to resume. Failed attempts remain in the timing data. The new bootstrap retries only failed branches once and keeps verified components.

The CLI originally found only 11 skills because two generated YAML descriptions contained unquoted colons. YAML serialization now preserves those descriptions safely. Published discovery confirms motion-graphics-video and avatar-video are present. Generic `npx skills add` installs skill files; it has no repository post-install hook. The skill's first-use setup prepares tools and recursively copies associated skills. The README lists installable skills, prerequisite layers, optional avatar environments, and commands for inspecting actual transitive package versions.

The LodgeStatus promotion uses product-launch-video, motion-graphics-video, explainer-video, slide-decks, voice-narration, visual-assets and marketing-copy workflows. HyperFrames supplies three scenes, Remotion the connected-operations scene, Slidev the setup scene, Kokoro the narration, faster-whisper measured caption timestamps, and FFmpeg assembly. The public homepage was checked for the claims used in the script. Original public product assets are recorded with hashes and provenance. Nigeria is the audience; the selected voice is British English.

The generation benchmark used an already-ready renderer runtime. Its narration and recognition were produced using the isolated sandbox installations. Research, planning and manual authoring are excluded from machine-generation times. No presenter footage was supplied, and the avatar capability probe rejected this machine's AMD/ROCm hardware. Talking-head and avatar inference were therefore not exercised. Hosted avatar and paid image-provider jobs were not used.

The benchmark delivery contained clean/captioned MP4s, audio, reviewed SRT/VTT captions, a portable assembly plan, editable HTML/GSAP, Remotion and Slidev sources, and provenance. Generated deliveries are local outputs, excluded from Git, and are not retained in this skills repository.

Verification: 160 Python tests passed; all 625 generated files matched their sources. Five native video-runtime tests passed, with one ignored integration test. This verifies Linux behavior and source-level OS handling; it does not certify Windows/macOS installation or native app UI interactions. App changes were pushed to `feat/parallel-video-setup` in the devmock repository; unrelated concurrent app work was preserved.
