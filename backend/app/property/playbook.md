# Execution Playbook: Property Valuation, Compliance and RAG

Built from your Member 4 brief and Property\_valuation\_system\_design\_v2.html

## 1. What you are building

Three modules that share one contract: **market facts, model estimates and regulatory evidence are always stored and reported separately**, and anything uncertain goes to a human.

```
subject property + loan data
        |
        +--> Property agent:   provider -> normalize -> comps -> estimate (+interval or abstain)
        |
        +--> Compliance agent: rules -> RAG retrieval -> evidence package -> flags
        |
        v
   Guardrail gate -> shared case state (market_facts | model_output | evidence | compliance | needs_human)
```

Your design file defines eight invariants. Treat them as acceptance tests, not prose:

1. Never fabricate MLS or property data; no data means abstain and escalate.
2. Market facts and model estimates live in separate fields and report sections.
3. A flag without an evidence reference is rejected by validation.
4. Any failure or low confidence goes to a human, never to a guess.
5. No protected-class proxies as valuation features.
6. The LLM explainer cannot change flags, severity or the estimate.
7. Output says "potential issue for review", never a legal conclusion.
8. Rules apply as of the loan date; stale sources raise an alert.

Your design also fixes the contracts you must emit: Comparable record, Valuation output (is\_estimate=true), Evidence item, Compliance output, and the Shared case state. Use those field names exactly.

## 2. Tech stack

| Layer | Choice | Why |
| --- | --- | --- |
| Language | Python 3.12 | Best ecosystem for RAG and data work |
| API / models | FastAPI, Pydantic v2 | Contracts become validated schemas |
| Orchestration | LangGraph (or plain functions first) | Matches the agent graph in your design; checkpointing |
| Primary DB | PostgreSQL 16 | Facts, estimates, findings, audit |
| Vector store | pgvector (HNSW index) in the same Postgres | One database to run; join evidence to findings in SQL |
| Geo | PostGIS | Distance from subject, radius search |
| Migrations / ORM | SQLAlchemy 2 + Alembic | Versioned schema |
| Cache | Redis | Provider response cache with TTL (design B-fixes) |
| Raw file store | MinIO (S3 compatible) | Original PDFs/HTML snapshots with sha256 |
| Embeddings | sentence-transformers, BAAI/bge-small-en-v1.5 (384 dims) | Free, local, good quality |
| Reranker (optional) | BAAI/bge-reranker-base | Skip under load, as your design says |
| Keyword search | Postgres tsvector | Hybrid search catches exact section numbers |
| Parsing | PyMuPDF, pdfplumber, BeautifulSoup, trafilatura, lxml | PDFs, HTML, XML |
| HTTP | httpx + tenacity (retries) | Polite fetching with backoff |
| Valuation math | pandas, numpy, scipy, statsmodels, scikit-learn | Weighted medians, bootstrap, regression |
| Testing | pytest, hypothesis, pytest-postgresql or testcontainers | Property-based tests for invariants |
| Quality | ruff, mypy, pre-commit | Keeps shared repo clean |
| Runtime | Docker Compose (postgres, redis, minio, api) | Same setup for every teammate |
| LLM (explainer/router only) | Claude API | Wording only; never decides flags or values |

Start simple: Postgres + pgvector + local embeddings. You can run everything on a laptop with no paid service.

## 3. Data sources

### 3a. Property data (authorized only)

Your brief says "authorized comparable-property data" and "never fabricate". That has a practical consequence: **do not scrape Zillow, Redfin, Realtor.com or MLS portals.** Their terms prohibit it, and it would also break your own `license_scope` field. Use this ladder instead:

| Stage | Source | Use |
| --- | --- | --- |
| Now | **Synthetic fixtures you generate** (labelled `source=synthetic`) | All development and tests |
| Free, real | County assessor / recorder open data portals (many US counties publish sales via open data portals) | Real sale price, date, sqft, year built |
| Free, real | FHFA House Price Index (fhfa.gov), FRED (fred.stlouisfed.org, free API key), Zillow Research data downloads (ZHVI CSVs), Redfin Data Center downloads, Census ACS (census.gov API) | **Market indicators** and time adjustment |
| Free, real | HUD datasets (huduser.gov) | Area context, fair market rents |
| Paid / licensed | **RESO Web API** via an MLS or broker agreement (the standard interface MLSs expose), ATTOM Data, CoreLogic, Regrid (parcels) | Production comps. Requires a license, which is the real meaning of "authorized" |

Build the provider interface so a licensed MLS can be swapped in later without touching valuation code. Check each source's terms and record them in `data_source.terms_url`.

### 3b. Regulatory sources (RAG corpus)

Take these from official publishers, preferably through APIs or official downloads rather than page scraping.

| Topic | Source | How to get it |
| --- | --- | --- |
| RESPA (Reg X, 12 CFR 1024) | eCFR, ecfr.gov | eCFR versioner API returns XML by title/part, with dates |
| TILA (Reg Z, 12 CFR 1026) | eCFR; CFPB eRegulations (consumerfinance.gov/rules-policy/regulations) | Same API; eRegs has helpful commentary |
| HMDA (Reg C, 12 CFR 1003) | eCFR; FFIEC HMDA pages (ffiec.cfpb.gov, ffiec.gov) incl. the Filing Instructions Guide | API + PDF download |
| Fair Housing Act | 42 U.S.C. 3601 and following (uscode.house.gov); HUD regulations 24 CFR Part 100 (eCFR) | Official site downloads / eCFR |
| ECOA / Reg B (fair lending, strongly related) | eCFR 12 CFR 1002 | eCFR API |
| Fannie Mae | Selling Guide (selling-guide.fanniemae.com) | Official PDF/HTML; confirm reuse terms |
| Freddie Mac | Single-Family Seller/Servicer Guide (guide.freddiemac.com) | Official PDF/HTML; confirm reuse terms |

Get your team lead or instructor to confirm this is the "approved/authoritative" list (step 1 of your sequence). Store each document with its version/effective date, because invariant 8 depends on it. Verify citation numbers (for example specific section numbers) against the retrieved text rather than trusting memory or this document.

### 3c. "Scraper" policy

For the regulatory corpus you barely need a scraper: eCFR gives structured XML with section IDs, which is better than scraping because section references come for free. For the GSE guides, download the official PDF or HTML once, hash it, and keep it in MinIO.

If you must fetch pages: use `httpx` with a descriptive User-Agent, respect robots.txt and terms, rate-limit to about one request per second, cache by URL + sha256, and parse with BeautifulSoup/trafilatura. Never fetch private or login-gated pages.

## 4. Database design

One Postgres, six concerns. The audit hash chain belongs to the audit service in your design, so your code only emits events.

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Where every fact came from
CREATE TABLE data_source (
  source_id     serial PRIMARY KEY,
  name          text NOT NULL,
  kind          text NOT NULL CHECK (kind IN ('synthetic','mls_reso','avm','public_records','market_stats')),
  license_scope text NOT NULL,
  terms_url     text,
  approved      boolean NOT NULL DEFAULT false
);

CREATE TABLE property (
  property_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  address_norm      text NOT NULL UNIQUE,
  geo               geography(Point,4326),
  property_type     text,
  beds              numeric(3,1),
  baths             numeric(3,1),
  living_area_sqft  int,
  lot_size_sqft     int,
  year_built        int
);

-- MARKET FACTS (retrieved, never modelled)
CREATE TABLE comparable_sale (
  comp_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id          int NOT NULL REFERENCES data_source,
  provider_record_id text NOT NULL,
  property_id        uuid NOT NULL REFERENCES property,
  sale_price         numeric(12,2) NOT NULL CHECK (sale_price > 0),
  sale_date          date NOT NULL,
  living_area_sqft   int NOT NULL CHECK (living_area_sqft > 0),
  price_per_sqft     numeric(10,2) GENERATED ALWAYS AS (sale_price / living_area_sqft) STORED,
  license_scope      text NOT NULL,
  fetched_at         timestamptz NOT NULL DEFAULT now(),
  raw                jsonb,
  UNIQUE (source_id, provider_record_id)
);
CREATE INDEX ON comparable_sale (sale_date);

CREATE TABLE market_indicator (
  geo_key text, period date, metric text, value numeric,
  source_id int REFERENCES data_source,
  PRIMARY KEY (geo_key, period, metric, source_id)
);

-- MODEL ESTIMATES (separate table on purpose)
CREATE TABLE valuation_run (
  run_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id           uuid NOT NULL,
  subject_id        uuid NOT NULL REFERENCES property,
  estimate          numeric(12,2),
  interval_low      numeric(12,2),
  interval_high     numeric(12,2),
  confidence_level  numeric(3,2),
  method            text,
  n_comps           int NOT NULL,
  comp_ids          uuid[] NOT NULL DEFAULT '{}',
  dispersion        numeric,
  abstain_reason    text,
  model_version     text NOT NULL,
  is_estimate       boolean NOT NULL DEFAULT true CHECK (is_estimate),
  created_at        timestamptz NOT NULL DEFAULT now(),
  CHECK (estimate IS NOT NULL OR abstain_reason IS NOT NULL)
);

-- REGULATORY EVIDENCE
CREATE TABLE reg_document (
  doc_id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_name     text NOT NULL,
  authority       text NOT NULL,
  version_or_date text,
  url             text NOT NULL,
  sha256          text NOT NULL,
  retrieved_at    timestamptz NOT NULL,
  approved        boolean NOT NULL DEFAULT false
);

