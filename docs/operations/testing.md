# Testing Gates

This protocol is normative in `GEMINI.md` Section 11. Every change must pass three gates before it is
reported as complete:

1. **Unit** — fast, isolated tests with no live services required.
2. **Integration** — tests against the live PostGIS + pgvector database and object store.
3. **TED (test with development)** — the application running against the local development stack.

A run that skips the integration tests because Postgres is unavailable does **not** satisfy gate 2.
Capture the actual command output; do not infer a pass from a previous run.

Current local baseline (2026-10-25): **370** unit/evaluation tests, **8** integration tests, **378**
total.

## 1. Unit

```bash
./.venv/Scripts/python.exe -m pytest backend/tests/unit backend/tests/evaluation \
  --disable-warnings -o addopts="" -q
```

`-o addopts=""` removes the repository's default `-q` so pytest prints the final count. The gate
requires `0 failed`, `0 errors`, and no crash at interpreter shutdown.

## 2. Integration

Start the database, then run the integration tests:

```bash
docker compose up -d postgres
./.venv/Scripts/python.exe -m pytest backend/tests/integration \
  --disable-warnings -o addopts="" -q
```

A release-gate run must report the integration tests as **passed**, not `skipped`. The tests exercise
PostGIS geometry persistence, pgvector retrieval, SQL approval/index/date filters, idempotent
ingestion, bronze deduplication, and source freshness.

## 3. TED (test with development)

TED is a manual smoke test of the same code against the running development stack. Use local-only
credentials; never put them in the repository.

### 3.1 Start services and migrate

```bash
MINIO_ACCESS_KEY=<local-user> MINIO_SECRET_KEY=<local-secret> \
  docker compose up -d postgres redis minio
./.venv/Scripts/python.exe -m alembic upgrade head
./.venv/Scripts/python.exe scripts/check_migrations.py
./.venv/Scripts/python.exe scripts/check_database.py --connect
```

Expected: one Alembic head, all expected tables present, and live PostGIS/pgvector extensions.

### 3.2 Start the API

```bash
APP_ENV=development \
API_KEY=<local-test-key> \
RAW_DOCUMENT_STORE=minio \
MINIO_ENDPOINT=localhost:9000 \
MINIO_ACCESS_KEY=<local-user> \
MINIO_SECRET_KEY=<local-secret> \
MINIO_BUCKET=mortgage-ted-raw \
./.venv/Scripts/python.exe -m uvicorn app.main:app \
  --app-dir backend --host 127.0.0.1 --port 8010
```

### 3.3 Smoke checks

With the server running, verify:

| Check | Expected |
|---|---|
| `GET /api/v1/health` | `200`, `database: connected` |
| `POST /api/v1/compliance/check` without a key | `401` |
| `POST /api/v1/compliance/check` with the key | `200`; incomplete evidence returns `cannot_verify` and `human_review_required: true` |
| Same request with a raw PAN/Aadhaar/account field | `422`; no raw identifier is accepted or stored |
| MinIO put/read round-trip | bytes match and the SHA-256 key verifies |
| Command handler `/compliance` then `/approve` | approval is blocked while findings remain unresolved; loan-officer approval is denied |

TED is not a substitute for regression tests. If TED exposes a defect, add or update a unit and/or
integration test that would have caught it, then rerun all three gates.
