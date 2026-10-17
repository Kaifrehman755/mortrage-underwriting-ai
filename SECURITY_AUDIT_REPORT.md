Phase 2: Security Remediation and Verification
==============================================

You are working on the mortrage-underwriting-ai project, a Python-based India property-valuation backend.

Use the previous security audit report as the baseline. The report identified findings F-01 through F-20, with F-01 (synthetic comparables entering production valuation) as the highest priority.

Your objective is to verify the reported issues, remediate them systematically, run tests, and produce an evidence-based verification report.

STRICT RULES
------------

1.  Read CLAUDE.md, GEMINI.md, backend/app/property/playbook.md, applicable .clinerules files, and the existing audit report before making changes.
    
2.  Preserve the existing project architecture and follow its India property-valuation scope.
    
3.  Do not implement out-of-scope RAG, compliance, frontend, or US-mortgage functionality.
    
4.  Do not fabricate government data, source URLs, regulatory citations, market indices, credentials, or test results.
    
5.  Never print, expose, commit, or overwrite real secrets.
    
6.  Do not access production systems, use real customer data, or perform destructive operations.
    
7.  Do not make broad refactors when a targeted fix is sufficient.
    
8.  Before changing files, provide a concise implementation plan and list the files expected to change.
    
9.  Preserve unrelated user modifications and untracked files. Inspect Git status and diffs before editing.
    
10.  If a fix requires a product decision, an external source verification, unavailable credentials, or destructive database operation, explain the blocker and ask me before proceeding.
    
11.  Do not claim a vulnerability is fixed until the relevant regression test passes.
    
12.  Do not silently skip failed or unexecuted tests.
    

PHASE 1 — Establish the baseline
--------------------------------

Inspect the current Git status and existing diffs. Confirm the project root and identify the authoritative audit report.

Revalidate the findings against the current source code before applying fixes. Use exact file paths and line numbers.

Create a finding tracker for F-01 through F-20 containing:

*   Original finding and severity
    
*   Current verification status
    
*   Evidence from the current code
    
*   Planned remediation
    
*   Regression test
    
*   Final status
    

Distinguish confirmed issues, partially confirmed issues, false positives, and issues that cannot be verified.

Do not assume the previous report is infallible.

PHASE 2 — Fix the highest-risk findings
---------------------------------------

Work in small, independently testable changesets, in this order.

### Priority 1: F-01 — Synthetic valuation data leakage

*   Prevent synthetic comparables from entering production valuation by default.
    
*   Require an explicitly injected, approved provider for production use.
    
*   Allow synthetic data only through an explicit test-only mechanism.
    
*   Ensure the comparable-selection logic checks the synthetic-data discriminator.
    
*   Preserve existing abstention and human-review behavior.
    
*   Ensure valuation outputs and persisted records cannot misrepresent synthetic estimates as real market valuations.
    
*   Add tests for default construction, synthetic-only evidence, mixed evidence, and approved real evidence.
    
*   Confirm that synthetic-only evidence produces no production estimate.
    

### Priority 2: F-03 and F-02 — Data provenance and market indices

*   Verify the claimed source and licensing status of every reference-rate dataset using authorized evidence.
    
*   Never label unverified records as official or approved.
    
*   Preserve unverified records as pending or quarantined according to project rules.
    
*   Replace unprovenanced hard-coded index values with versioned data carrying source, publication date, units, and verification status.
    
*   If reliable index data is unavailable, abstain from the affected time adjustment rather than inventing a value.
    
*   Add tests for missing provenance, unverified sources, and missing index values.
    

Do not invent replacement data. If verification requires external access or a human decision, report the blocker instead of guessing.

### Priority 3: F-04, F-15, F-16 and F-17 — Ingestion integrity

*   Route invalid rows into quarantine with explicit reason codes.
    
*   Prevent silent row loss.
    
*   Correct rejected-row accounting and reconcile imported, accepted, rejected, quarantined, and duplicate counts according to the documented invariant.
    
*   Require valid source provenance for transactions; remove fabricated fallback URLs.
    
*   Standardize area and rate units across ingestion, database models, and API responses.
    
*   Add regression tests for invalid rows, missing source URLs, incorrect units, and row-accounting invariants.
    

### Priority 4: F-05, F-06, F-07 and F-08 — API and configuration security

*   Determine the intended public/private access policy for each active endpoint.
    
*   Implement appropriate authentication and authorization where required. Do not invent a user-management system or break explicitly public health/reference-data endpoints without documenting the decision.
    
*   Make malformed CORS configuration fail closed.
    
*   Reject wildcard origins when credentials are enabled.
    
*   Require secure production secrets and database configuration.
    
*   Retain safe development defaults only where the environment explicitly permits them.
    
*   Validate external ingestion URLs against an approved host policy and block unauthorized internal-network destinations, including redirect targets.
    
*   Constrain file ingestion to approved directories and prevent path traversal.
    
*   Add tests for malformed configuration, unauthenticated protected routes, unsafe URLs, redirects, and invalid file paths.
    

Do not send requests to real internal infrastructure or metadata endpoints during testing. Use mocked transports and temporary directories.

### Priority 5: F-09, F-10, F-11 and F-12 — Maintainability and deployment

*   Synchronize .env.example with supported configuration fields using placeholders only.
    
*   Resolve the embedding-model mismatch without downloading models or introducing out-of-scope RAG work.
    
*   Identify the canonical valuation pipeline and database model tree from the governing instructions.
    
*   Avoid deleting legacy files until their references and compatibility implications are understood.
    
*   Resolve duplicate or conflicting dependency declarations.
    
*   Correct the Dockerfile and build instructions so they reference an existing, authoritative dependency manifest.
    
*   Create Alembic migrations only after verifying the canonical ORM models and existing migration configuration.
    
*   Test migration upgrade and rollback only against a disposable local database.
    
*   Do not connect to, reset, or migrate a production database.
    

### Priority 6: F-13, F-14, F-18 and F-19 — Scope and reliability

*   Ensure fabricated RAG content cannot be presented as verified regulatory evidence.
    
*   Do not expand RAG functionality; isolate or clearly mark out-of-scope components as required by project instructions.
    
*   Replace unsafe broad exception handling and generic numeric fallbacks with explicit errors, safe reason codes, and appropriate logging.
    
*   Avoid exposing raw exception details to clients.
    
*   Resolve conflicting documentation and identify missing required deliverables.
    
*   Do not build a Flask frontend or ML model unless the governing requirements explicitly change.
    

PHASE 3 — Automated verification
--------------------------------

First inspect the available Python version, dependency manifests, virtual environment, test configuration, and installed tools.

After reviewing the implementation plan, run appropriate checks in a safe local environment:

1.  Targeted pytest regression tests for each fix.
    
2.  The full backend test suite.
    
3.  Ruff lint checks.
    
4.  Mypy type checks using the existing project configuration.
    
5.  Dependency vulnerability scanning, if the scanner is available and its data source is accessible.
    
6.  Docker Compose configuration validation.
    
7.  Docker build validation if dependencies and build context are available.
    
8.  Alembic migration and rollback verification against a disposable PostGIS database.
    

Do not install tools or download dependencies without approval. Do not run migration commands against an unverified database.

If a check cannot run, report the exact reason and mark it NOT RUN.

PHASE 4 — Final verification report
-----------------------------------

Update the audit tracker and produce a report with:

1.  Executive summary.
    
2.  Findings confirmed, fixed, partially fixed, false positive, or unresolved.
    
3.  Files changed and the purpose of each change.
    
4.  Regression tests added.
    
5.  Commands actually executed and their exit statuses.
    
6.  Test results and any failures.
    
7.  Remaining vulnerabilities ranked by severity.
    
8.  Requirements compliance matrix.
    
9.  Data provenance verification status.
    
10.  Migration and deployment readiness.
    
11.  Known limitations and unreviewed files.
    
12.  Recommended next actions.
    

Use evidence from the current code and actual command output. Never claim all findings are resolved when checks remain unexecuted.

EXECUTION PROTOCOL
------------------

Begin with Phase 1 and present the implementation plan before modifying files.

Then proceed with the highest-priority remediation in small, reviewable steps. After each changeset, run the relevant approved regression tests and show the results.

If you encounter a decision that requires my approval, stop that specific change, explain the options and risks, and continue only with independent safe tasks.

Do not declare the project production-ready until the critical findings are resolved and the remaining security, data-quality, testing, and deployment risks are explicitly assessed.

How to use it
-------------

1.  Open the project root in OpenCode.
    
2.  Ensure the previous audit report is accessible to the agent.
    
3.  Paste the prompt into the conversation.
    
4.  Review the implementation plan before allowing edits.
    
5.  Start with F-01, and require a passing regression test before moving on.
    

Important: Your previous report describes a large amount of untracked and modified code. Keep a backup or use a dedicated Git branch before authorizing remediation, and don't discard existing work.

Once OpenCode completes this phase, the next useful step is an independent review of the patch and its test results before deploying anything.

what should i choose

I recommend choosing these options:

1\. Canonical pipeline — choose option 1
----------------------------------------

app/valuation + app/database/models

Your audit report identifies this as the structure matching the recommended architecture in CLAUDE.md and migrations/env.py. Treat app/property + app/models as legacy and isolate it.

However, because F-01 concerns the synthetic provider in the property-agent pipeline, ask OpenCode to verify which pipeline is actually called in production before deprecating anything.

2\. Approvals — select options 1 and 4 first
--------------------------------------------

1\. Run local tests/lint/mypy with existing .venv

Choose this

Uses existing tools without installing packages. It gives you evidence about the current state.

4\. Allow external source verification

Choose this

Useful for checking whether the claimed government reference-rate sources and licensing information are genuine. It is particularly important for F-02 and F-03.

3\. Use disposable PostGIS for migrations

Choose this later, once the migration configuration and Docker setup have been reviewed. Ensure it uses a throwaway database.

2\. Install approved development tools

Skip for now. First establish what is already installed; install only missing tools you approve.

### What to do now

*   In the first screen, select option 1.
    
*   In the second screen, select options 1 and 4.
    
*   Leave options 2 and 3 unselected for now.
    

One extra instruction to give OpenCode:

> Before modifying or deleting either pipeline, trace the actual production entry points and imports. Fix F-01 wherever synthetic data can reach production, then isolate the legacy pipeline only after verifying its callers. Preserve my existing untracked and modified files. Run the approved checks and report failures without claiming success when tests have not passed.

This is the safest route because it prioritizes the critical valuation-integrity issue without prematurely deleting code or installing unnecessary dependencies.

the opencode asks me for these - Blocked on: the authoritative audit report. Please paste it here (or tell me the path) so I can bind the F-01…F-20 tracker to its exact wording/severities rather than my reconstruction.- Not authorized, so will be marked NOT RUN: dev-tool installs (pip-audit, pytest-postgresql, geopy) and disposable-PostGIS Alembic upgrade/downgrade.- Authorized: local pytest/ruff/mypy using the existing .venv (Python 3.11.0), and external official-source verification for F-02/F-03.- Still needs a decision (F-05): the intended public/private policy per endpoint — today only /health and /circle-rates/lookup exist. I need to know which are meant to stay public so I don't break them.

