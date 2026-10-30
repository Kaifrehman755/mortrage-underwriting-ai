# Playbook Gap Analysis

**Project:** `mortrage-underwriting-ai`
**Playbook:** `backend/app/property/playbook.md`
**Date:** 2026-10-25
**Mode:** initial gap review, followed by a first remediation slice on 2026-10-25.
**Deliverable:** prioritized mapping of every playbook area to the current repository state.

> **Status update (2026-10-25):** the compliance/RAG P0 items below have been remediated in code.
> Implemented: compliance output contract (`backend/app/compliance/schemas.py`), deterministic engine
> and versioned config, eight India starter rules, `ComplianceAgent`, `/compliance`/`/evidence`/
> `/missing`/`/review`/`/approve`/`/sources` commands, fail-closed `/market`, RAG approval gate,
> unapproved synthetic seed metadata, Postgres/pgvector evidence persistence, a SHA-256 raw-document
> store, bronze fingerprints, and migration `a7c9e2f4b6d8` for the evidence/finding/bronze tables.
> Threshold rules still abstain because production thresholds remain `verified: false`. Still open:
> owner-approved real sources (real hashes/terms/review dates), live source ingestion and a gold-set
> approved active index, canonical property/valuation table renames, and release tooling. See
> `docs/PROGRESS.md` and `docs/operations/evidence-store.md` for the current status.

---

## 1. Executive summary

The **property valuation core is substantially complete** and is the strongest part of the repo:

- comparable retrieval interface + synthetic/CSV providers;
- India normalization and rejection logging;
- comp selection with step widening, similarity weights, weighted-median PPSF, bootstrap interval, abstain logic;
- HPI provenance gate with abstention instead of an invented index;
- typed `ValuationOutput` with `is_estimate=True`, estimate-or-abstain validation and human-review escalation;
- property agent + shared state + in-memory audit events;
- multi-state jurisdiction packs and state-isolation tests;
- Alembic initial migration and PostGIS integration tests;
- a passing **378-test** suite, clean `ruff`, clean `mypy`, plus live PostGIS/pgvector integration
  tests against the local database.

The **compliance and evidence side now has a deterministic engine, evidence contract, command set,
and database persistence**. The synthetic RAG corpus remains test-only and unapproved; real
owner-approved sources and reviewed thresholds are still absent by design.

The **database/source-governance layer now includes** `market_indicator`, `raw_record`,
`jurisdiction`, `reg_document`, `reg_chunk`, and `compliance_finding`, along with the playbook's
approval-record fields and constraints in `data_sources`. The remaining schema deviation is the
canonical property/valuation table naming and field set (see P1-7).

### Highest-risk findings

| # | Risk | Why it matters |
|---|---|---|
| 1 | Compliance module is six `pass` stubs | No rule can run, no finding can be produced, no evidence can be attached. Invariants 3 and 7 are unenforced. |
| 2 | RAG corpus is fabricated text with placeholder hashes, marked `approved: true` | Directly violates hard rule 1 ("never fabricate regulatory text / hashes / section numbers") and open finding F-13. |
| 3 | `GuardrailGate` is never called | The invariant checker exists but nothing enforces it at an agent or API boundary. |
| 4 | `/market` returns hard-coded, fabricated figures | Violates invariant 1 and the "market facts are retrieved, never modelled" rule. |
| 5 | No `ComplianceOutput` schema and no evidence-less-flag rejection | Invariant 3 has no schema-level or database-level test. |

---

## 2. Verification baseline

Commands run for this review:

| Check | Result |
|---|---|
| `pytest backend/tests -q` | all 378 tests pass, including live PostGIS/pgvector integration |
| `ruff check backend/app` plus new persistence/migration tests | clean |
| `mypy app` from `backend/` | clean (162 source files) |
| live external source fetch | not performed |
| database migration | applied to local `mortgage_underwriting` only; no production database touched |
| object-store smoke test | live MinIO-compatible local container: put/read verified by SHA-256 |

The passing suite is **not** evidence that the playbook is complete: the RAG tests pass against a
synthetic corpus, and there are no compliance tests at all.

---

## 3. P0 gaps — correctness and safety

### P0-1. Compliance is entirely stubbed

