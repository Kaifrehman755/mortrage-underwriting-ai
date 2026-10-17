# Phase-2 Remediation — Summary Report

**Project:** `mortrage-underwriting-ai` (India property-valuation backend)
**Report date:** 2026-10-17
**Authoritative brief + append-only status log:** `SECURITY_AUDIT_REPORT.md`
**Baseline audit:** findings F-01…F-20, audit date 2026-10-17
**Scope:** India property-valuation backend only. No RAG / compliance / frontend / US-mortgage work.
**Governing instructions (not edited):** `CLAUDE.md` / `GEMINI.md`, `backend/app/property/playbook.md`, `data/regulatory_docs/.clinerules/*`

> This is a **summary/roll-up** document. It does not replace `SECURITY_AUDIT_REPORT.md`
> (the brief and per-finding status log) or `docs/security/access_policy.md` (the endpoint
> access-policy decision record). Where the two disagree, the audit report is authoritative.

---

## 1. Executive summary

| Metric | Value |
|---|---|
| Findings remediated and verified | **15** (F-01, F-02, F-03, F-04, F-05, F-06, F-07, F-08, F-09, F-10, F-11, F-14, F-15, F-16, F-17) |
| Findings blocked (documented, not guessed at) | **1** (F-12 — needs an authorised disposable PostGIS DB) |
| Findings partially advanced | **1** (F-18 — R21 deliverables added; doc conflicts documented) |
| Findings still fully open | **1** (F-13 — RAG, out of scope); F-19/F-20 are informational |
| Priorities completed | **Priority 1–5 (except F-12) and the in-scope Priority 6 items** |
| Priorities not started | — |
| Full test suite | **231 collected, 0 failed** (exit 0) |
| New regression tests written this effort | **113** across the F-01…F-18 suites |
| Lint (touched files) | **0 findings** |
| Type check | 9 errors in 7 files (down from 17), **none** in touched files |
| VCS state | **No commits made** — all changes remain uncommitted/untracked on `main` |

### What was achieved
The critical, high- and medium-severity **data-integrity** and **API/config security** findings were
closed, plus the **maintainability** and **reliability** sets: synthetic-comparable exclusion (F-01),
provenance and market-index handling (F-02, F-03), ingestion row integrity (F-04, F-15, F-16, F-17),
the whole API/config trust boundary (F-05 authentication, F-06 CORS, F-07 secrets, F-08 SSRF),
**F-09** (env/embedding-model sync), **F-10** (canonical pipeline/ORM designation), **F-11**
(dependency-manifest de-duplication) and **F-14** (no failure hiding, no raw-exception disclosure).
**F-18** is partially closed: the R21 scripts/reports now exist and the doc conflicts are documented.

### What remains
F-12 (Alembic migrations) is **blocked on an authorised disposable PostGIS database** and is documented
rather than guessed at; **F-13** (RAG fabricated content) is explicitly out of scope and left untouched;
F-19/F-20 are informational.

---

## 2. Findings tracker (F-01 … F-20)

