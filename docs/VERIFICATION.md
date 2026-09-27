# Verification evidence

## Executed checks

- Backend: `python -m pytest tests -q` — **11 passed**. Tests include full upload/process/moderation/search/RAG flow; JWT login/logout; private access and cross-user conversation isolation; invalid file/MIME rejection; DOCX/CSV/PDF extraction; overlapping chunks; media draft/public/archive protection; generated quizzes and scores; role restrictions and audit access.
- Frontend: `npm run build` — passed; `npm run lint` (TypeScript static validation) — passed; `npm test` — **3 passed**. Component tests verify actual source routes, unpublished status, accessible API failures and disabled submission controls.
- Browser, live local backend: administrator demo sign-in; search sea ice; open source and extracted metadata; document-scoped Copilot; visible citations; generate a public-awareness article; navigate education; answer the three-question quiz and receive 3/3 plus Polar Explorer; upload a new synthetic zirconium document using the file chooser; observe UPLOADED → COMPLETED; review → approve → publish; search the newly published document; ask Copilot about its tracer readings and receive source-linked evidence.
- Map: select Bharati and inspect station coordinates, research activities and linked documents. External OSM tiles were blocked; replaced with bundled Natural Earth geography. Browser confirms offline geometry, station markers and expedition routes render.
- Health: running database and worker return `ok`. Local service is served at http://localhost:8000.

## Non-failing warnings

The installed FastAPI test client emits an upstream Starlette/httpx deprecation warning. React Router emits future-version opt-in warnings in component tests. Neither failed a test. Build output includes the chart/map/motion libraries in a single application bundle; route splitting is a future performance improvement.

## Not exercised on this host

Docker is not installed, so the five-service Compose deployment and PostgreSQL/pgvector/Redis integration were not executed. The tested local deployment uses SQLite and the durable standalone worker. Live OpenAI/local-model, sentence-transformer download and S3 adapters require services/credentials and were not exercised. No external model-quality claim is made. OCR is not included; scanned PDFs fail with an explicit actionable message.

- Additional executed tests: PDF text extraction with a page-1 citation; administrator-only settings and registration pause. Alembic migration completed successfully on the local database. Mobile layout checked at 390 × 844 with page width 389 px (no horizontal overflow).


- Final live smoke test: scripts/smoke_local.py passed against the restarted service, covering page/API availability, database/worker health, privileged routes, media, settings, source-grounded zirconium retrieval, unsupported-query abstention and logout revocation. Final browser check confirmed the mobile drawer closes after navigation. The server and worker were left running.

