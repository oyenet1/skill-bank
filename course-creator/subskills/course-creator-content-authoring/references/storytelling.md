# Storytelling treatment

Read this when storytelling is explicitly selected, including inside another
workflow. A product anecdote alone does not change an existing video into a
storytelling project. The selected storytelling video framework is **Slidev**;
use another framework only when the requester explicitly overrides that choice.
Posts and voice-only scripts do not require a renderer or a deck.

## Resolve the output before writing

Follow [intake](intake.md). Ask whether the result is a ready-to-post text story, a
video, or both when the request does not say. Resolve topic, audience and purpose;
ask about posting platform and length for text, and delivery platform/layout,
duration and audio mode for video. Ask for real incidents, facts or source
materials when the story depends on them. Do not turn an unanswered question
into an assumed video request. Do not install video runtimes for text-only work.

## Write a catchy story that explains

Use [sell-with-story](sell-with-story.md) as the default method, based on Paul Smith's
*Sell with a Story*. Select the story for the audience's intended understanding,
feeling or next action, then structure it as hook → context → challenge → conflict
→ resolution → lesson → action. Record each storyboard beat's narrative function.
Apply this same method to ready-to-post text and Slidev video narration, including
storytelling selected inside other skills. The requester can override the method.

Open with a concrete situation, a surprising question or a recognizable problem
that the story actually resolves. Introduce a consistent character or object,
show its goal and obstacle, explain what changes and why, then end with the
payoff and an appropriate takeaway or verified CTA. Keep the promise in the
hook. Avoid generic suspense, fake metrics and claims of real customer success.
Label invented scenarios as illustrative; never present them as testimony.

Use clear language at the audience's level. Connect each action to its cause and
result. Where the story teaches, explain what the concept is, why it matters,
where and when it is useful, and how it works with a concrete example. Distinguish
the analogy from the real mechanism and explain where the analogy stops fitting.
A programming story must leave the viewer able to follow the actual execution.

For posts, produce standalone text with a strong opening, short readable
paragraphs and the complete payoff; fit the selected platform. For video, write
spoken narration separately from concise on-screen text. When both are requested,
adapt one grounded story to the two formats; do not paste slide bullets as a post.

## Show what the story talks about

Resolve assets with [objects](objects.md) and [brand](brand.md). For each visual beat,
record the narration, the actual object/entity/substance being discussed, its
visual representation, the action or flow, labels and asset provenance. Show a
recognizable object or labelled illustration when it helps understanding, not
just a wall of text. Prefer supplied assets and real product captures; draw or
generate original illustrations when appropriate. Copy assets into the project.

Show processes as input → action → result, with labelled arrows and meaningful
state changes. For physical topics, identify the substance, parts and direction
of movement; keep scale and illustrative simplifications explicit. Illustrations
must not masquerade as scientific evidence or product functionality.

For programming, use **Mermaid** inside Slidev for algorithms, request/data flow,
component interactions and state changes. Choose flowcharts for decisions and
control flow, sequence diagrams for messages/API calls, and state or ER diagrams
when the concept needs them. Use real names and boundaries of the system.
Explain each arrow with a concrete input and output; connect it to the relevant
code or operation. Show the overview, then highlight the active step while the
other parts remain visible. Run meaningful code examples and check their results.

## Smooth Slidev scenes

Read [slidev](slidev.md). Each storyboard beat records entrance → readable hold/action
→ exit, and its transition into the next beat. Use Slidev's `v-click`, `v-motion`
and slide transitions; prefer small purposeful translations and fades with
consistent easing. Avoid sudden jumps, overlap, flashing and perpetual motion.
Keep labels visible while their object acts; do not remove a flow before its
explanation finishes. Sync narration, highlights and object movement.

Use live browser recording/capture of Slidev playback to preserve motion in
the MP4, including click reveals, entrances, exits and slide transitions. Measure
narration first, allow readable holds, and verify captured timing.
`render_slidev_video.py` exports static PNG states: it is useful for static
slides and handouts but **does not capture `v-motion` or transition animation**.
Do not use that path alone to claim a smooth animated story. If motion capture
is unavailable, deliver editable Slidev sources and report the blocked animated
render; ask before substituting a static montage or another renderer.

Preview the hook, every diagram, object entrance/action/exit and final payoff
at delivery size. Verify no text clipping, obscured connectors or off-screen
assets, and check that narration names what is actually visible. Inspect the
exported MP4 itself; source animation declarations do not prove exported motion.