**Playbook:** Sections 8, 14.1, 16.6, Prompt P4.
**Status:** remediated in code; real-source thresholds remain unverified.

Evidence:

- `backend/app/compliance/rules.py` — `ComplianceRuleEngine` is a `pass` class.
- `backend/app/compliance/tila.py`, `respa.py`, `hmda.py`, `fnma_fhlmc.py`, `fair_lending.py` — all `pass` classes.
- `backend/app/agents/compliance_agent.py` — `ComplianceAgent` is a `pass` class.
- `backend/app/schemas/compliance.py` — request/response models are empty placeholders.
- `backend/app/api/compliance.py` — router with no endpoints.

Missing per playbook:

- the eight India starter rules: `KFS-001`, `LTV-001`, `RERA-001`, `TITLE-001`, `VAL-001`,
  `KYC-001`, `FAIR-001`, `DATA-001`;
- required-input declaration per rule;
- deterministic check functions;
- `cannot_verify` + `missing_information` on absent inputs;
- evidence retrieval per affected requirement;
- versioned thresholds/deadlines in config (not code);
- `no_issue_detected` / `potential_issue` / `cannot_verify` only — never "compliant";
- four tests per rule (no issue, potential issue, missing data, empty retrieval).

### P0-2. RAG corpus is fabricated and marked approved

**Playbook:** Sections 3b, 9 (P2/P3), 14.1, 18.2; hard rules 1, 11.
**Status:** remediated in code; real sources still unapproved (F-13 partial).

Evidence:

- `backend/app/rag/seed_corpus.py:34`, `:59`, `:80`, `:101`, `:117`, `:136`, `:157`, `:180` use
  placeholder "hashes" such as `"rbi_kfs_2024_hash"` and `"rera_act_2016_hash"`.
- The same file contains hand-written statutory text presented as RBI/RERA/SARFAESI/KYC/IBBI
  source text. It has not been verified against the official publishers.
- `backend/app/rag/sources.yaml:16-17`, `:32-33`, `:48-49`, `:64-65`, `:80-81`, `:96-97`,
  `:112-113`, `:128-129` mark every document `approved: true` with fake 64-character hashes and
  `approved_by: "Lead Compliance Officer"`.
- `backend/app/rag/schemas.py:31` defaults `RegDocument.approved` to `True`.
- `backend/app/rag/retriever.py` never filters on `approved`; it will return any ingested chunk.
- `backend/app/rag/retriever.py:97` hard-codes `version_or_date="2026-10-01"` instead of using the
  document's version/effective date, so even a real document would be cited incorrectly.
- The gold-set test (`backend/tests/evaluation/test_retrieval_gold_set.py`) measures Hit@5 against
  this fabricated corpus, so a green test is not evidence of regulatory accuracy.

Note: `DocumentIngestionPipeline.ingest_document_text()` overwrites `doc_metadata.sha256` with the
hash of the text it was handed. That proves integrity of the fabricated fixture, not origin. It does
not fix the provenance problem.

> **Current state (post-remediation):** `sources.yaml` now reports zero approved sources and
> `TODO-VERIFY` hashes; the seed corpus is marked `synthetic_test_fixture`; retrieval excludes
> unapproved chunks by default. The bullets above are retained as the pre-remediation audit record.

### P0-3. Invariant 3 and invariant 7 have no enforcement

**Playbook:** Section 1 invariants 3 and 7; Section 10; Definition of Done.
**Status:** remediated (schema validator, `GuardrailGate`, and DB check constraint).

Evidence:

- No `ComplianceOutput` (or finding) schema exists with a validator requiring `evidence_refs` when
  `status == "potential_issue"`.
- `backend/app/property/schemas.py:167-168` stores `evidence` and `compliance` as
  `list[dict[str, Any]]`, so nothing is validated.
- `GuardrailGate` (`backend/app/property/gate.py`) checks invariants 2, 4, 5 and 8 only. It never
  checks evidence presence (3) or wording (7), and `grep` shows it is **not called anywhere** in
  `backend/app`.
- No test named for invariant 3 or 7 exists. The test suite names invariants 1, 2, 4, 5, 6 and 8.
- The database has no `compliance_finding` table and no
  `CHECK (status = 'cannot_verify' OR cardinality(evidence_refs) > 0)`.