You can answer OpenCode with the following. The audit report you uploaded is available at:

/mnt/data/Pasted text(1).txt

If OpenCode is running on your Windows computer, that Linux path may not be accessible to it. Use the original report file in your project or paste the report into OpenCode.

1\. Reply to OpenCode
---------------------

Use the authoritative audit report I provide as the baseline for the exact F-01 through F-20 wording, severities, and requirements. Do not reconstruct or silently change the findings.

Approvals:

*   Authorized: Run local pytest, Ruff, and mypy using the existing Python 3.11 virtual environment. Do not install packages.
    
*   Authorized: Verify F-02 and F-03 against official external sources. Do not invent source URLs or claim verification without evidence.
    
*   Not authorized yet: Install additional development tools.
    
*   Not authorized yet: Run disposable PostGIS migrations or Alembic upgrade/downgrade.
    

Canonical pipeline:Use app/valuation + app/database/models as the intended canonical structure, subject to verification against CLAUDE.md and the actual production entry points. Treat app/property + app/models as legacy until its callers are traced. Do not delete or refactor either pipeline prematurely.

Endpoint access policy:

*   /health: Keep public for basic liveness checks. Do not expose credentials, internal configuration, or sensitive diagnostics in the response.
    
*   /circle-rates/lookup: Treat as public reference data only for now, provided the endpoint returns no personal, confidential, or restricted information. Apply input validation, safe error handling, and reasonable rate limiting where appropriate. Document this as an explicit public-endpoint decision.
    
*   All placeholder endpoints: Keep unimplemented or protected by default. Do not introduce new public functionality.
    

Before editing:

1.  Read the authoritative report and governing project instructions.
    
2.  Inspect Git status and preserve all existing modified, untracked, and deleted files.
    
3.  Run the authorized baseline checks and report their actual results.
    
4.  Verify F-02 and F-03, recording the evidence and remaining uncertainties.
    
5.  Present the proposed changes for F-01 and the affected files before implementing them.
    

Proceed in small, testable changesets. Never claim a finding is fixed unless the relevant verification supports that claim. If a command fails, report the error and continue with independent authorized tasks.

2\. What you have authorized
----------------------------

Action

Decision

Existing-environment tests, lint and type checks

Approved

Official-source verification

Approved

Additional tool installations

Not approved

Disposable PostGIS migration testing

Not approved

Public health endpoint

Approved, with safe response requirements

Public circle-rate lookup

Approved for reference data only

Important: Public access does not mean unrestricted behavior. The lookup endpoint still needs input validation, safe database access, and protection against abuse.

3\. What should happen next?
----------------------------

Have OpenCode run the existing checks first, then verify the government-source claims. After that, prioritize F-01, because synthetic data influencing a production valuation is the most serious finding in your report.

Keep the migration tests marked NOT RUN until you explicitly authorize them.

can u provide the report

Yes — here is the authoritative audit report you shared with me, covering findings F-01 through F-20 for mortrage-underwriting-ai.

The report includes the requirements checklist, vulnerability evidence, remediation recommendations, file-by-file coverage, unverified areas, and pending approvals. You can give it to OpenCode so it can use the exact original findings instead of reconstructing them.

Download the complete audit report (.txt)

### How to provide it to OpenCode

1.  Download the file.
    
2.  Copy it into your project root, for example as reports/initial\_security\_audit.txt (create the reports folder if necessary).
    
3.  Tell OpenCode:
    

The authoritative audit report is available at reports/initial\_security\_audit.txt. Read it completely and use its exact F-01 through F-20 findings, severities, evidence, and requirements as the baseline for remediation. Do not reconstruct or silently change the report. Preserve the original report unchanged and update the finding tracker with current verification results. Continue only with the previously authorized checks and source verification.

Note: This is the original report text you supplied, copied into a downloadable file—not a newly generated or independently verified audit.

