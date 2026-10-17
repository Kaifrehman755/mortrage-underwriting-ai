# Verification report

Generated: 2026-10-17T09:01:45.856597+00:00
Python: `C:\Users\HP\Documents\mortrage-underwriting-ai\.venv\Scripts\python.exe`

| Check | Blocking | Exit | Status |
|---|---|---|---|
| pytest (full suite) | yes | 0 | PASS |
| ruff (remediation files) | yes | 0 | PASS |
| mypy (backend app) | no | 1 | INFO |
| data provenance (check_sources --verify-fixtures) | yes | 0 | PASS |
| migration config (check_migrations --config-only) | yes | 0 | PASS |
| dataset validation (validate_dataset) | yes | 0 | PASS |
| database config (check_database) | yes | 0 | PASS |

> `mypy` is informational: the repository has pre-existing type errors outside this
> remediation's scope, and none are in the files it touched.

## pytest (full suite)

Command: `C:\Users\HP\Documents\mortrage-underwriting-ai\.venv\Scripts\python.exe -m pytest backend/tests -q` (cwd: `C:\Users\HP\Documents\mortrage-underwriting-ai`)

Exit code: **0**

```
........................................................................ [ 31%]
........................................................................ [ 62%]
........................................................................ [ 93%]
...............                                                          [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\fastapi\testclient.py:1
  C:\Users\HP\Documents\mortrage-underwriting-ai\.venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

tests/unit/test_exceptions.py::test_validation_exception
  C:\Users\HP\Documents\mortrage-underwriting-ai\backend\tests\unit\test_exceptions.py:22: StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.
    exc = ValidationException("Invalid borrower income", details={"field": "income"})

tests/unit/test_health.py::test_root_status_endpoint
  <frozen abc>:123: RuntimeWarning: coroutine 'Connection._cancel' was never awaited
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
```

## ruff (remediation files)

Command: `C:\Users\HP\Documents\mortrage-underwriting-ai\.venv\Scripts\python.exe -m ruff check backend/app/agents/property_agent.py backend/app/core/config.py backend/app/security/auth.py backend/app/security/rate_limit.py backend/app/ingestion/circle_rates.py backend/app/models/__init__.py backend/app/property/__init__.py backend/app/property/comps.py backend/app/property/normalize.py backend/app/property/market_index.py backend/app/valuation/__init__.py backend/tests/unit/test_f02_market_index.py backend/tests/unit/test_f03_data_provenance.py backend/tests/unit/test_f04_circle_rate_quarantine.py backend/tests/unit/test_f05_auth_access_policy.py backend/tests/unit/test_f06_cors_config.py backend/tests/unit/test_f07_secrets_config.py backend/tests/unit/test_f08_ingestion_ssrf.py backend/tests/unit/test_f09_settings_env_sync.py backend/tests/unit/test_f10_canonical_pipeline.py backend/tests/unit/test_f11_dependency_manifest.py backend/tests/unit/test_f12_migration_checker.py backend/tests/unit/test_f14_error_handling.py backend/tests/unit/test_f17_unit_semantics.py backend/tests/unit/test_f18_deliverables.py scripts/check_sources.py scripts/check_migrations.py scripts/check_database.py scripts/validate_dataset.py scripts/build_dataset.py scripts/run_verification.py` (cwd: `C:\Users\HP\Documents\mortrage-underwriting-ai`)

Exit code: **0**

```
All checks passed!
```

## mypy (backend app)

Command: `C:\Users\HP\Documents\mortrage-underwriting-ai\.venv\Scripts\python.exe -m mypy app` (cwd: `C:\Users\HP\Documents\mortrage-underwriting-ai\backend`)

Exit code: **1**

_informational: pre-existing type errors outside the remediation scope_

```
app\calculations\risk_score.py:4: error: Missing return statement  [empty-body]
app\calculations\ltv.py:4: error: Missing return statement  [empty-body]
app\calculations\ltv.py:9: error: Missing return statement  [empty-body]
app\calculations\fico.py:4: error: Missing return statement  [empty-body]
app\calculations\dscr.py:4: error: Missing return statement  [empty-body]
app\property\schemas.py:76: error: Returning Any from function declared to return "float"  [no-any-return]
app\rag\vector_store.py:20: note: By default the bodies of untyped functions are not checked, consider using --check-untyped-defs  [annotation-unchecked]
app\rag\vector_store.py:22: note: By default the bodies of untyped functions are not checked, consider using --check-untyped-defs  [annotation-unchecked]
app\rag\seed_corpus.py:186: error: Argument 1 to "ingest_document_text" of "DocumentIngestionPipeline" has incompatible type "object"; expected "RegDocument"  [arg-type]
app\rag\seed_corpus.py:186: error: Argument 2 to "ingest_document_text" of "DocumentIngestionPipeline" has incompatible type "object"; expected "str"  [arg-type]
app\valuation\evaluation.py:102: error: Incompatible types in assignment (expression has type "date | None", variable has type "date")  [assignment]
Found 9 errors in 7 files (checked 140 source files)
```