### P0-4. `/market` returns fabricated numbers

**Playbook:** Sections 7.8, 14.6, 14.7; invariant 1.
**Status:** remediated; `/market` now abstains without persisted indicators.

`backend/app/property/commands.py:153-167` returns:

- `median_registered_ppsf: 5200.0`
- `median_asking_ppsf: 5600.0`
- `gap_percent: 7.69`
- `source: "RBI HPI / Registration Department"`
- `period: "2026-Q3"`

These are constants with no source, period or retrieval provenance. The real engine already
computes market indicators separately in `PropertyValuationEngine._compute_market_indicators()`;
the command should read persisted indicators or abstain.

### P0-5. Retrieval does not enforce source approval or scope

**Playbook:** Sections 3b, 15.4, 18.2; hard rule 11.
**Status:** remediated in code (in-memory and Postgres stores enforce approval/scope).

- `GuidelineRetriever.retrieve()` accepts `state_code` and `loan_date`, but there is no `approved`
  check, no `access_mode` check, and no source-registry lookup.
- `VectorStoreManager` is an in-memory `dict` (`backend/app/rag/vector_store.py:20-23`); there is
  no pgvector, no tsvector/GIN index, no HNSW index, and no persistence across processes.
- State isolation and effective-date filtering are implemented in memory
  (`vector_store.py:60-85`), which is good logic, but it is not the database-level guarantee the
  playbook requires.

---

## 4. P1 gaps — missing playbook functionality

### P1-1. No compliance rule engine, config or rule packs

**Playbook:** Sections 8, 14.1, 15.2, 16.6.
**Status:** missing.

Needed:

- `backend/app/compliance/engine.py` that runs rules, attaches evidence, validates, and never flags
  without evidence.
- `backend/app/compliance/rules/` with one module per rule family and a national/state split.
- `backend/app/compliance/rules/states/up/` (and later other states) for state-specific rules.
- A versioned `rule_set_version` and threshold config copied from retrieved text.
- A regression set of fixture cases per SOP-6.

### P1-2. No `ComplianceOutput`, evidence linkage or shared-state contract

**Playbook:** Sections 1, 4, 8, 14.7; Prompt P1.
**Status:** missing.

Missing fields/objects:

- `ComplianceOutput` with `finding_id`, `case_id`, `rule_id`, `rule_set_version`, `status`,
  `severity`, `affected_requirement`, `evidence_refs`, `missing_information`, `explanation`,
  `human_review_required`.
- `EvidenceItem` with `source_name`, `version_or_date`, `section_or_page`, `retrieval_ref`,
  snippet, `index_version`, `retrieved_at`, `score` (the RAG schema exists but is not wired into a
  finding).
- Validation: `status == "potential_issue"` requires at least one evidence ref.
- Shared state should hold typed `evidence` and `compliance` objects, not `dict[str, Any]`.

### P1-3. No compliance agent or audit integration

**Playbook:** Section 9 (P7), Section 16 SOP-7/SOP-8.
**Status:** missing.

`ComplianceAgent` must:

- read subject, loan data and property output from shared state;
- run rules with evidence retrieval;
- write `evidence`, `compliance` and `missing_information` keys;
- set `needs_human` when any finding is `cannot_verify`, or `potential_issue` with high severity;
- emit an audit event with actor, node, input digest, output digest and versions;
- never use an LLM to decide flags, severity or values.

### P1-4. RAG is not persisted in Postgres/pgvector and has no raw-file store

**Playbook:** Sections 2, 4, 16 SOP-3.
**Status:** implemented in code and verified against local PostGIS/pgvector; real approved-source
ingestion and active-index promotion remain open.

Implemented:

- `reg_document` and `reg_chunk` tables (with `embedding vector(384)`, generated `tsv`, HNSW and GIN).
- `scope`, `state_code`, `effective_from`, `effective_to`, `index_version`.
- S3-compatible raw-document storage with SHA-256 (MinIO SDK; local filesystem fallback).
- Idempotent database upsert by document SHA-256 and chunk natural key.
- `RAG_ACTIVE_INDEX_VERSION` config; blank until an approved gold-set gate passes.
- SQL-level approval/scope/effective-date/index-version filtering in `PostgresVectorStore`.