mortrage-underwriting-ai-audit-report.txtDocument Project: mortrage-underwriting-ai · Root: C:\\Users\\HP\\Documents\\mortrage-underwriting-aiAudit date: 2026-10-17 · Mode: read-only · Governing instructions: CLAUDE.md / GEMINI.md (identical) + backend/app/property/playbook.md + .clinerules/\* · Scope: India property-valuation backend · Excluded: .kilo/worktrees/tasteful-fenderExecuted: static review only. NOT run (awaiting approval): pytest, ruff, mypy, alembic, docker build. Findings relying on dynamic verification are marked NOT\_RUN.1. Inventory & exclusionsVCS state: 143 tracked files; a large untracked India layer (backend/app/{ingestion,valuation,providers,database/{models,repositories},schemas}, backend/tests/{unit,evaluation}, data/\*, migrations/\*, CLAUDE.md, GEMINI.md, alembic.ini); modified-unstaged: property/\*, rag/\*, agents/property\_agent.py, api/router.py, core/config.py, calculations/dti.py; deleted: backend/requirements.txt.Included in audit: backend/app (India modules), backend/tests, scripts/, migrations/, data/, docs/, .clinerules/, root meta files.Excluded: .env (secrets — presence & ignore-status checked only), .venv/, \*\*/\_\_pycache\_\_/, .mypy\_cache/, .ruff\_cache/, .pytest\_cache/, .git/ internals, .kilo/worktrees/\*\*.Out of India scope (inventoried, not deeply reviewed): frontend/\*\*, US-mortgage placeholder layer (agents except property, calculations except DTI, compliance/\*, document\_processing/\*, reports/\*, workflows/\*, security/{encryption,permissions}, legacy models/\*, US schemas/\*), rag/\*.2. Requirement checklist (extracted)#Requirement (source)StatusR1Never fabricate records/prices/URLs/section numbers/thresholds (CLAUDE §2.1, §14.3; hard-rule 1)❌ F-01, F-02, F-03, F-13R2Circle rates/asking prices never treated as sale prices (CLAUDE §2.2-2.3; hard-rule 9)✅ (validate.py:227-237; comps.py:44-49)R3Transactions/listings/reference-rates stored separately (CLAUDE §4; hard-rule 2)✅ models separateR4Never bypass CAPTCHA/login; authorized sources only (CLAUDE §2.5-2.7)⚠️ F-03, F-08R5Full provenance per record (CLAUDE §2.8)⚠️ F-04R6No silent drop/impute; quarantine + reason codes (CLAUDE §6; hard-rule 13)❌ F-04 (partial ✅ in main pipeline)R7No personal data; no protected-class proxies (CLAUDE §2.10-2.11; hard-rule 7,10)✅ normalize.py:40-44,146-155R8Abstain/human-review when uncertain (CLAUDE §2.12; playbook Inv.4)✅ estimate.py:105-148; valuation.pyR9Distinguish authenticity vs verification; keep raw+units (CLAUDE §2.13-2.14)✅ schemas/property.py, transaction.pyR10No real-data validation claims (CLAUDE §2.15, §15.9; hard-rule)⚠️ DATA\_CARD §2.1 claimsR11Source-readiness register, unknown preserved (CLAUDE §3)✅ source\_readiness.csvR12Source approval gate before adapters (CLAUDE §3)✅ registry.py:90-105; provider.py:54-60R13Canonical Pydantic v2 schemas + unit conversions (CLAUDE §4-5, Step 2)✅R14Idempotent imports; row-accounting invariant (CLAUDE §6, Step 3)⚠️ F-15R15PostGIS models + Alembic migrations (CLAUDE Step 4)❌ F-12R16Multi-state, no default state, unsupported→explicit error (CLAUDE Step 5; playbook §15.4)✅ providers/registry.pyR17Valuation: eligible evidence, robust estimator, abstention, evaluation (CLAUDE Step 6)✅ + ⚠️ F-01R18Synthetic excluded from production valuation by default (CLAUDE §15.4)❌ F-01R19Config secrets via env; .env.example in sync; no secrets/creds in code (CLAUDE §14.9-14.10)❌ F-07, F-09R20Tests for every transformation/failure; run before "done" (.clinerules/testing)⚠️ NOT\_RUNR21Required scripts/reports: check\_database.py, check\_migrations.py, validate\_dataset.py, build\_dataset.py, run\_verification.py, reports/implementation\_audit.md, reports/verification\_report.md, docs/PROGRESS.md (CLAUDE §15; .clinerules)❌ all MISSINGR22Do not implement RAG/compliance/frontend this phase (CLAUDE §1)❌ F-13, F-193. Routes, modules, dependencies, trust boundariesRoutes (api/router.py:14-26, mounted at /api/v1 in main.py:77):- GET /health (live, health.py:13-31) — DB health probe.- GET /circle-rates/lookup (live, circle\_rates.py:21-63) — DB query, ilike filters, ORM-bound.- GET / root descriptor (main.py:79-87).- Empty placeholder routers: /auth, /applications, /documents, /underwriting, /compliance, /reports.Dependencies: root requirements.txt (⚠️ duplicate/contradictory blocks, F-11), backend/requirements-dev.txt, backend/pyproject.toml (ruff/mypy/pytest, target py311), backend/Dockerfile (py3.11, expects backend/requirements.txt that is deleted).Trust boundaries:1. External portals → ingestors — circle\_rates.py:80-90 (arbitrary httpx GET), parse\_file:122-179 (arbitrary local path). (F-08)2. Client → API — no authn/authz; CORS with credentials. (F-05, F-06)3. Config/env → app — default creds & insecure default secret. (F-07)4. DB layer — ORM/select()/pg\_insert only; no string-interpolated SQL found ✅ (grep clean).5. RAG corpus → LLM — fabricated text/hashes. (F-13)4. FindingsF-01 — CRITICAL — Synthetic comparables feed the production valuation estimate by default- Evidence: backend/app/agents/property\_agent.py:46 self.provider = provider or SyntheticProvider(); backend/app/property/providers/synthetic.py:98-102 assigns real-looking price\_type (registered\_deed/valuer\_report/survey, 85% weight); synthetic.py:194 is\_synthetic=True; backend/app/property/comps.py:44-49 usable\_pool filters only price\_type/state\_code/property\_type — never is\_synthetic.- Impact: the default agent path computes market-value estimates from fabricated comps, violating CLAUDE §2.1/§15.4, DATA\_CARD §3.4, hard-rule 1. is\_synthetic is only surfaced in commands.py:137, never enforced.- Confidence: High.- Remediation: reject synthetic comps unless an explicit test flag is set; require an injected approved provider; assert source\_type != synthetic\_test in non-test mode; propagate is\_synthetic into ValuationOutput/DB as the synthetic/real discriminator (CLAUDE §15.4).- Verification test: unit test — build subject + only-synthetic comps with allow\_synthetic=False; assert valuate() abstains/raises and no estimate is produced.F-02 — HIGH — Hard-coded, unprovenanced market index data- Evidence: backend/app/property/valuation.py:17-30 HPI\_SERIES (literal RBI HPI values) and valuation.py:266 "rbi\_hpi\_yoy\_growth\_percent": 8.2, # RBI reported 8.2% YoY; used for time adjustment at valuation.py:151-155; CURRENT\_HPI at :30.- Impact: estimates are silently time-adjusted by index levels not sourced to a versioned file/release date; violates hard-rule 12 ("thresholds live in versioned config copied from retrieved text") and R1.- Confidence: Medium-High.- Remediation: move index series to a versioned data file with source URL, release date, and TODO-VERIFY; load via config; stop if unsourced.- Verification test: test that the index value carries source metadata and that a missing series ⇒ abstain, not 100.0 fallback (valuation.py:39-41).F-03 — HIGH — Reference-rate fixtures appear synthetic but are labeled as approved government snapshots- Evidence: data/reference\_rates/up\_lucknow\_circle\_rates\_2024.csv (12 rows, rounded values, source\_url=https://igrsup.gov.in/igrsup/rates/lucknow/2024), plus MH/KA/TS files with analogous fabricated-looking paths (.../easr/rates/mumbai/2024, .../rates/bengaluru/2024); data/source\_readiness.csv:2 marks UP license\_review\_status=approved, decision=approved; data/DATA\_CARD.md:24-42 presents these as "Approved Multi-State Reference Rate Snapshots" with SHA-256 (which I verified match the files — internal consistency, not provenance).- Impact: if synthetic, this is fabricated "official government" data (R1/R4). The SHA-256 only proves file integrity, not origin. The URL structure is not consistent with a real IGRSUP download path.- Confidence: Medium (cannot confirm externally in a local read-only pass).- Remediation: verify each URL against the live portal; if synthetic, reclassify source\_type=synthetic\_test, set decision=pending, and correct DATA\_CARD; store a real terms-page hash per playbook §18.2.- Verification test: scripts/check\_sources.py --check-connectivity (currently only validates CSV schema — check\_sources.py:1-180) must fetch and hash the live URL and fail when it does not match.F-04 — HIGH — Circle-rate HTML/excel/pdf ingestion silently drops invalid rows- Evidence: backend/app/ingestion/circle\_rates.py:200-202 except Exception: logger.warning("Skipping invalid circle rate row"); \_normalize\_row returns None for missing/invalid data (:281-288) and rows are discarded at :113-115, :137-141, :154-160, :173-179. Contrast the canonical pipeline which does quarantine with reason codes (ingestion/provider.py:116-119, ingestion/validate.py:36-170; sample data/quarantine/quarantine\_7bbfff48-….jsonl).- Impact: violates R6/hard-rule 13 ("rejected rows are logged with a reason, never silently fixed"). Two divergent ingestion paths with different safety guarantees.- Confidence: High.- Remediation: route parse failures through validate\_reference\_rate\_row/QuarantineRecord; emit a quarantine file and an IngestionRunAccounting; or delete this path in favour of the canonical provider.- Verification test: feed a CSV with a null rate / bad unit; assert a quarantine record with MISSING\_PRICE/INVALID\_UNIT is written (mirror the existing 4-row defect fixture data/raw/reference\_rates/up\_lucknow\_rates\_intake\_raw.csv).F-05 — HIGH — No authentication/authorization on any endpoint- Evidence: backend/app/api/auth.py:1-7 (empty router), backend/app/security/auth.py:1-6 (AuthService stub); main.py:77 mounts routers with no dependency; live /circle-rates/lookup is public (api/circle\_rates.py:21-63).- Impact: trust boundary #2 is open. Phase-0 data surface is small, but the pattern means any future data endpoint ships unauthenticated; no rate limiting / audit of callers.- Confidence: High.- Remediation: add an auth dependency (or explicit "public data only" decision documented in README/PROGRESS) before exposing borrower-adjacent data; add rate limiting.- Verification test: request /api/v1/circle-rates/lookup without credentials → expect 401 once auth is added; document current 200 as accepted risk.F-06 — MEDIUM — CORS wildcard fallback combined with credentials- Evidence: backend/app/core/config.py:30-33 default origins; config.py:59-73 validator returns \["\*"\] on any unexpected type (no exception); backend/app/main.py:44-50 allow\_credentials=True, allow\_methods=\["\*"\], allow\_headers=\["\*"\].- Impact: a malformed CORS\_ORIGINS silently widens to \*; combined with credentials this is a misconfiguration hazard.- Confidence: Medium.- Remediation: fail closed (raise on unparseable origins); refuse \* when allow\_credentials=True.- Verification test: Settings(CORS\_ORIGINS="{bad json}") → expect validation error, not \["\*"\].F-07 — MEDIUM — Hard-coded default DB credentials and insecure default secret- Evidence: config.py:24 SECRET\_KEY="default-insecure-dev-secret-key-replace-in-production"; config.py:36 DATABASE\_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/...; alembic.ini:29 sqlalchemy.url = postgresql://postgres:postgres@...; .env.example:12,26.- Impact: insecure defaults ship to any environment that forgets to override .env. Violates R19 (no creds in code).- Confidence: High.- Remediation: no default for SECRET\_KEY/DATABASE\_URL in non-development; raise at startup; keep .env.example placeholders only.- Verification test: Settings(APP\_ENV="production", SECRET\_KEY=None) → raises.F-08 — MEDIUM — SSRF / arbitrary local file read in circle-rate ingestor- Evidence: circle\_rates.py:80-90 fetches self.source\_url (from --source CLI or CIRCLE\_RATE\_SOURCE\_URL) via httpx.AsyncClient(... follow\_redirects=True) with no host allowlist; circle\_rates.py:122-131 parse\_file(path) opens any path from --file.- Impact: internal-tool exposure; could be pointed at metadata endpoints (169.254.169.254) or read arbitrary files if the CLI is ever reachable.- Confidence: Medium.- Remediation: allowlist official hosts; constrain file paths to an approved directory; disable redirects or validate final host.- Verification test: pass --source http://169.254.169.254/ → expect rejection.F-09 — MEDIUM — .env.example out of sync with config; embedding-model mismatch- Evidence: config.py:44-57 defines CIRCLE\_RATE\_SOURCE\_URL/STATE/PILOT\_CITY/PILOT\_DISTRICT/INGESTION\_SCHEDULE\_CRON, LLM\_PROVIDER, EMBEDDINGS\_MODEL, VECTOR\_DB\_\*; .env.example documents none of the circle-rate vars (:38-45). EMBEDDINGS\_MODEL=sentence-transformers/all-MiniLM-L6-v2 (config) vs rag/embeddings.py:21 BAAI/bge-small-en-v1.5.- Impact: violates R19/CLAUDE §14.9; silent embedding-dimension drift (hard rule: don't silently change model identifiers).- Confidence: High.- Remediation: document all settings; unify the embedding model.- Verification test: test asserting every Settings field has a .env.example entry.F-10 — MEDIUM — Two parallel valuation pipelines and two ORM trees- Evidence: backend/app/property/{valuation,comps,gate}.py (playbook AVM) vs backend/app/valuation/{estimate,comps,confidence,outliers}.py (GEMINI engine); backend/app/database/models/\* (canonical) vs backend/app/models/\* (legacy stubs). Different price-type vocabularies (registered\_deed vs sale\_consideration) and different abstain reason codes.- Impact: invariant drift (F-01 exists only in the property/ path); maintenance risk; unclear source of truth.- Confidence: High.- Remediation: designate the valuation/+database/ path canonical (it is stricter); deprecate/remove the other or make it a thin adapter.- Verification test: dependency/import test asserting one engine is referenced by the API and agent.F-11 — MEDIUM — Duplicated dependency declarations; deleted backend/requirements.txt still referenced- Evidence: requirements.txt:1-81 contains two merged blocks (fastapi/pydantic/sqlalchemy pinned twice with different ranges, e.g. :2 vs :28); Makefile:16 and README reference backend/requirements.txt; backend/Dockerfile:18 COPY requirements.txt requirements-dev.txt ./ while backend/requirements.txt is deleted (git status).- Impact: non-reproducible/contradictory installs; Docker build reads a missing file ⇒ broken image build.- Confidence: High.- Remediation: single requirements source; restore or fix Dockerfile/Makefile.- Verification test: docker build ./backend (or pip install --dry-run -r requirements.txt) succeeds; assert no duplicate requirement names.F-12 — MEDIUM — No Alembic revision files- Evidence: migrations/ contains only env.py and script.py.mako; migrations/versions/ is absent (no files under migrations/ besides those two). ORM is complete (database/models/\*).- Impact: R15 unmet; a clean DB cannot be created; integration tests cannot run against a real schema.- Confidence: High.- Remediation: alembic revision --autogenerate -m "initial" and test upgrade/downgrade.- Verification test: alembic upgrade head on a clean PostGIS DB then alembic downgrade base (playbook SOP-1/SOP-12 requires a tested rollback).F-13 — MEDIUM — RAG layer implements out-of-scope functionality with fabricated content- Evidence: rag/seed\_corpus.py:24 sha256="rbi\_kfs\_2024\_hash" (non-hash), procedural "Section 3…" text; rag/sources.yaml:16 placeholder hash a1b2c3…; rag/embeddings.py:et al random-projection fallback; tests/evaluation/test\_retrieval\_gold\_set.py asserts Hit@5 ≥ 85% against that corpus.- Impact: violates R1 (fabricated regulatory text) and R22 (RAG explicitly out of scope this phase). Green RAG tests give false confidence.- Confidence: High.- Remediation: move RAG out of the India valuation deliverable or mark all synthetic content TODO-VERIFY; do not cite these as regulatory evidence.- Verification test: provenance test asserting every corpus doc’s sha256 matches a real fetched document.F-14 — LOW — Broad exception handling hides failures and leaks error text- Evidence: property\_agent.py:126-142 except Exception as e → abstain\_reason=f"unexpected\_agent\_error: {str(e)}"; valuation.py:40-41 bare except: return 100.0; circle\_rates.py:200.- Impact: masks real defects (turns crashes into "abstained"), and embeds raw exception text in output (potential info disclosure).- Confidence: Medium.- Remediation: catch specific exceptions; log with correlation id; use generic reason code.- Verification test: inject a non-provider failure and assert it surfaces as an error, not a silent abstain.F-15 — LOW — rows\_rejected accounting is unreachable (always 0)- Evidence: ingestion/provider.py:121-123 (if model is None: rows\_rejected += 1) but validate\_reference\_rate\_row/validate\_transaction\_row only ever return (model, None) or (None, quarantine) (validate.py:44,170,251); every manifest shows rows\_rejected: 0.- Impact: accounting semantics are misleading; the documented mutually-exclusive counting rules lack a real "rejected" category.- Confidence: Medium.- Remediation: either define a rejected path (e.g., structurally unusable rows) or drop the field from the invariant.- Verification test: assert no validator path returns (None, None); reconcile totals.F-16 — LOW — validate\_transaction\_row defaults a missing source\_url to http://local-source- Evidence: validate.py:248 source\_url=str(raw\_row.get("source\_url", "http://local-source")).- Impact: fabricates a provenance URL (R1/R5) instead of quarantining PROVENANCE\_MISSING as the reference-rate path does (validate.py:146-153).- Confidence: High.- Remediation: require source\_url; quarantine when absent.- Verification test: transaction row without source\_url → PROVENANCE\_MISSING quarantine.F-17 — LOW — Reference-rate unit semantics inconsistent across layers- Evidence: ingestion/validate.py:88 normalizes rate\_inr\_normalized to per sq ft; database/models/circle\_rate.py:24-... and api/circle\_rates.py expose rate\_per\_sqm; ingestion/circle\_rates.py:220 stores raw per\_sqm. API default property\_type="residential" (api/circle\_rates.py:36) vs data value residential\_flat.- Impact: an API consumer may read a per-sqft figure labeled/assumed per-sqm.- Confidence: Medium.- Remediation: name fields by basis and document the unit in the schema/OpenAPI.- Verification test: assert the served value’s unit matches its field name for a known fixture.F-18 — INFO — Instruction/artifact conflicts and missing deliverables- CLAUDE.md/GEMINI.md say no frontend/RAG/compliance this phase, but frontend/, rag/, compliance stubs exist (R22). README.md+docs/\* describe a US full-stack system, contradicting the India scope. AGENTS.md absent. .clinerules/\* located under data/regulatory\_docs/ instead of repo root. docs/PROGRESS.md, .clineignore, docs/playbook/, and the §15 scripts/reports are all missing (R21).F-19 — INFO — No Flask frontend and no ML model integration exist- The frontend is Next.js 14 (frontend/package.json), not Flask; there are no trained model artifacts — valuation is deterministic (weighted median) and RAG uses a random-projection fallback (rag/embeddings.py). Both are outside India scope; recorded so they are not assumed present.F-20 — Positive controls observed (no action)- Source approval gate enforced (registry.py:90-105, provider.py:54-60); provenance hashing (provider.py:32-35,83-84); canonical quarantine with reason codes (validate.py, sample quarantine file); protected-class proxy rejection (normalize.py:40-44,146-155); sensitive-data logging filter is attached (logging.py:39); no string-interpolated SQL anywhere (grep clean); state isolation enforced in both comp selectors (comps.py:44-49, valuation/comps.py:112-120); abstention + bounds gating (estimate.py:105-148; valuation.py:135-200).5. File-by-file coverage checklistFile / groupReviewedNotesCLAUDE.md, GEMINI.md, README.md, .env.example, .gitignore, requirements.txt, docker-compose.yml, Makefile, alembic.ini✅ backend/pyproject.toml, requirements-dev.txt, Dockerfile, .dockerignore✅F-11backend/app/main.py, core/{config,exceptions,logging}.py✅F-06,07,09,20api/{router,health,circle\_rates,auth,applications,documents,underwriting,compliance,reports}.py✅F-05,17property/{\_\_init\_\_,valuation,comps,normalize,gate,provider,data\_provider,jurisdictions,schemas,commands,playbook.md}✅F-01,02,14property/providers/{synthetic,assessor\_csv}.py✅F-01valuation/{\_\_init\_\_,comps,estimate,confidence,outliers,evaluation}.py✅ ingestion/{\_\_init\_\_,provider,registry,normalize,validate,deduplicate,quarantine,schemas,circle\_rates}.py✅F-04,15,16providers/{\_\_init\_\_,base,registry,up,maharashtra,karnataka,telangana}/…✅ database/{base,connection}.py, database/models/\*, database/repositories/\*✅F-12schemas/{\_\_init\_\_,property,transaction,source,valuation,circle\_rate,health}.py✅ agents/{\_\_init\_\_,property\_agent,credit\_agent,decision\_agent}.py✅F-01,14calculations/dti.py, compliance/rules.py, workflows/{state,nodes,underwriting\_graph}.py, models/{\_\_init\_\_,application}.py, security/auth.py✅US/placeholderrag/{chunking,embeddings,ingestion,reranker,retriever,schemas,seed\_corpus,vector\_store}.py, rag/sources.yaml✅F-13 (out of scope)tests/conftest.py, tests/{unit/test\_canonical\_schemas,unit/test\_circle\_rate\_ingestion,unit/test\_ingestion\_pipeline,unit/test\_multi\_state\_providers,unit/test\_property\_agent,unit/test\_valuation\_engine,unit/test\_config,unit/test\_exceptions,unit/test\_health}.py, integration/test\_db\_connection.py, evaluation/\*✅ (read)not executedmigrations/{env.py,script.py.mako}✅F-12scripts/{check\_sources,import\_dataset,setup\_dev}.py, scripts/README.md, data/{source\_readiness.csv,schema.md,DATA\_CARD.md}, all data/reference\_rates/\*.csv, data/raw/…, all manifests/\*.json, data/quarantine/\*.jsonl, data/processed/reference\_rates/\*.jsonl✅F-03data/{ground\_truth,sample\_documents,regulatory\_docs,test\_cases}/README.md, .gitkeep✅ docs/{architecture,api,compliance,evaluation}/overview.md, .clinerules/{architecture,coding,testing}.md✅F-18Not reviewed (documented gaps)File / groupReasonbackend/app/calculations/{dscr,fico,ltv,risk\_score,\_\_init\_\_}.pyUS scope — out of India auditbackend/app/compliance/{tila,respa,hmda,fnma\_fhlmc,fair\_lending,\_\_init\_\_}.pyUS scopebackend/app/document\_processing/\*US scopebackend/app/reports/\*US scopebackend/app/security/{encryption,permissions,\_\_init\_\_}.pyUS scopebackend/app/schemas/{application,document,report,underwriting,compliance}.pyUS scopebackend/app/models/{applicant,audit,credit,decision,document,property,risk}.pyUS scope / legacybackend/app/workflows/edges.pyplaceholderfrontend/\*\* (20 files)out of India scope; also F-19architecture/workflow.drawio, backend/app/property/build\_tracker.htmlnon-source artifacts, not readdata/processed/reference\_rates/\*.jsonl (full), some manifestssampled, not exhaustively diffed.env (root & worktree)intentionally unread (secrets); existence + gitignore confirmed.kilo/worktrees/tasteful-fender/\*\*excluded per instruction6. Requested approvals to complete dynamic verificationI can close the NOT\_RUN items only with your approval. Proposed read-only/non-destructive commands:1. cd backend && python -m pytest -q (tests; no data mutation — integration test only probes DB health and returns a bool).2. cd backend && ruff check . and mypy app.3. cd backend && alembic upgrade head on a disposable local PostGIS DB, then alembic downgrade base (to confirm F-12 and playbook SOP-12 rollback).4. docker compose config (config validation only) and a requirements.txt duplicate-name check.Static conclusions above do not depend on these; they would upgrade F-12/F-20 confidence and confirm the R20 testing requirement.Top priorities to remediate, in order: F-01 (synthetic leakage) → F-03 (provenance/fabrication) → F-02 (hard-coded index) → F-04 (silent drops) → F-05/F-07 (auth & secrets) → F-12 (migrations) → F-11 (build break).Want me to run the approved commands (#1–#4) now, or extend the review into the out-of-scope US/frontend files (F-19)

