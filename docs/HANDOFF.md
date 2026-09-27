# A–M project handoff

## A. Completion summary
Working local frontend/backend with persistent documents, authentication, processing, search, citations, approvals, map, expeditions, datasets, media, outreach, education, analytics, notifications and administration. The browser workflow was exercised against the live local database. Validation and deployment limitations are stated separately.

## B. Architecture
React SPA calls same-origin `/api/v1` FastAPI routes. Repository permission helpers are shared by discovery, previews, downloads and retrieval. Service modules handle storage, extraction, vectors and rate limiting. A standalone worker claims durable database jobs. Processing and publication are separate state machines.

## C. Technologies
React, TypeScript, Vite, Tailwind, Radix/CVA accessible components, React Router, TanStack Query, Zustand, Recharts, Leaflet, Framer Motion, Lucide; FastAPI, SQLAlchemy, Alembic, Pydantic; SQLite locally; PostgreSQL/pgvector and Redis in Compose; local/S3 storage adapters.

## D. AI/RAG
Deterministic demo embeddings plus lexical ranking, overlap-aware chunks, source permissions, top-k and relative relevance filtering. Demo responses are source excerpts with real document/chunk references. OpenAI and local compatible LLM adapters and OpenAI/sentence-transformer embedding adapters are provided. No unsupported model-quality claims.

## E. Database
Persistent UUID-based entities for accounts, refresh sessions, documents, versions, chunks, jobs, typed catalog resources, conversations, messages with citations, generations, attempts, notifications, analytics and audit. Indexed identifiers/foreign keys and unique constraints protect core relations. Catalog metadata uses JSON records as a documented design simplification.

## F. APIs
All live routes and request schemas are listed by `/openapi.json`, `/swagger` and `/redoc`. The concise route convention is in API.md.

## G. Security
Scrypt, short-lived JWTs, rotating/revocable sessions, account lockout, per-client rate limiting, role restrictions, private-resource filtering, source-aware conversation history, safe storage keys, input/file validation, security headers and audit events. Redis provides shared limiting when configured.

## H. Local run
Use scripts/start-local.ps1. The app is served by FastAPI at localhost:8000. Keep the worker running for uploads. Data persists in data/polaris.db and data/uploads. Startup logs are in data/. Browser refresh requires signing in again because credentials remain in memory.

## I. Docker
Set POSTGRES_PASSWORD and JWT_SECRET, then docker compose up --build. Five service definitions and three Dockerfiles are included. Docker execution was not tested because the host has no Docker installation.

## J. Demo credentials
Use the role buttons on /login. Unique generated values are in data/demo-accounts.json. These are local demonstration accounts, never production credentials.

## K. Known limitations
Live model APIs, S3, PostgreSQL/pgvector and Redis execution are unverified on this host. Local demo retrieval is deterministic and not equivalent to a trained semantic model. Metadata parsing identifies labeled fields and explicitly marks missing values. Scanned PDFs need OCR before upload. The worker is configured for a single consumer; external orchestration, retries across distributed leases and high-volume ingestion need deployment validation. Catalog normalization is intentionally compact rather than the brief's illustrative full table list. Map geometry is low resolution; with three station points clustering is unnecessary. No external social-platform posting occurs.

## L. Future improvements
Benchmark live retrieval on an expert-labeled corpus; add OCR; evaluate rerankers and model-specific structured extraction; add finer catalog relations and institution-specific sharing; scale worker leases and indexing; add live observatory connectors and approved official datasets; introduce CI/container integration tests and route-based frontend splitting.

## M. SIH presentation flow
Open the landing page → map → Bharati → linked expedition/research → search sea ice → open metadata and source preview → sign in via demo role → Copilot question and citation → Content Studio awareness article → Education Hub quiz → Analytics → administrator → upload TXT/PDF/DOCX/CSV → wait for COMPLETED → Review → Approve → Publish → search distinctive uploaded text → ask Copilot about it. The synthetic zirconium validation document remains as a browser-tested example.
