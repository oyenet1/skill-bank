# Written Course Production

Use this when the teacher requests written chapters, lesson pages, course notes, an index, a schedule, or a print PDF. These are separate actions; do not generate them all because one was requested. The course map remains the source of order and stable IDs.

## Written course metadata and outline

For a full written outline, show the title, subject or track, learner profile, goal, prerequisites, selected stack where relevant, duration and weekly hours if supplied, and the story premise if used. List every section, chapter, lesson, and mapped concept. A chapter overview states its objective, prerequisites, estimated time when available, full lesson list, outcomes, and small project. Counts shown in headings must match listed items.

If the teacher requests a weekly schedule, give each week a focus, hours target, deliverable, and checkpoint. Keep the total within the stated time budget; warn when a desired stack or depth cannot realistically fit.

## Lesson page and review

Use the mapped lesson's stable path. Preserve the old text-first teaching strengths in a flexible page:

1. Outcome, prerequisites, and navigation to existing pages.
2. Terms needed for this lesson in plain language; teach each at its first practical use.
3. A relatable story or real-life example **before** abstract explanation.
4. For each mapped concept: **What, Why, Where, When, How**, then a deeper explanation when useful.
5. A practical example or worked demonstration. Use a labeled code block with comments only when code is relevant.
6. Likely mistakes and fixes, when they would help the learner.
7. A short learner check. A larger exercise set is optional and generated separately.
8. Verified primary and supplementary references with direct topic links.

At the end of a chapter, a requested review checkpoint can recap the concepts, ask learners to explain and apply them, and connect to the chapter's small project. Assignments may progress from guided to independent, with objectives, task, expected outcome, and rubric when requested.

## Navigation and index

Keep navigation between **existing** written files: course table of contents → chapter overview → lesson pages → available review or practice → next chapter. Skip an optional file that was never created. Update affected links when the map moves a lesson. Stable IDs and file paths allow the table of contents to change without renaming content files.

On a separate index request, create `index.md`: alphabetized terms and concepts actually taught, each with a one-line learner-friendly definition and the first chapter/lesson where it appears. Include only material present in the course, not the entire optional technical term bank. Refresh index references after a reorder.

## Print PDF from written material

A lesson-notes PDF, chapter compilation, and full-course compilation are separate outputs. Compile only existing requested material in course-map order. For a chapter compilation, use overview → lesson notes/pages → any requested exercises or assignments → review. For a full-course compilation, put chapters in section order and include a linked table of contents when the renderer supports it.

Preserve the useful original print rules:

- Cover or opening page with title, audience/track, relevant stack, and edition date when applicable; each lesson starts clearly on a new page in a compilation.
- Body around 11 pt using a readable font such as Inter or Source Sans Pro; headings visibly larger; code in a monospaced font such as JetBrains Mono or Fira Code. Preserve code indentation and language labels.
- Keep code blocks together when they fit on a page; use a light code background and clear border. Keep tables readable with distinct headers and left-aligned body text.
- Strip frontmatter, source-file header comments, and Markdown navigation bars from the print body. Suppress browser or OS default file-path, URL, and date headers/footers.
- For Bonifade-branded output, retain the original clickable footer: school URL on the left, page number centered, and `biz@bowofade.com` on the right. Use teacher-supplied branding for their courses, or a plain page number if none is specified.
- Inspect the resulting PDF for missing pages, broken diagrams or links, clipped code, and misplaced footers. If conversion is unavailable, deliver the editable Markdown and report that the PDF could not be rendered.