| ID | Severity (audit) | Area | Status | Verification basis |
|---|---|---|---|---|
| F-01 | CRITICAL | Synthetic comps reach production valuation | **REMEDIATED** | 7 regression tests in `test_property_agent.py` (`test_f01_*`, passing) |
| F-02 | HIGH | Hard-coded, unprovenanced market index | **REMEDIATED** | `test_f02_market_index.py` (11) |
| F-03 | HIGH | Reference-rate fixtures labelled as government data | **REMEDIATED** | `test_f03_data_provenance.py` (6) + `check_sources.py --verify-fixtures` |
| F-04 | HIGH | Circle-rate ingestion silently drops invalid rows | **REMEDIATED** | `test_f04_circle_rate_quarantine.py` (8) |
| F-05 | HIGH | No authentication/authorization on any endpoint | **REMEDIATED** | `test_f05_auth_access_policy.py` (15) |
| F-06 | MEDIUM | CORS wildcard fallback + credentials | **REMEDIATED** | `test_f06_cors_config.py` (7) |
| F-07 | MEDIUM | Hard-coded default DB creds / insecure default secret | **REMEDIATED** | `test_f07_secrets_config.py` (10) |
| F-08 | MEDIUM | SSRF / arbitrary local file read in ingestor | **REMEDIATED** | `test_f08_ingestion_ssrf.py` (20) |
| F-09 | MEDIUM | `.env.example` out of sync + embedding-model mismatch | **REMEDIATED** | `test_f09_settings_env_sync.py` (5) |
| F-10 | MEDIUM | Two parallel valuation pipelines / two ORM trees | **REMEDIATED** | `test_f10_canonical_pipeline.py` (7) + `docs/architecture/canonical_pipeline.md` |
| F-11 | MEDIUM | Duplicated deps; deleted `backend/requirements.txt` referenced | **REMEDIATED** (static) | `test_f11_dependency_manifest.py` (6) |
| F-12 | MEDIUM | No Alembic revision files | **BLOCKED — documented** (needs authorised DB) | `scripts/check_migrations.py` + `test_f12_migration_checker.py` (3) |
| F-13 | MEDIUM | RAG layer out-of-scope with fabricated content | **OPEN** — out of scope (documented) | Priority 6 |
| F-14 | LOW | Broad exception handling hides failures / leaks text | **REMEDIATED** | `test_f14_error_handling.py` (8) |
| F-15 | LOW | `rows_rejected` accounting unreachable | **REMEDIATED** | `test_ingestion_pipeline.py` (9 total) |
| F-16 | LOW | Transaction validator fabricates fallback source URL | **REMEDIATED** | `test_ingestion_pipeline.py` |
| F-17 | LOW | Reference-rate unit semantics inconsistent | **REMEDIATED** | `test_f17_unit_semantics.py` (7) |
| F-18 | INFO | Instruction/artifact conflicts; missing deliverables | **PARTIAL** — R21 scripts/reports added; conflicts documented | `test_f18_deliverables.py` (21) + `docs/PROGRESS.md` |
| F-19 | INFO | No Flask frontend / no ML model integration | **OPEN** (informational, out of scope) | — |
| F-20 | INFO | Positive controls observed | **NO ACTION** (recorded) | — |

---

## 3. Tasks executed, by priority

### Priority 1 — F-01 (synthetic valuation data leakage) — COMPLETE ✅
> Recorded as **REMEDIATED** in the authoritative status log
> (`SECURITY_AUDIT_REPORT.md` § *F-01 … REMEDIATED*). Controls verified by 7 dedicated `test_f01_*`
> tests (28/28 in `test_property_agent.py`): `ComparableSalesAnalyzer`/`PropertyValuationEngine`/
> `PropertyAgent` exclude `is_synthetic=True` comps unless `allow_synthetic=True` (test-only), the agent
> requires an explicitly injected provider (default construction raises), and `evidence_is_synthetic`
> propagates the discriminator into the output. See §4.

### Priority 2 — Data provenance and market indices (COMPLETE ✅)

**F-03 — reference-rate provenance (HIGH)**
- Relabelled the reference-rate fixtures as **synthetic development fixtures** (not government snapshots).
- Flipped `data/source_readiness.csv` rows to `pending_review`; set `reference_rate_approved=False`.
- Corrected `data/DATA_CARD.md` (§2.1–2.3).
- Added provenance tooling: `scripts/check_sources.py --verify-fixtures` and `--verify-connectivity`.
- Refreshed 4 SHA-256 hashes.
- Tests: `backend/tests/unit/test_f03_data_provenance.py` (6).

**F-02 — unprovenanced hard-coded market index (HIGH)**
- Moved the HPI series into a **versioned JSON data file with provenance + `verification_status`**
  (`data/market_indices/rbi_hpi_urban_lucknow.json`).
- New loader `backend/app/property/market_index.py`; the engine now **abstains** when the index is
  absent / unverified / uncovered — no invented replacement values and no silent `100.0` fallback.
- Unverified synthetic fixtures are usable only with an explicit `allow_synthetic=True`.
- `data/DATA_CARD.md` §2.4 records the provenance status and the promotion rule.
- Register `market_index` row left `pending_review`.
- Tests: `backend/tests/unit/test_f02_market_index.py` (11).

> **Provenance honesty note:** RBI DBIE HPI values were **not** fetched. The series is a labelled
> *unverified fixture* and its register row stays `pending_review` — no fabricated official values.

### Priority 3 — Ingestion integrity (COMPLETE ✅)

**F-04 — circle-rate ingestion silently drops invalid rows (HIGH)**
- Parse methods now return a `ParseOutcome` (accepted rows + **reason-coded rejections**).
- Added reason codes: `MISSING_REQUIRED_FIELD`, `MISSING_PRICE`, `INVALID_DATE`; schema failures are
  returned as rejections rather than swallowed.
