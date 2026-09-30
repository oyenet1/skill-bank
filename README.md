<!--
  ──────────────────────────────────────────────────────────────────
  🏢 Company Name: Bonifade Technologies
  👨‍💻 Developer: Bowofade Oyerinde
  🐙 GitHub: oyenet1
  📅 Created Date: 2026-04-05
  🔄 Updated Date: 2026-04-05
  ──────────────────────────────────────────────────────────────────
-->

# Agent Skills

A collection of reusable AI agent skills by [Bowofade Oyerinde](https://github.com/oyenet1) / **Bonifade Technologies**.

## Available Skills

### [course-creator](./course-creator/)

Plans and builds instructor-led courses one action at a time, for technology or other subjects. A course map contains sections, chapters, lessons, concepts, prerequisites, and a simple-to-complex project ladder. Teachers can reorder it without losing stable lesson IDs.

Installing `course-creator` includes its [eleven focused subskills](./course-creator/SKILL.md): curriculum mapping, content authoring, visual assets, Slidev decks, Remotion or HyperFrames lesson video, Kokoro voice narration, marketing copy, motion graphics, product launch, talking-head packaging, and avatar video. The parent chooses only the subskills needed for the teacher's request. They can work alone or share the same course map and assets.

Independent actions include lesson writing; notes as PDF or an online page; optional exercises; publishable assignments, quizzes, and rubrics; lesson-by-lesson Slidev decks; optional local Kokoro voice narration; Remotion or HyperFrames videos using supplied text, audio, or teacher footage; captioning or overlay packaging of an existing talking-head clip; AI avatar, talking-photo or dubbed presenter video; and a timecoded CapCut Desktop handoff. Written material, decks, narration, and video can be produced separately or combined. Visual outputs can use the 580 bundled SVG images and icons. Videos use a shared course style and a per-video `style.md`.

For separate installation or invocation outside the parent, use [curriculum-map](./curriculum-map/SKILL.md), [content-authoring](./content-authoring/SKILL.md), [visual-assets](./visual-assets/SKILL.md), [slide-decks](./slide-decks/SKILL.md), [explainer-video](./explainer-video/SKILL.md), [motion-graphics-video](./motion-graphics-video/SKILL.md), [voice-narration](./voice-narration/SKILL.md), [marketing-copy](./marketing-copy/SKILL.md), [product-launch-video](./product-launch-video/SKILL.md), [talking-head-video](./talking-head-video/SKILL.md), or [avatar-video](./avatar-video/SKILL.md). Each accepts a standalone brief or existing files, and each is craft-first: it leads with the artifact it produces and treats course work as one optional branch rather than a requirement. The marketing-copy skill is general purpose — it writes for any product, service or brand — and draws from the LodgeStatus campaign notes for credible hooks and sales copy on skills and courses.

The [product-launch-video](./product-launch-video/SKILL.md) skill is also included as a subskill in `course-creator`. It turns supplied screenshots and product information into a motion ad or screenshot-based demo, using genuine screens as evidence. It writes a per-video `style.md` and delivers editable Remotion or HyperFrames source plus an MP4 when rendering is available.

The [talking-head-video](./talking-head-video/SKILL.md) skill packages an existing talking-head, interview or podcast clip with captions or designed graphic overlays — the footage itself is never altered. It transcribes locally and renders in HyperFrames. The [avatar-video](./avatar-video/SKILL.md) skill generates a presenter from a script — an AI avatar, a talking photo, or a dubbed clip — through the hosted HeyGen provider, and falls back to the script, narration and storyboard when the provider is not authenticated.

The skill teaches each concept through a relatable example, **What, Why, Where, When, and How**, a visual explanation, and a practical demonstration. Absolute beginner programming courses begin with computer basics. Each chapter has a small project; a larger section project follows at least three small projects.

The canonical course map is `course-plan.json`. The bundled validator checks prerequisite order, project placement, artifact paths, and table-of-contents synchronization:

```bash
python course-creator/scripts/validate_course.py path/to/course-plan.json --sync-toc
```

See [the skill](./course-creator/SKILL.md) and its linked references for each action's output contract. The original written-course guidance is retained in the [text production reference](./course-creator/references/text-course-production.md), [technical depth reference](./course-creator/references/technical-depth.md), [term bank](./course-creator/references/technical-terms.md), and [roadmap notes](./course-creator/references/pdf-derived-roadmap-notes.md).

Example prompts:

```text
Map a beginner programming course from computer basics through a first web app. List every section, chapter, lesson, concept, and proposed project; do not write lessons yet.
Write the lesson on file extensions from my course map, then create its Slidev deck.
Make a Remotion lesson video from this deck and my recorded narration; include a CapCut Desktop editing pack.
Create a Remotion launch ad from these product screenshots and the product website; show only real UI states.
```

**Install:**
```bash
npx skills add oyenet1/skill-bank --skill course-creator
```

---

### [motion-graphics-video](./motion-graphics-video/SKILL.md)

Generate kinetic typography, animated charts, process flows, diagrams, logo
reveals and visual concept explanations with Remotion or HyperFrames. Delivers
an MP4 and editable source, with optional narration and captions. Works alone
or as the motion graphics subskill inside `course-creator` for lesson diagrams
and chapter titles, reusing the course style and lesson IDs.

```bash
npx skills add oyenet1/skill-bank --skill motion-graphics-video -g
```

Example: “Create a 20-second motion graphics video explaining the water cycle
with animated arrows and labels.” For a course: “Animate this lesson's process
diagram using the course style and register the video under the lesson.”

---

### 🔬 [spec-driven-development](./spec-driven-development/)

**Specification-Driven Development (SDD)** — transforms vague ideas into structured, implementation-ready specifications.

Takes any rough requirement and produces:
- `requirements.md` — User stories + testable acceptance criteria (WHEN/SHALL/IF)
- `design.md` — Architecture, components, data model, API contracts
- `tasks.md` — Ordered, dependency-aware implementation checklist

**Install:**
```bash
npx skills add oyenet1/skill-bank --skill spec-driven-development
```

**Triggers on:** "spec this", "SDD", "plan this feature", "break this down", "generate requirements", "write a spec", and more.

---

## Installing Skills

These skills work in a coding agent that can read files and run commands; the
desktop app is not required. Install Node.js with npm first so `npx` is available.
The installation commands below work in Linux/macOS terminals and Windows
PowerShell or Command Prompt.

### Choose a video skill

| Skill | Use it for |
|---|---|
| `product-launch-video` | Product launch ads and demos with real desktop/mobile screenshots |
| `motion-graphics-video` | Kinetic typography, animated diagrams, charts, processes and lesson titles |
| `explainer-video` | Explainers, lessons, motion graphics and product walkthroughs |
| `talking-head-video` | Captions and graphic overlays on supplied presenter footage |
| `avatar-video` | Avatar or talking-photo presenters; provider or hardware requirements apply |
| `voice-narration` | Local narration audio |
| `slide-decks` | Slide presentations |
| `course-creator` | The full course workflow with its bundled subskills |

Install one skill globally (available across projects):

```bash
npx skills add oyenet1/skill-bank --skill product-launch-video -g
npx skills add oyenet1/skill-bank --skill motion-graphics-video -g
npx skills add oyenet1/skill-bank --skill explainer-video -g
npx skills add oyenet1/skill-bank --skill talking-head-video -g
npx skills add oyenet1/skill-bank --skill avatar-video -g
npx skills add oyenet1/skill-bank --skill voice-narration -g
npx skills add oyenet1/skill-bank --skill slide-decks -g
```

Run only the command for the skill you need, or install several together:

```bash
npx skills add oyenet1/skill-bank --skill product-launch-video --skill explainer-video --skill voice-narration -g
```

Install the complete course bundle:

```bash
npx skills add oyenet1/skill-bank --skill course-creator -g
```

Omit `-g` to install into the current project. The installer prompts for the agent
to use; add `-a codex` to target Codex explicitly. To inspect available skills or
check your global installation:

```bash
npx skills add oyenet1/skill-bank --list
npx skills list -g
```

### Complete installable skill catalog

All thirteen top-level skills can be installed independently. Use
`npx skills add oyenet1/skill-bank --skill NAME -g -a codex` with any name below.
Omit `-a codex` to choose another supported agent.

| Skill name | Direct associated skills installed on first use |
|---|---|
| `spec-driven-development` | None |
| `curriculum-map` | None |
| `content-authoring` | None |
| `marketing-copy` | None |
| `visual-assets` | None |
| `voice-narration` | `explainer-video`, `product-launch-video` |
| `slide-decks` | `visual-assets`, `explainer-video` |
| `explainer-video` | `voice-narration`, `product-launch-video`, `slide-decks`, `visual-assets` |
| `motion-graphics-video` | `voice-narration`, `visual-assets` |
| `product-launch-video` | `explainer-video`, `voice-narration` |
| `talking-head-video` | `avatar-video`, `explainer-video`, `product-launch-video` |
| `avatar-video` | `talking-head-video`, `voice-narration` |
| `course-creator` | All eleven course subskills already bundled; no separate sibling copies |

The associated graph is resolved recursively, including dependencies of
dependencies. `npx skills add` itself copies only the selected skill; its
first-use launcher installs the associated graph and prepares runtimes.

Install every top-level skill for Codex in one command:

```bash
npx skills add oyenet1/skill-bank --skill '*' -g -a codex -y
```

The CLI supports many agents, but some do not support global installation.
Selecting an agent explicitly avoids unrelated agent-specific installation
errors. Older generated YAML descriptions containing unquoted colons caused
the CLI to skip `motion-graphics-video` and `avatar-video` and report only eleven
skills. The generator now serializes valid YAML and checks every target.

For a fresh isolated installation audit with per-stage timing, run:

```bash
python3 scripts/smoke_install_video_skill.py
# Discovery/copy only, without runtime downloads:
python3 scripts/smoke_install_video_skill.py --files-only
```

The script writes logs and `report.json` under a new temporary sandbox. It
measures skill copying, first-use setup, cached setup and read-only verification.
Installed skills, npm/UV/browser caches and downloaded models stay isolated;
compatible host Node/npm, Python, UV and FFmpeg may be reused. Use `--source PATH`
to test a local checkout or `--sandbox-dir EMPTY_DIR` to retain a chosen location.

### Prepare the runtime on first use

`npx skills add` copies files and has no setup hook. Each runtime skill now
instructs the agent to run automatic first-use setup before production. This
installs its associated skills, including indirect dependencies, from the
bundled verified snapshot. The complete course bundle has its own launcher.
For immediate setup from a repository checkout, run
`python3 scripts/install_video_skill.py explainer-video --target /path/to/skills`.
For manual
setup, open the installed skill directory and use the command for your OS:

| OS | Command |
|---|---|
| Linux/macOS | `sh tools/setup.sh --yes` |
| Windows PowerShell | `powershell -ExecutionPolicy Bypass -File tools\setup.ps1 --yes` |
| Windows Command Prompt | `tools\setup.cmd --yes` |

Setup downloads the supported private runtimes and associated skills. Use
`--check` instead of `--yes` for a read-only verification of cached runtimes
(it fails if anything required is missing), or add `--no-skills` to prepare
runtimes without installing associated skills. First setup needs internet access
and space for tools/models. No desktop application is needed. Windows/macOS
end-to-end rendering remains unverified; local avatar generation also needs
supported hardware, and hosted providers need credentials.

Example requests after installation:

```text
Use product-launch-video to make a 30-second mobile demo of my app at http://localhost:3000. Capture real mobile screens; ask for private login access if needed.
Use explainer-video to make a 60-second narrated walkthrough using both desktop and mobile screenshots of my website.
Use talking-head-video to caption my recorded presentation.
```

### Automatic product screenshots

`product-launch-video` and `explainer-video` can capture real public or logged-in
web product screens using their bundled `tools/capture_product_screens.py`.
Choose desktop, mobile, or both; mobile capture uses responsive browser device
emulation. Credentials come from private environment variables or an existing
session outside exported assets. The capture tool prepares its own private
Playwright/Chromium runtime and outputs PNGs with provenance. See the
[capture plan and login guide](skills-src/_shared/product-capture.md).
Native mobile apps require supplied captures or a separate emulator tool.

Optional intake choices use a 30-second default when the agent host supports
asynchronous questions and timers. Required access details and approvals remain
pending. This is skill behavior, not a timer installed into third-party apps.

## Editing Skills

For the current video production steps, installer gaps, subtitle contract, and
the Tauri app integration plan, see [video desktop integration audit](docs/video-desktop-integration.md).

Kokoro narration bootstraps its own `uv`, Python 3.12 environment, packages and
verified model files on first use via `tools/kokoro/start.sh`. Slide decks and
video skills ship `tools/ensure_video_runtime.py`; their first-use preflight
checks and installs Node, Slidev, Remotion, HyperFrames, Chromium, FFmpeg and FFprobe as
needed. For example, from an installed `product-launch-video` skill directory,
run `python3 tools/ensure_video_runtime.py product-launch-video` to see the
verified executable paths. `--check` reports status without installing.
`npx skills add` copies files and does not run a post-install hook, so setup
runs when the skill is first used.

### First-use bootstrap on any OS

Every runtime-backed skill ships a small cross-platform bootstrap that detects
the operating system and CPU architecture, prepares the private runtime, and
offers to install the associated sibling skills that are not present. Run the
launcher for the host:

| OS | Command |
|---|---|
| Linux, macOS | `sh tools/setup.sh` |
| Windows (PowerShell) | `powershell -ExecutionPolicy Bypass -File tools\setup.ps1` |
| Windows (Command Prompt) | `tools\setup.cmd` |

The launcher runs `tools/bootstrap.py`, which reads the shipped
`tools/dependencies.json` and:

1. installs missing Node, FFmpeg/FFprobe, the selected renderers and Chromium
   into the private user data directory;
2. prepares Kokoro narration and local speech recognition where the skill needs
   them;
3. installs missing associated skills from its bundled, hash-verified source
   snapshot into the exact requested directory. For example, `explainer-video`
   installs `voice-narration`, `product-launch-video`, `slide-decks` and
   `visual-assets`. No npx or Git is needed for these sibling installations;
   existing skills and user edits are preserved.

### Dependency order, parallel setup, and reuse

Setup respects prerequisites while overlapping independent work. The desktop
app's **Prepare tools** action resolves Node once, then runs renderer profiles
and FFmpeg/FFprobe setup concurrently, with at most four workers. Each renderer
installs its packages before preparing its browser. Duplicate profile names are
handled once. The app joins all active workers before reporting success or
failure; only a completely verified setup reports ready.

Standalone setup and `scripts/install_video_skill.py` use the same bootstrap.
It runs up to four independent branches concurrently: video tools, speech
recognition, Kokoro narration, and associated skill copies. Renderer routes
within the video-tools branch remain sequential because they share Node and
media directories. Sibling copies remain sequential because their cyclic
dependency graphs overlap. Associated skill files are copied recursively;
their own runtimes are prepared when those skills are first used.

The dependency layers, from prerequisites to consumers, are:

1. **Host and download utilities:** Windows/macOS/Linux on x64 or ARM64,
   writable user data, internet for first downloads, and enough disk space.
   Launchers reuse Python 3.10+ or prepare private Python. Without Python,
   Unix setup uses curl/wget, archive extraction and SHA-256 utilities;
   Windows uses PowerShell. Linux browser system libraries must already be
   available; setup does not invoke a distribution package manager.
2. **Runtime managers:** Node.js 22.12.0 or newer with npm for rendering;
   private UV and Python 3.12 environments for narration and transcription.
   Compatible existing runtimes are reused.
3. **Media tools:** FFmpeg and FFprobe. Standalone setup uses working system
   binaries or `ffmpeg-static` and `@derhuerst/ffprobe-static`; the desktop app
   uses its existing native media installer and platform archives.
4. **Renderers and their browsers:** Slidev uses `@slidev/cli`,
   `@slidev/theme-default`, `playwright-chromium` and Chromium; Remotion uses
   `@remotion/cli`, `remotion`, `react`, `react-dom` and Chrome Headless Shell;
   HyperFrames uses `hyperframes`, `gsap` and its managed browser. Each engine
   also installs its npm dependencies recursively.
5. **Narration:** Kokoro uses `kokoro-onnx`, `soundfile`, `espeakng-loader`,
   `misaki` and `imageio-ffmpeg`. Its locked indirect dependencies include
   `addict`, `attrs`, `cffi`, `cloudpickle`, `dlinfo`, `flatbuffers`, `joblib`,
   `numpy`, `onnxruntime`, `packaging`, `phonemizer`, `protobuf`, `pycparser`,
   `regex` and `typing-extensions`. The two model files,
   `kokoro-v1.0.onnx` and `voices-v1.0.bin`, total approximately 354 MB.
6. **Transcription:** `faster-whisper`, `ctranslate2`, PyAV (`av`), their
   recursively resolved Python dependencies, and the `small.en` speech model.
   `small` is the multilingual option; older macOS has an alternative PyAV pin.
7. **Skills:** `visual-assets` has no associated skills.
   `explainer-video`, `product-launch-video`, `voice-narration` and
   `slide-decks` form a connected group that also installs `visual-assets`.
   `motion-graphics-video` brings in that group through its narration/asset
   associations. `talking-head-video` and `avatar-video` install each other
   and that group. Cycles are visited once and existing skills are preserved.
   `course-creator` already contains all eleven course subskills, so it does
   not install separate sibling copies.
8. **Optional features:** Local avatars require compatible accelerator hardware,
   backend-specific Python/PyTorch packages and model downloads; ordinary setup
   does not install these models. Hosted avatars require HeyGen credentials.
   Generated scene images require an OpenAI credential and quota. Docker and
   Pocket TTS are optional alternatives, not default bootstrap dependencies.

Exact direct versions live in
[`runtime_requirements.json`](skills-src/_shared/tools/runtime_requirements.json).
The complete Kokoro package versions/hashes live in
[`requirements.lock`](course-creator/tools/kokoro/requirements.lock), and avatar
package/model requirements live in
[`avatar_models.json`](skills-src/_shared/tools/avatar_models.json).
Renderer and transcription transitive versions are resolved at installation;
there is no single checked-in lock covering all platforms and features.

Repeated setup verifies and reuses ready packages, browsers, model files and
environments rather than downloading them again. Missing or failed components
are retried. Browser readiness checks inspect the actual browser, not a stale
marker file. The installer also reuses an existing skill directory containing
`SKILL.md`; it preserves user edits and refuses incomplete directories or
symlink destinations. `--resume` remains available after a failed install.
`--check` stays read-only. Cancellation stops active bootstrap child process
trees; native renderer workers share the app's cancel flag. The native FFmpeg
download keeps its existing cancellation granularity: setup waits for that
download to return before finishing cancellation.

Use `--check` to report the plan and install nothing, `--yes` to run without an
interactive prompt, `--no-skills` to prepare runtimes only, and `--target DIR`
to name the skills directory. Unsupported OS/architecture combinations report
the missing runtime rather than selecting a binary for another platform. No
global `npm`/`pip` install is ever performed and PATH is never modified.

The explainer and product launch skills ship `tools/assemble_video.py` for joining rendered scene
files with narration or footage audio and timed subtitles. See the
[scene assembly contract](docs/video-assembly.md).
The explainer skill also includes `tools/render_slidev_video.py` for exporting
Slidev click states into that assembly flow.
Those skills include `tools/render_remotion_video.py` for packaging an
editable Remotion composition with its audio and captions.
They also include `tools/render_hyperframes_video.py` for editable HTML
compositions.
All video skills ship `tools/transcribe_captions.py` to create word-timed
caption files from final spoken audio, with recognition marked for review.
The four video skills also ship `tools/run_video_job.py` for a single request
with renderer setup, progress events, verified output, subtitles, cancellation,
and retry. See the [desktop job contract](docs/video-job-contract.md).

To prepare dependencies at install time from a clone of this repo, use the
bundled installer and choose the skills directory for your agent:

```bash
python3 scripts/install_video_skill.py explainer-video --target ~/.agents/skills
python3 scripts/install_video_skill.py product-launch-video --target ~/.agents/skills
```

On Windows Command Prompt, run the same command with `py -3` and a Windows skills directory,
for example `py -3 scripts/install_video_skill.py explainer-video --target %USERPROFILE%\.agents\skills`.
The installer selects managed Node archives for Windows, macOS, or Linux
(`x64` and `arm64`) and stores Kokoro's Python, packages, and models in the
user data directory. Linux setup uses the same path for Debian, Arch, Fedora,
RPM packages, and AppImage; it does not invoke `apt`, `pacman`, or `dnf`.
Unsupported CPU/OS combinations report the missing runtime instead of
silently choosing a binary for another platform.

This copies the generated skill, installs its video runtime, and prepares local
Kokoro narration and speech recognition where required. It also accepts
`motion-graphics-video`, `slide-decks`, `talking-head-video`,
`avatar-video`, `voice-narration`, and `course-creator`. Existing valid skill
directories are reused without overwriting their files. If setup fails
after the files are copied, rerun the same command with `--resume` to retry the
missing prerequisites.
For `avatar-video`, it checks local capabilities without downloading models and
lets the provider dispatcher prefer a verified local backend or the editable
script, voice and storyboard fallback when no hosted provider is available.

`install_video_skill.py` invokes the same parallel bootstrap as first-use setup,
including indirect associated skill copies. Installations made through
`npx skills add` or a manual copy complete that setup on first use.

Skills are generated. The source of truth is [`skills-src/`](./skills-src/); the
`course-creator/subskills/` folders and the top-level skills are build output.
**Do not edit generated folders by hand** — the next build overwrites them.

| Path | What it holds |
|---|---|
| `skills-src/manifest.yaml` | which capabilities exist, their names, and which shared modules each ships |
| `skills-src/<capability>/skill.md` | one capability — frontmatter for both targets, shared craft, `{{mode:…}}` blocks for target-specific text |
| `skills-src/<capability>/bootstrap` | the capability's `bootstrap:` block also emits `tools/bootstrap.py`, the `setup.sh/.cmd/.ps1` launchers, and `tools/dependencies.json` |
| `skills-src/_shared/` | the intake modules: `intake`, `brand`, `video`, `voice`, `preflight`, `objects` |
| `skills-src/_shared/prompts/<category>/` | script and storyboard patterns, one file per pattern |
| `skills-src/_shared/library/<name>/` | full-text source material shipped verbatim to the capabilities that declare `library:` |
| `skills-src/<capability>/files/` | extra files a target ships (e.g. the product launch workflow) |

One capability emits two install targets: the `course-creator` bundle subskill
(`course-creator-<id>`) and the standalone skill (`<id>`). Tokens in a
`skill.md` resolve per target — `{{ref:brand}}` links the shared module,
`{{doc:narration.md}}` links a `course-creator` reference, `{{sibling:voice-narration}}`
links another capability, and `{{asset:tools/kokoro/README.md}}` resolves a
shipped path at the right depth.

```bash
# regenerate every target (requires pyyaml)
python scripts/gen_skills.py

# verify committed output matches the source — run before committing
python scripts/gen_skills.py --check

# behaviour tests
cd scripts && python -m unittest
```

The tool trees follow the same rule: `course-creator/tools/kokoro/` is canonical
and `voice-narration/tools/kokoro/` is generated from it, so the standalone
install works alone.

## Intake

Every producing skill runs the same intake protocol before it makes anything.
See [`skills-src/_shared/intake.md`](./skills-src/_shared/intake.md): present
inputs are used, inferable inputs get a stated default recorded with a reason,
and missing inputs that would change the deliverable are asked in **one batched
block with options and a recommended pick**. Brand values and evidence are never
invented.

Brand identity lives in a `brand.md` that skills read and write — colour, type,
tone, vertical, claims and accessibility all inherit from it, and each per-video
`style.md` records only its deltas. A local project can be read with
`python scripts/extract_brand.py <path>`; secrets and dotfiles are never read.

## License

MIT — see [LICENSE](./LICENSE).