CREATE TABLE reg_chunk (
  chunk_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  doc_id        uuid NOT NULL REFERENCES reg_document,
  section_ref   text,
  page_ref      text,
  text          text NOT NULL,
  embedding     vector(384) NOT NULL,
  tsv           tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
  index_version text NOT NULL
);
CREATE INDEX ON reg_chunk USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON reg_chunk USING gin (tsv);

-- COMPLIANCE OUTPUT (invariant 3 enforced by the database)
CREATE TABLE compliance_finding (
  finding_id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id                uuid NOT NULL,
  rule_id                text NOT NULL,
  rule_set_version       text NOT NULL,
  status                 text NOT NULL CHECK (status IN ('no_issue_detected','potential_issue','cannot_verify')),
  severity               text CHECK (severity IN ('low','medium','high')),
  affected_requirement   text,
  evidence_refs          uuid[] NOT NULL DEFAULT '{}',
  missing_information    jsonb NOT NULL DEFAULT '[]',
  explanation            text,
  human_review_required  boolean NOT NULL,
  CHECK (status = 'cannot_verify' OR cardinality(evidence_refs) > 0)
);
```

Redis holds provider responses (key = provider + normalized query, TTL in hours or days). MinIO holds raw documents so any chunk can be traced back to a hashed original.

## 5. Repository layout

```
backend/app/
  property/
    provider.py       # abstract class CompProvider
    providers/synthetic.py, providers/reso.py (later), providers/assessor_csv.py
    normalize.py      # address, type, units; reject impossible values
    comps.py          # selection, adjustment, similarity weights
    valuation.py      # estimate + interval + abstain logic
    schemas.py        # Comparable, ValuationOutput
  compliance/
    rules/            # one file per rule family, rules are data + a check function
    engine.py         # runs rules, attaches evidence, validates
    schemas.py        # ComplianceOutput
  rag/
    sources.yaml      # approved source registry
    ingest/ (fetch.py, clean.py, chunk.py, metadata.py)
    embed.py, store.py, retrieve.py, rerank.py
    evidence.py       # builds Evidence items
  agents/property_agent.py, compliance_agent.py
