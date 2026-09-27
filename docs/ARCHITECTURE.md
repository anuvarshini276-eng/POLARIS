# POLARIS architecture

React/TypeScript/Vite client → versioned FastAPI services → SQLAlchemy repositories → PostgreSQL in Docker, SQLite for the portable local demo. A durable database job queue is consumed by a separate worker. Files use a storage provider; text chunks and embeddings are persisted. Authentication uses short-lived JWTs and rotating opaque refresh sessions. Public access includes only published public material; owners and moderators can inspect unpublished submissions. Processing never publishes a resource.

Modules: discovery, documents/versioning, processing, search/RAG, expeditions, stations/map, datasets, media, outreach, education, analytics, notifications, moderation, users and audit. Visual direction: deep navy scientific navigation, glacier-blue working surfaces, restrained cyan accents, compact editorial research cards and map-led exploration.

Local portability is intentional: no Docker executable is present on this host. PostgreSQL/pgvector and Redis are configured for container deployment. Demo embeddings are deterministic hashed vectors and demo answers are extractive, explicitly labeled. Live providers remain configurable. API calls use same-origin bearer authorization; client tokens are kept in memory.
