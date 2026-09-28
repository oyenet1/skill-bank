# Technical Terms Reference

This optional term bank preserves the original plain-language definitions for written programming lessons and indexes. Read only the categories relevant to the current lesson. Treat definitions as drafting aids: verify changing framework, service, and API details against current official sources, then teach each selected concept with **What, Why, Where, When, and How** at its first practical use. Do not turn this list into a standalone glossary chapter or require every term in a course.

### Programming Languages

| Term | Plain-language definition |
|------|--------------------------|
| JavaScript | The language of the web browser; also runs on servers via Node.js or Bun |
| TypeScript | JavaScript with static types added — catches errors before the code runs |
| PHP | A server-side scripting language widely used for web backends, especially with Laravel |
| Go (Golang) | A compiled, statically typed language by Google known for speed and simplicity |
| Rust | A systems language focused on memory safety and performance without a garbage collector |
| Python | A readable, general-purpose language popular for scripting, data, and backend APIs |
| SQL | A language for querying and managing relational databases |
| HTML | The markup language that defines the structure of web pages |
| CSS | The language that controls the visual presentation of HTML elements |
| Bash / Shell | A command-line scripting language used to automate tasks in Unix/Linux environments |
| YAML | A human-readable data format used for configuration files (Docker, CI/CD, etc.) |
| JSON | A lightweight data format used to exchange data between systems |
| Markdown | A lightweight markup language for writing formatted text using plain characters |

---

### Frontend Frameworks and Libraries

| Term | Plain-language definition |
|------|--------------------------|
| React | A JavaScript library by Meta for building component-based user interfaces |
| Vue.js | A progressive JavaScript framework for building UIs, known for its gentle learning curve |
| Nuxt.js | A framework built on top of Vue that adds SSR, file-based routing, and full-stack capabilities |
| Next.js | A React framework by Vercel that adds SSR, SSG, API routes, and file-based routing |
| Angular | A full-featured TypeScript framework by Google for building large-scale SPAs |
| Svelte | A compiler-based UI framework that ships no runtime — components compile to vanilla JS |
| SolidJS | A reactive UI library similar to React but with fine-grained reactivity and no virtual DOM |
| Astro | A static site builder that ships zero JS by default and supports multiple UI frameworks |
| Alpine.js | A lightweight JS library for adding interactivity to HTML without a full framework |
| HTMX | A library that lets you add AJAX, WebSockets, and SSE directly in HTML attributes |
| Tailwind CSS | A utility-first CSS framework for building designs directly in markup |
| Bootstrap | A CSS framework with pre-built responsive components and a grid system |
| Shadcn/ui | A collection of accessible, unstyled UI components built on Radix UI and Tailwind |
| Radix UI | A low-level, accessible component library for React |
| Framer Motion | An animation library for React |
| React Query (TanStack Query) | A data-fetching and server-state management library for React |
| Zustand | A small, fast state management library for React |
| Pinia | The official state management library for Vue.js |
| Vite | A fast frontend build tool and dev server that uses native ES modules |
| Webpack | A module bundler that compiles JavaScript, CSS, and assets into optimized bundles |
| Babel | A JavaScript compiler that converts modern JS into backward-compatible versions |
| ESLint | A static analysis tool that finds and fixes problems in JavaScript/TypeScript code |
| Prettier | An opinionated code formatter that enforces consistent style |

---

### Backend Frameworks and Libraries

| Term | Plain-language definition |
|------|--------------------------|
| Node.js | A JavaScript runtime built on Chrome's V8 engine for running JS outside the browser |
| Bun | A fast all-in-one JavaScript runtime, bundler, test runner, and package manager |
| Express.js | A minimal and flexible Node.js web framework for building APIs and web apps |
| Hono | A lightweight, ultra-fast web framework for the edge and Node.js/Bun runtimes |
| Fastify | A high-performance Node.js web framework with a focus on low overhead |
| NestJS | A TypeScript-first Node.js framework with Angular-inspired architecture (modules, decorators) |
| Laravel | A PHP framework with expressive syntax, built-in auth, ORM (Eloquent), and CLI tooling |
| Gin | A high-performance HTTP web framework for Go |
| Fiber | An Express-inspired web framework for Go |
| Axum | A modular, ergonomic web framework for Rust built on Tokio |
| Actix Web | A powerful, high-performance web framework for Rust |
| Django | A batteries-included Python web framework with built-in admin, ORM, and auth |
| FastAPI | A modern, fast Python framework for building APIs with automatic OpenAPI docs |
| Spring Boot | A Java framework for building production-ready backend services quickly |
| Koa | A lightweight Node.js framework by the Express team, using async/await middleware |
| tRPC | A TypeScript-first RPC framework for building end-to-end type-safe APIs without REST or GraphQL |
| GraphQL | A query language for APIs that lets clients request exactly the data they need |
| REST | An architectural style for APIs using HTTP methods and stateless communication |
| gRPC | A high-performance RPC framework using Protocol Buffers, common in microservices |
| WebSockets | A protocol for full-duplex, real-time communication between client and server |
| Socket.io | A library that enables real-time, event-based communication using WebSockets with fallbacks |