- `ingest_html` / `ingest_file` emit `QuarantineRecord`s + an `IngestionRunAccounting`, and write
  `quarantine_<run_id>.jsonl`. `run()` returns an accounted result.
- Removed the `logger.warning("Skipping invalid circle rate row")` silent-drop path.
- Decision taken: **keep** the legacy `CircleRateIngestor` (do not delete) and make it
  quarantine-aware with run accounting.
- Tests: `backend/tests/unit/test_f04_circle_rate_quarantine.py` (8).

**F-16 — fabricated fallback source URL (LOW)**
- `validate_transaction_row` now requires `source_url` and returns `PROVENANCE_MISSING` quarantine
  instead of defaulting to `http://local-source`.

**F-15 — `rows_rejected` accounting semantics (LOW)**
- Removed the unreachable `rows_rejected` branch in `provider.py` (replaced with a fail-loud guard).
- `rows_rejected` documented as a **reserved** field. Invariant unchanged.
- Test: `test_validators_never_return_none_none` in `test_ingestion_pipeline.py`.

**F-17 — unit semantics inconsistent (LOW)**
- Contract field renamed `rate_inr_normalized` → **`rate_inr_per_sqft`** (square-foot basis documented);
  ORM attribute / physical DB column keep the historical name (**no migration needed**) with a
  contract→column mapping in the repository.
- `rate_per_sqm` (square-metre basis) documented in model comment, Pydantic description, OpenAPI.
- API + circle-rate ingestion `property_type` default aligned to `residential_flat`.
- Regenerated 5 processed JSONL files; updated `data/schema.md` and 4 provider metadata strings.
- Tests: `backend/tests/unit/test_f17_unit_semantics.py` (7).

**Bonus — latent bug found and fixed (not a claimed finding)**
Both upserts used `pg_insert.excluded.<col>`, which is invalid in SQLAlchemy 2.1 (`excluded` lives on
the built statement). Rebuilt as `insert_stmt.excluded.<col>`; verified by statement compilation (no DB
required). This also removed 7 pre-existing `attr-defined` mypy errors.

### Priority 4 — API and configuration security (COMPLETE ✅)

**Access-policy decision (prerequisite for F-05)** — recorded in `docs/security/access_policy.md`:
public = `GET /health`, `GET /circle-rates/lookup`, `GET /`; protected = `/auth`, `/applications`,
`/documents`, `/underwriting`, `/compliance`, `/reports`. No user-management system invented; no live
public endpoint broken.

**F-05 — no authentication on any endpoint (HIGH)**
- Implemented `require_api_key` (`backend/app/security/auth.py`) — constant-time `hmac.compare_digest`,
  accepts `Authorization: Bearer <key>` or `X-API-Key`; **fails closed** (`503` if `API_KEY` unset,
  `401` if missing/invalid). Real `AuthService`.
- Protected routers now constructed with `dependencies=[Depends(require_api_key)]` → **protected by
  default**.
- New best-effort rate limiter `backend/app/security/rate_limit.py`, applied to the public lookup.
- Lookup query params length/pattern-constrained; `404` detail no longer reflects raw input.
- Tests: `backend/tests/unit/test_f05_auth_access_policy.py` (15).

**F-06 — CORS wildcard fallback (MEDIUM)**
- `CORS_ORIGINS` parser now **fails closed** (unparseable JSON / non-list JSON / unexpected type /
  empty all raise). New `CORS_ALLOW_CREDENTIALS`; `"*"` rejected while credentials are enabled.
- `main.py` reads the settings flag; methods/headers are explicit allowlists instead of `["*"]`.
- Tests: `backend/tests/unit/test_f06_cors_config.py` (7).

**F-07 — insecure secret / DB defaults (MEDIUM)**
- `SECRET_KEY` / `DATABASE_URL` have **no usable default**; dev environments get recognisable throwaway
  values; any other environment **raises at construction** unless both are set explicitly, must not use
  the dev values, and `SECRET_KEY` must be ≥ 32 chars.
- `alembic.ini` URL blanked (still overridden at runtime by `migrations/env.py`).
- `.env.example` rewritten with placeholders only.
- Tests: `backend/tests/unit/test_f07_secrets_config.py` (10).

**F-08 — SSRF / arbitrary file read (MEDIUM)**
- `validate_ingestion_url`: HTTPS-only; IP literals in internal/reserved ranges **blocked even when
  allowlisted**; host must be on `CIRCLE_RATE_ALLOWED_HOSTS`; **empty allowlist ⇒ refuse to fetch**;
  **redirects are not followed**.