---

# Phase 2 — Remediation Status Log

## F-03 — Reference-rate provenance (HIGH) — REMEDIATED ✅

**Status:** Fixed and verified. Date: 2026-10-17.

### External source verification (authorized)
Fetched each dataset's previously-claimed snapshot URL:

| Dataset | Claimed snapshot URL | Result |
|---|---|---|
| UP Lucknow circle rates | https://igrsup.gov.in/igrsup/rates/lucknow/2024 | Not resolved (generic portal error page) |
| MH Mumbai ready reckoner | https://easr.igrmaharashtra.gov.in/easr/rates/mumbai/2024 | Not resolved (request timed out) |
| KA Bengaluru guidance values | https://kaveri.karnataka.gov.in/rates/bengaluru/2024 | Not resolved (landing page only) |
| TS Hyderabad market values | https://registration.telangana.gov.in/rates/hyderabad/2024 | HTTP 404 |

Conclusion: the datasets' claimed provenance is unverifiable, so they must not be labelled official/approved.

### Files changed
| File | Purpose |
|---|---|
| `data/reference_rates/*.csv` (4) | Replace fabricated deep official URLs with `local://synthetic/...`; add `[SYNTHETIC DEV FIXTURE - UNVERIFIED PROVENANCE]` notes |
| `data/raw/reference_rates/up_lucknow_rates_intake_raw.csv` | Same provenance correction |
| `data/source_readiness.csv` | 4 reference-rate rows `approved`→`pending_review`; TS `evidence_url` corrected; `next_action` records evidence |
| `data/DATA_CARD.md` | §2.1 relabelled "Unverified … (NOT approved)"; new §2.3 provenance verification table; §4 provenance rule strengthened; SHA-256 refreshed |
| `backend/app/providers/{up,maharashtra,karnataka,telangana}/provider.py` | `reference_rate_approved` True→False |
| `scripts/check_sources.py` | New `--verify-fixtures` (local/synthetic provenance) and `--verify-connectivity --timeout` |
| `backend/tests/unit/test_f03_data_provenance.py` | New regression tests (6) |
| `backend/tests/unit/test_multi_state_providers.py`, `test_ingestion_pipeline.py` | Assert the gate now blocks unverified sources; preserve normalisation coverage via an approved synthetic source |
| `data/processed/reference_rates/*.jsonl`, `data/processed/manifests/*.json` | Refreshed provenance/hashes |

### Regression tests added
`backend/tests/unit/test_f03_data_provenance.py`: sources not approved; gate blocks them; fixtures use local/synthetic provenance; DATA_CARD hashes match; DATA_CARD no longer claims "Approved … Snapshots"; `source_readiness.csv` is well-formed.

### Commands executed and results
| Command | Result |
|---|---|
| `.venv/Scripts/python.exe -m pytest backend/tests -q` | 101 passed (exit 0) |
| `.venv/Scripts/python.exe -m ruff check <F-03 files>` | exit 1 — 2 pre-existing findings only (0 introduced) |
| `../.venv/Scripts/python.exe -m mypy app` (from `backend/`) | exit 1 — 17 pre-existing errors, none in changed files |
| `.venv/Scripts/python.exe scripts/check_sources.py --verify-fixtures` | exit 0 — provenance check passed |

### Residual / next
- F-03 closed for the reference-rate layer.
- The four `source_readiness.csv` rows remain `pending_review` until an authorized export is obtained, hashed (`terms_snapshot_sha256`), and a named verifier signs off.
- Next Priority-2 item: **F-02** (hard-coded, unprovenanced market index).

## F-02 — Unprovenanced hard-coded market index — REMEDIATED ✅

**Status:** Fixed and verified. Date: 2026-10-17.

### What was wrong
`backend/app/property/valuation.py` hard-coded an RBI HPI series (`HPI_SERIES`, `CURRENT_HPI`), a
magic year-on-year growth constant (`rbi_hpi_yoy_growth_percent: 8.2`) and a silent `100.0`
fallback for any missing quarter. None of it carried a source, publication date, units or
verification status, yet the values were used to time-adjust production comparables.

### External source verification (authorized)
Not run to completion for the index: the RBI DBIE series was not fetched, so **no replacement
values were invented**. The legacy numbers are preserved only as an explicitly unverified fixture.

