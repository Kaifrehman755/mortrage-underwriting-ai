# Implementation Audit — Phase-2 Security Remediation

**Project:** `mortrage-underwriting-ai` (India property-valuation backend)
**Date:** 2026-10-17
**Scope:** India property-valuation backend. No RAG / compliance / frontend / US-mortgage work.
**Brief + per-finding status log:** `SECURITY_AUDIT_REPORT.md` (authoritative).
**Owner-facing roll-up:** `REMEDIATION_SUMMARY.md`.

This is the R21 `reports/implementation_audit.md` deliverable (F-18). It records what was implemented,
which files changed and why, the regression tests added, and the decisions taken.

---

## 1. Executive summary

Sixteen of the twenty findings are remediated and verified (F-01 through F-12, plus F-14, F-15, F-16,
F-17). F-12 (Alembic revisions) was unblocked by the owner and completed against the disposable
`mortgage_underwriting_test` database. F-13 (RAG) is an out-of-scope documented residual; F-18 is
partially closed; F-19/F-20 are informational.

Verification at the time of writing (updated 2026-10-24): **311 tests collected, 0 failed**
(`pytest backend/tests`), including **5 integration tests executed against a live
PostgreSQL/PostGIS instance**. `ruff` is clean on every remediation file **and** `migrations/`;
`mypy app` is now **clean** (0 errors); `check_sources.py --verify-fixtures` exit 0;
`check_migrations.py` **Ready: YES** exit 0; `validate_dataset.py` exit 0;
`check_database.py --connect` exit 0 against `mortgage_underwriting` (all 10 expected tables plus
PostGIS); and `alembic upgrade head` / `downgrade base` / `upgrade head` were re-verified on a
freshly reset `mortgage_underwriting_test`.

## 2. Findings disposition

| Finding | Disposition |
|---|---|
| F-01 synthetic comps in production valuation | Remediated (verified: 7 `test_f01_*` tests) |
| F-02 hard-coded market index | Remediated (versioned provenance file + abstention) |
| F-03 fixtures mislabelled as government data | Remediated (relabelled; sources `pending_review`) |
| F-04 silent row drops in circle-rate ingestion | Remediated (reason-coded quarantine + run accounting) |
| F-05 no authentication | Remediated (API-key dependency; protected-by-default) |
| F-06 CORS wildcard + credentials | Remediated (fails closed) |
| F-07 default creds / insecure secret | Remediated (no usable defaults; raise in non-dev) |
| F-08 SSRF / arbitrary file read | Remediated (host allowlist, no redirects, path confinement) |
| F-09 `.env.example` + embedding model | Remediated (settings sync test; identifier unified) |
| F-10 duplicate pipelines / ORM trees | Remediated (canonical designation + guard test) |
| F-11 duplicate dependency declarations | Remediated (single runtime manifest; static verification) |
| F-12 no Alembic revisions | Remediated (initial revision + tested upgrade/downgrade on disposable DB) |
| F-13 RAG fabricated content | Open — out of scope, documented |
| F-14 broad exceptions / leaked text | Remediated (generic reason code + correlation id) |
| F-15 unreachable `rows_rejected` | Remediated (documented reserved field) |
| F-16 fabricated fallback source URL | Remediated (`PROVENANCE_MISSING` quarantine) |
| F-17 inconsistent unit semantics | Remediated (renamed field; unit documented) |
| F-18 conflicting docs / missing deliverables | Partially closed (R21 deliverables added; doc conflicts documented) |
| F-19 no Flask frontend / no ML model | No action (informational) |
| F-20 positive controls | No action (recorded) |

## 3. Files changed and purpose

### Data provenance and market indices (F-02, F-03)
| File | Purpose |
|---|---|
| `data/market_indices/rbi_hpi_urban_lucknow.json` | Versioned HPI series with provenance + `verification_status=unverified` |
| `backend/app/property/market_index.py` | Loader + snapshot API; no fallback constant |
| `backend/app/property/valuation.py` | Engine abstains from HPI time adjustment when the series is absent/unverified/uncovered |
| `data/source_readiness.csv` | Reference-rate + market-index rows set to `pending_review` with UNVERIFIED notes |
| `data/DATA_CARD.md` | §2.1–2.4 record synthetic-dev-fixture provenance and the promotion rule |
| `data/reference_rates/*.csv` | Provenance markers point at `local://synthetic/...`, not fabricated official URLs |
| `scripts/check_sources.py` | `--verify-fixtures` provenance gate for reference-rate + market-index fixtures |