- `resolve_intake_path`: local ingestion confined to `CIRCLE_RATE_INTAKE_DIR`, traversal rejected,
  suffix allowlist. CLI gains `--intake-dir` / repeatable `--allow-host`.
- No official host assumed (provenance still unverified per F-03).
- Tests: `backend/tests/unit/test_f08_ingestion_ssrf.py` (20) — all offline (mocked transport, temp dirs).

### Priority 5 — Maintainability and deployment (COMPLETE ✅ except F-12)

**F-09 — `.env.example` sync + embedding-model mismatch (MEDIUM)**
- `.env.example` already documents every setting (synchronised as an F-07 side-effect) and was verified
  by a test that enumerates `Settings.model_fields`.
- `EMBEDDINGS_MODEL` default changed from `sentence-transformers/all-MiniLM-L6-v2` to
  **`BAAI/bge-small-en-v1.5`** — a **deliberate, documented** identifier change aligning config with the
  governing playbook (§ stack) and `rag/embeddings.py`. Both are 384-dim, so no dimension break; no RAG
  code changed and no model downloaded.
- Tests: `backend/tests/unit/test_f09_settings_env_sync.py` (5).

**F-10 — two parallel valuation pipelines / two ORM trees (MEDIUM)**
- **Owner-ratified decision:** `app/property/*` + `app/database/models/*` are **canonical**
  (`app.property.valuation` is the only engine wired into a live entry point and carries the F-01 gate
  and F-02 index gating); `app/valuation/*` is retained as the **stricter migration target**;
  `app/models/*` is **deprecated**.
- New decision record `docs/architecture/canonical_pipeline.md`; deprecation marker (runtime
  `DeprecationWarning`) added to `app/models/__init__.py`; canonical/migration-target notes added to the
  two package docstrings. **No files deleted, no runtime behaviour changed.**
- Tests: `backend/tests/unit/test_f10_canonical_pipeline.py` (7) — include a guard asserting **exactly one**
  valuation engine is imported by live entry points.

**F-11 — duplicated/conflicting dependency declarations (MEDIUM)**
- `backend/requirements.txt` rewritten as a **single de-duplicated runtime manifest** (one constraint per
  package; competing `psycopg[binary]` dropped, `psycopg2-binary` kept); `backend/requirements-dev.txt`
  now `-r requirements.txt` + test/lint tooling only; `backend/Dockerfile` copies only the manifest it
  installs.
- Tests: `backend/tests/unit/test_f11_dependency_manifest.py` (6). Per owner decision, **no `docker build`**
  was run — the defect class is caught statically.
- Residual: `app/rag/ingestion.py` imports `yaml` (PyYAML), undeclared and out of scope.

**F-12 — no Alembic revision files (MEDIUM) — BLOCKED, documented**
- Preparing/testing the initial revision needs a **live disposable PostGIS DB** (autogenerate +
  `upgrade head` / `downgrade base`), which is **not authorised**. Per owner decision F-12 stays blocked.
- Prepared without a database: `scripts/check_migrations.py` (static readiness checker — validates
  `env.py`/`script.py.mako`/`alembic.ini`, confirms the canonical ORM target, confirms the URL embeds no
  credentials, inventories revisions/heads) and `migrations/versions/.gitkeep`.
- Tests: `backend/tests/unit/test_f12_migration_checker.py` (3). The checker exits non-zero today
  (`Ready: NO`, "no revision files — F-12 open") so the gap is never silent.

### Priority 6 — Scope and reliability (in-scope items COMPLETE ✅; F-13 out of scope)

**F-14 — broad exception handling hides failures and leaks text (LOW)**
- `property_agent.py`: a generic `unexpected_agent_error` reason code replaces the raw
  `f"unexpected_agent_error: {str(e)}"`; the full traceback is logged server-side against a
  correlation id and only the generic code + correlation id reach the output/state/audit trail.
- `property/comps.py`: catch narrowed to `(ValueError, TypeError)` and the neutral-recency fallback is
  now logged, not silent.
- `property/normalize.py`: catch narrowed to `(ValueError, TypeError)` (still reason-coded).
- Tests: `backend/tests/unit/test_f14_error_handling.py` (8), including an AST guard against new
  bare/`except Exception` swallows in the in-scope property modules.

