---
name: storytelling
description: Create catchy explanatory stories for posts, Slidev videos or both. Handles /story prompts, with Mermaid programming flows and relevant visual assets. Uses Paul Smith's Sell with a Story method.
---

# Storytelling

## Automatic first-use setup

For video or deck output only, after clarification, run the bundled launcher with `--yes`; it detects the host, prepares private runtimes, and installs the declared sibling dependency graph. Do not ask the requester to install packages manually.

- Linux/macOS: `sh tools/setup.sh --yes`
- Windows: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/setup.ps1 --yes`

Use `--check` for a read-only readiness check. If prerequisites are missing, rerun setup. Follow the returned `pythonExecutable` and runtime paths for later commands. Model-license acceptance, image rights and account credentials remain explicit inputs.

Turn a topic, supplied account or source material into a catchy story that
explains clearly and pays off its opening hook. Deliver post text, an editable
Slidev video project, or both, according to the request. A post does not require
video production.

## Social media output

Read [social-media](references/social-media.md) before producing audience-facing text or video.
Resolve the publishing platform and audience, keep the hook and payoff clear,
and verify mobile readability, captions and the chosen channel's format.
Ask for missing material choices at intake. Aim for shareability without
claiming guaranteed viral performance; preserve the requested teaching depth.

## Clarification breakpoint

Read [intake](references/intake.md). When the format is unclear, ask **post / video / both**,
then batch any missing topic, audience, purpose and delivery choices. Wait for
answers before writing or producing dependent artifacts. Treat the text after
`/story` as the brief. Do not re-ask supplied details; explicit "choose for me"
delegates creative choices.

## Build the story

Read [sell-with-story](references/sell-with-story.md) first. Use its story-selection method and seven-part
narrative structure for posts and Slidev videos; keep original events, imagery
and explanations grounded in the supplied material.

Follow [storytelling](references/storytelling.md) for the hook, relatable situation, cause and effect,
payoff, asset plan, Mermaid programming diagrams and smooth entrances/exits.
Preserve verified facts, keep analogies understandable and label invented
scenarios as illustrative. Use [code](references/code.md) for runnable technical examples.

For post-only work, deliver platform-appropriate text ready to copy, with a
complete explanation and payoff. Do not prepare video dependencies.

For video or deck work, use **Slidev**, [slidev](references/slidev.md) and
`slide-decks`. Resolve needed assets through [objects](references/objects.md),
[generated-assets](references/generated-assets.md) and `visual-assets`. Write `story.md`, `script.md`,
`storyboard.md`, `style.md` and the asset manifest. Record each beat's narration,
on-screen objects, flow, Mermaid diagram when needed, entrance, hold/action, exit
and transition. Use [voice](references/voice.md) and `voice-narration` when speech is
requested, preserving supplied audio.

After intake, read [preflight](references/preflight.md) and prepare only the selected video needs.
Use verified runtime paths. Render through live Slidev playback capture to
preserve animation; static frame exports alone do not meet the motion contract.
Reuse `explainer-video` for narration/caption timing, assembly and
delivery checks while retaining Slidev as the visual authoring framework.

## Deliver and verify

Check the hook's promise, causal explanation, factual grounding, labels and
payoff. Review the exported video for actual smooth entrances/exits, readable
holds and synced flows. Deliver requested post text, narration, portable assets,
editable `slides.md` and the MP4 when rendering succeeds. Report a blocked render
explicitly and retain sources. When both post and video are requested, deliver
both adaptations of the same story.
