# Intake Protocol

Run this before producing anything. The goal is a complete working brief without
dragging the requester through a drip of single questions.

## The three states of every input

| State | Behaviour |
|---|---|
| **Present** | Use it as given. |
| **Inferable** | Apply a stated default, and record it in the working brief as `inferred: <value> — <reason>`. |
| **Missing and deliverable-changing** | **Ask.** Never guess. |

An input is *deliverable-changing* when a different answer produces a different
artifact: aspect ratio, duration, category, palette, font, voice, language,
CTA destination, evidence for a claim. An input is *inferable* when a defensible
default exists and the requester can correct it cheaply.

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
