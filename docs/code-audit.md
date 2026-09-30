# Source and installation audit — 2026-09-30

Audited the skill sources, generator, dependency installers, private runtimes,
video jobs, narration, transcription, generated distributions, and the DevMock
integration. App builds and Cargo compilation were not run, as requested.

## Fixes delivered

| Finding | Fix |
|---|---|
| Installing direct sibling skills could leave indirect dependencies missing | Resolve the entire bundled graph from hash-verified dependency manifests, visit cycles once, preserve existing skills, and install missing dependencies into the exact requested root. Existing direct dependencies also trigger indirect dependency checks. |
| The complete course bundle and visual assets lacked their own first-use entry points | Generate their launchers and dependency manifests. Every runtime skill instructs the agent to run setup automatically before production; course subskills use the parent launcher when narration is needed. |
| Bootstrap readiness could describe OS support without verifying installed tools | `--check` now executes read-only renderer, transcription and narration checks and fails for missing prerequisites. Child setup must return a JSON object with `ready: true`; a successful exit alone is insufficient. |
| Child progress was buffered and pretty JSON responses were discarded | Relay stderr live, bound captured output, preserve structured results and executable paths, use UTF-8, and terminate the child process group on cancellation. |
| ASR recorded a Python executable in a temporary UV build directory | Create a persistent private Python environment keyed by package versions. Install binary wheels there, reuse it, and verify the actual cached interpreter, packages and model before reporting readiness. |
| Narration had unlocked indirect packages and different shell/Python runtime locations | Pin direct versions, ship a universal Python 3.12 lock with hashes, require wheel-only installation, and delegate the shell wrapper to the same private Python runtime. Docker uses the same lock. |
| Failed audio encoding could damage an existing output | Validate speed and output format, encode to a temporary file, verify nonempty audio, and replace the destination only on success. Clean temporary files on failure. |

Regenerated all distributions, synchronized 33 shared Python/JSON resources into
DevMock, and refreshed its complete integration patch. Existing unrelated app
changes were preserved. The UI source contains no remaining `USelect` tags;
searchable selection uses `USelectMenu`.

## Verification

- **150 repository tests passed:**
  `python3 -m unittest discover -s scripts -p 'test_*.py'`.
- **Nine course validator tests passed:**
  `python3 -m unittest discover -s course-creator/scripts -p 'test_*.py'`.
- **Seven frontend tests and the full Vue/TypeScript no-emit check passed**
  during this audit. Later changes affected shared Python resources and skill
  packaging; the checked frontend sources were not modified.
- **555 generated files verified current** with
  `python3 scripts/gen_skills.py --check`.
- **70 canonical Python files parsed**, changed shell launchers passed `sh -n`,
  and all **580 bundled SVGs parsed**. Repository and app whitespace checks passed.
- A fresh bundled snapshot installation into a directory containing spaces
  installed `voice-narration`, `explainer-video`, `product-launch-video`,
  `slide-decks`, and `visual-assets`, including their launchers and narration lock.
  It required no npx, Git, remote clone or global package installation.
- Cold Linux ASR preparation installed private Python 3.12.14, pinned wheel
  packages and the `tiny.en` model. Its persistent interpreter survived setup.
  Offline cached verification succeeded without changing runtime file sizes or
  modification times.
- Cold Linux Kokoro preparation downloaded verified model files, installed the
  hash-locked packages, and produced actual spoken WAVs. Cached readiness
  verification left runtime file sizes and modification times unchanged.
- A complete spoken project rendered successfully:
  `/tmp/skill-bank-audit-final-project/project/video.mp4` is **4.021354 seconds**,
  with H.264 video, AAC audio, exported narration, script, storyboard, visual
  assets, local-ASR JSON/SRT/VTT and a project manifest. Captions are correctly
  marked as requiring review. The latest atomic narration path also produced
  `/tmp/skill-bank-audit-kokoro-runtime/final.wav`.
- The exported DevMock integration patch passes applicability verification
  against the integrated checkout without changing it.

## Installation behavior

`npx skills add` copies skill files and has no post-install execution hook.
The skills therefore require the agent to run their bundled setup automatically
on first use. For immediate runtime preparation from a repository checkout:

```sh
python3 scripts/install_video_skill.py explainer-video --target /path/to/skills
```

Alternatively, run `sh tools/setup.sh --yes` from an installed skill, or its
PowerShell/Command Prompt equivalent. The complete `course-creator` bundle has
the same entry point. Setup installs the dependency skill graph and prepares the
selected runtime; each associated skill can prepare its own runtime on use.
Downloads require network access and disk space. Model consent, image rights and
hosted credentials remain explicit inputs.

## Verification limits

The source detects Windows, macOS and Linux environments and uses private user
data paths, including for Debian, Arch, Fedora, RPM and AppImage installations.
This audit executed on Linux; it does not certify Windows/macOS native behavior
or the current Tauri bridge because builds remain deferred.

Local avatar inference needs a supported NVIDIA or Apple Silicon test host;
this AMD/ROCm host is ineligible. SadTalker remains disabled because its pinned
model data does not satisfy the required license terms. Hosted provider requests
were not made. Source checks and regression tests cannot guarantee that every
external service, hardware configuration or future dependency change will work.
