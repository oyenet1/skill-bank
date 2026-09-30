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

Installing `course-creator` includes its [ten focused subskills](./course-creator/SKILL.md): curriculum mapping, content authoring, visual assets, Slidev decks, Remotion or HyperFrames lesson video, Kokoro voice narration, marketing copy, product launch, talking-head packaging, and avatar video. The parent chooses only the subskills needed for the teacher's request. They can work alone or share the same course map and assets.

Independent actions include lesson writing; notes as PDF or an online page; optional exercises; publishable assignments, quizzes, and rubrics; lesson-by-lesson Slidev decks; optional local Kokoro voice narration; Remotion or HyperFrames videos using supplied text, audio, or teacher footage; captioning or overlay packaging of an existing talking-head clip; AI avatar, talking-photo or dubbed presenter video; and a timecoded CapCut Desktop handoff. Written material, decks, narration, and video can be produced separately or combined. Visual outputs can use the 580 bundled SVG images and icons. Videos use a shared course style and a per-video `style.md`.

For separate installation or invocation outside the parent, use [curriculum-map](./curriculum-map/SKILL.md), [content-authoring](./content-authoring/SKILL.md), [visual-assets](./visual-assets/SKILL.md), [slide-decks](./slide-decks/SKILL.md), [explainer-video](./explainer-video/SKILL.md), [voice-narration](./voice-narration/SKILL.md), [marketing-copy](./marketing-copy/SKILL.md), [product-launch-video](./product-launch-video/SKILL.md), [talking-head-video](./talking-head-video/SKILL.md), or [avatar-video](./avatar-video/SKILL.md). Each accepts a standalone brief or existing files, and each is craft-first: it leads with the artifact it produces and treats course work as one optional branch rather than a requirement. The marketing-copy skill is general purpose — it writes for any product, service or brand — and draws from the LodgeStatus campaign notes for credible hooks and sales copy on skills and courses.

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
npx skills add oyenet1/spec-driven-development --skill course-creator
```

---

### 🔬 [spec-driven-development](./spec-driven-development/)

**Specification-Driven Development (SDD)** — transforms vague ideas into structured, implementation-ready specifications.

Takes any rough requirement and produces:
- `requirements.md` — User stories + testable acceptance criteria (WHEN/SHALL/IF)
- `design.md` — Architecture, components, data model, API contracts
- `tasks.md` — Ordered, dependency-aware implementation checklist

**Install:**
```bash
npx skills add oyenet1/spec-driven-development --skill spec-driven-development
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
| `explainer-video` | Explainers, lessons, motion graphics and product walkthroughs |
| `talking-head-video` | Captions and graphic overlays on supplied presenter footage |
| `avatar-video` | Avatar or talking-photo presenters; provider or hardware requirements apply |
| `voice-narration` | Local narration audio |
| `slide-decks` | Slide presentations |
| `course-creator` | The full course workflow with its bundled subskills |

Install one skill globally (available across projects):

```bash
npx skills add oyenet1/spec-driven-development --skill product-launch-video -g
npx skills add oyenet1/spec-driven-development --skill explainer-video -g
npx skills add oyenet1/spec-driven-development --skill talking-head-video -g
npx skills add oyenet1/spec-driven-development --skill avatar-video -g
npx skills add oyenet1/spec-driven-development --skill voice-narration -g
npx skills add oyenet1/spec-driven-development --skill slide-decks -g
```

Run only the command for the skill you need, or install several together:

```bash
npx skills add oyenet1/spec-driven-development --skill product-launch-video --skill explainer-video --skill voice-narration -g
```

Install the complete course bundle:

```bash
npx skills add oyenet1/spec-driven-development --skill course-creator -g
```

Omit `-g` to install into the current project. The installer prompts for the agent
to use; add `-a codex` to target Codex explicitly. To inspect available skills or
check your global installation:

```bash
npx skills add oyenet1/spec-driven-development --list
npx skills list -g
```

### Prepare the runtime on first use

Skill installation copies files; it does not automatically download video tools.
Ask your agent to use the installed skill and run its first-use setup. For manual
setup, open the installed skill directory and use the command for your OS:

| OS | Command |
|---|---|
| Linux/macOS | `sh tools/setup.sh --yes` |
| Windows PowerShell | `powershell -ExecutionPolicy Bypass -File tools\setup.ps1 --yes` |
| Windows Command Prompt | `tools\setup.cmd --yes` |

Setup downloads the supported private runtimes and associated skills. Use
`--check` instead of `--yes` for a read-only check, or add `--no-skills` to prepare
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
Kokoro narration. It also accepts `slide-decks`, `talking-head-video`,
`avatar-video`, `voice-narration`, and `course-creator`. Use a fresh destination;
the installer refuses to replace an existing skill directory. If setup fails
after the files are copied, rerun the same command with `--resume` to retry the
missing prerequisites.
For `avatar-video`, it also checks the hosted HeyGen CLI and authentication.
That provider step requires a user account; the local script, voice, and
storyboard fallback remains available if it is not ready.

`install_video_skill.py` prepares the runtime for the one skill you name. The
associated skills are offered by the first-use bootstrap instead, so an install
made any way — the installer, `npx skills add`, or a manual copy — can complete
its own setup.

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
