# Progress — India Property-Valuation Backend

**Scope:** India property-valuation backend, extended with deterministic compliance and RAG
governance. RAG/compliance are now partially in scope (see the status update below); frontend and
US-mortgage work remain out of scope.
**Governing instructions (not edited):** `GEMINI.md` (the duplicate `CLAUDE.md` was removed in the
ratification commit), `backend/app/property/playbook.md`, `data/regulatory_docs/.clinerules/*`.
**Authoritative brief + per-finding status log:** `SECURITY_AUDIT_REPORT.md`.
**Roll-up report:** `REMEDIATION_SUMMARY.md`.

This file is the R21 `docs/PROGRESS.md` deliverable (F-18). It records where the remediation stands,
the required scripts/reports, and the documented deviations.

### Compliance/RAG completion update (2026-10-25)

Implemented:

- `backend/app/compliance/` now has a deterministic engine, evidence contract, versioned rule config,
  and eight India starter rules (`KFS-001`, `LTV-001`, `RERA-001`, `TITLE-001`, `VAL-001`, `KYC-001`,
  `FAIR-001`, `DATA-001`). Findings without evidence are downgraded to `cannot_verify`.
- `ComplianceAgent` runs the engine, attaches evidence, and emits an audit event.
- `/compliance`, `/evidence`, `/missing`, `/review`, `/approve`, `/sources` commands were added with
  role checks. `/market` now abstains instead of returning hard-coded figures.
- RAG documents default to `approved=false`; retrieval excludes unapproved documents unless a test
  explicitly opts in. Synthetic seed text is marked `synthetic_test_fixture`.
- Postgres/pgvector evidence persistence is implemented in `backend/app/rag/postgres_store.py`, with
  idempotent ingestion by document SHA-256, approval/state/effective-date/index-version SQL filters,
  and hybrid vector + full-text fusion. A raw-document store (`backend/app/rag/raw_store.py`) uses
  MinIO/S3 in production and a local filesystem store for offline tests.
- Migration `a7c9e2f4b6d8` adds `compliance_finding`, `reg_document`, `reg_chunk`, `market_indicator`,
  `raw_record`, `jurisdiction`, source approval/freshness columns, the vector extension, HNSW/GIN
  indexes, and the evidence-required database constraint. It was applied to the local
  `mortgage_underwriting` database and the full **378-test** suite (including live PostGIS/pgvector
  integration tests) passes.
- Bronze ingestion (`backend/app/ingestion/bronze.py`) provides a deterministic, PII-free
  `record_fingerprint` and `(source_id, record_type, record_fingerprint)` deduplication.
- `SourceFreshnessRepository` records per-source attempts, successes, bounded failures, and stale
  approved sources. Staleness is queryable for `DATA-001` and operational alerts; approval remains a
  separate owner action.
- The real embedding runtime is declared in `backend/requirements-rag.txt`; production construction
  fails closed when it is absent instead of using the deterministic test projection.
- Docker Compose now provisions a PostGIS + pgvector Postgres image, Redis, and an S3-compatible
  object store. The upstream `minio/minio` images were removed in September 2026; compose uses the
  maintained Chainguard MinIO build and documents the local root-user/volume caveat.

Still OPEN:

- Owner-approved real regulatory sources with real hashes, terms snapshots and review dates.
- Numeric thresholds in `rules.v1.json` remain `verified: false`; those rules abstain by design.
- Ingestion of real source PDFs/XML and an owner-approved active `index_version` after a gold-set gate.
- Canonical property/valuation table names still differ from the playbook's field-level names; this
  is a documented deviation rather than a completed migration.

---

## 1. Finding status

| Finding | Severity | Status |
|---|---|---|
| F-01 synthetic comps reach production valuation | CRITICAL | REMEDIATED |
| F-02 unprovenanced hard-coded market index | HIGH | REMEDIATED |
| F-03 reference-rate fixtures labelled as government data | HIGH | REMEDIATED (relabelled as unverified dev fixtures; sources `pending_review`) |
| F-04 circle-rate ingestion silently drops rows | HIGH | REMEDIATED |
| F-05 no authentication on any endpoint | HIGH | REMEDIATED |
| F-06 CORS wildcard fallback + credentials | MEDIUM | REMEDIATED |
| F-07 default DB creds / insecure default secret | MEDIUM | REMEDIATED |
| F-08 SSRF / arbitrary local file read | MEDIUM | REMEDIATED |
| F-09 `.env.example` out of sync + embedding-model mismatch | MEDIUM | REMEDIATED |
| F-10 two parallel valuation pipelines / ORM trees | MEDIUM | REMEDIATED (canonical designation) |
| F-11 duplicated dependency declarations | MEDIUM | REMEDIATED (static verification) |
| F-12 no Alembic revision files | MEDIUM | REMEDIATED (initial revision + tested upgrade/downgrade on a disposable DB) |
| F-13 RAG out-of-scope with fabricated content | MEDIUM | PARTIALLY REMEDIATED — synthetic corpus is marked unapproved and excluded from default retrieval; approved real-source ingestion remains OPEN |
| F-14 broad exception handling / leaked error text | LOW | REMEDIATED |
| F-15 `rows_rejected` accounting unreachable | LOW | REMEDIATED |
| F-16 fabricated fallback source URL | LOW | REMEDIATED |
| F-17 reference-rate unit semantics inconsistent | LOW | REMEDIATED |
| F-18 instruction/artifact conflicts; missing deliverables | INFO | IN PROGRESS (this file + R21 scripts; conflicts documented below) |
| F-19 no Flask frontend / no ML model | INFO | NO ACTION (informational, out of scope) |
| F-20 positive controls observed | INFO | NO ACTION (recorded) |

---

## 2. Required scripts and reports (R21)