**F-18 — conflicting docs and missing R21 deliverables (INFO) — PARTIAL**
- Added `scripts/check_database.py`, `scripts/validate_dataset.py`, `scripts/build_dataset.py`,
  `scripts/run_verification.py`, `reports/implementation_audit.md`, `reports/verification_report.md`
  and `docs/PROGRESS.md`; `scripts/check_migrations.py` + `scripts/check_sources.py` already existed.
- `build_dataset.py` is **gated**: dry-run by default and it fails closed (exit 2) on unapproved
  sources (all four fixture sources are `pending_review`, so it currently refuses them by design).
- Conflicts were **documented, not silently edited**: `.clinerules` intentionally stays under
  `data/regulatory_docs/`; the US-oriented `README.md` was left as unrelated user content;
  `AGENTS.md`/`.clineignore` are recorded as absent.
- Tests: `backend/tests/unit/test_f18_deliverables.py` (21).

**F-13 — RAG fabricated content (MEDIUM) — OPEN, out of scope**
- `backend/app/rag/*` is excluded from this phase; **no RAG file was modified**. Recorded so the
  synthetic RAG corpus is never cited as regulatory evidence. Residual: `rag/ingestion.py` imports
  PyYAML, undeclared in any manifest.

**F-19 / F-20 — informational — NO ACTION**

---

## 4. Attribution / resolution note (F-01)

F-01's remediation (synthetic-exclusion gate + `evidence_is_synthetic` discriminator + agent guard)
has been explicitly re-verified against the full test suite (7 dedicated `test_f01_*` tests passing,
28/28 `test_property_agent.py` passing) and formally appended to the authoritative status log in
`SECURITY_AUDIT_REPORT.md`. Both documents now agree that F-01 is **REMEDIATED**.

---

## 5. Verification evidence

**Environment:** `.venv` Python 3.11.0; pytest 8.4.2; ruff 0.17.0; mypy 2.4.0.

| Command | Result |
|---|---|
| `.venv/Scripts/python.exe -m pytest backend/tests -q` | **231 collected, 0 failed (exit 0)** |
| `.venv/Scripts/python.exe -m ruff check <remediation files>` | **All checks passed** (0 findings) |
| `../.venv/Scripts/python.exe -m mypy app` (from `backend/`) | 9 errors in 7 files — down from 17 at baseline; **none** in touched files |
| `.venv/Scripts/python.exe scripts/check_sources.py --verify-fixtures` | exit 0 (reference-rate + market-index provenance OK) |
| `.venv/Scripts/python.exe scripts/check_migrations.py` | config OK, **Ready: NO**, exit 1 (F-12 open, as documented) |
| `.venv/Scripts/python.exe scripts/check_migrations.py --config-only` | exit 0 |
| `.venv/Scripts/python.exe scripts/validate_dataset.py` | exit 0 (5 processed files / 38 rows, 6 manifests, 1 quarantine file, 0 errors) |
| `.venv/Scripts/python.exe scripts/check_database.py` | exit 0 (static; 10 expected tables; credentials redacted; no connection) |
| `.venv/Scripts/python.exe scripts/build_dataset.py` | exit 2 — **fails closed** (all fixture sources `pending_review`, F-03 gate enforced, nothing written) |
| `.venv/Scripts/python.exe scripts/run_verification.py` | exit 0 — all blocking checks PASS (mypy INFO) |

