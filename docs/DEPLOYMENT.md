# Deployment

Portable local mode: install backend requirements, build frontend, seed data, start durable worker and FastAPI serving the built SPA at localhost:8000. SQLite/files remain in data. Docker Compose starts PostgreSQL with pgvector, Redis, backend, worker and frontend. Run Alembic before serving. Environment selects database, storage, AI and embedding providers. Local demo credentials are generated at seed time into ignored data/demo-accounts.json and exposed only in explicit local DEMO_MODE. No official data or production credentials are bundled.

Checks: API authentication/permissions, extraction/upload/queue, citations, moderation, refresh revocation, quiz scoring, frontend build/component tests and browser end-to-end flow. Deployment limitations and actual evidence are recorded in HANDOFF.md.