---

### ORMs and Database Libraries

| Term | Plain-language definition |
|------|--------------------------|
| Drizzle ORM | A lightweight, TypeScript-first ORM with SQL-like syntax and full type safety |
| Prisma | A TypeScript ORM with a schema-first approach and auto-generated client |
| TypeORM | A TypeScript ORM that supports Active Record and Data Mapper patterns |
| Sequelize | A promise-based Node.js ORM for relational databases |
| Mongoose | An ODM (Object Document Mapper) for MongoDB in Node.js |
| Eloquent | Laravel's built-in Active Record ORM for PHP |
| GORM | The most popular ORM for Go |
| SQLAlchemy | A Python SQL toolkit and ORM |
| Knex.js | A SQL query builder for Node.js — often used as the foundation for ORMs |
| MikroORM | A TypeScript ORM based on the Data Mapper pattern with Unit of Work support |

---

### Databases

| Term | Plain-language definition |
|------|--------------------------|
| PostgreSQL | A powerful, open-source relational database known for reliability and advanced features |
| MySQL | A widely used open-source relational database, common in LAMP stacks |
| SQLite | A lightweight, file-based relational database, ideal for development and embedded use |
| MongoDB | A NoSQL document database that stores data as JSON-like BSON documents |
| Redis | An in-memory key-value store used for caching, sessions, queues, and pub/sub |
| PlanetScale | A serverless MySQL-compatible database platform built on Vitess |
| Supabase | An open-source Firebase alternative built on PostgreSQL |
| Firebase Firestore | A NoSQL cloud database by Google with real-time sync capabilities |
| CockroachDB | A distributed SQL database designed for global scale and resilience |
| Turso | A distributed SQLite database built for the edge |
| Neon | A serverless PostgreSQL platform with branching support |
| Cassandra | A distributed NoSQL database designed for high availability and massive scale |
| Elasticsearch | A distributed search and analytics engine based on Lucene |

---

### Authentication and Security

| Term | Plain-language definition |
|------|--------------------------|
| JWT (JSON Web Token) | A compact, self-contained token used to securely transmit user identity between parties |
| OAuth 2.0 | An authorization framework that lets users grant third-party apps limited access to their accounts |
| OpenID Connect (OIDC) | An identity layer on top of OAuth 2.0 that provides user authentication |
| Session | A server-side record of a user's login state, identified by a session ID stored in a cookie |
| Cookie | A small piece of data stored in the browser, used for sessions, preferences, and tracking |
| CSRF (Cross-Site Request Forgery) | An attack where a malicious site tricks a user's browser into making unwanted requests |
| XSS (Cross-Site Scripting) | An attack where malicious scripts are injected into web pages viewed by other users |
| SQL Injection | An attack where malicious SQL is inserted into a query to manipulate the database |
| HTTPS | HTTP over TLS — encrypts data in transit between client and server |
| TLS (Transport Layer Security) | The cryptographic protocol that secures internet communications |
| Bcrypt | A password hashing algorithm designed to be slow and resistant to brute-force attacks |
| Argon2 | A modern, memory-hard password hashing algorithm recommended over bcrypt for new projects |
| RBAC (Role-Based Access Control) | A system where permissions are assigned to roles, and users are assigned to roles |
| ABAC (Attribute-Based Access Control) | A system where access decisions are based on attributes of the user, resource, and environment |
| API Key | A secret token passed in requests to authenticate a client application |
| Rate Limiting | Restricting how many requests a client can make in a given time window |
| CORS (Cross-Origin Resource Sharing) | A browser security mechanism that controls which origins can access a server's resources |
| Helmet.js | A Node.js middleware that sets security-related HTTP headers |
| Passport.js | A Node.js authentication middleware that supports many strategies (local, OAuth, JWT) |
| Auth.js (NextAuth) | An authentication library for Next.js and other JS frameworks |
| Clerk | A hosted authentication and user management service |
| Supabase Auth | Built-in authentication for Supabase projects |