Still missing:

- A source fetch/clean pipeline for official PDFs/XML.
- Owner approval of any real source and a real active `index_version`.

The current RAG pipeline is in-memory only and cannot meet SOP-3's "re-run same sha256 adds no
duplicates" or "switch active index_version" requirements across processes.

### P1-5. Embedding model is not actually bge-small

**Playbook:** Section 2; Section 16 SOP-1.
**Status:** partial / dev-only.

- `backend/app/rag/embeddings.py` attempts `sentence-transformers` and silently falls back to a
  deterministic random projection if the package is absent.
- `sentence-transformers` is not installed in the current environment; the production runtime is
  declared in `backend/requirements-rag.txt`. `EmbeddingService` now fails closed in
  `APP_ENV=production` instead of silently using the deterministic fallback.
- `pyyaml` was added to `backend/requirements.txt`. `.env.example` now selects `pgvector` and no
  longer conflicts with the database design.
- Python in the venv is 3.11, while the playbook targets 3.12.

### P1-6. Loan-officer command set and roles are incomplete

**Playbook:** Section 14.7; Section 16 SOP-7/SOP-8.
**Status:** partial.

Implemented (`backend/app/property/commands.py`): `/intake`, `/valuate`, `/comps`, `/market`,
`/explain`, `/escalate`.

Missing:

- `/compliance`, `/evidence`, `/missing`, `/review`, `/approve`, `/sources`.
- Role enforcement: loan officer cannot approve; compliance reviewer can review/approve; admin
  manages sources.
- Approval blocked when any unresolved high-severity finding remains.
- Every command writes an audit event and returns a plain-language summary.
- `/explain` currently summarises only property facts/estimate; it has no findings or
  evidence sections, and it is not protected from later mutation by a separate service boundary.

### P1-7. Database schema diverges from the playbook

**Playbook:** Sections 4, 14.4, 15.3, 18.2, 19.3.
**Status:** evidence/finding/bronze tables implemented; canonical property/valuation naming still
divergent.

The initial migration had 10 tables. Follow-on revision `a7c9e2f4b6d8` now adds the playbook's
evidence/finding/bronze tables and source approval/freshness columns.

Added tables:

- `market_indicator`
- `raw_record`
- `jurisdiction`
- `reg_document`
- `reg_chunk`
- `compliance_finding`

Added columns/constraints:

- `data_source`: `approved_by`, `approved_at`, `terms_snapshot_sha256`, `review_due`,
  `decision_note`, `access_mode`, `supports_transactions`, `supports_guideline_values`,
  `supports_land_records`, `refresh_interval_days`, `last_attempt_at`, `last_success_at`,
  `last_error`; the `approved_needs_record` and access-mode constraints.
- `raw_record`: `record_type`, `record_fingerprint`, `UNIQUE (source_id, record_type,
  record_fingerprint)`.
- New evidence tables include `scope`/`state_code` FKs to `jurisdiction`, and the database check
  `status = 'cannot_verify' OR cardinality(evidence_refs) > 0`.

Still divergent:
- `valuation_run`: playbook fields `estimate`, `interval_low`, `interval_high`,
  `confidence_level`, `method`, `n_comps`, `comp_ids`, `dispersion`, `abstain_reason`,
  `is_estimate`; the canonical ORM uses `estimate_inr`, `lower_bound_inr`, `upper_bound_inr`,
  `status`, `reason_codes`, `method_version`, `dataset_cutoff` instead.
- `property`: playbook fields `address_norm`, `geo`, `beds`, `baths`, `living_area_sqft`,
  `lot_size_sqft`, `year_built`; canonical ORM uses `property_records` with different field names.
- `comparable_sale`: playbook table; canonical ORM uses `property_transactions`.
- `reference_rate` and `circle_rate` both exist as separate tables, creating two
  representations of the same reference-rate concept.
- No `state_code` foreign key to a `jurisdiction` table.
- No `is_estimate` column in the database.

The playbook does allow adaptation for India, but its explicit contract says to use the field
names in the design. The current code cannot satisfy a direct field-level conformance check.