tests/ property/, compliance/, rag/, fixtures/
```

## 6. Workflow and schedule

This follows your brief's sequence. Durations are suggestions; stretch or compress them.

| Phase | Days | Do | Exit check |
| --- | --- | --- | --- |
| 0. Setup | 1-2 | Docker Compose with Postgres+pgvector+PostGIS, Redis, MinIO; Alembic migration of the Section 4 schema; Pydantic schemas copied from design contracts | `docker compose up` works; schemas validate sample JSON |
| 1. Sources | 2-3 | Fill `sources.yaml`; get lead approval; download eCFR parts 1024, 1026, 1003, 1002, 24 CFR 100; save GSE guide PDFs; hash and store | Every document has url, version/date, sha256 |
| 2. Ingestion | 3-4 | Clean, chunk (by section for eCFR, by heading/page for PDFs), attach metadata, embed, insert | Spot-check 20 chunks: text matches the source section |
| 3. Retrieval | 2-3 | Hybrid search (vector + tsvector), optional reranker, `EvidenceItem` builder | 20-question gold set: right section in top 5 for most |
| 4. Compliance rules | 4-5 | Rule engine, 6-8 rules, validation that rejects evidence-less flags | Each rule has pass, fail and missing-data tests |
| 5. Provider + fixtures | 2 | `CompProvider` interface, synthetic provider (100-300 comps over 3-4 fake markets, seeded), assessor CSV loader | Same interface serves synthetic and CSV data |
| 6. Valuation | 4-5 | Selection, adjustment, estimate, interval, abstain rules | Backtest on held-out comps; abstains when thin |
| 7. Agents + state | 2-3 | Wrap both modules as agents; write to shared state; emit audit events | Run end to end on 10 fixture cases |
| 8. Test + harden | 3 | Fill test gaps, fairness checks, failure modes from design | Definition of Done checklist (Section 11) |

Work order recommendation: do 0, 1, 2, 3 first (RAG), because compliance depends on it, and use the waiting time to write the synthetic fixtures for phase 5.

## 7. Valuation method

Keep it transparent and explainable; this is a comps estimate, not a black box.

1. **Select comps**: same property type, within a radius (start 1 mile urban, 5 miles rural), sold in the last 6-12 months, living area within +/-20%. Widen in steps and record how far you had to widen.
2. **Time-adjust** each sale: `adj_price = sale_price x HPI(now) / HPI(sale month)` using FHFA or Zillow index for that area.
3. **Normalize**: `adj_ppsf = adj_price / living_area_sqft`. Optionally add simple adjustments (beds, baths, age) from a small regression, and document them.
4. **Weight** each comp by similarity: closer distance, more recent, smaller size gap get more weight.
5. **Estimate**: `estimate = subject_sqft x weighted_median(adj_ppsf)`.
6. **Interval**: bootstrap the weighted median (1000 resamples), take the 10th and 90th percentiles for an 80% interval. Describe it as a comp-dispersion interval; calibrate against held-out sales before claiming coverage.
7. **Abstain** (set `abstain_reason`, no estimate): fewer than 3 usable comps, or fewer than 5 for an interval; dispersion (coefficient of variation) above a configured threshold; subject missing sqft or location; stale data.
8. **Market indicators** (median price, days on market, inventory, HPI trend) go in a separate block; never fold them into the estimate silently.

Confidence label (low / medium / high) from n\_comps, dispersion and comp distance; low always sets `needs_human`.

## 8. Compliance rules (starting set)

Each rule is data (id, requirement text, required inputs, evidence query) plus a pure check function. Thresholds and deadlines come from retrieved evidence stored in config, **not from memory**. Statuses are only `no_issue_detected`, `potential_issue` and `cannot_verify`; never "compliant".

| Rule | Checks | Needs | Evidence query |
| --- | --- | --- | --- |
| HMDA-001 | Required HMDA data points present for the loan record | Loan application data | Reg C 1003.4 data points |
| TILA-001 | APR / finance charge / disclosure fields present and consistent | Loan terms | Reg Z disclosure sections |
| RESPA-001 | Timing of required disclosures after application (date arithmetic) | Application and disclosure dates | Reg X / Reg Z timing provisions |
| FHA-001 | Protected-class terms in free text; protected-class proxies among valuation features | Notes, feature list | 24 CFR 100; Fair Housing Act |
| GSE-001 | Comp count, recency and distance versus configured guide thresholds | Comps from the Property agent | Selling Guide / Seller-Servicer Guide appraisal sections |
| GSE-002 | Appraised or contract value diverges from model estimate beyond a threshold | Value inputs, estimate | Guide appraisal sections |
| DATA-001 | Evidence version older than loan date coverage; index missing or stale | Evidence metadata | None (system check) |

Flow per rule: check inputs, mark `cannot_verify` with `missing_information` if absent, run the deterministic check, retrieve evidence for the affected requirement, attach evidence refs, validate. If the retrieval returns nothing relevant, status is `cannot_verify`, never a flag without evidence.

## 9. Prompts

Use these with your coding assistant (Claude Code or chat). Paste P0 first in every session.

**P0: project context**

> You are helping me build Member 4 of a property valuation agentic system: property valuation, compliance and RAG. Stack: Python 3.12, FastAPI, Pydantic v2, Postgres 16 with pgvector and PostGIS, Redis, MinIO, sentence-transformers (bge-small-en-v1.5), pytest. Hard rules: never fabricate property or regulatory data; market facts, model estimates and regulatory evidence are separate objects; a compliance flag without evidence references must fail validation; low confidence or ambiguity sets human\_review\_required; compliance outputs say "potential issue for review", never a legal conclusion; no protected-class proxies as valuation features. Contracts: Comparable record, Valuation output, Evidence item, Compliance output (fields exactly as I provide). Write small, typed, tested modules. Ask before assuming anything about data sources.

**P1: scaffold and contracts**

> Create the repo layout under backend/app (property, compliance, rag, agents) and Pydantic v2 schemas for ComparableRecord, ValuationOutput (is\_estimate must be True), EvidenceItem, ComplianceOutput, with validators: ComplianceOutput with status potential\_issue requires at least one evidence\_ref; ValuationOutput requires estimate or abstain\_reason. Add the Alembic migration for the SQL I paste next. Include unit tests for every validator.

**P2: ingestion**

> Build backend/app/rag/ingest. Input: sources.yaml listing approved documents (name, authority, url, version\_or\_date). Steps: fetch (httpx, retries, polite rate limit, store raw bytes in MinIO with sha256), clean (strip headers/footers/navigation, keep section numbers), chunk (eCFR XML by section; PDFs by heading with 400-800 tokens and 15% overlap, never split a numbered paragraph mid-sentence), attach metadata (source\_name, version\_or\_date, section\_ref, page\_ref, url, sha256, index\_version), embed with bge-small, upsert into reg\_chunk. Make it idempotent: re-running the same sha256 must not duplicate chunks. Write tests with a tiny fixture document.

**P3: retrieval and evidence**

> Implement retrieve(query, filters, k) as hybrid search: pgvector cosine top 30 plus tsvector top 30, merge by reciprocal rank fusion, optional cross-encoder rerank to top k. Return EvidenceItem objects with source\_name, version\_or\_date, section\_or\_page, retrieval\_ref (chunk\_id), the exact snippet, index\_version, retrieved\_at and score. If the best score is below a configured threshold, return an empty list rather than the closest guess. Add a gold-set test file: 20 questions mapped to expected section\_refs, and report hit@5.

**P4: compliance rules**

> Build backend/app/compliance/engine.py and rule files for HMDA-001, TILA-001, RESPA-001, FHA-001, GSE-001, GSE-002, DATA-001 as per my table. Each rule: declare required inputs; if any are missing return cannot\_verify with missing\_information; otherwise run a deterministic check; then call the retriever for the affected requirement and attach EvidenceItems. Thresholds come from a versioned config file, not code. Reject any finding without evidence unless status is cannot\_verify. Tests per rule: no-issue, potential-issue, missing-data, and empty-retrieval.

**P5: provider and fixtures**

> Define abstract CompProvider with fetch\_comps(subject, radius\_mi, months, filters) returning list\[ComparableRecord\] plus provider metadata (source, license\_scope, fetched\_at). Implement SyntheticProvider that generates seeded, reproducible comps for 3 fake markets with realistic noise, every record tagged source=synthetic. Implement AssessorCsvProvider for a county CSV with column mapping. Add normalization that rejects negative or zero prices, sqft outside plausible bounds, and impossible dates, and logs rejects instead of fixing them silently. A provider error or empty result must raise ProviderUnavailable, never return invented rows.

**P6: valuation**

> Implement comps selection, time adjustment from a market index table, similarity weights, weighted-median PPSF estimate, bootstrap 80% interval, and abstain rules from Section 7. Output ValuationOutput with comp\_ids, n\_comps, dispersion, method and model\_version. Keep market\_indicators in a separate field. Add a backtest script: hold out each synthetic sale, predict from the others, report median absolute percentage error and interval coverage. Add a hypothesis test that the function never returns an estimate when n\_comps < 3.

**P7: agents and shared state**

> Write property\_agent.py and compliance\_agent.py as thin wrappers that read the subject and loan data from shared state, call the modules, write market\_facts, model\_output, evidence, compliance and missing\_info keys, set needs\_human when any status is cannot\_verify or potential\_issue with severity high or confidence is low, and emit an audit event (actor, node, input\_digest, output\_digest, versions). They must not call an LLM to decide flags or values.

**P8: tests**

> Review my tests for gaps. For each design invariant, show which test enforces it; write missing ones. Add end-to-end tests: (a) healthy case, (b) provider outage, (c) fewer than 3 comps, (d) retrieval returns nothing, (e) stale source, (f) protected-class term in notes. Assert the expected human\_review\_required in each.

**P9: runtime explainer prompt (for the LLM that writes report text)**

> You write plain-language explanations for a human reviewer. You receive structured JSON: market\_facts, model\_output, compliance findings with evidence snippets. Rules: do not change, add or remove flags, severities, estimates or intervals; quote evidence only from the snippets provided and cite its source\_name and section; keep "retrieved facts" and "model estimate" in separate sections; call the estimate an estimate; use the words "potential issue for review", never "violation" or "compliant"; if information is missing, say what is missing and that human review is required. If any input is absent, say so instead of filling it in.

## 10. Tests that matter

- **Retrieval**: gold-set hit@5, empty result on out-of-scope query, correct version filter by loan date.
- **Rules**: each rule has pass, fail, missing-data and no-evidence cases.
- **Missing evidence**: finding with no evidence\_refs is rejected at schema and database level.
- **Valuation**: abstains under 3 comps; interval never returned with fewer than 5; estimate unchanged when only market indicators change.
- **No fabrication**: provider failure returns an error and a human case, not rows.
- **Fairness**: protected-class proxy columns fail the feature allow-list.
- **Determinism**: same inputs and versions give identical outputs.

## 11. Definition of Done checklist

- [ ] Property analysis returns structured comps and valuation without fabricated data (synthetic rows are labelled)
- [ ] Market facts and model estimate are in separate fields and report sections
- [ ] Every compliance finding has evidence with source name, version/date, section/page, retrieval ref and snippet
- [ ] Low-confidence, ambiguous, empty-retrieval and provider-failure cases set human\_review\_required
- [ ] Outputs are written to the shared state with audit events
- [ ] All design invariants have a named test
- [ ] A short README explains sources, versions, thresholds and known limits

## 12. What to learn, in order

1. Comparable sales approach: how appraisers choose and adjust comps (search "sales comparison approach" and Fannie Mae's appraisal sections).
2. RAG basics: chunking, embeddings, cosine similarity, hybrid search, reciprocal rank fusion. The sentence-transformers and pgvector READMEs are enough to start.
3. Source provenance: why every chunk needs a document hash and version.
4. Rule-based validation with Pydantic validators.
5. Evidence vs interpretation: evidence is the quoted snippet; the finding is your rule's result; the explanation is wording only.
6. Basic statistics: weighted median, bootstrap, coefficient of variation, calibration.

## 13. Caveats

- Regulatory texts change; always store the effective date and re-ingest on a schedule.
- GSE guides are publicly available but check their reuse terms for your project.
- This system flags potential issues for compliance staff; it is not legal advice and should never state a legal conclusion.
- Synthetic data is for development only; label it in every output.

# 14. India edition (Lucknow pilot)

The structure above still holds: facts, estimates and evidence stay separate, and the system abstains when data is thin. What changes is the data, the units and the rulebook. I read your request for loan officer rule as the loan officer role and its commands; see 14.7.

## 14.1 US rules mapped to Indian counterparts

Ingest these as your authoritative corpus, and confirm the list with your compliance lead. Section numbers and thresholds must come from the retrieved text, not from memory.

| Brief item | India counterpart |
| --- | --- |
| FNMA / FHLMC guides | Your lender's credit and valuation policy; empanelled valuer guidelines; valuation standards (IVS, RICS, Registered Valuers rules under IBBI) |
| TILA | RBI directions on the Key Fact Statement (KFS) and APR disclosure; RBI Fair Practices Code |
| RESPA | Fair Practices Code on charges and communication; RERA disclosure and escrow rules for under-construction projects |
| HMDA | No direct equivalent; closest are regulatory returns and credit-bureau reporting norms |
| Fair Housing Act | Article 15 of the Constitution; non-discrimination expectations in RBI fair lending practice |
| New for India | RERA 2016 and UP-RERA rules; SARFAESI Act 2002 and CERSAI registration; KYC Master Direction and PMLA; Digital Personal Data Protection Act 2023; RBI housing-loan LTV and risk-weight norms; NHB directions for housing finance companies; state stamp duty and Registration Act |

Official sites: rbi.org.in, nhb.org.in, indiacode.nic.in (Acts), up-rera.in, igrsup.gov.in, cersai.org.in, ibbi.gov.in.

**Starter rules (replaces Section 8):** KFS-001 (KFS fields present), LTV-001 (loan to value within configured cap), RERA-001 (project registered, RERA ID valid), TITLE-001 (title documents, encumbrance certificate and CERSAI check present), VAL-001 (valuation by empanelled valuer; gap versus circle rate and model estimate), KYC-001 (KYC fields present), FAIR-001 (protected attribute or proxy in notes or features), DATA-001 (stale source or index). Statuses stay no\_issue\_detected, potential\_issue, cannot\_verify.

## 14.2 Where to collect property data in India

| Priority | Source | Gives you | Caveat |
| --- | --- | --- | --- |
| 1 | Your bank or HFC internal valuation reports and collateral records | Real valuations with area, address, date | Needs internal approval; mask personal data |
| 2 | State registration department (UP: igrsup.gov.in) | Registered sale deeds, circle rates | Deed value often sits near the circle rate, not the true price; check portal terms before bulk access |
| 3 | UP-RERA (up-rera.in) | Registered projects, unit and carpet areas, promoter, status | Mostly project level; prices not always listed |
| 4 | RBI Residential Property Price Index; NHB Residex | City-level price index | Use for time adjustment and indicators; confirm Lucknow coverage |
| 5 | Licensed research data (PropEquity, Liases Foras, Anarock, Knight Frank India) | Transaction and launch data | Paid, licence terms apply |
| 6 | Listing portals (99acres, MagicBricks, Housing.com) | Asking prices | Their terms forbid scraping; asking is not sale price. Use only via official partnership or API, or small manual samples tagged asking |
| 7 | OpenStreetMap, Census 2011, data.gov.in | Geography, amenities, pincode directory | Context only |
| 8 | Your own field survey or broker quotes | Local checks | Tag as survey |

Rule: every row carries price\_type (registered\_deed, valuer\_report, asking, survey). Valuation uses registered and valuer rows first. Asking prices only feed market indicators unless validated.

## 14.3 Target fields and how each is cleaned

| Field | Raw variants in India | Cleaning rule |
| --- | --- | --- |
| Address / location | Free text, locality names, 6-digit pincode | Keep original; trim; expand abbreviations; extract pincode; geocode with a confidence score; reject points outside the pilot box |
| Property type | flat, apartment, builder floor, kothi, villa, plot | Map to apartment, independent\_house, builder\_floor, villa, plot, commercial; unknown becomes null plus a flag |
| Bedrooms / bathrooms | 2BHK, 3 BHK | Beds from BHK; baths only if stated, never imputed |
| Size | sq ft, sq m, sq yd, gaj; carpet, built-up, super built-up | Convert to sq ft; store area\_basis; never compare across bases; bigha and biswa are not auto-converted because they vary by state |
| Year built | 2015, ready to move, possession Dec 2026 | Integer year; future possession sets under\_construction; age = current year minus year built |
| Sale price / date | 85 Lac, 1.2 Cr, 8,500,000; dd/mm/yyyy | Convert to INR number; parse day-first; reject price at or below 0 and future dates |
| Price per sq ft | Derived | price / area in sq ft, same basis only; computed in the database |
| Distance from subject | Derived | PostGIS distance in km; null if either side is not geocoded |
| Market indicators | Indexes, circle rates, volumes | Separate table by locality and period (14.6) |

## 14.4 Schema changes for India

```sql
ALTER TABLE property
  ADD COLUMN original_address text, ADD COLUMN locality text, ADD COLUMN pincode char(6),
  ADD COLUMN city text DEFAULT 'Lucknow', ADD COLUMN state text DEFAULT 'Uttar Pradesh',
  ADD COLUMN floor_no int, ADD COLUMN total_floors int, ADD COLUMN rera_id text,
  ADD COLUMN geocode_confidence numeric(3,2);

