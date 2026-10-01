---
standalone:
  name: storytelling
  description: >-
    Create catchy explanatory stories for posts, Slidev videos or both. Handles
    /story prompts, with Mermaid programming flows and relevant visual assets.
bundle:
  name: course-creator-storytelling
  description: >-
    Explain course concepts through catchy stories, post text and Slidev videos
    with clear object visuals and Mermaid programming flows.
---

# Storytelling

Turn a topic, supplied account or source material into a catchy story that
explains clearly and pays off its opening hook. Deliver post text, an editable
Slidev video project, or both, according to the request. A post does not require
video production.

## Clarification breakpoint

Read {{ref:intake}}. When the format is unclear, ask **post / video / both**,
then batch any missing topic, audience, purpose and delivery choices. Wait for
answers before writing or producing dependent artifacts. Treat the text after
`/story` as the brief. Do not re-ask supplied details; explicit "choose for me"
delegates creative choices.

## Build the story

Follow {{ref:storytelling}} for the hook, relatable situation, cause and effect,
payoff, asset plan, Mermaid programming diagrams and smooth entrances/exits.
Preserve verified facts, keep analogies understandable and label invented
scenarios as illustrative. Use {{ref:code}} for runnable technical examples.

For post-only work, deliver platform-appropriate text ready to copy, with a
complete explanation and payoff. Do not prepare video dependencies.

For video or deck work, use **Slidev**, {{ref:slidev}} and
{{sibling:slide-decks}}. Resolve needed assets through {{ref:objects}},
{{ref:generated-assets}} and {{sibling:assets}}. Write `story.md`, `script.md`,
`storyboard.md`, `style.md` and the asset manifest. Record each beat's narration,
on-screen objects, flow, Mermaid diagram when needed, entrance, hold/action, exit
and transition. Use {{ref:voice}} and {{sibling:voice-narration}} when speech is
requested, preserving supplied audio.

After intake, read {{ref:preflight}} and prepare only the selected video needs.
Use verified runtime paths. Render through live Slidev playback capture to
preserve animation; static frame exports alone do not meet the motion contract.
Reuse {{sibling:explainer-video}} for narration/caption timing, assembly and
delivery checks while retaining Slidev as the visual authoring framework.

## Deliver and verify

Check the hook's promise, causal explanation, factual grounding, labels and
payoff. Review the exported video for actual smooth entrances/exits, readable
holds and synced flows. Deliver requested post text, narration, portable assets,
editable `slides.md` and the MP4 when rendering succeeds. Report a blocked render
explicitly and retain sources. When both post and video are requested, deliver
both adaptations of the same story.
