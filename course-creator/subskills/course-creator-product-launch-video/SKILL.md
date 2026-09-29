---
name: course-creator-product-launch-video
description: Turn real screenshots and product information into a Remotion launch ad or screenshot-based demo for a course or other product inside the course-creator bundle. Stores output under marketing/product-launch and registers real dependencies.
---

# Product Launch Video

Accept product screenshots as the main input; also use any supplied product
brief, site, repository, brand assets, screen recording or founder footage.
Inspect every selected screenshot before writing a claim. A screenshot-only
request is workable. Ask only for a missing decision that changes the
deliverable; infer ordinary defaults and label unverified details.

Produce the requested video, not an unrelated course or marketing campaign.

## 1. Establish what is true

Inventory the supplied screenshots and inspect them at readable size. Record each
file, screen name, visible action or feature, cropped or private details,
resolution, and the claim it can support. Read any supplied brief, website,
repository README or product docs. If the product is identifiable and a public
site exists, inspect the current site and verify that its name and branding match
the screenshots before using its claims. Prefer current product source to older
marketing drafts. When sources conflict, use the most direct current evidence and
flag the conflict.

**A screenshot proves a visible screen exists.** It does not prove a later click
works, a process is automatic, or a customer achieved a result. Blur sensitive
data before production. If only one screen is supplied, make a focused feature
reveal or screen tour.

Create a short `product-brief.md`: audience, problem, product promise, actual
features shown, verified evidence, open claims, offer, destination, and any
footage or audio supplied.

## 2. Intake

Read [intake](references/intake.md) and [video](references/video.md). Resolve `brand.md` ([brand](references/brand.md)) —
falling back to colours and type read off the product screenshots when there is
no brand source. Then ask platform (derives aspect and resolution), audio mode,
ending and offer details. The category is `launch-ad` unless the requester wants
a longer walkthrough.

## 3. Tell one product story

Pick one buyer and one useful outcome. Start with a specific recognisable
problem, reveal the relevant product screen early, demonstrate a small real
workflow, show the practical result supported by source material, and end with
**one verified CTA**. Make a short ad when asked for an ad; allow a longer
walkthrough when the screenshots need careful explanation.

Write `script.md` and `storyboard.md` with stable beat IDs. Each beat records
narration or on-screen copy, exact screenshot or recording source, highlighted UI
region, visible claim, motion direction, duration and transition. If an apparent
interaction is essential, use a real screen recording or matching before/after
screenshots. A cursor may guide attention on a still but cannot imply an
unobserved click result.

## 4. Design and build

Write `style.md` before coding: palette and fonts (from `brand.md`), tone, canvas
and safe areas, frame examples, screenshot treatment, caption placement, and an
effects bible. Record `## Delivery`: category, platform, aspect, master
resolution, delivery resolution and fps. **Floor is 1080p; render a 4K master
when the platform accepts it.**

Build an editable Remotion project. Put screenshots and brand assets in its
public folder and reference them through current Remotion asset APIs. Keep shots
as reusable components, and keep timing in data where practical. Confirm current
syntax and rendering options against installed guidance and official docs before
implementing.

Draw from [objects](references/objects.md). **Zoom in on form filling and typing**, keep the
cursor visible, and pair the moment with `typing`, `click`, `alert` and `success`
SFX. Highlight the hook phrase as it appears. One concept per scene. Generate any
narration with [voice](references/voice.md) and let it run in the background while the visuals
are built — it is the timing master.

With stills alone, describe the result as a **screenshot-based product demo**
rather than live captured interaction.

## 5. Review the real output

Inspect the opening, each product screen, transitions and the final CTA at the
target size. Confirm every claim matches the brief, every screenshot is genuine
and readable, private information is hidden, captions match final audio, music
does not mask speech, and the video still communicates when muted. Check logo,
URL, offer and brand consistency. Record any unverified claim left out and any
render limitation. Keep source screenshot filenames and their use in the asset
manifest so the owner can replace a screen later.

Keep `product-brief.md`, `script.md`, `storyboard.md`, `style.md`,
`assets/manifest.json`, the Remotion source project and the rendered MP4 together
so later edits can be made selectively.





## Course integration

Read the [screenshot-to-video workflow](../../references/product-launch.md) plus the
sibling [workflow](references/workflow.md) for the detailed build sequence, and
[marketing copy](../../references/marketing-copy.md) for the copy patterns. For a course
product, the existing course map, sample lesson and learner projects may supply
evidence.

If TTS is selected, also read the [course-creator-voice-narration](../course-creator-voice-narration/SKILL.md) subskill. Store
course launch output under `marketing/product-launch/`, register real
dependencies, and inspect final frames and claims.