ALTER TABLE comparable_sale
  ADD COLUMN currency char(3) NOT NULL DEFAULT 'INR',
  ADD COLUMN price_type text NOT NULL DEFAULT 'survey'
    CHECK (price_type IN ('registered_deed','valuer_report','asking','survey')),
  ADD COLUMN area_basis text CHECK (area_basis IN ('carpet','built_up','super_built_up')),
  ADD COLUMN clean_flags text[] NOT NULL DEFAULT '{}';

-- bronze layer: untouched source records
CREATE TABLE raw_record (
  raw_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id int REFERENCES data_source, payload jsonb NOT NULL,
  file_sha256 text, fetched_at timestamptz DEFAULT now(), status text DEFAULT 'new');

CREATE TABLE circle_rate (
  locality text, effective date, property_class text, rate_per_sqm numeric,
  source_id int REFERENCES data_source, PRIMARY KEY (locality, effective, property_class));
```

Distance from the subject:

```sql
SELECT c.comp_id, ST_Distance(p.geo, s.geo) / 1000 AS distance_km
FROM comparable_sale c JOIN property p USING (property_id), property s
WHERE s.property_id = :subject AND ST_DWithin(p.geo, s.geo, 3000);
```

## 14.5 Collect, clean, process

Three layers: **bronze** (raw\_record, plus the original file in MinIO), **silver** (cleaned rows with clean\_flags), **gold** (property, comparable\_sale, market\_indicator, ready for valuation). Collectors only read approved sources and save what they fetched; nothing is cleaned or invented at that step. Rejected rows are logged with a reason, never silently repaired.

```python
import re, math, pandas as pd
MULT = {'cr': 1e7, 'crore': 1e7, 'l': 1e5, 'lac': 1e5, 'lakh': 1e5, 'k': 1e3}
AREA = {'sqft': 1.0, 'sqm': 10.7639, 'sqyd': 9.0, 'gaj': 9.0}
LKO = (26.6, 27.1, 80.7, 81.2)  # pilot box: lat_min, lat_max, lon_min, lon_max

def parse_price_inr(s):
    s = str(s).lower().replace(',', '').replace('₹', '').strip()
    m = re.search(r'([0-9]+[.]?[0-9]*)[ ]*(crore|cr|lakh|lac|l|k)?', s)
    return float(m.group(1)) * MULT.get(m.group(2), 1) if m else None

def parse_area_sqft(s):
    m = re.search(r'([0-9]+[.]?[0-9]*)[ ]*(sq[ .]*ft|sq[ .]*m|sq[ .]*yd|gaj)', str(s).lower().replace(',', ''))
    return float(m.group(1)) * AREA[re.sub('[ .]', '', m.group(2))] if m else None

def parse_bhk(s):
    m = re.search(r'([0-9]+)[ ]*bhk', str(s).lower())
    return int(m.group(1)) if m else None

def haversine_km(lat1, lon1, lat2, lon2):
    p = math.pi / 180
    a = math.sin((lat2 - lat1) * p / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(a))

def clean(df):
    d = df.copy()
    d['sale_price'] = d['price_raw'].map(parse_price_inr)
    d['area_sqft'] = d['area_raw'].map(parse_area_sqft)
    d['beds'] = d['title_raw'].map(parse_bhk)
    d['sale_date'] = pd.to_datetime(d['date_raw'], dayfirst=True, errors='coerce')
    d['pincode'] = d['address_raw'].str.extract(r'(?<![0-9])([1-9][0-9]{5})(?![0-9])')
    outside = ~d.lat.between(LKO[0], LKO[1]) | ~d.lon.between(LKO[2], LKO[3])
    bad = (d.sale_price <= 0) | d.sale_price.isna() | d.area_sqft.isna() | d.sale_date.isna() \
          | (d.sale_date > pd.Timestamp.today()) | outside
    rejects, d = d[bad], d[~bad].copy()          # log rejects; never fix silently
    d['price_per_sqft'] = d.sale_price / d.area_sqft
    g = d.groupby(['locality', 'property_type'])['price_per_sqft']
    mad = g.transform(lambda x: (x - x.median()).abs().median()).replace(0, float('nan'))
    d['outlier'] = (d.price_per_sqft - g.transform('median')).abs() / (1.4826 * mad) > 3.5   # flag, do not delete
    d['lat4'], d['lon4'] = d.lat.round(4), d.lon.round(4)
    d = d.drop_duplicates(['lat4', 'lon4', 'area_sqft', 'sale_price', 'sale_date'])
    return d, rejects
```

Geocoding: use a provider whose terms allow your use, cache every result, and store the confidence. OpenStreetMap Nominatim has a strict public usage policy (about one request per second), so for volume run your own instance or use a paid geocoder.

## 14.6 Market indicators (separate table, never mixed into the estimate)

Median price per sq ft per locality and quarter; number of transactions; registered-deed price versus circle rate gap; asking versus registered gap (when both exist); RBI or NHB index level and year-on-year change; months of data and sample size per locality. Every indicator row stores its source and period.

## 14.7 Loan officer role and commands

The loan officer reads and requests; they never edit estimates or flags. Every command writes an audit event and returns structured output plus a short plain-language summary.

| Command | Who | What it does |
| --- | --- | --- |
| /intake \<address> --type --area --basis --price-quoted | Loan officer | Creates the case and normalizes the subject property |
| /valuate \<case\_id> | Loan officer | Runs comps and returns estimate with interval, or an abstain reason |
| /comps \<case\_id> --radius 2km --months 12 | Loan officer | Lists comps with price type, area basis, distance, price per sq ft |
| /market \<locality> | Loan officer | Shows market indicators with sources and periods |
| /compliance \<case\_id> | Loan officer | Runs rules; shows status, severity, requirement, evidence |
| /evidence \<finding\_id> | Loan officer | Shows source, version or date, section or page, snippet |
| /missing \<case\_id> | Loan officer | Lists missing documents and fields |
| /explain \<case\_id> | Loan officer | Plain-language summary; cannot change any result |
| /escalate \<case\_id> --reason | Loan officer | Sends the case to a human reviewer |
| /review \<case\_id> --decision --note | Compliance reviewer | Records the human decision |
| /approve \<case\_id> | Compliance reviewer | Allowed only when no unresolved high-severity finding remains |
| /sources | Admin | Lists approved sources, versions, last ingest date |

Rules for every command: no fetching outside approved providers; low confidence, abstain, empty retrieval or provider failure always set human review; wording is potential issue for review, never a legal conclusion; a loan officer cannot approve a case that has a flagged finding.

## 14.8 First two weeks, India edition

1. Get internal approval for the bank or HFC valuation reports (anonymized) and agree the approved source list.
2. Download RBI and NHB directions and the RERA, SARFAESI and KYC texts; record version and date; ingest.
3. Collect UP circle rates and UP-RERA project data for Lucknow by hand or approved download; load into bronze.
4. Run the cleaning script on 200 to 500 rows; review every reject and every outlier flag by eye.
5. Load gold tables; compute market indicators for the top 10 localities.
6. Run the valuation backtest and the 20-question retrieval gold set.

# 15. Multi-state design (all of India)

Section 14 used Uttar Pradesh as the pilot. This section makes the system work for any state: one national core plus one small configuration pack per state.

## 15.1 National core and state packs

| Layer | Contents | Changes per state? |
| --- | --- | --- |
| National core | Schema, cleaning pipeline, valuation method, RAG pipeline, commands, roles, audit | No |
| National rules and evidence | RBI and NHB directions, RERA Act 2016, SARFAESI, KYC and PMLA, data protection law | No |
| State pack | Boundary, portals, guideline-value name and unit, land-unit conversions, localities, collector, state rules and evidence | Yes, one pack per state |

## 15.2 Jurisdiction pack (one file per state)

```yaml
state_code: MH
name: Maharashtra
status: planned            # planned, pilot, live, paused
config_version: 2026-10-01
rera_portal: <official url, verified>
registration_portal: <official url, verified>
guideline_value:
  local_name: <name used in that state, verified>
  unit: <per sq m or per sq ft, verified>
area_units:                # every conversion verified against an official source
  sq_ft: 1
  sq_m: 10.7639
  local_units: {}          # bigha, katha, guntha, cent: fill only from official sources
