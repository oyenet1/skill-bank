---
name: video-shortcuts
description: Route /tutorial, /product-launch, /motion-graphics, /talking-head, /avatar, /narration and /story prompts to video skills, asking for missing details before production.
---

# Video shortcuts

Use this router when a request uses one of these short prefixes, optionally
preceded by "Use" or this skill's name. The text after the prefix is the brief.
These are portable prompt aliases; native slash-menu registration belongs to
the host, and may require an adapter. Do not claim an instruction file registers
commands in every coding agent. This workflow does not depend on Codex tools.

| Shortcut | Skill to load | Purpose |
|---|---|---|
| `/tutorial` | `explainer-video` | Create an explainer or tutorial video |
| `/product-launch` | `product-launch-video` | Create a product advert, promo or demo |
| `/motion-graphics` | `motion-graphics-video` | Animate text, charts, diagrams or a logo |
| `/talking-head` | `talking-head-video` | Caption and add overlays to existing footage |
| `/avatar` | `avatar-video` | Generate a presenter or talking photo |
| `/narration` | `voice-narration` | Generate speech audio from a script |
| `/story` | `storytelling` | Create a catchy story for posts, Slidev videos or both |

Load the chosen skill's SKILL.md from the agent's available skill catalog or a
sibling skill directory. Use its own tools, source requirements and production
workflow. If the skill is absent, report its exact name and installation command
`npx skills add oyenet1/skill-bank --skill NAME`; do not pretend the router itself
can render. If multiple shortcuts are supplied, use the requested workflows in
dependency order. If the shortcut is unknown, show the supported list and ask
which output is intended; do not select a different workflow silently.

## Storytelling mode

`/story` selects storytelling. If another shortcut explicitly requests a
storytelling treatment, load the storytelling skill or the selected skill's
storytelling reference before production. Resolve post / video / both first.
Story videos use Slidev, assets that show the objects being discussed, Mermaid
programming flows and smooth entrances/exits. Posts do not need video choices
or runtime setup.

## Clarification breakpoint

Read [intake](references/intake.md). Use the prompt, previous answers and supplied
materials to resolve the brief. Before scripts, storyboards, source authoring or
rendering, ask a concise batch for any missing or ambiguous detail that affects
the result. Video briefs need the subject or product, purpose, audience,
platform or aspect ratio, duration and audio mode. Ask about language, accent,
voice, source footage or photos, brand assets and CTA where the selected workflow
needs them. Narration alone needs its text or subject, language and voice choices;
do not ask it for a video platform or aspect ratio.

Offer recommendations and let the requester answer in their own words. Pause
dependent production until the questions are answered. If the host supplies a
question tool, use it; otherwise ask in a normal message and wait for the next
turn. A timer or unavailable UI is not a reason to assume answers. If only some
questions are answered, keep the remaining material questions pending.

Proceed without extra questions when the brief is complete. "Choose for me"
delegates creative choices and permits stated defaults; it does not supply
missing identity, files, access, verified claims or CTA links. Record the resolved
brief and pending questions so a later message can resume the same request.
