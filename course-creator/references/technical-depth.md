# Technical Concept Placement and Depth

Use this only when a technical course or project reaches the relevant topic. It preserves the original problem-first system design and everyday-first DSA teaching patterns without requiring every topic in every course. For vocabulary prompts, see [technical terms](technical-terms.md); for broad coverage prompts, see [roadmap notes](pdf-derived-roadmap-notes.md).

## Introduce concepts where they are needed

Teach a supporting idea inside the lesson or project step that first uses it. Begin with the practical problem, answer **What, Why, Where, When, How**, then show the implementation. A term mentioned earlier in passing still needs its real introduction when first used.

| Concept | Useful first context |
|---|---|
| Files and extensions | Saving, finding, or opening the learner's first file |
| Middleware, hashing, sessions, tokens | Building registration and login |
| CORS | First browser request to a separate backend |
| Foreign keys and relationships | First linked database tables |
| Indexes and query plans | First searchable table or slow query |
| Transactions | A task with multiple writes that must succeed together |
| Redis or another cache | Repeated expensive reads or session storage |
| Queue or background job | Work such as sending mail that delays a request |
| Rate limiting | Protecting a sensitive endpoint |
| Webhooks | First third-party callback integration |
| Docker and CI/CD | Preparing and automating deployment |
| Big O | First code path whose work grows noticeably with input size |
| Pagination | First list too large to return at once |

## System design: problem first

For a selected system design concept, use **problem → visible symptom → root cause → possible approaches → chosen solution → how it works → diagram → practical test**. Useful scenarios from the original skill include a slow site needing scale, repeated reads needing a cache, distant images needing a CDN, slow table searches needing an index, welcome email delaying signup, bot traffic at login, server failure, read-heavy databases, breaking API changes, and deciding whether a monolith should split. Cover only scenarios tied to the course goal and project. An architecture diagram should use an editable Mermaid or SVG form with a caption.

## Data structures and practical math: everyday first

For a selected DSA topic, start with an everyday analogy, map it to the technical concept, explain What/Why/Where/When/How, then show a small code example and its project use. The original topic pool includes arrays/iteration, hash maps, stacks, queues, binary search, sorting, practical Big O, an in-memory search, percentages, averages, pagination offsets, and growth rate. Teach the subset learners will apply. Keep complexity examples numerical and concrete; explain a built-in production operation alongside any teaching algorithm.

## Architecture and delivery

If a backend or fullstack project needs them, introduce use cases, data flow diagrams, and ERDs before implementation; explain database relationships and schema changes before ORM usage. Include testing and deployment when the learner reaches a runnable project. Preserve dependency order while allowing the teacher to choose a smaller course that stops before advanced operations.