boundary_file: boundaries/mh.geojson
localities_file: localities/mh.csv
collector: app/property/providers/mh_registry.py
rule_pack: app/compliance/rules/states/mh/
regulatory_sources: []     # state RERA rules, stamp duty and registration acts
min_comps: 5               # raise for thin markets
```

Never copy numbers from another state. A blank value means the state is not ready.

## 15.3 Schema changes

```sql
CREATE TABLE jurisdiction (
  state_code char(2) PRIMARY KEY, name text NOT NULL,
  status text NOT NULL DEFAULT 'planned' CHECK (status IN ('planned','pilot','live','paused')),
  config jsonb NOT NULL, config_version text NOT NULL);

ALTER TABLE property
  ADD COLUMN state_code char(2) REFERENCES jurisdiction, ADD COLUMN district text,
  ALTER COLUMN city DROP DEFAULT, ALTER COLUMN state DROP DEFAULT;
ALTER TABLE circle_rate
  ADD COLUMN state_code char(2) REFERENCES jurisdiction, ADD COLUMN local_name text;
ALTER TABLE reg_document
  ADD COLUMN scope text NOT NULL DEFAULT 'national' CHECK (scope IN ('national','state')),
  ADD COLUMN state_code char(2) REFERENCES jurisdiction,
  ADD COLUMN effective_from date, ADD COLUMN effective_to date;
