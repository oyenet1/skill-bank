---
standalone:
  name: sales-copy
  description: >-
    Write honest, attention-grabbing sales copy for a course, skill, product or
    service — hooks, listings, landing pages, posts, emails and promotional
    scripts. Verifies offer details before using them and never invents figures,
    reviews or urgency. Use for promotional requests, not ordinary writing.
bundle:
  name: course-creator-sales-copy
  description: >-
    Write honest hooks, course listings, sales pages, posts, emails, and
    promotional scripts to sell a course or skill inside the course-creator
    bundle, keeping promotional files under marketing/.
---

# Sales Copy

Identify the buyer, the learner, their level, their actual struggle, the desired
capability, the proof available, the offer, the destination and the channel.
Write only the requested asset.

## 1. Intake

Read {{ref:intake}}. Resolve tone, person and vocabulary from {{ref:brand}} —
including the `words we never use` list. Ask what changes the deliverable: who
the buyer is, the one action you want them to take, the real destination for that
action, and which proof you can actually cite. Batch the rest.

## 2. Shape the piece

Lead with a specific situation and an attainable result. Choose a question, a
useful promise, a short story, or a respectful current-to-improved comparison as
the hook. Then show the problem, its consequence, a real demonstration or sample,
the outcome the reader can reasonably expect, and **one clear next step**. Give
useful information before asking for the sale when the audience is still
exploring.

Write several hook options when asked, each concrete enough to test. Match the
CTA to a real destination — a syllabus, sample lesson, waitlist or enrolment
page.

## 3. Verify before you claim

Confirm price, dates, seat limits, certificates, support, job outcomes,
testimonials and guarantees before using them. **Do not invent figures, reviews,
urgency or learner success.** A dramatized success story must be labelled as an
example. Use the requester's real story and voice. For beginner-facing material,
speak plainly about the first useful action rather than aspirational outcomes.

## 4. Hand off

A copy script stands alone. If the requester also wants slides, narration or
video, pass the chosen script and stable beat IDs to those skills and do not
produce extra formats by default. For video production, use
{{sibling:explainer-video}}, write a per-video `style.md`, and show real material
as proof. Review mobile caption legibility and keep one CTA visible at the end.

{{mode:bundle}}
## Course integration

Read {{doc:marketing-copy.md|marketing copy}} for the fuller pattern set,
drawn from the LodgeStatus campaign notes: buyer specificity, question / promise
/ story hooks, problem-to-proof sequencing, human presentation, honest evidence
and a single action. Use the real course map, sample lesson and projects as
proof when present.

Keep promotional files in `marketing/` and register them at the course or lesson
level as appropriate. For a screenshot-driven product ad, use
{{sibling:product-launch-video}} when installed.
{{/mode}}

{{mode:standalone}}
## Standalone output

Keep promotional files in a `marketing/` folder when one exists, otherwise where
the requester names. If a `course-plan.json` is present, register the output at
the course or lesson level as appropriate.
{{/mode}}
