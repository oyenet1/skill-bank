# Technology Dependency Hints

This is a planning aid for technical courses. Use only the rows relevant to the selected goal and stack. Confirm changing framework behavior against current official documentation. Do not treat the topic lists as mandatory chapters or a glossary to copy into lessons.

| Target | Likely foundations before application |
|---|---|
| Browser/frontend | Computer and browser use if needed → HTML → CSS → JavaScript fundamentals → TypeScript if selected → UI framework → testing and deployment |
| API/backend | Computer and terminal use if needed → language fundamentals → HTTP/API basics → data modeling and SQL if relational data is used → framework routes, persistence, auth, testing, operations |
| Fullstack | Frontend and backend foundations → browser-to-server requests and data flow → integrated features → deployment |
| DevOps | Operating systems and terminal → networking, DNS, HTTP, Git → deployment and containers → CI/CD and observability |

## Common framework dependencies

| Chosen framework | Language/runtime foundations to teach first |
|---|---|
| React, Vue, Next.js, Nuxt, Angular, Svelte, Astro | JavaScript; TypeScript when chosen or used by the course |
| Express, Hono, Fastify, NestJS | JavaScript or TypeScript and the chosen runtime |
| Laravel | PHP |
| Gin, Fiber | Go |
| Axum, Actix Web | Rust |
| Django, FastAPI | Python |
| Spring Boot | Java or Kotlin as chosen |

Teach SQL and schema design before an ORM abstraction when the project uses a relational database. Teach API request/response flow before authentication internals. Introduce security, architecture, scalability, DSA, and deployment concepts when a concrete lesson or project needs them. Do not assume every beginner needs Kubernetes, microservices, WebSockets, or a specific package manager.

For breadth, consult the relevant [roadmap.sh](https://roadmap.sh/) map when useful. For syntax and behavior, use official language and framework documentation. For simpler supplementary explanations, use a verified beginner tutorial. Record actual source pages used in the lesson; never fabricate deep links.