ALTER TABLE compliance_finding ADD COLUMN state_code char(2);
```

## 15.4 Rules that keep states apart

1. Retrieval filter: evidence must have scope national, or state\_code equal to the subject property's state. A test proves a UP case never receives Maharashtra evidence.
2. Comparables must come from the subject's own state. Never borrow another state's data to fill a gap.
3. A state whose status is not pilot or live returns state not supported and escalates to a human.
4. The cleaning bounding box and unit conversions come from the state pack, not from code.
5. Evidence is selected as of the loan date using effective\_from and effective\_to, so old cases still cite the rules that applied then.

## 15.5 Data tiers and what the system does

| Tier | What exists in the state | Behaviour |
| --- | --- | --- |
| A | Registered sale data accessible plus RERA plus guideline values plus lender's own reports | Estimate with interval when comps are enough |
| B | Guideline values and RERA only, thin sale data | Estimate only with lender's own reports; otherwise abstain often; indicators shown |
| C | Only lender's internal reports | Abstain unless internal comps are enough; every case goes to human review |

Decide each state's tier in SOP-10 and record it in the pack.

## 15.6 Rollout order

Start with states that hold most of your lender's loan book. A sensible default is UP (pilot), then Maharashtra, Delhi NCR, Karnataka and Tamil Nadu. A state moves planned, pilot, live only through SOP-10.

# 16. Standard procedures (SOPs)

These are the repeatable procedures. Each has an owner, ordered steps, a check that proves it was done, and a record that is kept. Do not skip the record: the audit trail is part of the product.

## 16.1 Who does what

| Role | Responsible for |
| --- | --- |
| Builder (you, Member 4) | SOP-1 to SOP-6, SOP-9 technical fixes, SOP-11, SOP-12 |
| Team lead | Approves sources (SOP-2), state go-live, releases |
| Loan officer | SOP-7 |
| Compliance reviewer | SOP-6 sign-off, SOP-8 |
| Admin | Access, secrets, retention (SOP-13) |

## SOP-1 Set up the environment

1. Clone the repository; copy the example env file to .env; keep secrets out of git.
2. Start services: Postgres with pgvector and PostGIS, Redis, MinIO.
3. Apply migrations with Alembic; confirm the schema from Sections 4, 14 and 15 exists.
4. Load the synthetic fixtures with a fixed seed.
5. Run the full test suite; every test must pass.
6. Record versions: Python, database extensions, embedding model, index\_version.

**Check:** health endpoint returns ok and every fixture row is labelled synthetic. **Record:** setup note with versions.

## SOP-2 Approve and register a data source

1. Add an entry: name, authority, kind, url, terms url, licence scope, update frequency, data owner.
2. Read the terms: is automated access allowed, is reuse allowed, does it contain personal data?
3. If the answer is unclear or no, do not collect. Ask the owner or the lender's legal contact and leave approved=false.
4. Get written sign-off from the team lead, and from the data owner for internal bank data.
5. Set approved=true in a reviewed commit.

**Check:** a test confirms collectors and ingestion refuse any source with approved=false. **Record:** the signed approval and the registry entry.

## SOP-3 Ingest or update a regulatory document

1. Download only from the official publisher; note url, date and version or effective date.
2. Store the raw file in MinIO and compute sha256. If this sha256 was ingested before, stop.
3. Parse the file. Compare the number of sections found with the document's own contents list; spot-check 20 chunks against the source text.
4. Chunk by section, embed, and tag with scope, state\_code, version, effective\_from and effective\_to.
5. Build a new index\_version. Run the retrieval gold set; hit@5 must not fall compared with the active version. If it falls, do not switch.
6. Switch the active index\_version. Set effective\_to on superseded documents; never delete them.
7. List the rules that cite changed sections and ask their owners to re-check them (SOP-6).

**Check:** gold set result stored with the index\_version. **Record:** ingest log with hashes and counts.

## SOP-4 Collect property data (bronze)

1. Pick an approved source and confirm the access method: API, official download or manual entry.
2. Fetch politely (rate limit, descriptive user agent). Save the raw file in MinIO with sha256 and fetched\_at.
3. Load rows unchanged into raw\_record with source\_id and status new.
4. Never edit raw rows. Corrections happen only in the cleaning step.
5. Log counts: fetched, loaded, duplicates skipped.
6. For manual entry, use the template file with required columns, record who entered it, and have a second person check at least 10 percent of rows.

**Check:** re-running the same file adds no new rows. **Record:** batch note with source, date, counts.

## SOP-5 Clean and promote to the database (silver to gold)

1. Run the cleaning function on the batch (Section 14.5) using the state pack for boundary and units.
2. Read every rejected row and its reason. Fix the source or the parser, not the row.
3. Apply the quality gates below.
4. A person reviews every outlier-flagged row. Flagged rows stay stored with their flag.
5. Promote passing rows to gold with a batch id; recompute market indicators.
6. Run a quick check: ten random rows traced back to their raw record.

| Gate | Default | If it fails |
| --- | --- | --- |
| Reject rate | Over 20 percent | Stop; investigate the source or parser |
| Rows missing area basis | Over 30 percent | Do not use those rows for price per sq ft comps |
| Geocode confidence | Under 0.6 | Leave distance empty |
| Rows outside the state boundary | Any | Reject |
| Price type asking | Any | Indicators only, never an estimate input |

Thresholds live in config and are tuned in review, not in code.

**Record:** batch id, accept and reject counts, reviewer name.

## SOP-6 Add or change a compliance rule

1. Write the requirement in plain words and the data it needs.
2. Find the source section by retrieval; save the evidence reference.
3. Define required inputs and the deterministic check. Put thresholds and deadlines in config, copied from the retrieved text.
4. Write four tests: no issue, potential issue, missing data, empty retrieval.
5. A compliance reviewer reads the rule and the evidence and signs it off.
6. Bump rule\_set\_version; run the regression set of 10 fixture cases; compare outputs with the previous version.
7. Write a changelog entry stating what changed and why.

**Check:** a finding without evidence is still rejected after the change. **Record:** changelog, reviewer, version.

## SOP-7 Handle a loan case (loan officer)

Case states: new, intake done, valued or abstained, compliance checked, needs review, reviewed, approved or rejected.

1. `/intake` with the property details. If the state is not supported, stop and escalate.
2. `/missing`: collect each missing item from the applicant. Repeat until nothing is missing, or escalate.
3. `/valuate`: if there is an estimate, note its interval and confidence. If the system abstains, go to step 7.
4. `/comps`: sanity check. Same locality? Same price type and area basis? Recent? Anything odd goes in the escalation note.
5. `/compliance`: read every finding; for each potential issue or cannot verify, open `/evidence`.
6. `/explain` for a plain-language summary to attach to the file.
7. If there is any potential issue, cannot verify, low confidence or abstain: `/escalate` with a reason. Otherwise submit for reviewer approval.
8. The case is locked after approval. Every command is in the audit log.

The system estimate is decision support. The official valuation remains the empanelled valuer's report, and the estimate is never quoted to the applicant as a valuation.

**Record:** audit events for each command, escalation note.

## SOP-8 Human review and escalation

1. The reviewer picks up the case within the lender's service level (set by the lender, tracked as backlog age).
2. Read the flagged findings and open the source snippets; for anything doubtful, open the original document by its reference.
3. Check the comps and the data gaps.
4. Decide with `/review`: confirm, request more information, or override with a written reason. An override records the decision; it never edits the stored estimate or flag.
5. High-severity findings need a second reviewer.
6. Log each disagreement between the system and the reviewer. Review these weekly to tune rules and thresholds through SOP-6.

**Record:** decision, reason, reviewer, time.

## SOP-9 Failures and incidents

| Situation | Do this | Who |
| --- | --- | --- |
| Data provider down or empty | Serve cache within its TTL; otherwise return insufficient data and open a human case; never generate data | Builder |
| Retrieval returns nothing | Status cannot verify; human review; log the query; add to gold set after review | Builder |
| Index missing or stale | Compliance becomes cannot verify for all cases; re-run SOP-3 | Builder |
| Database primary down | Read-only mode; queue writes; block approvals | Builder, Admin |
| Audit hash mismatch | Stop approvals; escalate to team lead immediately; preserve logs | Team lead |
| Wrong rule or wrong citation found | Disable the rule; re-check affected cases; fix through SOP-6 | Builder, Compliance reviewer |
| Personal data found in a property table or prompt | Isolate and delete under SOP-13; notify the lender's data protection contact | Admin, Team lead |

After any incident write a short note: what happened, which cases were affected, the fix, the new test.

## SOP-10 Onboard a new state

1. Draft the jurisdiction pack (Section 15.2); leave unknown values blank.
2. Approve the state's registration, RERA and guideline-value sources (SOP-2).
3. Ingest state RERA rules and the stamp duty and registration texts with scope state (SOP-3).
4. Verify each land-unit conversion against an official source and record the source.
5. Decide the data tier (Section 15.5).
6. Build the collector; load 200 to 500 rows from the top 5 to 10 localities (SOP-4).
7. Clean and review (SOP-5).
8. Write the state rule pack and tests (SOP-6).
9. Run the valuation backtest; record error and interval coverage.
10. Run the isolation test: state evidence and data never cross into another state.
11. Dry-run 10 historical cases with a reviewer.
12. Set status to pilot. For the first month every case in the state goes to human review.
13. Team lead signs off to move to live, based on the backtest, the escalation rate and reviewer feedback.

**Record:** signed checklist and pack config\_version.

## SOP-11 Scheduled upkeep

| When | Task |
| --- | --- |
| Daily | Provider error rate, audit chain check, token spend |
| Weekly | Reject rate, empty-retrieval rate, escalation rate, reviewer disagreements |
| Monthly | Load new comps and circle-rate changes; re-check source terms; re-run the retrieval gold set; check for new regulatory circulars |
| Quarterly | Update RBI and NHB index series; re-run the valuation backtest; review thresholds |
| On any regulatory change | SOP-3 then SOP-6 for the rules that cite it |

## SOP-12 Release and definition-of-done check

1. All tests pass, including the named test for each invariant in Section 1.
2. Migrations reviewed, with a tested rollback.
3. rule\_set\_version, index\_version and model\_version recorded in the release note.
4. Synthetic data is labelled in every output.
5. A demo case runs end to end: healthy, abstain, and provider outage.
6. README updated: sources, versions, thresholds, known limits.
7. Team lead approves; keep the previous version ready to restore.

## SOP-13 Privacy and security

1. Never store applicant names, phone numbers, PAN, Aadhaar or account numbers in property or comparable tables. If a document must be kept, store it separately with access limited by role.
2. Mask personal data before anything is sent to the language model; the explainer receives only structured, non-identifying fields.
3. Aadhaar numbers are specially restricted by law; do not store them unless the lender's legal team confirms it is allowed and how.
4. Access by role: loan officers read and request; reviewers decide; admins manage sources and access.
5. Keep secrets in environment variables or a vault; use TLS in transit and disk or object-store encryption at rest.
6. Log who accessed what, and apply the lender's retention period.
7. Confirm consent and purpose handling under the Digital Personal Data Protection Act 2023 with the lender's compliance team.

**Record:** access list, retention policy, last review date.

# 17. Using the playbook with Cline

Cline is a coding agent that runs inside VS Code. It can read your project, edit files and run commands, asking your approval along the way. It cannot open this doc, so the playbook has to live inside your repository as files. Cline features and menu names change between versions, so check the current Cline documentation (docs.cline.bot) if something below does not match what you see.

## 17.1 How the pieces fit

| Piece | Where it lives | Job |
| --- | --- | --- |
| Playbook | docs/playbook/\*.md in the repo | The knowledge Cline reads for each task |
| Rules | .clinerules/ folder | Instructions Cline follows in every task |
| Workflows | .clinerules/workflows/\*.md | Reusable checklists you start with a slash command |
| Progress file | docs/PROGRESS.md | Cline's memory between tasks; mirrors the tracker page |
| Ignore file | .clineignore | Keeps secrets and big files out of Cline's view |

Cline has two modes. **Plan mode** reads and proposes but changes nothing. **Act mode** edits files and runs commands. Always plan first, approve the plan, then switch to Act.

## 17.2 One-time setup

1. Install the Cline extension in VS Code and add your model provider and API key.
2. Export this doc to Markdown from the doc menu. Split it into the files in the table below and put them in docs/playbook/. Small files let Cline read only what a task needs; the whole playbook in one go wastes its context.
3. Create the .clinerules folder with the files in 17.3.
4. Create .clineignore (below) and docs/PROGRESS.md (below).
5. Auto-approve: allow reading files only. Keep file edits and commands on manual approval until you trust the setup. Never auto-approve anything that touches .env or deletes data.
6. Commit this setup, then create a git branch for each task. Cline checkpoints help, but git is your real undo.

| Playbook section | Save as |
| --- | --- |
| 1 and 2 (goal, invariants, stack) | docs/playbook/01-overview.md |
| 3 and 14.2 (data sources) | docs/playbook/02-data-sources.md |
| 4, 14.4 and 15.3 (database) | docs/playbook/03-database.md |
| 7 (valuation) and 14.5 to 14.6 (cleaning, indicators) | docs/playbook/04-valuation-and-cleaning.md |
| 8 and 14.1 (compliance rules) | docs/playbook/05-compliance.md |
| 9 (prompts) | docs/playbook/06-prompts.md |
| 16 (procedures) | docs/playbook/07-sops.md |
| 14.7, 15 (commands, multi-state) | docs/playbook/08-commands-and-states.md |

.clineignore:

```
.env
.env.*
data/
raw/
*.pdf
*.parquet
models/
.venv/
node_modules/
```

docs/PROGRESS.md:

```
# Progress
Last updated:
## Done
## In progress
## Next
## Decisions and why
## Items to verify (sources, section numbers, thresholds)
## Versions: rule_set_version, index_version, model_version
```

## 17.3 The rules files

**.clinerules/00-project.md**

```
# Project
Member 4: property valuation, compliance and RAG for an Indian lender, multi-state, UP first.
Stack: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 with Alembic, Postgres 16 (pgvector, PostGIS),
Redis, MinIO, sentence-transformers (bge-small-en-v1.5), pytest, ruff, mypy.
Layout: backend/app/property, compliance, rag, agents. Tests mirror this under tests/.
The source of truth is docs/playbook/. Read docs/PROGRESS.md at the start of every task.
If code and playbook disagree, stop and ask me.
```

**.clinerules/01-hard-rules.md**

```
# Hard rules (never break)
1. Never fabricate property data, regulatory text, URLs, section numbers or thresholds. If unknown, write TODO-VERIFY and ask me.
2. Market facts, model estimates and regulatory evidence are separate objects, tables and report sections.
3. A finding with status potential_issue must carry at least one evidence reference; validation rejects it otherwise.
4. Low confidence, abstain, empty retrieval, provider failure or unsupported state sets human_review_required.
5. Wording is 'potential issue for review'. Never 'violation', 'compliant' or a legal conclusion.
6. Estimates carry is_estimate=true. The language model never decides flags, severity or estimates.
7. No protected-class attributes or proxies as valuation features.
8. Data and evidence never cross states: filter by state_code. Comparables come from the subject's own state.
9. Every comparable has price_type and area_basis. Asking prices never feed an estimate.
10. No personal data (names, phone, PAN, Aadhaar, account numbers) in property tables, logs or prompts.
11. Only sources with approved=true are collected. Do not scrape listing portals.
12. Thresholds and deadlines live in versioned config copied from retrieved text, not in code or memory.
13. Never edit raw records. Rejected rows are logged with a reason, never silently fixed.
```

**.clinerules/02-working-method.md**

```
# Working method
- Start in Plan mode. Read docs/PROGRESS.md and the playbook file I mention. Reply with: files to touch, tests to write, assumptions, questions. Wait for my approval.
- After approval: tests first, then code. Keep each change small enough to review in one sitting.
- Before saying done, run pytest, ruff check and mypy, and show the results.
- Database changes only through Alembic migrations.
- Do not add dependencies without telling me why.
- Never read or print .env. Never run commands that delete data or force-push.
- Update docs/PROGRESS.md at the end of every task.
```

**Workflows** (files in .clinerules/workflows/, started by typing a slash and the file name; if your Cline version lacks workflows, paste the text as a prompt):

```
finish-task.md
1. Run pytest, ruff check and mypy; show the output.
2. List which hard rules this change touches and the test that proves each.
3. Confirm no data, URL, section number or threshold was invented.
4. Update docs/PROGRESS.md and propose a commit message.

ingest-source.md   (SOP-2 and SOP-3 in docs/playbook/07-sops.md)
1. Ask me for the source details and signed approval; refuse if approved is false.
2. Download only from the official url I give, hash it, store it, skip if already ingested.
3. Parse, chunk, tag with scope, state_code, version and dates, embed into a NEW index_version.
4. Run the retrieval gold set; do not switch the active index if hit@5 drops.

add-rule.md   (SOP-6)
1. Ask for the requirement in plain words; find the evidence by retrieval; show me the snippet.
2. Define inputs and the check; put thresholds in config copied from the snippet.
3. Write four tests: no issue, potential issue, missing data, empty retrieval.
4. Bump rule_set_version and run the regression cases.