### P1-8. Bronze layer, fingerprints and source freshness are missing

**Playbook:** Sections 14.5, 19.3; SOP-4, SOP-5.
**Status:** implemented for schema and repository; live collectors remain open.

- `raw_record` table and raw-document object store exist; Docker Compose includes S3-compatible
  storage.
- `record_fingerprint` and `UNIQUE (source_id, record_type, record_fingerprint)` dedupe exist.
- `record_type` separation (`registered_transaction`, `guideline_value`, `land_record`, `listing`,
  `survey`) is enforced by a database check.
- Per-source `last_attempt_at`, `last_success_at`, `last_error`, `refresh_interval_days` columns exist;
  no live collector updates them yet.
- Source freshness fields are available to `DATA-001`; production freshness policy still needs owner
  approval.
- The CSV reference-rate ingestion has quarantine/accounting; the property `raw_record` bronze
  repository now exists, but no live government collector is wired to it.

### P1-9. Source approval records are not in the database

**Playbook:** Sections 18.2, 19.3; SOP-2.
**Status:** implemented in the database and RAG schema; CSV registry reconciliation still open.

`backend/app/database/models/source.py` stores the approval record required by the playbook. The
database check `ck_data_source_approved_needs_record` rejects an approved row without it, and the
migration fail-closes any pre-existing approved row that lacks one.

Still open:

- `data/source_readiness.csv` does not yet carry `approved_by`, `approved_at`,
  `terms_snapshot_sha256` or `review_due` columns.
- `backend/app/rag/sources.yaml` reports zero approved sources and `TODO-VERIFY` hashes; it is
  consistent with fail-closed behaviour but still needs owner-approved content.
- The RAG registry and CSV approval gate are not yet one reconciled source of truth.

### P1-10. Multi-state packs are incomplete

**Playbook:** Section 15.2, Section 18.4.
**Status:** partial.

`backend/app/property/jurisdictions.py` packs exist for UP, MH, KA and TS with statuses and
bounding boxes, but the playbook's pack contract also requires:

- RERA portal URL and registration portal URL (verified);
- state-specific guideline-value name and unit (partially present);
- local land units with official conversions;
- boundary file and localities file;
- collector reference and rule-pack reference;
- state regulatory sources;
- `min_comps` overrides for thin markets (partially present via `min_comps_estimate`);
- a `jurisdiction` DB row with `config` and `config_version`.

The packs are Python objects, not the YAML/DB configuration the playbook describes.

### P1-11. Unsupported state handling is inconsistent

**Playbook:** Sections 15.4, 19.4; invariant 4.
**Status:** partial.

`get_jurisdiction()` raises `ValueError` for an unknown state. In
`backend/app/agents/property_agent.py`, that `ValueError` is caught by the generic
`except Exception` boundary and converted to `abstain_reason="unexpected_agent_error"` rather than
the playbook's explicit "state not supported" outcome. It still escalates, so it is safe in
direction, but the reason code is wrong and loses the intended semantics.

---

## 5. P2 gaps — quality, release and documentation

### P2-1. Test gaps for the playbook's "tests that matter"

**Playbook:** Section 10; Definition of Done.

| Required test | Current state |
|---|---|
| Retrieval gold-set Hit@5 | present, but against fabricated corpus |
| Empty result on out-of-scope query | present |
| Version filter by loan date | date filter exists in memory; no test named for it |
| Each rule: pass / fail / missing data / empty retrieval | impossible — no rules |
| Finding without evidence rejected at schema and DB level | missing |
| Valuation abstains under 3 comps | present |
| Interval never returned with fewer than 5 | present |
| Estimate unchanged when only market indicators change | missing |
| Provider failure returns error + human case | present |
| Fairness: proxy columns fail a feature allow-list | only free-text proxy scan; no feature allow-list |
| Determinism: same inputs/versions give identical outputs | no valuation determinism test |
| Invariant 3 named test | missing |
| Invariant 7 named test | missing |
| End-to-end cases: healthy, outage, <3 comps, empty retrieval, stale source, protected-class term | property-side cases exist; empty-retrieval/stale-source/compliance E2E cases do not |

### P2-2. Valuation uses a fixed reference date, not the loan date

