# Intake Protocol

Run this before producing anything. The goal is a complete working brief without
dragging the requester through a drip of single questions.

## The three states of every input

| State | Behaviour |
|---|---|
| **Present** | Use it as given. |
| **Inferable** | Derive it from explicit context or supplied materials; record the value and reason. A common default alone does not make an input inferable. |
| **Missing and deliverable-changing** | **Ask and wait.** Keep the input pending until answered or the requester explicitly delegates the choice. |

An input is *deliverable-changing* when a different answer produces a different
artifact: aspect ratio, duration, category, palette, font, voice, language,
CTA destination, evidence for a claim. An input is *inferable* when the supplied context determines it: for example,
TikTok determines portrait layout. An unspecified platform, duration or audio
mode remains a question even when a popular default exists.

## How to ask

**Batch.** Collect every missing deliverable-changing input and ask once, as a
single numbered block. Each item shows concrete options and one recommended pick
marked `(recommended)`. The requester answers once.

```
1. Platform — YouTube (recommended) / TikTok / Instagram Reels / LinkedIn / website
2. Audio mode — full (recommended) / voiceover / music / silent
3. Ending — main CTA (recommended) / logo sting / takeaway recap
4. Duration — 30s (recommended) / 15s / 60s
```

Do not re-ask what the request already states. If the request says "a 20-second
silent intro", items 2 and 4 are answered — move on.

## Wait for clarification

When missing or ambiguous details affect the deliverable, ask before writing the
script, storyboard, composition or final artifact. Offer recommendations as
choices, not as decisions already made. Do not silently assume purpose,
audience, platform, duration, key message or audio mode from a vague request.
Ask only what is missing and relevant; group related questions so the brief is
easy to answer. If the request is complete, proceed without another questionnaire.

Use the host's question tool when available. If no suitable tool exists, ask in
a normal message and end the turn to wait. A missing timer or question UI does
not authorize skipping clarification. Elapsed time is not an answer. You may
inspect supplied files or research facts independently while answers are pending;
do not start production that depends on them.

If the requester says "choose for me", "use your defaults", or delegates specific
choices, resolve those choices with stated reasons and proceed. That delegation
never supplies missing credentials, product identity, evidence or CTA links.
Record unanswered questions in the working brief. If only some are answered,
ask for the remaining material details before dependent production.

For example, "make a video for my business" needs the business or source URL,
the video's purpose and audience, destination platform, length and audio mode.
A supplied "20-second silent portrait logo intro using this logo" already
answers length, audio, layout and assets; ask only about any remaining material
ambiguity.

## Hard rules

- **Never invent brand values.** No palette, font, logo, price, metric, claim or
  testimonial may be created to fill a gap. If no `brand.md` exists, use neutral
  defaults and label the output `unbranded`. Where a `brand` module is shipped
  alongside this one, it defines the schema and the defaults.
- **Never invent evidence.** A screenshot proves a screen exists. It does not
  prove a click works, a process is automatic, or a customer got a result.
- **Record provenance for every derived value** in the working brief:
  `source: user-supplied` · `source: extracted-from <url|path>` · `source: default`.
- **Label anything unverified** rather than presenting it as fact.

## Working brief

Keep a short running brief alongside the output (`product-brief.md`, or the
`## Intake` section of `style.md`) holding: resolved inputs, inferred values with
reasons, provenance, open questions, and anything deliberately left out.