### Fix
| File | Change |
|---|---|
| `data/market_indices/rbi_hpi_urban_lucknow.json` | New versioned series carrying `source_name`, `source_url`, `publication_date`, `base_year`, `units`, `verification_status=unverified` and the legacy values as an explicitly UNVERIFIED dev fixture |
| `backend/app/property/market_index.py` | New `MarketIndexSnapshot` loader with an `is_verified` gate and period helpers; returns `None` (never a default) when absent/unparsable |
| `backend/app/property/valuation.py` | Removed `HPI_SERIES`, `CURRENT_HPI` and the `8.2` constant; loads the versioned series; **abstains from the HPI time adjustment** when the index is absent, unverified, or does not cover a comp quarter; flags `human_review_required`; reports index provenance in `market_indicators` |
| `data/source_readiness.csv` | New `market_index` row for the RBI HPI, `pending_review` |
| `data/DATA_CARD.md` | New §2.4 recording the F-02 provenance status and the promotion rule |
| `scripts/check_sources.py` | `--verify-fixtures` now also validates market-index provenance (`--market-index`) |
| `backend/tests/unit/test_f02_market_index.py` | New regression tests (11) |

### Behaviour after the fix
- Index absent → `market_index_unavailable` → adjustment abstained, `rbi_hpi_current=None`.
- Index present but unverified → `market_index_unverified` → adjustment abstained, output flagged for human review.
- Verified series with an uncovered comp quarter → `incomplete_index_coverage`, the missing period is
  recorded and there is **no `100.0` fallback** (the estimate equals the un-indexed estimate).
- Verified series, or an explicit test-only `allow_synthetic=True` opt-in, → adjustment applied.

### Regression tests
Missing file, unparsable file, unverified fixture, absent index, missing quarter (no default),
verified index enables adjustment, synthetic dev-fixture opt-in, helper guarantees, and a
source-level guard that `HPI_SERIES` / `CURRENT_HPI` / `118.2` / `8.2` no longer exist in the engine.

### Commands executed and results
| Command | Result |
|---|---|
| `.venv/Scripts/python.exe -m pytest backend/tests -q` | 112 passed (exit 0) |
| `.venv/Scripts/python.exe -m ruff check <F-02 files>` | exit 1 — 1 pre-existing SIM102 in `scripts/check_sources.py`; 0 introduced |
| `../.venv/Scripts/python.exe -m mypy app/property/market_index.py app/property/valuation.py` (from `backend/`) | 1 pre-existing error (`app/property/schemas.py:76`); changed files clean |
| `.venv/Scripts/python.exe scripts/check_sources.py --verify-fixtures` | exit 0 — fixture + market-index provenance passed |

### Residual (outside F-02 scope / not authorized)
- `backend/app/property/commands.py::market()` still returns hard-coded median PPSF/gap figures
  labelled `"source": "RBI HPI / Registration Department"` — a fabrication issue for F-13.
- `backend/app/property/jurisdictions.py` still declares `hpi_base_year="2022-23"` as a config default;
  tie it to the verification status once a verified export exists.
- The RBI DBIE export itself was not obtained (no network verification of HPI values was performed);
  the series stays a labelled unverified fixture until an authorized, hashed export is recorded.

## F-04 — Circle-rate ingestion silently drops invalid rows — REMEDIATED ✅

**Status:** Fixed and verified. Date: 2026-10-17.

### What was wrong
`backend/app/ingestion/circle_rates.py` had a second, divergent ingestion path that silently discarded
invalid rows: `_normalize_row` returned `None` and five `continue` sites dropped the row, while
`parse_records` swallowed any exception with `logger.warning("Skipping invalid circle rate row")`.
That violates R6 / hard-rule 13 ("rejected rows are logged with a reason, never silently fixed") and
diverged from the canonical provider pipeline (`provider.py`, `validate.py`).

### Fix
| File | Change |
|---|---|
| `backend/app/ingestion/circle_rates.py` | Parse methods now return a `ParseOutcome` carrying accepted rows **and** reason-coded rejections; `_normalize_row_with_reason` produces `MISSING_REQUIRED_FIELD` / `MISSING_PRICE` / `INVALID_DATE`; `validate_records` returns schema failures as rejections; new `ingest_html` / `ingest_file` emit `QuarantineRecord`s and an `IngestionRunAccounting` and write a `quarantine_<run_id>.jsonl` log; `run()` returns the accounted result; the silent `logger.warning("Skipping…")` path is gone |
| `backend/app/ingestion/quarantine.py` | Added reason code `MISSING_REQUIRED_FIELD` |
| `backend/app/ingestion/__init__.py` | Exported `ParseOutcome`, `CircleRateRejection`, `CircleRateIngestionResult` |
| `backend/tests/unit/test_f04_circle_rate_quarantine.py` | New regression tests (8) |
| `data/DATA_CARD.md` | §3.3 records that the no-silent-drop invariant now covers both ingestion paths |

### Row-accounting invariant
For every circle-rate run: `rows_received == rows_accepted + rows_quarantined + rows_duplicate + rows_rejected`
(enforced by `IngestionRunAccounting`). Regression tests assert this for CSV and HTML snapshots and
assert that invalid rows land in the quarantine JSONL with an explicit reason code.

### Regression tests
CSV missing-rate / bad-rate / bad-year / missing-locality rows → quarantined with the right reason codes;
over-long CSV row → quarantined; HTML short row + invalid row → quarantined; HTML page with no rate table
→ `IngestionError`; schema-validation failure → rejection (not swallowed); source guard that the
"Skipping invalid circle rate row" path no longer exists; backwards-compatible `parse_records` wrapper.

### Commands executed and results
| Command | Result |
|---|---|
| `.venv/Scripts/python.exe -m pytest backend/tests -q` | 120 collected, 0 failed (exit 0) — +8 vs. F-02 |
| `.venv/Scripts/python.exe -m ruff check <F-04 files>` | all checks passed (0 findings) |
| `../.venv/Scripts/python.exe -m mypy app` (from `backend/`) | 17 pre-existing errors, unchanged; no new errors |

### Residual (Priority 3 remainder)
- **F-15**, **F-16**, **F-17** — all addressed below.

## F-16 — Transaction validator fabricates a fallback source URL — REMEDIATED ✅

**Status:** Fixed and verified. Date: 2026-10-17.

### What was wrong
`backend/app/ingestion/validate.py` built transaction records with
`source_url=str(raw_row.get("source_url", "http://local-source"))`, inventing a provenance URL for a
row that had none (violating R1/R5) instead of quarantining it as the reference-rate path already does.

### Fix
`validate_transaction_row` now requires `source_url` and returns a `PROVENANCE_MISSING`
`QuarantineRecord` when it is absent; a present URL is preserved verbatim.

### Regression tests
`backend/tests/unit/test_ingestion_pipeline.py::test_transaction_validation_requires_source_url`:
missing `source_url` → `PROVENANCE_MISSING`; a real `source_url` still validates unchanged.

### Commands executed and results
| Command | Result |
|---|---|
| `.venv/Scripts/python.exe -m pytest backend/tests -q` | 121 collected, 0 failed (exit 0) |
| `.venv/Scripts/python.exe -m ruff check backend/app/ingestion/validate.py` | 6 pre-existing unused-import (F401) findings; 0 introduced |

## F-15 — `rows_rejected` accounting semantics — REMEDIATED ✅

**Status:** Fixed and verified. Date: 2026-10-17. Decision taken: reserved field + remove the dead branch.

### What was wrong
`provider.py` contained `if model is None: rows_rejected += 1` — an unreachable branch, because the
validators only ever return `(model, None)` or `(None, quarantine_record)`. The field was therefore
misleadingly always `0` with no documented meaning.

### Fix
| File | Change |
|---|---|
| `backend/app/ingestion/provider.py` | Removed the unreachable `rows_rejected` branch; replaced it with an explicit fail-loud guard if the validator contract is ever broken |
| `backend/app/ingestion/quarantine.py` | `rows_rejected` documented as a **reserved** field (still part of the invariant, `0` today) |
| `backend/tests/unit/test_ingestion_pipeline.py` | New `test_validators_never_return_none_none` — asserts every validator outcome is exactly one of `(model, None)` / `(None, quarantine)` for a matrix of reference-rate and transaction rows |

`rows_received == rows_accepted + rows_quarantined + rows_duplicate + rows_rejected` still holds (with
`rows_rejected == 0`), so the documented invariant in `GEMINI.md`/`CLAUDE.md` §4.6 is unchanged.

## F-17 — Reference-rate unit semantics inconsistent across layers — REMEDIATED ✅

**Status:** Fixed and verified. Date: 2026-10-17.

### What was wrong
`ingestion/validate.py` normalised into a generically named `rate_inr_normalized` (INR per square
**foot**) while the DB model / API exposed `rate_per_sqm` (INR per square **metre**), so a consumer
could read a per-sqft figure as per-sqm. The circle-rate lookup API also defaulted `property_type`
to `residential` while the canonical data value is `residential_flat`.

### Fix
| File | Change |
|---|---|
| `backend/app/schemas/transaction.py` | Contract field renamed `rate_inr_normalized` → `rate_inr_per_sqft`, with a description stating the square-foot basis (and that it is **not** per sq m) |
| `backend/app/database/models/reference_rate.py` | ORM attribute / DB column keep the historical name (no migration required); comment now states the INR-per-square-**foot** basis and points at the new contract name |
| `backend/app/database/repositories/reference_rate_repo.py` | Maps `record.rate_inr_per_sqft` → column `rate_inr_normalized`; upsert fixed to use the statement's `excluded` namespace |
| `backend/app/database/models/circle_rate.py`, `backend/app/schemas/circle_rate.py`, `backend/app/api/circle_rates.py` | `rate_per_sqm` documented in the model comment, the Pydantic field description, and the OpenAPI endpoint description; API `property_type` default aligned to `residential_flat` |
| `backend/app/ingestion/circle_rates.py` | New `DEFAULT_PROPERTY_TYPE = "residential_flat"`; ingestion default aligned with the API/data value; upsert fixed to use the statement's `excluded` namespace |
| `backend/app/providers/{up,maharashtra,karnataka,telangana}/provider.py` | Provider metadata `unit_conversion` strings updated to the new field name |
| `data/processed/reference_rates/*.jsonl` (5 files) | Regenerated with the `rate_inr_per_sqft` key |
| `data/schema.md` | Reference-rate field renamed with the unit basis documented; quarantine reason-code list updated for F-04 |
| `backend/tests/unit/test_f17_unit_semantics.py` | New regression tests (7) |

### Related latent bug found and corrected (not a claimed finding)
Both reference-rate and circle-rate upserts referenced `pg_insert.excluded.<col>` — but in SQLAlchemy
2.1 `pg_insert` is a *function*, so `excluded` is only available on the built **statement**
(`insert_stmt.excluded`). The old form raised `AttributeError` at runtime (never exercised because the
DB path is not covered by the test suite). Both upserts were rebuilt in the documented form and now
compile; verified with a statement-compilation check (no database required).