**Test suite composition (this effort's suites):**

| Suite | Tests | Finding |
|---|---|---|
| `test_f02_market_index.py` | 11 | F-02 |
| `test_f03_data_provenance.py` | 6 | F-03 |
| `test_f04_circle_rate_quarantine.py` | 8 | F-04 |
| `test_f17_unit_semantics.py` | 7 | F-17 |
| `test_f05_auth_access_policy.py` | 15 | F-05 |
| `test_f06_cors_config.py` | 7 | F-06 |
| `test_f07_secrets_config.py` | 10 | F-07 |
| `test_f08_ingestion_ssrf.py` | 20 | F-08 |
| `test_f09_settings_env_sync.py` | 5 | F-09 |
| `test_f10_canonical_pipeline.py` | 7 | F-10 |
| `test_f11_dependency_manifest.py` | 6 | F-11 |
| `test_f12_migration_checker.py` | 3 | F-12 |
| `test_f14_error_handling.py` | 8 | F-14 |
| `test_f18_deliverables.py` | 21 | F-18 |
| `test_ingestion_pipeline.py` | 9 | F-15, F-16 (+ canonical pipeline) |
| `test_property_agent.py` (`test_f01_*`) | 7 of 28 | F-01 (see §4) |

Reports of pre-existing lint/type findings elsewhere are **not** regressions introduced by this work.

---

## 6. Blocked / not authorised

These were **not performed** because they are outside the authorised scope:

- Installing dev tools (pip-audit, pytest-postgresql, geopy, …).
- Disposable-PostGIS **Alembic upgrade/downgrade** → F-12 stays blocked (owner decision).
- **Docker** build / compose → owner decided the F-11 static checks are sufficient.
- **Dependency vulnerability scan**.
- Fetching live government source URLs to verify F-02/F-03 provenance (external **partial**: RBI DBIE HPI
  values were not fetched → the market-index fixture remains an *unverified* labelled fixture).

---

## 7. Residual work & known gaps

| Item | Detail | Priority |
|---|---|---|
| F-12 migrations | No `migrations/versions/*` revision; needs an authorised disposable PostGIS DB for autogenerate + tested rollback. `scripts/check_migrations.py` reports the gap. | 5 |
| F-12 column rename | Renaming the physical `reference_rates.rate_inr_normalized` column needs an authorised migration | 5 |
| RAG `yaml` dependency | `app/rag/ingestion.py` imports PyYAML, undeclared in any manifest (RAG out of scope) | 5 |
| F-13 | RAG fabricated content (out of scope, untouched) + residuals `commands.py::market()` hard-coded figures and `jurisdictions.py` `hpi_base_year="2022-23"` | 6 |
| F-18 | R21 scripts/reports now present; remaining: conflicts documented (US-oriented `README.md`, `.clinerules` under `data/regulatory_docs/`), `AGENTS.md`/`.clineignore` absent, RAG `yaml` undeclared | 6 |
| Legacy trees | `app/models/*` (deprecated, warns on import) and `app/valuation/*` (migration target) retained per the Priority-5 instruction; removal needs the migration path in `docs/architecture/canonical_pipeline.md` | 5 |
| Rate limiting | Best-effort, per-process only — production should add an edge/gateway limiter | — |
| Redirect policy | Fail-closed (3xx rejected) rather than followed-and-validated | — |
| `API_KEY` model | Shared secret, not an identity provider — replace before exposing borrower-adjacent data | — |

---

## 8. Decisions requested from the owner

Resolved in this phase:
- **F-01 attribution** — F-01 is recorded as **REMEDIATED** in both documents (7 `test_f01_*` tests).
- **F-10 designation** — owner chose `app/property` + `app/database/models` as canonical.
- **F-12 / F-11 authorisation** — F-12 stays blocked (documented); no Docker build for F-11.

Still open:
1. **Access-policy location** — the F-05 remediation text suggested `README`/`PROGRESS`; the policy was
   recorded in `docs/security/access_policy.md` instead. Ratify that location or request a README pointer.
2. **`rate_inr_normalized` → `rate_inr_per_sqft`** — `GEMINI.md`/`CLAUDE.md` §4.5 still list the old
   field name (governing docs were **not** edited). Ratify the rename in the governing docs, or confirm
   the contract→column mapping documented in `data/schema.md`.

---

## 9. Reproduce the verification

From the repository root (`C:\Users\HP\Documents\mortrage-underwriting-ai`):

```bash
# Full test suite (expect exit 0)
./.venv/Scripts/python.exe -m pytest backend/tests -q

# Lint a changed file, e.g.
./.venv/Scripts/python.exe -m ruff check backend/app/core/config.py backend/app/security/

# Type check (run from backend/)
cd backend && ../.venv/Scripts/python.exe -m mypy app

# Provenance fixture check (expect exit 0)
cd .. && ./.venv/Scripts/python.exe scripts/check_sources.py --verify-fixtures

# Migration readiness (config OK, Ready: NO until F-12 is unblocked)
./.venv/Scripts/python.exe scripts/check_migrations.py --config-only

# One-pass verification of all approved checks (writes reports/verification_report.md)
./.venv/Scripts/python.exe scripts/run_verification.py --write reports/verification_report.md
```

> Notes: there is no `python` on the shell `PATH` — use `./.venv/Scripts/python.exe`. On Windows,
> printing emoji from `SECURITY_AUDIT_REPORT.md` via Python can raise `UnicodeEncodeError`; read/grep
> the file instead of streaming it.

---

*End of summary. Authoritative detail and per-finding evidence live in `SECURITY_AUDIT_REPORT.md`.*