**Playbook:** Sections 7.1, 7.7, 15.4.5.
**Status:** partial.

- `ComparableSalesAnalyzer.__init__` defaults `reference_date=date(2026, 10, 10)`
  (`backend/app/property/comps.py:34`).
- Recency weighting uses that fixed date.
- `select_comps()` does not enforce the playbook's sold-within-6/12-months rule; the synthetic
  provider applies `months`, but `AssessorCsvProvider` ignores `months`.
- No "stale comps" abstain reason exists, even though the playbook lists stale data as an abstain
  trigger.
- `SharedCaseState.loan_data` is an untyped dict; there is no canonical `loan_date` used for
  evidence or valuation as-of logic.

### P2-3. `survey` is accepted as an estimate input

**Playbook:** Section 14.2 / hard rule 9.

`backend/app/property/comps.py:59` includes `"survey"` in the valuation-eligible price types.
The playbook says valuation uses registered and valuer rows first and that asking prices only feed
indicators. It does not clearly authorise survey rows as estimate inputs without validation.
This needs an explicit policy decision, not silent inclusion.

### P2-4. Audit events are in-memory only

**Playbook:** Section 1 (audit), Section 9 (P7), Section 11.

`PropertyAgent` appends an `AuditEvent` to `SharedCaseState.audit_trail`, which lives in the
in-process `LoanOfficerCommandHandler.cases` dict. There is no persistence, no hash chain and no
audit service. The legacy `backend/app/models/audit.py` is a stub and is not in the canonical
migration. The playbook says the hash chain belongs to the audit service; that service is not
present.

### P2-5. No backtest script or release gate

**Playbook:** Section 7, Section 9 (P6), SOP-12.

- `PropertyValuationEngine.run_backtest()` exists as a method.
- There is no `scripts/backtest.py` (or equivalent) to run it on fixtures and print MAPE and
  interval coverage.
- `scripts/run_verification.py` does not run a valuation backtest, retrieval gold set, or
  compliance regression set.
- No release note records `rule_set_version`, `index_version`, `model_version`.
- No SOP-12 demo of healthy / abstain / provider-outage cases.

### P2-6. Repository documentation is incomplete or contradictory

**Playbook:** Section 17, Section 11.

- `docs/playbook/` does not exist; the playbook is one 1,200-line file at
  `backend/app/property/playbook.md`, contrary to Section 17.1's split-file guidance.
- `.clinerules/` is under `data/regulatory_docs/.clinerules/`, not the repo root.
- `README.md` still describes a US full-stack mortgage system and a Phase 1-7 roadmap, not the
  India property scope.
- `docs/PROGRESS.md:3` says "No RAG, compliance, frontend or US-mortgage work", which directly
  contradicts the playbook's compliance/RAG phases. This scope conflict must be resolved by the
  owner before implementation.
- `docs/compliance/overview.md` describes US statutes (TILA/RESPA/HMDA/FNMA) and says compliance is
  "planned", not the India rule set.
- No India README covering sources, versions, thresholds and known limits (DoD item).
- No `.clineignore`, no `AGENTS.md` (already recorded as absent in `docs/PROGRESS.md`).

### P2-7. Runtime services do not match the playbook stack

**Playbook:** Section 2.
**Status:** remediated.

`docker-compose.yml` now starts:

- PostGIS + pgvector Postgres (`docker/postgres/Dockerfile`);
- Redis;
- an S3-compatible object store (Chainguard MinIO build, because upstream MinIO images were removed
  in September 2026).

`pgvector`, `minio`, and `pyyaml` are declared in `backend/requirements.txt`, and `.env.example`
documents `VECTOR_DB_TYPE=pgvector`, `RAG_ACTIVE_INDEX_VERSION`, and the object-store settings.

### P2-8. Synthetic labeling is incomplete across the stored contract

The in-memory `ValuationOutput` carries `evidence_is_synthetic` and `ComparableRecord` carries
`is_synthetic`. But the canonical DB tables (`property_transactions`, `valuation_runs`) have no
synthetic discriminator. If these outputs are persisted, the playbook's "synthetic rows are
labelled in every output" requirement is not guaranteed at the storage layer.

---