---

### DevOps, Infrastructure, and Tooling

| Term | Plain-language definition |
|------|--------------------------|
| Git | A distributed version control system for tracking changes in source code |
| GitHub | A cloud platform for hosting Git repositories with collaboration and CI/CD features |
| GitLab | A DevOps platform with Git hosting, CI/CD pipelines, and project management |
| Docker | A platform for packaging applications into containers that run consistently anywhere |
| Docker Compose | A tool for defining and running multi-container Docker applications with a single file |
| Kubernetes (K8s) | An orchestration system for automating deployment, scaling, and management of containers |
| CI/CD | Continuous Integration and Continuous Deployment — automated pipelines for testing and releasing code |
| GitHub Actions | A CI/CD platform built into GitHub for automating workflows |
| Nginx | A high-performance web server and reverse proxy |
| Apache | A widely used open-source web server |
| Reverse Proxy | A server that sits in front of backend servers and forwards client requests to them |
| Load Balancer | A system that distributes incoming traffic across multiple servers |
| CDN (Content Delivery Network) | A network of edge servers that deliver content from locations close to the user |
| Vercel | A cloud platform optimized for frontend and full-stack JavaScript deployments |
| Netlify | A cloud platform for deploying static sites and serverless functions |
| Railway | A cloud platform for deploying backend services and databases with minimal config |
| Render | A cloud platform for deploying web services, databases, and static sites |
| AWS (Amazon Web Services) | A comprehensive cloud platform offering compute, storage, databases, and hundreds of services |
| GCP (Google Cloud Platform) | Google's cloud platform offering compute, ML, databases, and infrastructure services |
| Azure | Microsoft's cloud platform for hosting, computing, and enterprise services |
| Terraform | An infrastructure-as-code tool for provisioning cloud resources declaratively |
| Ansible | An automation tool for configuration management and application deployment |
| Prometheus | An open-source monitoring and alerting toolkit |
| Grafana | A visualization platform for metrics and logs, commonly paired with Prometheus |
| Sentry | An error tracking and performance monitoring platform |
| PM2 | A process manager for Node.js applications in production |
| Caddy | A modern web server with automatic HTTPS |
| FTP / SFTP | Protocols for transferring files between a client and a server |
| SSH | A cryptographic protocol for securely accessing remote servers |
| Environment Variables | Key-value pairs stored outside the codebase used to configure applications per environment |
| .env file | A file that stores environment variables locally, never committed to version control |

---

### Testing

| Term | Plain-language definition |
|------|--------------------------|
| Unit Test | A test that verifies a single function or module in isolation |
| Integration Test | A test that verifies multiple components working together |
| End-to-End (E2E) Test | A test that simulates a real user flow through the entire application |
| Test-Driven Development (TDD) | A practice where tests are written before the implementation code |
| Vitest | A fast unit testing framework for Vite-based projects |
| Jest | A popular JavaScript testing framework with built-in mocking and assertions |
| Playwright | A browser automation library for E2E testing across Chromium, Firefox, and WebKit |
| Cypress | An E2E testing framework that runs tests directly in the browser |
| Supertest | A Node.js library for testing HTTP servers |
| Mock | A fake implementation of a dependency used in tests to isolate the unit under test |
| Stub | A controlled replacement for a function that returns a preset value in tests |
| Code Coverage | A metric showing what percentage of code is exercised by tests |

---

### Architecture and Design Patterns

