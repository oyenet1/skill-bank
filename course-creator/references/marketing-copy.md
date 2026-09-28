# Marketing Copy for Courses and Skills

Use when the teacher asks for a course listing, sales page, launch post, ad, email, short video script, or spoken hook to sell a skill. Teaching assets remain separate: a lesson should teach, while marketing copy invites the right person to take the next step. This reference distills the useful patterns in the LodgeStatus marketing Markdown files; adapt the structure to the course, not the hotel's claims or visual identity.

## Decide what the buyer needs to hear

Identify the buyer, learner, entry level, real frustration, desired capability, proof available, offer, destination, and channel. A parent buying for a child, an adult changing careers, and a team buying training need different words. Read the course map and actual lessons/projects before claiming an outcome. If price, enrollment date, certificate, support, trial, or guarantee is unknown, omit it or ask; do not invent it.

Lead with the learner's result in ordinary words. Name one specific situation they recognize, then show the small change the course helps them make. A module list alone is weak evidence; a real lesson sample, demonstration, learner project, or teacher walkthrough is stronger. Use testimonials, completion numbers, job outcomes, and earnings claims only with evidence and permission.

## Build an attention-grabbing opening

Choose one hook shape that fits the audience:

- **Question:** Ask about a familiar stuck moment. Example: “Can your child explain what a file is before they start coding?”
- **Useful promise:** Offer a concrete takeaway the content genuinely delivers. Example: “Learn what a file extension tells you, then sort three files yourself.”
- **Story moment:** Begin with a person facing a small, recognizable problem. Example: “Amina saved her project, then could not find it. The lesson starts there.” Label fictional stories as examples or dramatizations.
- **Current workflow → improved workflow:** Respect what learners do today, then show a real lesson or project that changes it. Avoid shaming beginners.

Write several hooks when variation is requested; select the one that names the audience's actual problem fastest. The first sentence should make sense without a logo, course title, or jargon. Avoid generic urgency, fear, or a big promise before proof.

## Turn attention into a clear offer

A useful short sequence is **problem → consequence → demonstration or evidence → attainable outcome → one action**. For a teaching post, give the useful explanation before any invitation. For a sales page or ad, show the course's method through an actual example and a visible project. Use a concise story with person, setting, obstacle, attempted fix, change, and takeaway when it helps the audience picture learning.

Choose one action appropriate to readiness: view the syllabus, try a sample lesson, join a verified waitlist, or enroll in an available course. Match the CTA to the actual page or form. A free sample is an offer only if it exists. Use one CTA per short asset rather than scattering unrelated actions.

For a Nigerian audience, use familiar contexts and clear local payment language where relevant. Use Naira prices only when verified. Natural local speech can help when it is authentic to the teacher; avoid forced slang or assumptions about all learners.

## Channel and media handoff

- **Course listing or landing page:** clear learner outcome, who it is for, prerequisites, sample of the teaching method, project progression, logistics, evidence, and one enrollment action.
- **Short post or email:** one problem, one useful insight or example, one next step. Write a subject/headline that accurately matches the body.
- **Short video ad:** open on the human or visible problem, then show a real lesson moment, project, or teacher demonstration. Keep spoken copy natural, captions short and readable on a phone, and one CTA visible at the end. Make the video understandable muted and make the spoken message understandable without the visuals. Actual video production follows the video skill and requires its own `style.md`.
- **Campaign variants:** change one major element at a time, such as hook or CTA, and label untested ideas as hypotheses. Judge by relevant actions such as sample-lesson starts, qualified inquiries, or enrollments, not views alone.

Keep promotional artifacts separate from lesson artifacts in a `marketing/` folder when there is a course root. Register them in course-level `artifacts` when they belong to the whole course, or a lesson's `artifacts` when they sell that lesson. A copy brief or script may be produced alone; slides, TTS, and video are separate requested outputs and can use that script as an input. Record those real dependencies in `artifactSources`, using `node-id.artifactName` for an input owned by another node.

For a motion-led launch ad based on product screenshots, use the independent `product-launch-remotion` skill when available, or the course bundle's [product launch handoff](product-launch.md). Inspect the real screens and product information before adapting this copy into a demo story.

## Source notes

The distilled patterns come chiefly from the LodgeStatus `website/marketing/video-ads-playbook.md`, `docs/marketing/LODGESTATUS_10_ONE_MINUTE_AD_SCRIPTS.md`, `LODGESTATUS_OLD_WAY_NEW_WAY_COMPARISON_ADS.md`, `LODGESTATUS_CAPCUT_REAL_PRESENTER_GUIDE.md`, and `docs/marketing/content/README.md`. They contribute buyer specificity, question/promise/story hooks, problem-to-proof sequencing, real demonstration, one CTA, honest claims, and mobile legibility. Older campaign and content-engine drafts contain unverified figures and exaggerated outcomes; treat them as idea prompts only, never as proof for a course.