| Deliverable | Status | Purpose |
|---|---|---|
| `scripts/check_sources.py` | present | Source-readiness checks; `--verify-fixtures` verifies reference-rate + market-index provenance |
| `scripts/check_migrations.py` | present | Static Alembic readiness (config, canonical ORM target, revisions/heads); reports **Ready: YES** now that the initial revision exists |
| `scripts/check_database.py` | present | PostGIS config check (static by default) and `--connect` read-only probe (now part of `run_verification.py`) |
| `scripts/validate_dataset.py` | present | Validates on-disk processed rows, manifests and quarantine records |
| `scripts/build_dataset.py` | present | Gated dataset builder (dry-run by default; fails closed on unapproved sources) |
| `scripts/run_verification.py` | present | Runs the approved local checks; can write `reports/verification_report.md` |
| `reports/implementation_audit.md` | present | What changed and why |
| `reports/verification_report.md` | present | Generated from real command output |
| `docs/PROGRESS.md` | present | This file |

Reproduce:

```bash
./.venv/Scripts/python.exe scripts/run_verification.py            # all approved checks
./.venv/Scripts/python.exe scripts/validate_dataset.py            # dataset only
./.venv/Scripts/python.exe scripts/check_migrations.py            # F-12 readiness
./.venv/Scripts/python.exe scripts/check_database.py              # DB config (no connection)
./.venv/Scripts/python.exe scripts/check_database.py --connect    # live read-only probe
./.venv/Scripts/python.exe scripts/build_dataset.py              # dry-run; fails closed (F-03)
```

Testing requires all three gates for every change: unit, live integration, and **TED** (test with the
development stack). See `docs/operations/testing.md` for the commands and the current development-stack
smoke checks.

---

## 3. Documented blockers and gate consequences

* **F-12 (Alembic) — RESOLVED.** The initial revision
  `migrations/versions/e35561efe721_initial_schema.py` and the follow-on
  `migrations/versions/a7c9e2f4b6d8_playbook_evidence_and_bronze.py` now exist. The initial revision
  was generated and exercised against the disposable database `mortgage_underwriting_test` on the
  local PostGIS container. On **2026-10-24** the cycle was repeated on a freshly reset test database
  and the revision was then applied to the local development database `mortgage_underwriting`. On
  **2026-10-25** the follow-on revision added the evidence/bronze tables and was applied to
  `mortgage_underwriting`; the live integration suite confirms PostGIS and pgvector. No production
  environment has been migrated.

  | Step | Result |
  |---|---|
  | `CREATE DATABASE mortgage_underwriting_test TEMPLATE template_postgis` | exit 0 |
  | `alembic revision --autogenerate -m "initial schema"` | exit 0 → initial revision (10 tables) |
  | `alembic upgrade head` | exit 0 → 10 tables + `alembic_version`; `rate_inr_per_sqft` present |
  | `alembic downgrade base` | exit 0 → only `alembic_version` left (0 rows); PostGIS intact |
  | `alembic upgrade head` (repeat) | exit 0 → repeatable in both directions |
  | `scripts/check_migrations.py` | **Ready: YES** (2 revisions, 1 head) |

  Two hazards were fixed to make this work: the autogenerate `include_object` filter that keeps
  Alembic away from PostGIS internals (`spatial_ref_sys`, `tiger`, `topology` — otherwise the first
  draft dropped 47 system tables), and the duplicate spatial index on `property_records.location`
  (GeoAlchemy2 auto-created one *and* the generated `create_index` created another).
* **F-03 (source approval gate).** The four reference-rate fixture sources are `pending_review`, so the
  canonical, gated ingestion refuses them. Consequently `scripts/build_dataset.py` currently reports all
  four states as `BLOCKED` and exits `2`. That is the intended, fail-closed behaviour — the existing
  `data/processed/**` files remain labelled synthetic dev fixtures and are **not** rebuilt.
* **Not authorised / not run:** dependency vulnerability scan, Docker image build, live fetch of
  government sources (RBI DBIE HPI values were not fetched; the market-index series stays an unverified
  fixture). The Alembic migration was authorised and run against `mortgage_underwriting_test` and the
  local development database `mortgage_underwriting`; no production database was touched.

---

## 4. Deviations and conflicts (F-18)

| Item | Resolution |
|---|---|
| `.clinerules/*` located under `data/regulatory_docs/` rather than the repo root | **Not moved.** The governing instructions reference this path; relocating it would contradict the instructions. Recorded here instead. |
| `README.md` and `docs/*` describe a US full-stack system | **Not rewritten** (out of India scope and it is unrelated user content). The India scope is stated at the top of this file and in `SECURITY_AUDIT_REPORT.md`. |
| `AGENTS.md` and `.clineignore` absent | Recorded as absent. No file invented; the governing instructions are `CLAUDE.md`/`GEMINI.md`. |
| `docs/playbook/` absent | Recorded. The playbook lives at `backend/app/property/playbook.md`. |
| `frontend/`, `rag/`, compliance stubs exist although "not this phase" | Left untouched (R22). F-13 (RAG fabricated content) stays an out-of-scope documented residual. |
| `scripts/import_dataset.py` writes unconditionally | Superseded in practice by the safer, gated `scripts/build_dataset.py` (dry-run by default). `import_dataset.py` is retained to avoid deleting user work. |

---

## 5. Remaining open decisions

1. ~~Ratify `docs/security/access_policy.md` as the F-05 access-policy location~~ — **ratified**; the
   README now points to it.
2. ~~Ratify the `rate_inr_normalized` → `rate_inr_per_sqft` rename in the governing docs~~ —
   **ratified**; `GEMINI.md` §4.5 and `data/schema.md` now name `rate_inr_per_sqft`, and the physical
   column was renamed by the F-12 initial revision.