| Term | Plain-language definition |
|------|--------------------------|
| MVC (Model-View-Controller) | An architectural pattern separating data (Model), UI (View), and logic (Controller) |
| Modular Monolith | A single deployable application organized into isolated, self-contained feature modules |
| Microservices | An architecture where an application is split into small, independently deployable services |
| Monolith | A single application where all features are deployed together as one unit |
| Event-Driven Architecture | A pattern where services communicate by emitting and listening to events |
| CQRS (Command Query Responsibility Segregation) | Separating read (query) and write (command) operations into different models |
| Repository Pattern | An abstraction layer between the data access logic and the business logic |
| Service Layer | A layer that contains business logic, sitting between controllers and data access |
| Middleware | A function that runs between a request and a response, used for auth, logging, validation, etc. |
| Dependency Injection (DI) | A pattern where dependencies are passed into a class rather than created inside it |
| SOLID Principles | Five design principles for writing maintainable OOP code (Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion) |
| DRY (Don't Repeat Yourself) | A principle that every piece of knowledge should have a single, authoritative representation |
| KISS (Keep It Simple, Stupid) | A principle favouring simple solutions over unnecessarily complex ones |
| YAGNI (You Aren't Gonna Need It) | A principle against adding functionality until it is actually needed |
| API Gateway | A server that acts as the single entry point for all client requests to backend services |
| BFF (Backend for Frontend) | A dedicated backend service tailored to the needs of a specific frontend client |
| Serverless | A cloud execution model where the provider manages infrastructure and scales automatically |
| Edge Functions | Serverless functions that run at CDN edge locations close to the user |

---

### Web Concepts and Protocols

| Term | Plain-language definition |
|------|--------------------------|
| HTTP | The protocol used to transfer data between browsers and web servers |
| HTTPS | HTTP secured with TLS encryption |
| HTTP Methods | GET (read), POST (create), PUT (replace), PATCH (update), DELETE (remove) |
| HTTP Status Codes | Numeric codes indicating the result of an HTTP request (200 OK, 404 Not Found, 500 Server Error, etc.) |
| REST | An architectural style for APIs using HTTP methods, stateless requests, and resource-based URLs |
| GraphQL | A query language for APIs where clients specify exactly what data they need |
| WebSocket | A protocol for persistent, full-duplex communication between client and server |
| DNS (Domain Name System) | The system that translates human-readable domain names into IP addresses |
| IP Address | A numerical label assigned to each device on a network |
| Domain | A human-readable address for a website (for example `example.com`) |
| Subdomain | A prefix to a domain (for example `api.example.com`) |
| SSL/TLS Certificate | A digital certificate that enables HTTPS and verifies a server's identity |
| TCP/IP | The foundational communication protocols of the internet |
| UDP | A connectionless protocol faster than TCP, used for video streaming and gaming |
| Latency | The time it takes for a request to travel from client to server and back |
| Bandwidth | The maximum rate of data transfer across a network |
| Caching | Storing copies of data temporarily to serve future requests faster |
| Cookie | A small piece of data stored in the browser sent with every request to the same origin |
| Local Storage | Browser storage for key-value pairs that persists across sessions |
| Session Storage | Browser storage for key-value pairs that clears when the tab is closed |
| CORS | A browser mechanism controlling which origins can make requests to a server |
| Webhook | An HTTP callback triggered by an event in one system to notify another system |
| SSR (Server-Side Rendering) | Rendering HTML on the server and sending it to the browser |
| CSR (Client-Side Rendering) | Rendering HTML in the browser using JavaScript after the initial page load |
| SSG (Static Site Generation) | Pre-rendering HTML at build time for fast, cacheable pages |
| ISR (Incremental Static Regeneration) | Regenerating static pages in the background after deployment without a full rebuild |
| PWA (Progressive Web App) | A web app that uses modern APIs to deliver app-like experiences including offline support |

---

### Data and State Management

| Term | Plain-language definition |
|------|--------------------------|
| State | Data that changes over time and drives what the UI displays |
| Props | Data passed from a parent component to a child component |
| Side Effect | Any operation that affects something outside the current function (API calls, timers, DOM changes) |
| Reactive Programming | A programming paradigm where the UI automatically updates when underlying data changes |
| Immutability | The practice of never modifying data directly — always creating a new copy with changes |
| Serialization | Converting an object into a format (like JSON) that can be stored or transmitted |
| Deserialization | Converting serialized data back into an object |
| Pagination | Splitting large datasets into pages to avoid loading everything at once |
| Cursor-based Pagination | Pagination using a pointer to the last seen item instead of page numbers |
| Offset Pagination | Pagination using `LIMIT` and `OFFSET` in SQL queries |
| Normalization (DB) | Organizing database tables to reduce redundancy and improve data integrity |
| Denormalization | Intentionally introducing redundancy in a database for read performance |
| Migration | A versioned script that modifies the database schema in a controlled, repeatable way |
| Seed | A script that populates a database with initial or test data |
| Transaction | A group of database operations that either all succeed or all fail together |
| ACID | Atomicity, Consistency, Isolation, Durability — properties that guarantee reliable DB transactions |
| N+1 Problem | A performance issue where fetching a list runs one query per item instead of one query total |
| Eager Loading | Loading related data in the same query to avoid the N+1 problem |
| Lazy Loading | Loading related data only when it is actually accessed |
| Index (DB) | A data structure that speeds up lookups on a database column |
| Foreign Key | A column that references the primary key of another table to enforce relationships |
| Primary Key | A unique identifier for each row in a database table |
| Soft Delete | Marking a record as deleted without removing it from the database |

---

### Package Managers and Build Tools

| Term | Plain-language definition |
|------|--------------------------|
| npm | The default package manager for Node.js |
| Yarn | A fast, reliable package manager for JavaScript with workspaces support |
| Bun | An all-in-one JavaScript runtime and package manager significantly faster than npm |
| pnpm | A disk-efficient package manager that uses a content-addressable store |
| Composer | The dependency manager for PHP |
| Cargo | The package manager and build tool for Rust |
| Go Modules | Go's built-in dependency management system |
| pip | The package installer for Python |
| Vite | A next-generation frontend build tool using native ES modules for instant HMR |
| Webpack | A module bundler that processes and optimizes assets for production |
| Rollup | A module bundler optimized for libraries, producing smaller bundles than Webpack |
| esbuild | An extremely fast JavaScript bundler and minifier written in Go |
| Turbopack | A Rust-based successor to Webpack, used in Next.js |
| tsconfig.json | The TypeScript configuration file that controls compiler options |
| package.json | The manifest file for a Node.js project listing dependencies, scripts, and metadata |

---

### Realtime and Messaging

| Term | Plain-language definition |
|------|--------------------------|
| WebSocket | A protocol for persistent, bidirectional communication between client and server |
| Socket.io | A library providing WebSocket communication with automatic fallbacks |
| SSE (Server-Sent Events) | A one-way channel from server to client for streaming updates over HTTP |
| Pub/Sub (Publish/Subscribe) | A messaging pattern where publishers emit events and subscribers receive them |
| Message Queue | A buffer that stores messages between a producer and a consumer for async processing |
| BullMQ | A Node.js queue library backed by Redis for background job processing |
| RabbitMQ | A message broker that implements the AMQP protocol for reliable message delivery |
| Kafka | A distributed event streaming platform for high-throughput, fault-tolerant messaging |
| Long Polling | A technique where the client holds a request open until the server has new data |

---

### Miscellaneous Developer Terms

| Term | Plain-language definition |
|------|--------------------------|
| API (Application Programming Interface) | A defined contract for how two systems communicate |
| SDK (Software Development Kit) | A set of tools, libraries, and documentation for building on a platform |
| CLI (Command Line Interface) | A text-based interface for interacting with software via commands |
| IDE (Integrated Development Environment) | A software application for writing, running, and debugging code |
| Linting | Automatically checking code for style errors, bugs, and anti-patterns |
| Refactoring | Restructuring existing code without changing its external behaviour |
| Technical Debt | The implied cost of shortcuts taken now that will require rework later |
| Boilerplate | Repetitive code that must be included with little or no modification |
| Scaffold | A generated project or file structure used as a starting point |
| Monorepo | A single repository containing multiple related projects or packages |
| Polyrepo | A setup where each project or service lives in its own separate repository |
| Semantic Versioning (SemVer) | A versioning scheme using MAJOR.MINOR.PATCH to communicate the nature of changes |
| Open Source | Software with source code that anyone can inspect, modify, and distribute |
| License | A legal document specifying how software can be used, modified, and distributed |
| README | A markdown file at the root of a project explaining what it does and how to use it |
| Changelog | A file documenting all notable changes to a project by version |
| Hotfix | An urgent fix applied directly to production to resolve a critical bug |
| Feature Flag | A technique to enable or disable features at runtime without deploying new code |
| A/B Testing | Showing two versions of a feature to different users to measure which performs better |
| Observability | The ability to understand the internal state of a system from its external outputs (logs, metrics, traces) |
| Logging | Recording events and errors from an application for debugging and monitoring |
| Tracing | Tracking the path of a request through a distributed system |
| Metrics | Quantitative measurements of system behaviour (response time, error rate, throughput) |