### Ingestion integrity (F-04, F-15, F-16, F-17)
| File | Purpose |
|---|---|
| `backend/app/ingestion/circle_rates.py` | `ParseOutcome`, reason-coded `QuarantineRecord`s, `IngestionRunAccounting`, `quarantine_<run_id>.jsonl` |
| `backend/app/ingestion/validate.py` | `validate_transaction_row` requires `source_url` → `PROVENANCE_MISSING`; unit normalization documented |
| `backend/app/ingestion/provider.py` | `rows_rejected` documented as a reserved field; fail-loud guard replaces the unreachable branch |
| `backend/app/database/repositories/reference_rate_repo.py` | Maps contract field `rate_inr_per_sqft` → column `rate_inr_per_sqft` (renamed under the ratified F-12 migration) |
| `backend/app/database/models/reference_rate.py` | ORM attribute/column renamed `rate_inr_normalized` → `rate_inr_per_sqft` |
| `data/processed/reference_rates/*.jsonl`, `data/schema.md` | Regenerated rows carry `rate_inr_per_sqft`; unit semantics documented |

### API and configuration security (F-05, F-06, F-07, F-08)
| File | Purpose |
|---|---|
| `backend/app/security/auth.py` | `require_api_key` + `AuthService`; constant-time compare; fails closed (503/401) |
| `backend/app/security/rate_limit.py` | Best-effort limiter applied to the public lookup |
| `backend/app/api/*.py` | Routers constructed `dependencies=[Depends(require_api_key)]` (protected by default) |
| `backend/app/core/config.py` | CORS fail-closed parser, `CORS_ALLOW_CREDENTIALS`, no usable secret/DB defaults, dev-vs-prod validation, ingestion allowlist/intake-dir, `EMBEDDINGS_MODEL` |
| `backend/app/main.py` | Reads the CORS flag; explicit method/header allowlists |
| `alembic.ini` | Blank `sqlalchemy.url` (no embedded credentials) |
| `.env.example` | Placeholders only; documents every setting |
| `docs/security/access_policy.md` | Public vs protected endpoint decision record |

### Maintainability (F-09, F-10, F-11, F-12)
| File | Purpose |
|---|---|
| `backend/requirements.txt`, `backend/requirements-dev.txt`, `backend/Dockerfile` | Single de-duplicated runtime manifest; dev manifest extends it; Dockerfile copies only what it installs |
| `docs/architecture/canonical_pipeline.md` | F-10 decision record (canonical engine + ORM tree, migration path) |
| `backend/app/models/__init__.py` | Deprecation marker (runtime `DeprecationWarning`) for the legacy ORM tree |
| `backend/app/property/__init__.py`, `backend/app/valuation/__init__.py` | Docstring records canonical vs migration-target status |
| `scripts/check_migrations.py`, `migrations/versions/.gitkeep` | F-12 readiness checker + required `versions/` directory |
| `migrations/versions/e35561efe721_initial_schema.py` | F-12 initial revision (10 tables, 40 indexes; no PostGIS-managed objects) |
| `migrations/env.py` | F-12 autogenerate `include_object` filter excluding PostGIS internals (`spatial_ref_sys`, `tiger`, `topology`); unused `import os` removed |
| `migrations/script.py.mako` | Modernised template (PEP 604 annotations, `collections.abc.Sequence`) so generated revisions are lint-clean |
| `backend/app/database/models/property.py` | `spatial_index=False` on the geometry column so Alembic is the single owner of `idx_property_record_location` (a duplicate-index failure otherwise) |