### Regression tests
`test_f17_unit_semantics.py`: contract field is `rate_inr_per_sqft` (old name absent) and documents the
foot basis; `rate_per_sqm` documents the metre basis; a known 54,000 INR/sq m fixture normalises to
≈5,016.76 INR/sq ft and is asserted **not** equal to the raw per-sqm value (unit matches the field
name); ingestion and API defaults both equal `residential_flat`; the ORM column retains its historical
name with a square-foot comment; generated processed fixtures use the new key.

### Commands executed and results
| Command | Result |
|---|---|
| `.venv/Scripts/python.exe -m pytest backend/tests -q` | 129 collected, 0 failed (exit 0) |
| `.venv/Scripts/python.exe -m ruff check <F-17 files>` | only pre-existing findings (unused imports, `B008`, `UP042`); 0 introduced |
| `../.venv/Scripts/python.exe -m mypy app` (from `backend/`) | 10 errors in 8 files — **down from 17** (the fixed upserts removed 7 pre-existing `attr-defined` errors); none in F-17 files |
| `.venv/Scripts/python.exe scripts/check_sources.py --verify-fixtures` | exit 0 (reference-rate + market-index provenance OK) |

### Governing-doc note
`GEMINI.md` / `CLAUDE.md` §4.5 still list `rate_inr_normalized` as the recommended field name. Those
files are the governing instructions and were **not** edited. The code contract now uses
`rate_inr_per_sqft`; the DB column keeps `rate_inr_normalized`. Recommend the owner ratify the rename in
the governing docs, or keep the mapping documented in `data/schema.md` (current state).

## Priority 3 — residual / follow-ups
- **F-12 (migrations):** renaming the physical `reference_rates.rate_inr_normalized` column to match the
  contract name requires an authorised Alembic migration; deferred (migrations are not authorised to run).
- **F-13 residuals** (out of Priority-3 scope): `commands.py::market()` hard-coded figures and
  `jurisdictions.py` `hpi_base_year="2022-23"` remain open.

---

# Priority 4 — API and configuration security — REMEDIATED ✅

**Status:** Fixed and verified. Date: 2026-10-17. Scope: F-05, F-06, F-07, F-08.

## Access-policy decision (prerequisite for F-05)
The intended public/private policy for the *currently live* surface was determined and written down in
`docs/security/access_policy.md`:

| Endpoint | Decision | Rationale |
|---|---|---|
| `GET /health` | **Public** | Liveness/readiness probe; boolean DB status only |
| `GET /circle-rates/lookup` | **Public reference data** | Government-notified circle rates only; no personal/confidential data |
| `GET /` | **Public** | Static service descriptor |
| `/auth/*`, `/applications/*`, `/documents/*`, `/underwriting/*`, `/compliance/*`, `/reports/*` | **Protected** | Borrower-adjacent; empty placeholders today |

No user-management system was invented. The decision is explicit, and liveness/reference-data endpoints
were not broken.

## F-05 — No authentication/authorization on any endpoint — REMEDIATED ✅

### What was wrong
Every router was mounted with no dependency and `app/security/auth.py` was an empty stub, so any future
borrower-adjacent endpoint would ship unauthenticated.

### Fix
| File | Change |
|---|---|
| `backend/app/security/auth.py` | Implemented `require_api_key` (FastAPI dependency, constant-time `hmac.compare_digest`) and a real `AuthService`; accepts `Authorization: Bearer <key>` or `X-API-Key`. **Fails closed**: `503` when `API_KEY` is unset, `401` when missing/invalid |
| `backend/app/security/rate_limit.py` | New best-effort per-process sliding-window limiter (`SlidingWindowRateLimiter`, `enforce_rate_limit`, `limiter_for`, `reset_rate_limiters`) |
| `backend/app/api/{auth,applications,documents,underwriting,compliance,reports}.py` | Each protected router now constructed with `dependencies=[Depends(require_api_key)]` — **protected by default**, so a newly added route cannot ship unauthenticated |
| `backend/app/api/circle_rates.py` | Public lookup carries `Depends(enforce_rate_limit)`; query params length/pattern-constrained; `404` detail no longer reflects raw input |
| `backend/app/api/router.py` | Public vs protected sets documented and grouped |
| `docs/security/access_policy.md` | New authoritative decision record (classification, enforcement, accepted risk, outbound policy) |

### Accepted risk (documented)
`/health` and `/circle-rates/lookup` return `200` without credentials — an accepted, documented risk
(non-sensitive reference data only). The remediation explicitly permits this provided the decision is
explicit and future endpoints are protected.

### Regression tests
`backend/tests/unit/test_f05_auth_access_policy.py` (15): the policy document exists and classifies the
live endpoints; protected routers carry `require_api_key` and public routers do not; the lookup route
carries the limiter; a mini protected app returns **503** unconfigured, **401** missing/invalid, **200**
for valid `Bearer` and `X-API-Key`; limiter window/reset/`429`/disable behaviour; `AuthService.verify`
semantics.

## F-06 — CORS wildcard fallback combined with credentials — REMEDIATED ✅

### What was wrong
`CORS_ORIGINS` silently returned `["*"]` for unexpected types, and `main.py` combined it with
`allow_credentials=True` (plus wildcard methods/headers).

### Fix
| File | Change |
|---|---|
| `backend/app/core/config.py` | `CORS_ORIGINS` validator now **fails closed**: unparseable JSON, non-list JSON, non-str/list types and empty values all raise. A model validator rejects `"*"` whenever `CORS_ALLOW_CREDENTIALS` is enabled (new setting). |
| `backend/app/main.py` | CORS middleware reads `CORS_ALLOW_CREDENTIALS` from settings; methods/headers are explicit allowlists instead of `["*"]` |

### Regression tests
`backend/tests/unit/test_f06_cors_config.py` (7): malformed JSON raises; unexpected type raises; empty
raises; `["*"]` + credentials raises; `["*"]` without credentials is allowed; comma-separated still parses;
the built app's `CORSMiddleware` never widens to `"*"` while credentials are enabled.

## F-07 — Hard-coded default DB credentials and insecure default secret — REMEDIATED ✅

### What was wrong
`SECRET_KEY` defaulted to a literal insecure string and `DATABASE_URL` to `postgres:postgres@localhost`;
`alembic.ini` committed a working DB URL.

### Fix
| File | Change |
|---|---|
| `backend/app/core/config.py` | `SECRET_KEY`/`DATABASE_URL` have **no usable default**. Development environments (`development`/`dev`/`local`/`test`/`testing`/`ci`) receive recognisable throwaway values; any other environment **raises at construction** unless both are set explicitly, must not use the development values, and `SECRET_KEY` must be ≥ 32 chars |
| `alembic.ini` | `sqlalchemy.url` left **blank** (still overridden at runtime by `migrations/env.py`); no credentials committed |
| `.env.example` | Rewritten with placeholders only (`SECRET_KEY=`, `DATABASE_URL=`); new F-05/F-06/F-08 settings documented. NOTE: this also advances F-09, which stays tracked under Priority 5 |

### Regression tests
`backend/tests/unit/test_f07_secrets_config.py` (10): production without `SECRET_KEY`/`DATABASE_URL`
raises; development values rejected in production; short secret rejected; explicit secure values accepted;
development keeps throwaway defaults; `alembic.ini` has no `postgres:postgres@`; `.env.example` has no
working secret or credential.

## F-08 — SSRF / arbitrary local file read in circle-rate ingestor — REMEDIATED ✅

### What was wrong
`fetch_raw` fetched `self.source_url` with `follow_redirects=True` and no host allowlist, and
`parse_file` opened any path supplied via `--file`.

### Fix
| File | Change |
|---|---|
| `backend/app/ingestion/circle_rates.py` | New `validate_ingestion_url` (HTTPS-only; IP literals in private/loopback/link-local/reserved/multicast/unspecified ranges are **blocked even when allowlisted**; host must be on `CIRCLE_RATE_ALLOWED_HOSTS`; **empty allowlist ⇒ refuse to fetch**) and `resolve_intake_path` (path must resolve inside `CIRCLE_RATE_INTAKE_DIR`; traversal rejected; suffix allowlist). `fetch_raw` no longer follows redirects (a `3xx` raises). `parse_file`/`ingest_file` resolve through the intake guard. CLI gains `--intake-dir` / repeatable `--allow-host` |
| `backend/app/core/config.py` | New `CIRCLE_RATE_ALLOWED_HOSTS` (default empty ⇒ fail closed) and `CIRCLE_RATE_INTAKE_DIR` |
| `backend/app/ingestion/__init__.py` | Exports `validate_ingestion_url`, `resolve_intake_path` |

**No official host was assumed** — because F-03 established that provenance is unverified, the allowlist
is operator-supplied and empty by default (fail closed) rather than hard-coding a guessed `igrsup.gov.in`.

### Regression tests
`backend/tests/unit/test_f08_ingestion_ssrf.py` (20, all offline — no request reaches internal
infrastructure or a metadata endpoint): non-HTTPS/empty/off-allowlist/empty-allowlist rejected; allowlisted
host and subdomain accepted; metadata/loopback/private/IPv6 addresses rejected even when allowlisted;
`fetch_raw` refuses the metadata URL, refuses a `302` (with `follow_redirects=False` asserted) and returns
the body for an allowlisted host via a mocked transport; `resolve_intake_path` rejects traversal and
unsupported suffixes; `parse_file`/`ingest_file` reject files outside the intake dir and read files inside
it; an empty allowlist is the secure default and Settings normalises an empty value to `[]`.

## Priority 4 — commands executed and results
| Command | Result |
|---|---|
| `.venv/Scripts/python.exe -m pytest backend/tests -q` | 181 collected, 0 failed (exit 0) — 129 pre-existing + 52 new |
| `.venv/Scripts/python.exe -m pytest <F-05..F-08 test files> -v` | 52 passed (0.64s) |
| `.venv/Scripts/python.exe -m ruff check <all touched files>` | **All checks passed** (0 findings in the changed set) |
| `../.venv/Scripts/python.exe -m mypy app` (from `backend/`) | 9 errors in 7 files — down from 10 in 8 at the end of Priority 3; **none** in any file touched by this changeset |
| `.venv/Scripts/python.exe scripts/check_sources.py --verify-fixtures` | exit 0 (reference-rate + market-index provenance unchanged) |

## Priority 4 — residual / follow-ups
- **In-process rate limiting is best-effort only:** it is per-process and resets on restart. Production
  should additionally enforce limits at an edge/gateway; documented in `docs/security/access_policy.md`.
- **Redirect policy is fail-closed, not followed-and-validated:** a `3xx` from an approved host is
  rejected outright. If an official portal turns out to require redirects, re-validate each hop's host
  against the allowlist rather than enabling blind following.
- **`API_KEY` is a single shared secret, not an identity provider:** sufficient to stop unauthenticated
  access to the placeholder routers, but a real identity provider is required before borrower-adjacent or
  personal data is exposed.
- **F-09/F-10/F-11/F-12** remain under Priority 5 (`.env.example` was already synchronised as a
  side-effect of F-07).
- **Dependency vulnerability scan / Docker build / Alembic migrations** were not authorised and remain
  unverified.

---

# Priority 5 — Maintainability and deployment — REMEDIATED (F-12 blocked, documented) ✅

