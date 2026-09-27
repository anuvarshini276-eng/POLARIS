# Requirements traceability — all 42 sections

Status describes implementation; external deployment checks are not claimed as passed. See VERIFICATION.md for actual evidence and HANDOFF.md for boundaries.

| Section | Implementation / evidence | Status or boundary |
|---|---|---|
| 1 Analysis | Six design documents created before application source | Done |
| 2 Frontend stack | frontend/package.json, src/ | React/TS/Vite/Tailwind and requested libraries; composed Radix/CVA primitives |
| 3 Backend | backend/app, requirements.txt | FastAPI/SQLAlchemy; SQLite local, PostgreSQL configured |
| 4 AI pipeline | services/processing.py, retrieval.py, ai/providers.py | Functional local extraction/retrieval; live providers unverified |
| 5 Copilot | api/research.py, pages/Tools.tsx | Questions/history/sources/document scope; demo extractive answers |
| 6 Document analysis | processing.metadata | Structured labeled-field extraction; missing fields stated |
| 7 Search | api/documents.py, retrieval.py, SearchPage | Hybrid ranking, metadata filters, suggestions |
| 8 Map | Explore.tsx, map-layers.tsx, land.geojson | Offline geography, 3 station points, routes/datasets; clustering unnecessary at present size |
| 9 Expeditions | Resource records, Explore.tsx | Timeline, scientists, objectives, route, station/publication context |
| 10 Repository | models, api/documents.py, Repository.tsx | Upload/edit/version/preview/download/access control |
| 11 Content Studio | Generate schema, generate/publish routes, Tools.tsx | Eight formats/audiences/tones; labeled demo templates |
| 12 Education | education/quizzes/progress APIs, Tools.tsx | Lessons/glossary/MCQs/difficulty/progress/achievements |
| 13 Analytics | dashboard API, Analytics page | Live counts and line/bar/donut charts |
| 14 Trends | analytics/trends | Repository metadata trends; no invented scientific conclusions |
| 15 Roles | core/security.py, auth and users APIs | Public/researcher/content manager/admin enforced |
| 16 Authentication | auth.py, security.py | JWT, refresh rotation, scrypt, sessions, logout, lockout |
| 17 Security | validation, shared visibility queries, middleware | Tested invalid files and cross-user isolation |
| 18 Database | models/database.py, migrations | UUID/index/FK core schema; catalog JSON simplification documented |
| 19 REST API | api/ routers and schemas/requests.py | Versioned routes, filtering/pagination, OpenAPI schemas |
| 20 Documentation | main.py | /swagger and /redoc |
| 21 Pages | App.tsx routes | All named page types reachable |
| 22 Landing | App.Home | Hero, map-network motif, stats/search/publications/expeditions/education |
| 23 Admin | Admin, moderation API | Queue, review/approve/reject/publish, users, audit, worker status |
| 24 Notifications | Notification model and APIs | Upload/process/review/quiz/account events |
| 25 Background work | durable Job model, workers/run.py | Separate nonblocking worker and processing states |
| 26 Observability | middleware, health APIs, worker heartbeat | Request IDs, JSON logs, database/provider/worker checks |
| 27 Testing | tests/, components.test.tsx, VERIFICATION.md | 11 backend + 3 frontend passing; browser flow executed |
| 28 Sample data | scripts/seed_database.py, seed_media.py | Synthetic documents, expeditions, stations, researchers, datasets, education/media |
| 29 Providers | ai/providers.py | 3 LLM / 3 embedding adapters; live execution unverified |
| 30 RAG quality | retrieval.py, processing.py | Overlap/top-k/threshold/source tracking/compression/abstention |
| 31 Storage | services/storage.py | Local and S3-compatible abstraction; local exercised |
| 32 Docker | Dockerfiles, docker-compose.yml | Five services configured; host lacks Docker |
| 33 Environment | .env.example, config.py, .gitignore | Generated local secrets, configurable providers/storage |
| 34 Structure | frontend/backend/worker/data/scripts/tests/docs | Monorepo with layered backend; worker entry in app/workers |
| 35 Quality | typed frontend/Pydantic; modular backend | Build/type/tests pass; production tuning documented |
| 36 UX | styles.css, components.tsx, pages | Responsive navigation, dialogs, loading/error/empty states, labels |
| 37 Demo Mode | seed/provider/auth pages | Works without AI keys; persistent data and labeled mock AI |
| 38 Demonstration | VERIFICATION.md | Browser upload → processing → approval → search → citation flow passed |
| 39 README | README.md | Setup, credentials, architecture, testing, security, limits |
| 40 Incremental build | Design → backend → tests → UI → browser → fixes | Implemented in stages |
| 41 Preserve/inspect | Empty project inspected; original spec untouched | New monorepo in outputs/polaris |
| 42 Handoff A–M | HANDOFF.md | Included in project; chat response restricted to URL by user |
