# Screenshot to Product Launch Video

Keep the project in a named `videos/{product-slug}/` folder, or the location the user chose. Store `product-brief.md`, `script.md`, `storyboard.md`, `style.md`, `assets/manifest.json`, the Remotion source project, and the rendered MP4 there as each becomes available. Preserve original screenshots separately from redacted or cropped working copies so edits remain reversible.

## 1. Establish what is true

Inventory the supplied screenshots and inspect them at readable size. Record each file, screen name, visible action or feature, cropped/private details, resolution, and the claim it can support. Read any supplied product brief, website, repository README, product docs, or feature pages. If the product is identifiable and a public site exists, inspect the current site for context and verify that its name and branding match the screenshots before using its claims. Prefer the current product source to older marketing drafts. Compare product names, logo, colors, pricing, and CTA against the source; when sources conflict, use the most direct current evidence and flag the conflict. Do not present marketing language as proof of product behavior.

Create a short `product-brief.md` with audience, problem, product promise, actual features shown, verified evidence, open claims, offer, URL or CTA destination, and footage or audio supplied. A screenshot proves the visible screen exists; it does not prove a later click works, a process is automatic, or a customer achieved a result. If only one screen is supplied, make a focused feature reveal or screen tour. For a multi-step demo, use distinct real screenshots or screen recording for each state. Blur sensitive data before production.

## 2. Tell one product story

Pick one buyer and one useful outcome. Start with a specific, recognizable problem or question, reveal the relevant product screen early, demonstrate a small real workflow, show the practical result supported by source material, and end with one verified CTA. Use plain language. Make a short ad if the user asks for an ad; allow a longer walkthrough when the screenshots need careful explanation. A launch ad can show what the product is, who it helps, and the first useful action without listing every feature.

Write `script.md` and `storyboard.md` with stable beat IDs. Each beat records narration or on-screen copy, exact screenshot/recording source, highlighted UI region, visible claim, motion direction, duration, and transition. Mark a still-image reconstruction as such in the production notes. If an apparent interaction is essential, use a real screen recording or matching before/after screenshots. A cursor may guide attention on a still, but cannot imply an unobserved click result.

## 3. Design and build

Create `style.md` before coding: resolve palette and fonts from `brand.md` (falling back to colours and type read off the product screenshots when no brand source exists), tone, canvas, safe areas, frame examples, screenshot treatment, caption placement, and an effects bible. For each effect state its teaching or sales purpose, where it may appear, entrance, hold, exit, duration, and easing. Record `## Delivery`: category, platform, aspect ratio, master resolution, delivery resolution, renderer and frame rate — **4K master when the platform accepts it, then downscale; 1080p is the default delivery, 720p the smallest accepted, never below**. Use motion to reveal hierarchy and guide the eye; keep the actual UI readable. Use supplied icons and images when appropriate, copying selected assets into the video project and recording their source. Do not replace genuine product screens with generated imitations.

Ask once: **Remotion or HyperFrames?** Remotion (default) is a React project with the larger ecosystem and the more mature Lambda path. HyperFrames is the Apache-2.0 alternative — plain HTML + CSS + GSAP, no build step, no per-seat or per-render licence — choose it when the deliverable must ship without a source-available licence review or the handover must be editable by a non-developer. Both render the same screens, crops and callouts.

For **Remotion**, build an editable project. Put local screenshots and brand assets in its public asset folder and reference them using current Remotion asset APIs. The official documentation shows `<Img src={staticFile('screen.png')}/>` for assets in `public/`; frame-driven zoom and pan can use `useCurrentFrame()` with `interpolate()`. Keep shots as reusable components or clear scene units, and keep timing in data where practical.

For **HyperFrames**, build a plain-HTML composition. Screenshots are `<img>` elements; zoom, pan and callouts are GSAP tweens on a timeline created paused and registered on `window.__timelines["<composition-id>"]`; timing lives in `data-start` / `data-duration` / `data-track-index` on slots that carry `class="clip"`, and the determinism rules apply — no wall clocks, no unseeded randomness, no render-time network fetches.

Confirm the current syntax and rendering options from the installed guidance and official docs before implementing. Render an MP4 when available, and retain the source project.

When the user supplies a recording or narration, time scenes and captions to the actual media. If the user asks for TTS, create and verify its WAV first, then time to it — generate it early and let it run while the visuals are built, since its beat lengths drive scene durations. Without audio, make on-screen text sufficient for understanding. Plan sound as a real layer: a small named SFX set (`typing`, `click`, `alert`, `success`, `whoosh`, `pop`, `shutter`, `ambient`) used consistently, with music and ambient beds ducked roughly 12–18 LUFS under speech.

**Zoom in on every form-filling, typing or dense-UI moment**, keep the cursor visible, and pair the action with the matching SFX — `typing` while characters appear, `click` on commit, `alert` on a notification, `success` on completion. Keep labels and data legible at the zoomed size. Highlight the hook phrase as it appears on screen; one concept per scene. A CapCut package is optional and, when requested, includes separate clips and a timecoded guide.

## 4. Review the real output

Inspect opening, each product screen, transitions, and final CTA at the target size. Confirm every claim matches the product brief; every screenshot is genuine and readable; private information is hidden; captions match final audio; music does not mask speech; and the video still communicates when muted. Check logo, URL, offer, and brand consistency. Record any unverified claim left out and any render limitation. Keep source screenshot filenames and their use in an asset manifest so the product owner can replace a screen later.

Deliver three outputs: the **video** (MP4), the **audio** (the voiceover as MP3, converted from the verified WAV), and the **voiceover text** (timed SRT, or plain TXT when only the read is needed). Keep the editable source project, the WAV and the captions with them.