**Status:** F-09, F-10, F-11 fixed and verified; F-12 remains **blocked and documented**. Date: 2026-10-17.

## F-09 — `.env.example` out of sync; embedding-model mismatch — REMEDIATED ✅

### What was wrong
`.env.example` omitted the circle-rate/LLM/vector-store settings, and `Settings.EMBEDDINGS_MODEL`
(`sentence-transformers/all-MiniLM-L6-v2`) disagreed with the identifier the embedding service uses
(`BAAI/bge-small-en-v1.5`), risking silent embedding-model drift.

### Fix
| File | Change |
|---|---|
| `.env.example` | Already synchronised during F-07; `EMBEDDINGS_MODEL` value corrected (below) |
| `backend/app/core/config.py` | `EMBEDDINGS_MODEL` default changed to **`BAAI/bge-small-en-v1.5`** |

**Deliberate model-identifier change (documented, not silent).** The old value disagreed with both the
governing playbook (`§ stack`: *sentence-transformers (bge-small-en-v1.5), 384 dims*) and
`backend/app/rag/embeddings.py` (`EmbeddingService(model_name="BAAI/bge-small-en-v1.5", dimension=384)`).
Both models are 384-dimensional, so there was no dimension break — only an identifier mismatch. The
config was aligned to the playbook/RAG value. No RAG code was modified and no model was downloaded.

### Regression tests
`backend/tests/unit/test_f09_settings_env_sync.py` (5): every `Settings` field is documented in
`.env.example`; no unknown settings are documented; placeholders-only secrets; the configured
embedding identifier equals `EmbeddingService(...).model_name`; and the identifier matches the playbook.

## F-10 — Two parallel valuation pipelines and two ORM trees — REMEDIATED ✅

### What was wrong
No source of truth was declared between `app/property/*` (playbook AVM) and `app/valuation/*` (GEMINI
engine), or between `app/database/models/*` (canonical) and `app/models/*` (legacy US stubs).

### Decision (owner-ratified)
`app/property/*` + `app/database/models/*` are **canonical**. Rationale: `app.property.valuation` is the
only engine wired into a live entry point (`PropertyAgent`) and it carries the CRITICAL F-01 synthetic
gate and F-02 index gating; promoting the other engine would temporarily drop those controls.
`app/valuation/*` is retained as the **stricter migration target** (not deprecated); `app/models/*` is
marked **deprecated**.

### Fix
| File | Change |
|---|---|
| `docs/architecture/canonical_pipeline.md` | New decision record: evidence (AST import scan), designation, consequences, migration path |
| `backend/app/models/__init__.py` | Deprecation marker: docstring notice + runtime `DeprecationWarning` on import |
| `backend/app/property/__init__.py` | Docstring records canonical status |
| `backend/app/valuation/__init__.py` | Docstring records "migration target, not the current canon" |
| `backend/tests/unit/test_f10_canonical_pipeline.py` | New guard tests (7) |

No files were deleted (Priority-5 instruction), and no runtime behaviour changed.

### Regression tests
`test_f10_canonical_pipeline.py` (7): the decision record exists and names both trees; `PropertyAgent`
uses the canonical engine; **no** live entry point imports `app.valuation` (so exactly one engine is
live); `migrations/env.py` targets `app.database.models`; no live entry point imports the legacy tree;
importing `app.models` emits a `DeprecationWarning`.

## F-11 — Duplicated dependency declarations; broken Dockerfile reference — REMEDIATED ✅

### What was wrong
`backend/requirements.txt` contained **two merged blocks**, pinning `fastapi`/`uvicorn`/`pydantic`/
`pydantic-settings`/`sqlalchemy`/`alembic`/`httpx` twice with conflicting ranges, and declaring two
competing PostgreSQL drivers (`psycopg2-binary` and `psycopg[binary]`). Test/lint tooling was duplicated
between the runtime and dev manifests.

### Fix
| File | Change |
|---|---|
| `backend/requirements.txt` | Rewritten as a **single de-duplicated runtime manifest** (one constraint per package); `psycopg2-binary` kept (matches `migrations/env.py`, which builds a `postgresql://` sync URL); the competing `psycopg[binary]` removed |
| `backend/requirements-dev.txt` | Now extends the runtime manifest (`-r requirements.txt`) and holds test/lint tooling only (de-conflicted ranges) |
| `backend/Dockerfile` | `COPY requirements.txt ./` — no longer copies a file the image does not install; `-r requirements.txt` is the authoritative manifest |
| `backend/tests/unit/test_f11_dependency_manifest.py` | New static manifest tests (6) |

`Makefile` already referenced `backend/requirements.txt` + `backend/requirements-dev.txt`; both now exist,
and the test asserts every Makefile reference resolves. Per owner decision, no `docker build` was run —
the reported defect class (duplicate/conflicting declarations, missing referenced file) is caught
statically instead.

### Regression tests
`test_f11_dependency_manifest.py` (6): no duplicate packages in either manifest; the dev manifest extends
the runtime one with no re-declaration; exactly one Postgres driver; every Dockerfile `COPY`/`-r`
reference exists in the build context; every Makefile manifest reference exists.

### Residual
`app/rag/ingestion.py` imports `yaml` (PyYAML), which is not declared in any manifest (RAG is out of
scope for this phase). Recorded as an open residual rather than silently adding a dependency.

## F-12 — No Alembic revision files — BLOCKED (documented) ⛔

Generating and testing the initial revision requires a **live PostGIS database** (autogenerate +
`alembic upgrade head` / `alembic downgrade base`), which is **not authorised**. Per owner decision, F-12
stays blocked rather than guessed at.

### Prepared without a database
| File | Change |
|---|---|
| `scripts/check_migrations.py` | New R21 deliverable: a static, side-effect-free readiness checker (validates `env.py`/`script.py.mako`/`alembic.ini`, confirms Alembic targets the canonical ORM tree, confirms `sqlalchemy.url` embeds no credentials, inventories revision files and heads, and reports "ready" only when exactly one head exists) |
| `migrations/versions/.gitkeep` | Creates the `versions/` directory that `alembic revision` requires |
| `backend/tests/unit/test_f12_migration_checker.py` | New tests (3) |

`python scripts/check_migrations.py` currently reports the configuration as OK and readiness as **NO**
("no revision files — F-12 open"), exiting non-zero so the blocker is never silent.

### What is still required (needs authorisation)
1. A disposable local PostGIS database.
2. `alembic revision --autogenerate -m "initial"` against the canonical metadata.
3. Verify `alembic upgrade head` then `alembic downgrade base` on that disposable DB.

## Priority 5 — commands executed and results
| Command | Result |
|---|---|
| `.venv/Scripts/python.exe -m pytest backend/tests -q` | **202 collected, 0 failed (exit 0)** — 181 → 202 (+21) |
| `.venv/Scripts/python.exe -m ruff check <all touched files>` | **All checks passed** (0 findings) |
| `../.venv/Scripts/python.exe -m mypy app` (from `backend/`) | 9 errors in 7 files — unchanged; none in touched files |
| `.venv/Scripts/python.exe scripts/check_migrations.py` | config OK, **Ready: NO**, exit 1 (F-12 open, as documented) |
| `.venv/Scripts/python.exe scripts/check_migrations.py --config-only` | exit 0 |

**Per-file new test counts:** `test_f09_settings_env_sync.py` 5, `test_f10_canonical_pipeline.py` 7,
`test_f11_dependency_manifest.py` 6, `test_f12_migration_checker.py` 3.

## Priority 5 — residual / follow-ups
- **F-12 remains open** and is blocked on an authorised disposable PostGIS database (see above).
- **RAG `yaml` dependency** (`backend/app/rag/ingestion.py`) is undeclared and out of scope.
- **No `docker build`, no dependency vulnerability scan** — not authorised.
- **Legacy trees retained, not deleted:** `app/models/*` (deprecated, warns on import) and
  `app/valuation/*` (migration target) — removal would require the migration path in
  `docs/architecture/canonical_pipeline.md` to be completed first.

---

## F-01 — Synthetic valuation data leakage (CRITICAL) — REMEDIATED ✅

**Status:** Fixed and verified. Date: 2026-10-17.

### What was wrong
`backend/app/agents/property_agent.py` fell back to `SyntheticProvider()` by default, and `backend/app/property/comps.py` filtered only by price type and property type without checking `is_synthetic`. As a result, fabricated comps could enter production valuation estimates without explicit opt-in, violating `CLAUDE.md` §2.1 and §15.4.

### Fix
| File | Change |
|---|---|
| `backend/app/agents/property_agent.py` | `PropertyAgent` now requires an injected provider (default construction raises `ValueError`); passing a `SyntheticProvider` requires explicit `allow_synthetic=True` (test-only); propagates `evidence_is_synthetic` flag |
| `backend/app/property/comps.py` | `ComparableSalesAnalyzer.select_comps` checks `is_synthetic` discriminator; excludes synthetic comps unless `allow_synthetic=True`; records `synthetic_excluded` count in metadata |
| `backend/app/property/valuation.py` | `PropertyValuationEngine` abstains with `synthetic_evidence_not_permitted` when only synthetic comps are present in production mode; flags `human_review_required=True` and `evidence_is_synthetic=False` |
| `backend/tests/unit/test_property_agent.py` | 7 dedicated regression tests (`test_f01_*`) validating provider requirements, exclusion gates, abstention on synthetic-only evidence, and clean separation |

### Regression tests executed
`backend/tests/unit/test_property_agent.py::test_f01_*`:
- `test_f01_property_agent_requires_injected_provider` (PASSED)
- `test_f01_synthetic_provider_requires_explicit_optin` (PASSED)
- `test_f01_analyzer_meta_reports_excluded_synthetic` (PASSED)
- `test_f01_synthetic_only_evidence_yields_no_production_estimate` (PASSED)
- `test_f01_mixed_evidence_excludes_synthetic_comps` (PASSED)
- `test_f01_approved_real_evidence_produces_estimate` (PASSED)
- `test_f01_synthetic_optin_marks_output_discriminator` (PASSED)

### Commands executed and results
| Command | Result |
|---|---|
| `.venv/Scripts/python.exe -m pytest backend/tests/unit/test_property_agent.py -k test_f01 -v` | 7 passed (exit 0) |
| `.venv/Scripts/python.exe -m pytest backend/tests/unit/test_property_agent.py -v` | 28 passed (exit 0) |
| `.venv/Scripts/python.exe -m pytest backend/tests -q` | 231 collected, 0 failed (exit 0) — current full-suite total |

---

# Priority 6 — Scope and reliability — F-14 REMEDIATED, F-18 PARTIAL, F-13 out of scope

**Status:** F-14 fixed and verified; F-18 partially closed (deliverables added, conflicts documented);
F-13 explicitly out of scope; F-19/F-20 no action. Date: 2026-10-17.

## F-14 — Broad exception handling hides failures and leaks error text — REMEDIATED ✅

### What was wrong
`property_agent.py` converted any unexpected error into an abstain whose `abstain_reason` and audit
`note` embedded `str(e)` (raw exception text). `property/comps.py` swallowed every exception while
computing a recency weight and silently substituted a neutral value. (The other two lines named in the
audit — `valuation.py` bare `except: return 100.0` and `circle_rates.py` silent row drop — were already
removed by F-02 and F-04 respectively.)