onboard-state.md   (SOP-10)
1. Create the jurisdiction pack with blanks for anything unverified; ask me to fill them.
2. Walk the 13-step checklist one step at a time; stop at each step for my confirmation.
3. Run the isolation test: no evidence or data crosses states.
```

## 17.4 Task by task

For each task, open a fresh Cline task (long conversations drift and get expensive). Use this wrapper, replacing the bracketed parts:

```
Task: [name]. Read docs/PROGRESS.md and @docs/playbook/[file]. Use prompt [P-number] from @docs/playbook/06-prompts.md.
Plan mode first: list files to create or change, tests to write, assumptions and questions. Do not write code until I approve.
```

After you approve the plan, switch to Act mode and say: Approved. Implement in the order planned, tests first. When done, run the finish-task workflow.

| Step | Task | Playbook files to mention | Prompt | Done when |
| --- | --- | --- | --- | --- |
| 1 | Environment and Docker setup | 07-sops (SOP-1), 01-overview | none | Services start, migrations apply, tests pass |
| 2 | Schemas and migration | 03-database, 01-overview | P1 | Validators reject evidence-less findings |
| 3 | Source registry and regulatory ingestion | 02-data-sources, 07-sops (SOP-2, 3) | P2 | Re-running adds no duplicates; chunks match source |
| 4 | Retrieval and evidence builder | 05-compliance, 03-database | P3 | Gold set hit@5 reported; empty result on out-of-scope query |
| 5 | Provider interface, fixtures, loaders | 02-data-sources, 04-valuation-and-cleaning | P5 | Provider failure raises an error, never returns rows |
| 6 | Cleaning pipeline (India) | 04-valuation-and-cleaning, 07-sops (SOP-5) | adapt P5 | Rejects logged; gates enforced |
| 7 | Valuation | 04-valuation-and-cleaning | P6 | Abstains under 3 comps; backtest numbers printed |
| 8 | Compliance rules | 05-compliance, 07-sops (SOP-6) | P4 | Four tests per rule pass |
| 9 | Agents and shared state | 01-overview, 05-compliance | P7 | End-to-end fixture cases run; audit events emitted |
| 10 | Loan officer commands and roles | 08-commands-and-states, 07-sops (SOP-7) | none | Roles enforced; every command audited |
| 11 | Multi-state pack and isolation tests | 08-commands-and-states, 07-sops (SOP-10) | none | UP case never gets another state's evidence |
| 12 | Test gaps and release | 07-sops (SOP-12) | P8 | Every invariant has a named test |

After each step, tick it in the tracker page and in docs/PROGRESS.md.

## 17.5 What you must still do yourself

Cline writes code; it does not make the project correct. After each task:

1. Read the diff. Look for invented values: URLs, section numbers, thresholds, sample property data presented as real.
2. Run the tests yourself, and read at least one test to see whether it checks something meaningful.
3. Try to break it: remove a source, return an empty result, give a property from another state.
4. Check every regulatory citation against the real source text before it goes into config.
5. Commit only when the finish-task workflow passes and you understand the change.

## 17.6 If Cline struggles

| Problem | Fix |
| --- | --- |
| Loses track or repeats itself | Start a new task; mention only the one playbook file and PROGRESS.md |
| Invents a URL, rule or number | Point to hard rule 1, ask it to mark TODO-VERIFY, and fill the value yourself from the official source |
| Changes too many files | Reject the plan; ask for a smaller first slice |
| Tries to scrape a portal | Point to hard rule 11; use SOP-2 first |
| Wants to read data or secrets | Confirm .clineignore; keep auto-approve off for commands |
| Costs too high | Use shorter tasks and fewer mentioned files; plan in Plan mode and keep Act mode runs short |

Optional: connect a read-only Postgres tool so Cline can inspect table contents without writing. Use a database user that can only read, and never point it at production data.

# 18. Solo approver mode and multi-state from day one

This section overrides parts of SOP-2 (team lead sign-off) and Section 14.2 (bank reports as priority 1) for the case where you are the only approver and no lender data is available.

## 18.1 What changes

| Before | Now |
| --- | --- |
| Team lead signs source approvals | You approve, but only through a written checklist and a log entry |
| Bank valuation reports are the best source | Not available. Do not fake or guess them; treat lender data as an optional later add-on |
| UP pilot, other states later | Core is multi-state from the start; states are added one at a time after a short recon |
| Estimates validated against bank valuations | Validated by backtest on public registered-sale data where it exists; otherwise outputs are labelled indicative only |

You can approve public sources yourself. You cannot approve someone else's private data for yourself: loan files, borrower records or licensed datasets need the owner's permission, and that permission is theirs to give.

## 18.2 Source approval checklist (you fill this for every source)

1. Is the publisher the official authority (government department, regulator, central bank, exchange)? If not, mark it unofficial and use it only for indicators.
2. What do the terms of use say about automated or bulk access? Save a dated copy of the terms page.
3. Do the terms allow reuse for this purpose?
4. Does the data contain personal data? Registered deeds usually name buyers and sellers: drop those fields at ingestion and never store them.
5. Is it free, paid or licensed? Licensed data needs the licence in hand before any download.
6. Does it give a date or version so you can cite it?
7. How will you get it: official download, API, or manual copy of a small sample?
8. Does the portal use a CAPTCHA or login on each search? That is a signal against automation. Do not bypass it; use manual samples only if the terms allow, otherwise skip the source.
9. What happens if this data is wrong or stale?
10. Decision, date, your name, and the date you will re-check (6 months).

Rules: any answer you cannot establish means not approved. Never approve a source because it is convenient. Never scrape listing portals (their terms forbid it, and listings are asking prices).

Schema change so the database enforces this:

```sql
ALTER TABLE data_source
  ADD COLUMN approved_by text, ADD COLUMN approved_at date,
  ADD COLUMN terms_snapshot_sha256 text, ADD COLUMN review_due date,
  ADD COLUMN decision_note text,
  ADD CONSTRAINT approved_needs_record
    CHECK (NOT approved OR (approved_by IS NOT NULL AND approved_at IS NOT NULL AND terms_snapshot_sha256 IS NOT NULL));
```

Example registry entry (sources.yaml):

```yaml
- name: Maharashtra Ready Reckoner rates
  authority: Government of Maharashtra, Registration and Stamps Department
  kind: public_records
  url: TODO-VERIFY
  terms_url: TODO-VERIFY
  state_code: MH
  automated_access_allowed: unknown     # unknown means not approved
  contains_personal_data: false
  approved: false
  approved_by: null
  approved_at: null
  review_due: null
