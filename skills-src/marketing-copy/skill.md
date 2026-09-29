---
standalone:
  name: marketing-copy
  description: >-
    Write honest, attention-grabbing marketing and copywriting for anything — a
    course, product, service, app, event, book or brand. Produces hooks,
    headlines, taglines, listings, product descriptions, landing pages, ads,
    social posts, emails, launch announcements and video or audio scripts.
    Verifies every claim against real evidence and never invents figures, reviews
    or urgency. Use whenever the deliverable is written copy.
bundle:
  name: course-creator-marketing-copy
  description: >-
    Write honest marketing and promotional text for a course or skill inside the
    course-creator bundle — hooks, course listings, sales pages, posts, emails and
    scripts — keeping promotional files under marketing/.
---

# Marketing Copy

Write the exact piece that was asked for, for whatever is being sold, taught,
announced or explained. Identify the reader, the offer, the proof that actually
exists, the destination, and the channel. Write only the requested asset.

## 1. Intake

Read {{ref:intake}}. Resolve tone, person and vocabulary from {{ref:brand}} —
including the `words we never use` list, and the vertical, which sets the flavour.
Ask what changes the deliverable:

- who the reader is, and what they already believe
- the one action you want them to take
- the real destination for that action
- which proof you can actually cite
- the channel, since it sets length and format

Batch the rest.

## 2. Choose the shape

Lead with a specific situation and an attainable result. Pick the hook that fits
the reader's awareness:

| Reader state | Hook |
|---|---|
| does not know the problem | story, surprising fact, before/after |
| knows the problem, not the fix | name the problem plainly, then the turn |
| knows the fix, not your version | demonstration or comparison |
| comparing options | proof, specifics, honest trade-offs |
| ready to act | the offer, the terms, one clear step |

Then: problem → consequence → a real demonstration or sample → the outcome the
reader can reasonably expect → **one clear next step**. Give useful information
before asking for the sale when the reader is still exploring.

Write several hook options when asked, each concrete enough to test.

## 3. Write for the channel

Match form to where the piece will live — a landing page, a listing, a social
post and an email are not the same artifact in different lengths.

| Channel | Shape |
|---|---|
| landing page | hook → problem → proof → offer → CTA; scannable headings |
| product or course listing | what it is, who it's for, what you get, what changes, CTA |
| ad (search / social / display) | one idea, one promise, one action; respect the character limit |
| social post / thread | first line carries the hook; one idea per beat |
| email | subject, preview, one reason to open, one action |
| launch / announcement | what changed, why it matters, what to do now |
| video or audio script | spoken rhythm, stable beat IDs, timed to the format |
| short-form (SMS / push) | one sentence, one link, no preamble |

Match the CTA to a real destination — a product page, checkout, booking page,
waitlist or signup form. Never point at a page that does not exist.

## 4. Verify before you claim

Confirm price, dates, capacity, guarantees, support, outcomes and testimonials
before using them. **Do not invent figures, reviews, urgency or customer
success.** A dramatized success story must be labelled as an example. Use the
requester's real story and voice. When the reader is new to the subject, speak
plainly about the first useful action rather than aspirational outcomes.

Where a claim carries weight, show the evidence on screen or in the copy — a real
screenshot, a real sample, a real number with its source.

## 5. Use the source library

`references/library/marketing/` holds full-text source books — Hormozi on offers
and lead generation, Akin Alabi on selling in Nigeria, Paul Smith on selling with
story, Brian Tracy on selling psychology. The folder's `README.md` is the index.

Use it as a source of **principles**, never as text to reproduce:

- **Search, do not read.** Search the library for the concept you need — offer,
  guarantee, lead magnet, objection, scarcity, story structure — and read only the
  passage that answers it. A single book runs to tens of thousands of words; never
  load one into context whole.
- **Distil to a principle**, then write in the requester's voice and for their
  audience. Never paste a passage, a framework name or a distinctive phrase
  verbatim.
- **Attribute a specific framework** by book and author in the working brief, and
  credit it in the copy only if the requester wants it.
- **Adapt for context.** Nigeria-specific tactics apply where the audience and
  market actually match; do not transplant them where they do not.
- The library is reference material, not a licence. Do not reproduce its text in
  published output.

## 6. Hand off

A copy script stands alone. If the requester also wants slides, narration, a
diagram or video, pass the chosen script and stable beat IDs to those skills and
do not produce extra formats by default. For video production use
{{sibling:explainer-video}}, write a per-video `style.md`, and show real material
as proof. Review mobile caption legibility and keep one CTA visible at the end.

{{mode:bundle}}
## Course integration

Read {{doc:marketing-copy.md|the course marketing reference}} for the fuller
pattern set, drawn from the LodgeStatus campaign notes: buyer specificity,
question / promise / story hooks, problem-to-proof sequencing, human
presentation, honest evidence and a single action. Use the real course map,
sample lesson and projects as proof when present.

For a course or skill, the CTA destination is usually a syllabus, sample lesson,
waitlist or enrolment page; a parent may need confidence that a child can begin
from zero, while an adult learner may need the prerequisite path. Keep
promotional files in `marketing/` and register them at the course or lesson level
as appropriate. For a screenshot-driven product ad, use
{{sibling:product-launch-video}} when installed.
{{/mode}}

{{mode:standalone}}
## Standalone output

Keep promotional files in a `marketing/` folder when one exists, otherwise where
the requester names. If a `course-plan.json` is present, register the output at
the course or lesson level as appropriate. For a screenshot-driven product ad or
launch video, use the {{sibling:product-launch-video}} skill when installed.
{{/mode}}
