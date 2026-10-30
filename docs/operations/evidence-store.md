# Evidence Store Operations

This runbook covers the Postgres/pgvector evidence store and the raw-document
object store. It does **not** approve any source. Every regulatory document stays
unapproved until an owner records the approval metadata required by the playbook.

## 1. Apply the schema

```bash
./.venv/Scripts/python.exe -m alembic upgrade head
```

The follow-on revision `a7c9e2f4b6d8`:

- creates `jurisdiction`, `reg_document`, `reg_chunk`, `compliance_finding`,
  `market_indicator`, and `raw_record`;
- enables the `vector` extension and creates HNSW/GIN indexes;
- adds source approval/freshness columns and the
  `ck_data_source_approved_needs_record` constraint;
- downgrades any pre-existing `approved` source that has no complete approval
  record to `pending_review` before adding that constraint.

Verify:

```bash
./.venv/Scripts/python.exe -m alembic current
./.venv/Scripts/python.exe scripts/check_migrations.py
./.venv/Scripts/python.exe scripts/check_database.py --connect
```

## 2. Start PostGIS + pgvector, Redis, and object storage

Install the real embedding runtime where evidence is ingested or queried:

```bash
./.venv/Scripts/python.exe -m pip install -r backend/requirements-rag.txt
```

Without it, development/test code uses a deterministic lexical projection. In
`APP_ENV=production`, `EmbeddingService` raises `EmbeddingModelUnavailable`
instead of silently using that fallback.

```bash
docker compose up -d postgres redis minio
```

`docker-compose.yml` builds `docker/postgres/Dockerfile` from
`pgvector/pgvector:pg16` and installs PostGIS. The object store is S3-compatible.
The upstream `minio/minio` images were removed in September 2026, so Compose uses
the maintained Chainguard MinIO build.

Set these values in `.env` before starting:

```dotenv
MINIO_ACCESS_KEY=<local-owner-credential>
MINIO_SECRET_KEY=<local-owner-secret>
MINIO_BUCKET=mortgage-raw-documents
RAW_DOCUMENT_STORE=minio
```

`MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` are required by Compose; empty values
make startup fail closed instead of using a shared default credential.

### Local Windows caveat

The Chainguard image normally runs as UID `65532`. Docker Desktop named volumes
on Windows do not reliably preserve that ownership, so Compose defaults
`MINIO_UID`/`MINIO_GID` to `0` for local development. For a production or shared
environment, provision the volume explicitly and run non-root:

```bash
# Example named volume; adjust the volume name to your Compose project.
docker run --rm -v mortgage-underwriting-ai_minio_data:/data \
  busybox:1.37 chown -R 65532:65532 /data
MINIO_UID=65532 MINIO_GID=65532 docker compose up -d minio
```

## 3. Mirror jurisdiction packs

State-scoped regulatory documents and findings carry a foreign key to
`jurisdiction`. Mirror the reviewed Python packs before inserting them:

```python
from app.database.repositories.jurisdiction_repo import JurisdictionRepository

repository = JurisdictionRepository(session)
await repository.upsert_all()
```

The repository stores the pack payload and `config_version`; it does not promote
a state from `planned` to `live`.

## 4. Store raw evidence

`MinioRawDocumentStore` computes the SHA-256 from the bytes before writing and
uses the hash as the object key:

```python
from app.rag.raw_store import build_raw_document_store

store = build_raw_document_store()
stored = store.put_document(raw_bytes, content_type="application/pdf")
assert store.get_document(stored.key) == raw_bytes
```

For offline tests, set `RAW_DOCUMENT_STORE=local`; the local store verifies the
hash on read and rejects tampered bytes.

## 5. Persist approved evidence

`PostgresVectorStore.ingest_document()` refuses to persist chunks for a document
whose `approved` flag is false. Approval metadata is never inferred:

```python
from app.rag.postgres_store import PostgresVectorStore

store = PostgresVectorStore(session)
await store.ingest_document(approved_document, approved_chunks)
```

Retrieval filters approval, scope/state, effective dates, and (optionally) the
active `index_version` in SQL. An empty result is a valid outcome and must produce
`cannot_verify`, not a flag.

## 6. Active index switching

`RAG_ACTIVE_INDEX_VERSION` is blank by default. Do not set it until the owner has:

1. approved the source and recorded real hashes, terms snapshots, and review dates;
2. loaded the approved chunks under the new `index_version`;
3. run the gold-set retrieval gate against that exact version.

A blank active version means callers must not claim a trusted production index.

## 7. Source freshness

`SourceFreshnessRepository` centralizes the auditable per-source timestamps used by `DATA-001` and
operational alerts:

```python
from app.database.repositories.source_repo import SourceFreshnessRepository

repository = SourceFreshnessRepository(session)
await repository.record_attempt(source_id)
await repository.record_success(source_id)  # clears last_error
await repository.record_failure(source_id, error_summary)  # stored errors are capped at 500 chars
stale = await repository.list_stale(default_interval_days=90)
summary = await repository.freshness_summary(source_id)
```

Only sources with `approval_status="approved"` are returned by `list_stale`. A source with no recorded
success is stale. Recording a successful sync is not an approval action.

## 8. Known limits

- The repository contains no owner-approved real regulatory source.
- Thresholds in `backend/app/compliance/rules.v1.json` remain `verified: false`,
  so KFS/LTV/VAL/DATA rules abstain by design.
- Bronze `raw_record` persistence and fingerprints are implemented, but no live
  government collector is configured.
- The canonical property/valuation tables keep their existing names; the
  playbook's field-level renames are a documented deviation.