### Fix
| File | Change |
|---|---|
| `backend/app/agents/property_agent.py` | Added `UNEXPECTED_AGENT_ERROR` reason code and `_correlation_id()`; the last-resort handler now logs the full traceback server-side against a correlation id and returns only the generic reason code + correlation id — no raw exception text reaches the output, shared state or audit details |
| `backend/app/property/comps.py` | Narrowed the catch to `(ValueError, TypeError)` and added a `logger.warning` so the neutral-recency fallback is observable instead of silent |
| `backend/app/property/normalize.py` | Narrowed the date-parse catch to `(ValueError, TypeError)` (the rejection stays reason-coded) |

### Regression tests
`backend/tests/unit/test_f14_error_handling.py` (8): the unexpected-error path yields the generic reason
code with no leaked text in the output **or** the audit trail; the failure is still logged with a
traceback and correlation id; the comps fallback logs a warning and keeps weights finite; the
normalizer reason-codes an unparseable date; and a static AST guard asserts the in-scope property
modules contain no bare/`except Exception` swallows (the agent keeps exactly one documented
last-resort handler).

## F-18 — Instruction/artifact conflicts and missing deliverables — PARTIAL (documented) ◑

### R21 deliverables created
| Deliverable | Purpose |
|---|---|
| `scripts/check_database.py` | PostGIS readiness: static config check by default; `--connect` performs a read-only `SELECT 1` + expected-table probe. Never writes or migrates |
| `scripts/validate_dataset.py` | Validates every on-disk processed row (`ReferenceRateCreate`), manifest (`IngestionRunAccounting`) and quarantine record (`QuarantineRecord` + known reason codes) |
| `scripts/build_dataset.py` | Canonical, **gated** dataset builder: dry-run by default, `--write` to persist; fails closed (exit 2) on any unapproved source — it never bypasses the F-03 approval gate |
| `scripts/run_verification.py` | Runs the approved checks (pytest, ruff on remediation files, mypy* , `check_sources`, `check_migrations`, `validate_dataset`, `check_database`) and can emit `reports/verification_report.md` |
| `reports/implementation_audit.md` | What changed and why |
| `reports/verification_report.md` | Generated from real command output |
| `docs/PROGRESS.md` | Status, blockers, deviations and the R21 deliverable index |

`scripts/check_migrations.py` (F-12) and `scripts/check_sources.py` (F-03) were created earlier in this
remediation and complete the R21 script set. `mypy` is run in the report as informational, because the
concurrent remediation of other priorities left 9 pre-existing type errors outside this scope (none in
files touched here). Not claimed as clean until those are addressed: the report labels it `INFO`.

### Conflicts resolved by documentation (not by editing governing/user files)
| Conflict | Resolution |
|---|---|
| `.clinerules/*` lives under `data/regulatory_docs/` rather than the repo root | Left in place — the governing instructions reference that path; recorded in `docs/PROGRESS.md` |
| `README.md` / `docs/*` describe a US full-stack system | Not rewritten (out of India scope; unrelated user content); the India scope is stated in `docs/PROGRESS.md` and this report |
| `AGENTS.md`, `.clineignore`, `docs/playbook/` absent | Recorded as absent; nothing invented (the playbook is `backend/app/property/playbook.md`) |
| `frontend/`, `rag/`, compliance stubs exist despite "not this phase" | Left untouched (R22) |
| `scripts/import_dataset.py` persists unconditionally | Retained (not deleted per instruction); superseded in practice by the safer gated `build_dataset.py` |

### Regression tests
`backend/tests/unit/test_f18_deliverables.py` (21): every R21 deliverable exists; each script has a
clean `--help`; `validate_dataset.py` passes on disk; `check_database.py` defaults to static mode and
redacts credentials; `build_dataset.py` never bypasses the approval gate (fails closed with a gate
reason when sources are unapproved); `run_verification.py --list` reports the expected checks; and the
governing `.clinerules` directory remains in place.

## F-13 — RAG fabricated content — OPEN (out of scope, documented) ⛔
`backend/app/rag/*` is explicitly excluded from this phase (R22). No RAG file was modified. The
fabricated regulatory text/hashes and the out-of-scope RAG evaluation remain recorded here so they are
never cited as regulatory evidence. A supporting residual: `backend/app/rag/ingestion.py` imports
PyYAML, which is not declared in any manifest.

## F-19 / F-20 — informational — NO ACTION
F-19 (no Flask frontend / no ML model — the frontend is Next.js) and F-20 (positive controls observed)
are informational; nothing was built and no controls were changed.

## Priority 6 — commands executed and results
| Command | Result |
|---|---|
| `.venv/Scripts/python.exe -m pytest backend/tests -q` | **231 collected, 0 failed (exit 0)** — 202 → 231 (+29) |
| `.venv/Scripts/python.exe -m ruff check <remediation files>` | **All checks passed** (0 findings) |
| `../.venv/Scripts/python.exe -m mypy app` (from `backend/`) | 9 errors in 7 files — unchanged; none in touched files |
| `.venv/Scripts/python.exe scripts/validate_dataset.py` | exit 0 (5 processed files / 38 rows, 6 manifests, 1 quarantine file / 4 rows, 0 errors) |
| `.venv/Scripts/python.exe scripts/check_database.py` | exit 0 (static; 10 expected tables; credentials redacted; no connection) |
| `.venv/Scripts/python.exe scripts/build_dataset.py` | exit 2 — **fails closed**: all four fixture sources are `pending_review` (F-03 gate enforced, nothing written) |
| `.venv/Scripts/python.exe scripts/run_verification.py --write reports/verification_report.md` | exit 0 — all blocking checks PASS (mypy INFO) |

**Per-file new test counts:** `test_f14_error_handling.py` 8, `test_f18_deliverables.py` 21.

## Priority 6 — residual / follow-ups
- **F-12 remains blocked** on an authorised disposable PostGIS database (see Priority 5).
- **F-18 is only partially complete**: the R21 scripts/reports exist, but the conflicting `README.md`
  and the misplaced `.clinerules` were documented rather than changed, and `AGENTS.md` / `.clineignore`
  do not exist.
- **RAG `yaml` dependency** remains undeclared and out of scope.
- **No Docker build, no dependency vulnerability scan** — not authorised.

---

## Priority 7 — F-12 unblocked; owner ratifications RESOLVED (2026-10-17)

**Status:** **F-12 REMEDIATED**. This section supersedes the earlier "F-12 — BLOCKED (documented)"
entry (which was accurate when written) and closes the two ratifications that were listed as outstanding
in the F-17 and F-05 sections.

### Owner decisions applied
1. **F-12 authorised** against the **disposable** local database `mortgage_underwriting_test` only. The
   live `mortgage_underwriting` database was never touched.
2. **F-17 rename ratified**: the physical `reference_rates.rate_inr_normalized` column is renamed to
   `rate_inr_per_sqft`; `GEMINI.md` section 4.5 and `data/schema.md` were updated to name the new field.
3. **F-05 access policy ratified**: `docs/security/access_policy.md` is the authoritative policy, now
   linked from `README.md`.

### F-12 — what changed
| File | Change |
|---|---|
| `migrations/env.py` | Added an autogenerate `include_object` filter that excludes PostGIS-managed objects (`spatial_ref_sys`, the `tiger` and `topology` schemas) so application migrations never manage PostGIS internals. Removed a pre-existing unused `import os`. |
| `migrations/script.py.mako` | Modernised the revision template (PEP 604 unions, `collections.abc.Sequence`) so generated revisions are lint-clean. |
| `migrations/versions/e35561efe721_initial_schema.py` | New initial revision: 10 `create_table` + 40 `create_index`; zero PostGIS-managed objects. |
| `backend/app/database/models/reference_rate.py` | ORM attribute/column renamed `rate_inr_normalized` -> `rate_inr_per_sqft`. |
| `backend/app/database/repositories/reference_rate_repo.py` | Direct mapping to `rate_inr_per_sqft`; removed two pre-existing unused imports. |
| `backend/app/database/models/property.py` | Geometry column set to `spatial_index=False`; the explicit GIST `Index("idx_property_record_location", ...)` is now the single spatial index. Removed pre-existing unused imports. |
| `backend/tests/unit/test_f12_migration_checker.py` | +4 tests (3 -> 7) pinning the revision shape. |
| `backend/tests/unit/test_f17_unit_semantics.py` | Assertion updated: the ORM column now uses the unambiguous `rate_inr_per_sqft` name. |

### Hazards found and fixed while doing F-12 (both would have been destructive)
1. **PostGIS internals.** The first `alembic revision --autogenerate` run emitted **47 destructive
   `op.drop_table` operations** (24 `tiger.*` tables/objects, the `topology` schema, and
   `spatial_ref_sys`) and also tried to *create* `spatial_ref_sys`. The `include_object` filter removes
   all of them; the committed revision contains none.
2. **Duplicate spatial index.** `property_records.location` was declared with GeoAlchemy2's automatic
   spatial index (`spatial_index=True`, default) **and** an explicit GIST index, so `upgrade` failed with
   `relation "idx_property_records_location" already exists`. `spatial_index=False` makes Alembic the
   single owner of the explicitly-named `idx_property_record_location`.

### F-12 — commands executed and results
| Command | Result |
|---|---|
| `docker exec mortgage-postgres psql -c "CREATE DATABASE mortgage_underwriting_test TEMPLATE template_postgis"` | exit 0 |
| `alembic revision --autogenerate -m "initial schema"` | exit 0 -> `migrations/versions/e35561efe721_initial_schema.py` |
| `alembic upgrade head` | exit 0 -> 10 application tables + `alembic_version`; `reference_rates.rate_inr_per_sqft` present; `idx_property_record_location` present; `property_records.location` type `geometry` |
| `alembic downgrade base` | exit 0 -> only `alembic_version` remains (0 rows); PostGIS intact (`spatial_ref_sys` = 8,500 rows) |
| `alembic upgrade head` (repeat) | exit 0 -> 11 tables; both directions are repeatable |
| `psql -d mortgage_underwriting -tAc "SELECT count(*) FROM pg_tables ..."` | unchanged — the live database was never touched |
| `python scripts/check_migrations.py` | **Ready: YES** (1 revision `e35561efe721`, 1 head), exit 0 |
| `python -m pytest backend/tests -q` | **235 collected, 0 failed (exit 0)** |
| `python -m ruff check <remediation files + migrations/>` | all checks passed |
| `python scripts/run_verification.py --write reports/verification_report.md` | exit 0 — 8 checks, all blocking PASS |

### Residual after Priority 7
- **F-13 (RAG)** remains out of scope and unmodified; the undeclared `pyyaml` import remains a residual.
- **F-18** remains partially complete (see Priority 6 residual).
- The `rate_inr_per_sqft` rename was applied to the **disposable** database only; rolling it out to a
  real environment means running the initial revision there (out of scope here).
- `README.md` is still US-oriented; it now contains a pointer to the ratified access policy.