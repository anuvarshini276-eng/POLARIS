# Durable processing worker

The shared worker implementation is `backend/app/workers/run.py`. Keeping models and processing services in the backend package avoids divergent copies between the API and worker.

Run from the repository root with `PYTHONPATH=backend`:

```sh
python -m app.workers.run
```

Dockerfile.worker runs the same entry point. Use one worker instance with the included startup-recovery policy. Processing jobs persist in the database and are claimed atomically. The worker records a heartbeat used by `/api/v1/health/worker`. Failed jobs keep their error and can be retried from the document detail page.