```

## 18.3 What replaces bank data

| Need | Source | Note |
| --- | --- | --- |
| Real sale prices | State registration portals where they allow access; county-level open data where published | Check each portal's terms (checklist item 2 and 8); expect gaps |
| Government guideline values | State registration or revenue department publications | Different name and unit per state; verify |
| Project data | State RERA portals | Project level; carpet area is useful |
| Market indicators | RBI Residential Property Price Index (selected cities), NHB Residex, data.gov.in | City level only |
| Licensed transactions | PropEquity, Liases Foras, Anarock and similar | Paid; only if you or your organisation hold a licence |
| Test data | Synthetic generator, labelled synthetic | Never present as real |

Without lender data, the system cannot say how accurate it is against bank valuations. State that in the README and in every report: outputs are indicative decision support, not a valuation for credit decisions.

## 18.4 Multi-state from day one

Design rules:

1. state\_code is required on every property, comparable, circle rate, regulatory document and finding. No default state anywhere.
2. The synthetic generator reads a state pack and produces comps for any state with that state's localities and a plausible price range, all labelled synthetic.
3. Build and test with three synthetic states from the start (for example UP, MH, KA). This proves isolation before you have any real data.
4. Required tests: a UP case never receives MH evidence; comps never cross states; an unsupported state escalates; units convert only from that state's pack.
5. Real data arrives per state through SOP-10, one state at a time, and does not block the core build.

## 18.5 State recon (one day per state, before onboarding)

For each candidate state, fill one row and decide its tier (Section 15.5):

1. Registration portal: what can you see (sale price, area, date, locality)? Terms of access? CAPTCHA or login?
2. Guideline value: published name, unit, how often it changes, downloadable or search only?
3. RERA portal: project list, carpet area, status, downloadable or search only?
4. Local land units used and their official conversions.
5. State-specific rules you must ingest (RERA rules, stamp duty, registration act).
6. Tier A, B or C, with one sentence of reasoning.
7. Decide: onboard now, later, or not.

Candidate starting list (names and addresses below are from memory; confirm each from the state government's own site before approving):

| State | Registration portal | RERA portal | Guideline value name |
| --- | --- | --- | --- |
| Uttar Pradesh | igrsup.gov.in | up-rera.in | Circle rate |
| Maharashtra | igrmaharashtra.gov.in | maharera.maharashtra.gov.in | Ready Reckoner rate |
| Karnataka | kaveri.karnataka.gov.in | rera.karnataka.gov.in | Guidance value |
| Tamil Nadu | tnreginet.gov.in | tnrera.in | Guideline value |
| Telangana | registration.telangana.gov.in | rera.telangana.gov.in | Market value |
| Delhi | Revenue department site (verify) | rera.delhi.gov.in | Circle rate |

Pick your first onboarding wave by what the recon shows (best data access), not only by market size. Two or three states is plenty for a first wave.

## 18.6 Revised workflow

| Phase | Do | Output |
| --- | --- | --- |
| 0. Governance (day 1) | Create the approval checklist and log; add the data\_source columns above; write the scope in PROGRESS.md | Log ready; no source approved yet |
| 1. Core on synthetic data (weeks 1 to 2) | Schemas, synthetic generator for 3 states, cleaning, valuation, isolation tests | Estimate or abstain per state, tests pass |
| 2. National evidence (weeks 2 to 3) | Approve and ingest RBI, NHB, RERA Act, SARFAESI, KYC texts; retrieval and evidence builder | Gold set results |
| 3. Recon (week 3, in parallel) | One recon row per candidate state; pick wave 1 | Recon table, tiers |
| 4. Rules and agents (weeks 3 to 4) | 3 starter rules, agents, shared state, first commands | End-to-end synthetic case |
| 5. State onboarding, one at a time | SOP-10 for each wave 1 state | State status pilot |
| 6. Hardening | Backtests where real data exists; release checks (SOP-12) | Release note with stated limits |

## 18.7 First three tasks to do now

1. Add the data\_source columns and the constraint, and write the approval checklist as docs/approval-checklist.md.
2. Approve your first two sources: the RERA Act text (India Code) and one RBI direction. They are public and official, so they make a safe test of the process.
3. Write the synthetic generator that reads a state pack, and generate 3 states.

Everything that cannot be verified yet stays as TODO-VERIFY, and a source stays unapproved until the checklist is complete.

# 19. Verified source notes and design additions (checked 10 October 2026)

I checked the claims in the architecture notes you pasted, and some of my own earlier statements, against official or primary pages where I could find them. Where only blogs or news sites confirmed something, the table says so. Re-check anything before you rely on it: portals change.

## 19.1 What checked out

| Claim | Result | Basis |
| --- | --- | --- |
| State registration departments (the state IGR) are the custodians of registration data | Confirmed | Department of Land Resources (DoLR) NGDRS page |
| NGDRS is built by DoLR with NIC and deployed as state-specific instances | Confirmed | DoLR and NeGD pages |
| 13 states or UTs share data with the national NGDRS portal through user interface or API: Andhra Pradesh, Chandigarh, Haryana, Gujarat, Madhya Pradesh, Odisha, Puducherry, Rajasthan, Sikkim, Tamil Nadu, Telangana, Uttar Pradesh, West Bengal; 31 states and UTs covered | Confirmed, with caveats | DoLR page (undated; a DoLR monthly summary of February 2024 also gives 31 covered). This is data sharing with the national portal, not open access for you |
| The national portal ngdrs.gov.in shows dashboards drawn from state servers | Confirmed for statistics | National portal home page. I did not confirm a state directory page, and statistics are not individual sale records |
| Uttar Pradesh: igrsup.gov.in, circle rates published by district | Confirmed | District NIC page ties the site to the Stamp and Registration Department. Some blogs expand the acronym as a grievance system; rely on official pages |
| Maharashtra: igrmaharashtra.gov.in with e-search, Index II and Ready Reckoner | Confirmed | Blogs and finance sites only; free search is described as uncertified and informational. A data policy PDF is reported on the site: read it |
| Maharashtra portal address given in the pasted notes (isarita.igrmaharashtra.gov.in/PDE\_2\_0) | Not verified | Use igrmaharashtra.gov.in until you confirm it |
| Karnataka: kaveri.karnataka.gov.in, guidance value on the registration side; land records (RTC) on Bhoomi | Confirmed | Several portal guides |
| Tamil Nadu: tnreginet.gov.in, guideline value; separate record portal | Confirmed | Several portal guides |
| Telangana: registration.telangana.gov.in, market value search | Confirmed | NeGD directory plus portal guides |
| Gujarat: garvi.gujarat.gov.in, jantri rate (guideline value) | Confirmed | Revenue Department references and an audit report. Sources disagree on what GARVI stands for; it does not matter for you |
| Haryana Jamabandi (jamabandi.nic.in) is a record of rights for ownership and cultivation, not a sale-price source | Confirmed | Portal guides |
| UP-RERA: up-rera.in with registered-project search | Confirmed | One guide says searches use a CAPTCHA, which matters for checklist item 8 |
| Propstack sells residential transaction data and offers API access | Partly confirmed | Its own home page claims over a million sale, rent and loan transactions across more than 5,000 projects, a large private repository of registered sale, lease and mortgage data, and data through APIs. The copy appears to date from 2021, and it gives no state list, field list or date range. Ask them |
| Rajasthan e-Panjiyan, Andhra Pradesh IGRS, RERA portals for Maharashtra, Karnataka, Tamil Nadu, Telangana and Delhi | Not verified | Keep as TODO-VERIFY |

## 19.2 Corrections to my earlier sections

1. **RBI price index.** I called it the Residential Property Price Index and asked you to confirm Lucknow. RBI now publishes the House Price Index (HPI), base year 2022-23, built from transaction data supplied by registration authorities. It covers 18 cities, and Lucknow is included: Mumbai, Delhi, Chennai, Kolkata, Bangalore, Lucknow, Ahmedabad, Jaipur, Kanpur, Kochi, Hyderabad, Thiruvananthapuram, Pune, Ghaziabad, Thane, Gautam Buddha Nagar, Chandigarh and Nagpur. The latest I found is Q1 of 2026-27, released 24 August 2026. Time series are on RBI's DBIE portal (data.rbi.org.in). Use HPI wherever sections 3, 14 and 18 mention the older name, and tag it as a city-level indicator, never a property price.
2. **NHB Residex.** I did not verify that it is still published. Treat as TODO-VERIFY.
3. **Section 18.5 table.** Only the UP-RERA address is verified. The other RERA addresses were from memory.
4. **Delhi.** The NGDRS Delhi site (ngdrs.delhi.gov.in) describes itself as Delhi's online registration system; the registration-data access route still needs a recon row.
5. **Maharashtra deeds.** Index II summarises parties, price, market value, area and duty. Drop party names at ingestion, as in checklist item 4.

## 19.3 Design additions adopted from the pasted notes

These were checked against the playbook and fit it. The notes' own valuation table and scheduler skeleton are not adopted (see 19.5).

1. **Capabilities start as unknown.** Each source records how it can be accessed and what it supports, with unknown meaning not approved.
2. **Record types.** Sale records, guideline values and land records are kept apart and never merged. Land records (such as Haryana Jamabandi) show ownership, not prices.
3. **Fingerprint instead of a nullable ID.** Many public sources have no stable record ID. Build a fingerprint from documented stable fields and keep the raw record. A unique key on a nullable ID does not catch duplicates, because each NULL counts as different in Postgres.
4. **Freshness per source.** Track last attempt, last success and last error, plus a refresh interval set per source.

```sql
ALTER TABLE data_source
  ADD COLUMN access_mode text NOT NULL DEFAULT 'access_pending'
    CHECK (access_mode IN ('access_pending','official_api','official_download','portal_manual','licensed_feed','not_permitted')),
  ADD COLUMN supports_transactions boolean,        -- NULL means not verified
  ADD COLUMN supports_guideline_values boolean,
  ADD COLUMN supports_land_records boolean,
  ADD COLUMN refresh_interval_days int,
  ADD COLUMN last_attempt_at timestamptz,
  ADD COLUMN last_success_at timestamptz,
  ADD COLUMN last_error text;

-- run before loading any data
ALTER TABLE raw_record
  ADD COLUMN record_type text NOT NULL DEFAULT 'registered_transaction'
    CHECK (record_type IN ('registered_transaction','guideline_value','land_record','listing','survey')),
  ADD COLUMN record_fingerprint text NOT NULL,
  ADD CONSTRAINT raw_record_dedupe UNIQUE (source_id, record_type, record_fingerprint);
```

Fingerprint recipe: sha256 of source id, document or registration number, sub-registrar office, registration date, recorded consideration and area. Never include buyer or seller names.

A source cannot be set to approved while its access\_mode is access\_pending or not\_permitted. Add that to the approval constraint in section 18.2.

## 19.4 Valuation scope by property type

The pasted notes list what matters for each type. Treat this as design guidance, not verified fact.

| Type | Main comparable attributes | Status in your build |
| --- | --- | --- |
| Residential flat | Locality, carpet or built-up area, bedrooms, age, floor, amenities | Supported first |
| Independent house | Plot area, built-up area, age, condition, road access | Later |
| Vacant plot | Land area, zoning, frontage, land use, development status | Later |
| Commercial | Use, floor area, frontage, occupancy, lease terms | Later |
| Industrial or warehouse | Land and built-up area, clear height, loading access, power | Later |
| Agricultural land | Land area, irrigation, soil, land-use class, access | Later |

For every type except the first, the valuation returns abstain with reason unsupported\_property\_type and escalates. Add each type only with its own tests and backtest.

## 19.5 What I did not adopt

1. The notes' valuation table has no is\_estimate flag, comparable ids, abstain reason or state code. Keep the contract from your design file.
2. The notes have no compliance, evidence, audit, state-isolation or loan officer parts, and no India cleaning for units and rupee prices.
3. The scheduler code is a skeleton with undefined functions. A fixed six-hour refresh does not suit slow sources; use refresh\_interval\_days per source.

## 19.6 Questions to ask a commercial provider (for example Propstack) before any agreement

1. Which states, cities and property types are covered, and from which dates?
2. Is the data registered sale deeds, valuer reports, or modelled? What share is each?
3. Field list and sample records, including area basis and price type.
4. Update frequency and the lag between registration and delivery.
5. Are buyer and seller names included? (You must not store them.)
6. Permitted uses, retention period and redistribution rights, in writing.
7. API limits, authentication, uptime and support terms.
8. Price, and whether the licence covers a lender's credit decisions.

No commercial source is approved until you hold the licence and finish the checklist in section 18.2.
