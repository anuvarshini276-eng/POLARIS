# POLARIS

**Polar Research Intelligence, Knowledge & Outreach System · SIH26063**

POLARIS connects polar research discovery, document evidence, expeditions and public education in one working platform. The supplied sample research is synthetic and clearly labeled. It is not an official government research repository.

## Problem and proposed solution

Research documents, expedition context, datasets and public learning material are often disconnected. POLARIS joins them through a searchable repository, geographic explorer, source-grounded Copilot and moderated outreach workflow.

## Features

- Responsive scientific dashboard, landing page and repository.
- PDF, DOCX, TXT and CSV uploads with validation, version history, extracted metadata, previews and downloads.
- Durable asynchronous processing and independent publication approval.
- Hybrid keyword/vector retrieval with citations, document scoping and conversation history.
- Offline Leaflet polar map, stations, expedition routes and timelines.
- Downloadable synthetic datasets and moderated image/video gallery.
- Eight outreach formats, audience/tone controls and publication workflow.
- Eight education topics, glossary, source-based quizzes, progress and achievements.
- Live repository charts, activity counts and explicit repository-trend interpretation.
- Researcher, content-manager and administrator roles; notifications and audit records.

## Architecture and technologies

React 18 + TypeScript + Vite + Tailwind; Radix/shadcn-style accessible primitives; React Router; TanStack Query; Zustand; Recharts; Leaflet; Framer Motion; Lucide. Python 3.13, FastAPI, Pydantic, SQLAlchemy and Alembic form the backend. Docker deployment uses PostgreSQL/pgvector and Redis. Local demo uses SQLite with WAL and a separate durable job worker. Files use local or S3-compatible storage.

Read [architecture](docs/ARCHITECTURE.md), [database](docs/DATABASE.md), [API](docs/API.md), [AI architecture](docs/AI_ARCHITECTURE.md), [security](docs/SECURITY.md) and [deployment](docs/DEPLOYMENT.md).

## AI / RAG

Upload → validation → durable job → text extraction → overlapping chunks → metadata → embeddings → permission-filtered hybrid retrieval → relevance cutoff → compressed source excerpts → answer with citations. The default Mock provider extracts source text and identifies itself as Demo Mode. It abstains when no supporting source is found. It does not impersonate a live model or provide calibrated confidence.

Set `LLM_PROVIDER=openai` or `local` for a configured live endpoint. Local servers must expose OpenAI-compatible chat completions. Set `EMBEDDING_PROVIDER=openai` or `sentence_transformers` for semantic embeddings. Install sentence-transformers separately if selected; its first run may download a model. Keep `EMBEDDING_DIMENSIONS` aligned with the chosen model and reprocess all documents after changing embeddings. PostgreSQL uses a pgvector column and HNSW index; SQLite stores vectors as JSON for portability.

## Run locally on Windows

Requirements: Python 3.12+ and Node 20.19+ (tested with Python 3.13 and Node 24).

```powershell
./scripts/start-local.ps1
```

The script installs dependencies, builds the frontend, seeds persistent demo records and starts the backend and worker in hidden windows. Open **http://localhost:8000**. If already running, use the existing instance; do not start a second copy on the same port.

Manual setup:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
cd frontend
npm ci
npm run build
cd ..
./.venv/Scripts/python.exe scripts/seed_database.py
./.venv/Scripts/python.exe scripts/seed_media.py
$env:PYTHONPATH = "$PWD/backend"
./.venv/Scripts/python.exe -m app.workers.run
# In another terminal, set PYTHONPATH again, then:
./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The bundled `frontend/public/land.geojson` supports offline maps. To regenerate it after dependency installation: `node frontend/scripts/prepare-map.mjs`.

## Environment and demo access

Copy `.env.example` to `.env` when overriding defaults. The backend reads project-local `.env` without overriding process environment variables. Leave `DATABASE_URL` empty for the portable database. A unique local JWT secret is generated in ignored `data/.secret` when no environment secret exists.

The sign-in page includes one-click **Administrator**, **Researcher**, and **Content Manager** demo accounts. Seed time generates unique passwords in ignored `data/demo-accounts.json`; there are no fixed production passwords. This account discovery route exists only when `DEMO_MODE=true`. Turn demo mode off and remove demonstration accounts before exposing a real installation.

## API documentation

- Swagger: http://localhost:8000/swagger
- ReDoc: http://localhost:8000/redoc
- OpenAPI: http://localhost:8000/openapi.json
- API prefix: `/api/v1`

Core groups: auth, documents/versions/moderation/downloads, search/suggestions, expeditions/stations/map, datasets/media, chat/conversations, AI generation, education/quizzes/progress, analytics, users, notifications, audit and health.

## Testing

```powershell
./.venv/Scripts/python.exe -m pytest tests -q
cd frontend
npm run build
npm run lint
npm test
```

Actual results and browser walkthrough evidence: [VERIFICATION.md](docs/VERIFICATION.md). The lint command performs strict TypeScript validation. It does not claim a separate ESLint ruleset.

## Docker

Set strong `POSTGRES_PASSWORD` and `JWT_SECRET` values in `.env`, then:

```sh
docker compose up --build
```

Services: frontend (nginx), backend, worker, postgres and redis. Open port 8000. The backend migrates and seeds before its health check succeeds; the worker starts afterward. Database and research files use named volumes. PostgreSQL requires the pgvector extension included in the supplied image. Docker was not available on the build host, so container execution remains unverified.

## Security

Salted scrypt hashes; signed expiring JWT access tokens; rotating hashed refresh sessions; logout/session revocation; login lockout and rate limiting; role checks; permission-filtered retrieval and downloads; MIME/size/structure validation; ORM parameter binding; browser security headers; React escaping; audit records. Tokens stay in browser memory and sign-in must be repeated after a full page reload. Production deployment requires HTTPS, managed secrets, backups and deployment-specific monitoring.

## Screenshots

Presentation screenshot slots: landing/discovery, offline polar map, cited Copilot answer, administration review queue. Use the running app for current screenshots; no static screenshot substitutes for functionality.

## Limitations and future enhancements

The running demo uses extractive mock AI, deterministic metadata parsing and small synthetic sources. Live providers are configurable but not verified without credentials. Scanned PDFs require prior OCR. The local worker is intended as one process; distributed worker leases and large-scale retrieval tuning are production follow-ups. The resource catalog uses typed JSON records for stations, expeditions, datasets, media and education; document/auth/job relationships use foreign keys. A more granular catalog schema and organization-specific permission policies can be added with migrations. The offline map is low resolution and not for navigation. See [handoff](docs/HANDOFF.md) and [requirements checklist](docs/REQUIREMENTS.md).