### Reliability and deliverables (F-14, F-18)
| File | Purpose |
|---|---|
| `backend/app/agents/property_agent.py` | Generic `unexpected_agent_error` reason code; correlation id; raw exception text logged only, never returned |
| `backend/app/property/comps.py` | Narrowed catch (`ValueError`/`TypeError`) with a logged, observable recency fallback |
| `backend/app/property/normalize.py` | Narrowed catch for unparseable sale dates (still reason-coded) |
| `scripts/check_database.py` | PostGIS config check (static) + `--connect` read-only probe |
| `scripts/validate_dataset.py` | Validates processed rows, manifests and quarantine records on disk |
| `scripts/build_dataset.py` | Gated dataset builder; dry-run by default; fails closed on unapproved sources |
| `scripts/run_verification.py` | Runs the approved checks; writes `reports/verification_report.md` |
| `docs/PROGRESS.md`, `reports/implementation_audit.md`, `reports/verification_report.md` | R21 reports |

## 4. Regression tests added

| Suite | Tests | Finding |
|---|---|---|
| `backend/tests/unit/test_f02_market_index.py` | 11 | F-02 |
| `backend/tests/unit/test_f03_data_provenance.py` | 6 | F-03 |
| `backend/tests/unit/test_f04_circle_rate_quarantine.py` | 8 | F-04 |
| `backend/tests/unit/test_f05_auth_access_policy.py` | 15 | F-05 |
| `backend/tests/unit/test_f06_cors_config.py` | 7 | F-06 |
| `backend/tests/unit/test_f07_secrets_config.py` | 10 | F-07 |
| `backend/tests/unit/test_f08_ingestion_ssrf.py` | 20 | F-08 |
| `backend/tests/unit/test_f09_settings_env_sync.py` | 5 | F-09 |
| `backend/tests/unit/test_f10_canonical_pipeline.py` | 7 | F-10 |
| `backend/tests/unit/test_f11_dependency_manifest.py` | 6 | F-11 |
| `backend/tests/unit/test_f12_migration_checker.py` | 7 | F-12 |
| `backend/tests/unit/test_f14_error_handling.py` | 8 | F-14 |
| `backend/tests/unit/test_f17_unit_semantics.py` | 7 | F-17 |
| `backend/tests/unit/test_f18_deliverables.py` | 21 | F-18 |
| `backend/tests/unit/test_property_agent.py` (`test_f01_*`) | 7 of 28 | F-01 |

Total new/verified-by-suite regression tests: **138** (plus the 7 `test_f01_*` cases within the
pre-existing agent suite). Full suite: **235 collected, 0 failed**.

## 5. Decisions taken

1. **F-10 canonical designation** — `app/property` + `app/database/models` are canonical; `app/valuation`
   is the retained migration target; `app/models` is deprecated. No files deleted.
2. **F-09 embedding model** — `EMBEDDINGS_MODEL` deliberately set to `BAAI/bge-small-en-v1.5` to match
   the playbook and `rag/embeddings.py` (both 384-dim; no dimension break). Documented, not silent.
3. **F-03/F-12 fail-closed gates** — unverified fixtures stay `pending_review`, so the gated builder
   refuses them. F-12 is now complete (the checker reports `Ready: YES`), and the revision was tested
   only against the disposable database. No gate was bypassed.
4. **F-11 verification** — static manifest tests only; no Docker build (owner decision).
5. **F-17 field naming** — the contract, ORM attribute and physical column are all `rate_inr_per_sqft`;
   the rename was ratified into `GEMINI.md` §4.5 / `data/schema.md` and applied by the F-12 initial
   revision (the live `mortgage_underwriting` database was not migrated).

## 6. Remaining risk and next actions

* **F-13** (RAG fabricated content) remains an out-of-scope residual; RAG must not be cited as
  regulatory evidence.
* **Real data**: the reference-rate and market-index datasets remain labelled synthetic dev fixtures.
  They must be replaced by authorised exports (with recorded terms snapshot hashes and a named verifier)
  before any real-world use.
* **Live database**: connectivity, PostGIS and the initial revision are now verified against the local
  Docker instance (`mortgage_underwriting` and a reset `mortgage_underwriting_test`). No production
  environment has been migrated.
* **Pre-existing lint debt**: 65 `ruff` findings remain across `backend/app`, `scripts` and
  `migrations` outside the pinned remediation file list (mostly unused imports and import ordering).
  They do not affect the verification gate but are worth a dedicated cleanup pass.
* **`mypy`**: the 5 errors recorded earlier (including the `determine_qualifying_fico` placeholder)
  have been fixed; `mypy app` is clean. The FICO mid-score rule is now implemented and unit-tested.