## 6. Playbook phase checklist (Section 17.4)

| Step | Task | Status | Notes |
|---|---|---|---|
| 1 | Environment and Docker setup | done (local) | PostGIS + pgvector, Redis, S3-compatible storage in Compose; no production deployment |
| 2 | Schemas and migration | done (evidence) | evidence/finding/bronze migration applied; canonical property/valuation naming still divergent |
| 3 | Source registry and regulatory ingestion | partial | RAG corpus unapproved; no real fetch/clean |
| 4 | Retrieval and evidence builder | done (code) | Postgres/pgvector hybrid retrieval with approval/scope/date/index filters; no approved real index |
| 5 | Provider interface, fixtures, loaders | done | synthetic + CSV providers; provider failure raises |
| 6 | Cleaning pipeline (India) | mostly done | INR/area/BHK/pincode/bbox/outliers; bronze repository now exists; no live collector |
| 7 | Valuation | done (property core) | selection, weighted median, bootstrap, abstain, confidence, backtest method |
| 8 | Compliance rules | done (code) | eight India rules; validated thresholds remain `verified: false` |
| 9 | Agents and shared state | done (code) | property + compliance agents; audit remains in-memory |
| 10 | Loan officer commands and roles | done (code) | 12-command set with role checks; `/market` abstains |
| 11 | Multi-state pack and isolation tests | partial | 4 packs; isolation tests; packs incomplete vs 15.2 |
| 12 | Test gaps and release | partial | 378 tests; compliance/invariant/source-freshness tests added; backtest/release-note/E2E tests still open |

---

## 7. Invariant coverage matrix (Section 1)

| Invariant | Status | Evidence / gap |
|---|---|---|
| 1. Never fabricate; no data means abstain | done (code) | property path abstains; RAG corpus is test-only/unapproved; `/market` abstains; real sources still absent |
| 2. Market facts and estimates separate | done | `ComparableRecord` vs `ValuationOutput`; test `test_invariant_2...` |
| 3. Flag without evidence rejected | done | `ComplianceOutput` validator, `GuardrailGate`, DB check constraint, and invariant-3 tests |
| 4. Failure/low confidence to human | done (property + compliance) | property invariant-4 tests; compliance `cannot_verify` forces review |
| 5. No protected-class proxies | partial | free-text proxy scan + test; no feature allow-list/schema enforcement |
| 6. LLM explainer cannot change flags/estimate | partial | property `explain` test; no compliance explainer/service boundary |
| 7. "Potential issue for review", not legal conclusion | done (contract) | output wording validator and tests; reviewer workflow still minimal |
| 8. Rules as of loan date; stale source alert | done (code) | Postgres filters effective dates; `DATA-001` consumes source freshness; production policy unapproved |

---

## 8. What is already working (do not rewrite)

- `backend/app/property/comps.py` — comp selection, step widening, similarity weights, asking-price
  exclusion, state isolation, synthetic exclusion.
- `backend/app/property/valuation.py` — weighted median, bootstrap 80% interval, dispersion and
  confidence logic, abstain reasons, separate market indicators, HPI provenance gate.
- `backend/app/property/schemas.py` — `ValuationOutput` validators enforce `is_estimate=True`,
  estimate-or-abstain, and low-confidence human review.
- `backend/app/property/normalize.py` — INR/lakh/crore, sq ft/sqm/sq yd/gaj, BHK, pincode,
  bounding box, protected-term check, reject logging.
- `backend/app/property/provider.py` + providers — abstract provider, `ProviderUnavailable`,
  synthetic fixtures, CSV loader.
- `backend/app/agents/property_agent.py` — injected provider gate, synthetic opt-in, provider
  failure handling, shared-state separation, audit event digests.
- `backend/app/property/jurisdictions.py` — four state packs and unsupported-state error.
- `backend/app/ingestion/` — quarantine with reason codes, row-accounting invariant, source
  approval gate, dedupe, SHA-256 snapshot hash.
- `migrations/versions/e35561efe721_initial_schema.py` — 10 canonical tables + PostGIS index.
- `migrations/versions/a7c9e2f4b6d8_playbook_evidence_and_bronze.py` — evidence/finding/bronze
  tables, source approval record, pgvector/HNSW/GIN, and evidence-required check.
