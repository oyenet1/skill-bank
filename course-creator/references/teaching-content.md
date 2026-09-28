# Teaching Content

Use for a selected chapter, lesson, or concept. Read the course map first and expand only the named target. Keep the content useful on its own while linking to prerequisites and the next step.

## Chapter overview

Record the chapter outcome, prerequisite chapter or concept IDs, lesson sequence, estimated effort if the course uses a schedule, and its small project. Do not write every lesson because a chapter overview was requested.

## Lesson page

Write `lessons/{lesson-id}/lesson.md` with:

1. Lesson outcome and required prior knowledge.
2. A relatable story beat or everyday example before abstract definitions. Use the teacher's story if supplied; otherwise continue the course's recurring story. Keep the language simple without misrepresenting the idea or talking down to adults.
3. One concept section per mapped concept, in map order. Answer **What, Why, Where, When, How** in clear language. *How* is a process the learner can follow or observe. Introduce a term at its first practical use.
4. A visual explanation plan: what changes on screen in each step, what labels are visible, and what the learner should notice. Source or create the actual image only if requested or needed for this lesson's output.
5. A practical demonstration with expected observations or output. Use code only when relevant; for computer basics, the demo might be a file or OS task. Explain every new command, object, or step before it is used.
6. A learner check: a question, prediction, or short demonstration that reveals whether the learner understands. Full exercises remain optional.
7. Sources and further reading when factual claims or tool behavior depend on external material.

For each concept, align the visual and demonstration to the same explanation. A child should be able to understand the first pass; add a clearly separated deeper explanation for older or experienced learners when useful. Include common mistakes only when likely to help. Do not force identical section counts across unrelated subjects.

## Stories and accessibility

Maintain a short story brief in the course plan or teacher notes: setting, recurring characters or objects, audience, and teaching purpose. A supplied story takes priority. A generated story should connect the concept to a familiar consequence and lead naturally into the practical task. Avoid relying on the story as the only explanation.

Use descriptive headings, plain language, readable examples, and captions for visuals. Make the concept understandable without motion or audio alone: the lesson page and final slide state must carry the core meaning.

## Changes to existing content

When editing a concept, check the selected lesson's notes, slides, assessments, project dependencies, and video storyboard for direct references to it. Update those references or list the affected registered outputs in `staleArtifacts`; preserve unaffected work and teacher edits. Remove an output from that list after it has been refreshed and checked.