## data provenance (check_sources --verify-fixtures)

Command: `C:\Users\HP\Documents\mortrage-underwriting-ai\.venv\Scripts\python.exe scripts/check_sources.py --verify-fixtures` (cwd: `C:\Users\HP\Documents\mortrage-underwriting-ai`)

Exit code: **0**

```
================================================================================
 Indian Residential Property Valuation Agent - Source Readiness Audit
================================================================================

[OK] Audited 10 candidate sources across states.

State  | Source Name                                | Category             | Decision      
--------------------------------------------------------------------------------------
UP     | IGRSUP Circle Rate Services                | reference_rate       | pending_review
UP     | IGRSUP Deed Search & Property Search       | property_transaction | rejected      
MH     | IGR Maharashtra eASR (Ready Reckoner Rates | reference_rate       | pending_review
MH     | IGR Maharashtra eSearch Portal             | property_transaction | rejected      
KA     | Kaveri 2.0 Guidance Value Services         | reference_rate       | pending_review
KA     | Kaveri 2.0 Document & Encumbrance Services | property_transaction | rejected      
TS     | IGRS Telangana Market Value & Unit Rates   | reference_rate       | pending_review
TS     | IGRS Telangana Registered Transaction Serv | property_transaction | rejected      
ALL    | Synthetic Property Test Fixture Generator  | property_transaction | approved      
ALL    | RBI House Price Index (HPI) - Lucknow      | market_index         | pending_review

Summary by State & Decision:
  ALL   -> approved: 1, pending_review: 1
  KA    -> pending_review: 1, rejected: 1
  MH    -> pending_review: 1, rejected: 1
  TS    -> pending_review: 1, rejected: 1
  UP    -> pending_review: 1, rejected: 1

[OK] Fixture provenance check passed: all reference-rate fixtures use local://synthetic/ provenance.

[OK] Market-index provenance check passed: market_index rbi_hpi_urban_lucknow: verification_status=unverified, periods=9.
```

## migration config (check_migrations --config-only)

Command: `C:\Users\HP\Documents\mortrage-underwriting-ai\.venv\Scripts\python.exe scripts/check_migrations.py --config-only` (cwd: `C:\Users\HP\Documents\mortrage-underwriting-ai`)

Exit code: **0**

```
Migration readiness check (F-12)
  [OK  ] migrations/env.py
  [OK  ] migrations/script.py.mako
  [OK  ] alembic.ini
  [OK  ] targets canonical ORM tree (app.database.models)
  [OK  ] sqlalchemy.url has no embedded credentials
  [OK  ] migrations/versions/ exists
  revision files: none
Config: OK
  - migrations/versions/ has no revision files - F-12 open (blocked on an authorised disposable PostGIS database for autogenerate + upgrade/downgrade)
```

## dataset validation (validate_dataset)

Command: `C:\Users\HP\Documents\mortrage-underwriting-ai\.venv\Scripts\python.exe scripts/validate_dataset.py` (cwd: `C:\Users\HP\Documents\mortrage-underwriting-ai`)

Exit code: **0**

```
Dataset validation (R21 / F-18)
  processed:  5 file(s), 38 row(s), 0 error(s)
  manifests:  6 file(s), 0 error(s)
  quarantine: 1 file(s), 4 row(s), 0 error(s)
Result: OK
```

## database config (check_database)

Command: `C:\Users\HP\Documents\mortrage-underwriting-ai\.venv\Scripts\python.exe scripts/check_database.py` (cwd: `C:\Users\HP\Documents\mortrage-underwriting-ai`)

Exit code: **0**

```
Database readiness check (R21 / F-18)
  expected tables: 10
    - circle_rates
    - data_sources
    - ingestion_runs
    - property_listings
    - property_records
    - property_transactions
    - quarantine_records
    - reference_rates
    - valuation_comparables
    - valuation_runs
  database url:   postgresql+asyncpg://postgres:***@localhost:5432/mortgage_underwriting
Static mode: no connection attempted (pass --connect for a live probe).
```