- `backend/app/rag/postgres_store.py` — pgvector + tsvector hybrid retrieval with SQL-level approval,
  scope, effective-date, and index-version filters.
- `backend/app/rag/raw_store.py` — SHA-256 S3/MinIO and local raw-document stores.
- `backend/app/ingestion/bronze.py` — deterministic PII-free record fingerprints and idempotent
  bronze inserts.
- `backend/app/database/repositories/source_repo.py` — source attempt/success/failure recording,
  bounded errors, stale-source queries, and a compact freshness summary.
- `backend/tests` — 378 passing tests, including live PostGIS/pgvector integration, F-01/F-02/F-03/
  F-04/F-10/F-12/F-14/F-17 regressions, and property invariants.
- `scripts/check_sources.py`, `validate_dataset.py`, `check_migrations.py`,
  `check_database.py` — existing governance/verification tooling.

---

## 9. Recommended completion order

> This was the pre-remediation plan. Items 2-7 and 9 have since been implemented or partially
> implemented as recorded above; the remaining work is owner approval, live ingestion, release
> tooling, and the canonical schema deviation.

1. **Resolve the scope conflict first.** Decide whether the playbook's compliance/RAG sections
   supersede `GEMINI.md` and `docs/PROGRESS.md` ("no RAG/compliance this phase"). Without that
   decision, implementation is working against contradictory instructions.
2. **Remove the fabricated RAG material from any trusted path.** Mark the seed corpus as
   test-only/unapproved, remove fake `approved: true` metadata, and make retrieval fail closed when
   no approved source exists. Do this before adding compliance evidence on top of it.
3. **Add the evidence contract.** `ComplianceOutput` + `EvidenceItem` linkage + schema validator
   + database `CHECK` + named invariant-3 test.
4. **Build the rule engine and the eight India starter rules**, with versioned config thresholds
   and four tests per rule.
5. **Implement `ComplianceAgent` and wire `GuardrailGate`** into the agent boundary.
6. **Move RAG to Postgres/pgvector + MinIO**, with approved-source filtering, real `effective_from`
   / `effective_to`, idempotent ingestion and an active `index_version`.
7. **Add bronze/fingerprint/freshness and source-approval columns**; reconcile
   `source_readiness.csv` with `sources.yaml`.
8. **Complete the command set and roles**; fix `/market` to read real indicators or abstain.
9. **Close the DB contract gaps** (`market_indicator`, `jurisdiction`, `raw_record`,
   `reg_*`, `compliance_finding`) and decide whether to rename canonical tables to the playbook
   names or document a formal deviation.
10. **Release:** backtest script, invariant 3/7 tests, determinism test, stale-source test,
    E2E cases, README, DoD sign-off and version record.

---

## 10. Decisions needed from the owner

1. **Scope authority:** Does the playbook's India compliance/RAG scope replace the "no RAG /
   compliance" instruction in `GEMINI.md` and `docs/PROGRESS.md`?
2. **Source authorization:** Which regulatory documents and property sources are actually approved,
   with a signed checklist per Section 18.2? Without this, the correct behaviour is to keep
   `approved=false` and return `cannot_verify`.
3. **RAG storage:** Confirm pgvector in the existing Postgres (playbook recommendation) vs the
   current in-memory store and `.env.example`'s `VECTOR_DB_TYPE=chromadb`.
4. **Embedding runtime:** Install and pin `sentence-transformers` + `BAAI/bge-small-en-v1.5`, or
   formally accept a lexical fallback for development only.
5. **Canonical schema:** Keep the GEMINI canonical ORM names (`property_records`,
   `property_transactions`, `valuation_runs`) as a documented deviation, or migrate to the
   playbook's `property`, `comparable_sale`, `valuation_run` names and fields.
6. **Survey price type:** Is a `survey` row eligible for the estimate, or indicators only?
7. **State rollout:** Which state is the first live/pilot state after UP, and what is its data tier
   (Section 15.5)?

---

*This report now records the remediation implemented on 2026-10-25. No source approval, real
regulatory hash, threshold value, or production data was invented. The only database migration was
applied to the local development database; nothing was committed or pushed.*
