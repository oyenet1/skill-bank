# Teaching Assets

Create only the asset and target the teacher requests. Use the relevant lesson or project outcome and the learner's level. Keep editable sources alongside exported files.

## Lesson notes and links

- Write `lessons/{lesson-id}/notes.md` as the editable notes source. It may include the story/example, What/Why/Where/When/How, a still visual or diagram, demonstration steps, takeaway, and references.
- On request, render `notes.pdf` from the notes source. For online notes, prepare a readable Markdown or HTML page with local assets; provide a public link only if the teacher supplies one or a publishing action creates it. Add curated external links only after verifying that they lead to the relevant material.
- A Slidev deck PDF is a **different** handout from the lesson-notes PDF. Export only the requested one. Chapter or whole-course PDF compilations are separate actions.
- Respect supplied branding. For Bonifade-branded courses that retain the existing format, use the school URL at left, page number at center, and contact email at right with clickable links. Otherwise use the teacher's specified branding or a plain page-number footer. Keep navigation metadata and source-file comments out of the PDF body.

## Practice and assessment

- An exercise bank may contain zero, a few, or many exercises for a lesson. When requested, vary the work from recognition and explanation to guided application and independent use. Give each exercise an objective, task, success condition, and optional hint or solution for the instructor.
- Online assignment means a **publishable package**, not a hosted submission service: learner instructions, prerequisite concept IDs, deliverable and submission requirements, any starter files, assessment criteria, rubric, and teacher answer guidance. Do not create hosting or student accounts as a side effect.
- Quizzes and exams align each question to an outcome and include an answer key or marking guide as a separate teacher-facing asset. Use formats suitable to the subject; code is not a default requirement.
- Handouts and lesson plans are separate. A lesson plan gives timing, story cues, questions, demonstrations, expected responses, and accommodations if relevant. A learner handout contains only the material the learner needs.

Store each requested asset under its lesson or project ID, then add its relative path to that node's `artifacts` map in `course-plan.json`. Record `artifactSources` only for outputs that actually use another registered artifact, for example `"notesPdf": ["notes"]`. If notes change, mark that PDF stale until it is regenerated and checked. A separately authored assignment may have no source artifact. Check that teacher-only answers do not appear in learner-facing files. Validate the course map after registering a new artifact.
