# Gemini Project Instructions: Indian Residential Property Valuation Agent

## 1. Project Purpose

Build a Python-first backend for an Indian residential property valuation agent.

The agent should estimate a residential property's market value using eligible comparable-property evidence, transparent calculations, and clear uncertainty handling.

### Scope

- Backend only. Do not build a frontend.
- Focus only on the property valuation agent.
- Do not implement compliance, regulatory RAG, document-understanding, or other agents in this phase.
- Use PostgreSQL with PostGIS for structured and geographic data.
- Support multiple Indian states from the start at the schema and provider-interface level.
- Initial state candidates:
  - Uttar Pradesh
  - Maharashtra
  - Karnataka
  - Telangana
- Treat these states as source-discovery candidates, not as confirmation that their data is available for bulk download or model training.
- Prefer official government or explicitly authorized sources.
- Synthetic data is permitted for tests and development fixtures only. Clearly label it as synthetic and never present it as real market evidence.

## 2. Core Safety and Data Principles

1. Never fabricate property records, transactions, prices, locations, or source references.
2. Never treat government circle rates, guidance values, ready-reckoner rates, or other administrative reference values as actual sale prices.
3. Never treat asking prices from listings as verified transaction prices.
4. Store transaction records, listings, and government reference rates separately.
5. A government website being publicly viewable does not automatically grant permission for bulk collection, redistribution, or model training.
6. Do not bypass login controls, CAPTCHA, rate limits, access restrictions, or provider terms.
7. Do not ingest or redistribute data unless its intended use is authorized.
8. Preserve provenance for every record: source, source record ID, retrieval time, publication/effective date where relevant, source URL, license/permission status, and transformation version.
9. Do not silently drop or silently impute data. Record rejected or quarantined rows and the reason for each decision.
10. Do not collect unnecessary personal information about buyers, sellers, or owners.
11. Do not use protected-class attributes or proxies as valuation features.
12. If data is insufficient, contradictory, stale, or poorly verified, abstain or request human review rather than producing an unjustified estimate.
13. Distinguish source authenticity from transaction verification and individual-attribute verification.
14. Keep raw values and original units alongside normalized values.
15. Never claim that a state-specific valuation model is validated on real market data unless a suitable independent evaluation set exists.

## 3. State and Data-Source Readiness

### Initial state candidates

| State | Source-discovery starting point | Current readiness |
|---|---|---|
| Uttar Pradesh | IGRSUP registration and circle-rate services: https://igrsup.gov.in/ | Government search services identified; open bulk transaction API and reuse rights not confirmed |
| Maharashtra | IGR Maharashtra: https://esearchigr.maharashtra.gov.in/ ; eASR: https://easr.igrmaharashtra.gov.in/ | Registration search and reference-rate services identified; bulk transaction access and reuse rights not confirmed |
| Karnataka | Kaveri 2.0: https://kaveri.karnataka.gov.in/ | Registration/property services identified; bulk historical transaction access and reuse rights not confirmed |
| Telangana | Government land and market-value services; start at https://services.india.gov.in/ | Market-value/land-detail services identified; bulk verified residential transaction access and reuse rights not confirmed |

These are starting points for source verification, not guarantees of API availability, completeness, or permission to use data for model training. Recheck current official sources before implementation decisions.

### Required source-readiness register

Create `data/source_readiness.csv` with at least these fields:

- `state_code`
- `source_name`
- `source_url`
- `data_category`
- `access_method` (API, downloadable file, manual authorized export, licensed provider, unknown)
- `api_available` (true, false, unknown)
- `sample_download_available` (true, false, unknown)
- `historical_coverage`
- `residential_coverage`
- `transaction_price_available` (true, false, unknown)
- `license_review_status` (approved, pending_review, restricted, rejected)
- `commercial_use_allowed` (true, false, unknown)
- `redistribution_allowed` (true, false, unknown)
- `last_checked_at`
- `evidence_url`
- `next_action`
- `decision`

Use `unknown` when access or permission has not been tested. Do not convert unknown into false.

### Source approval gate

Do not implement an automated state-specific adapter until:

1. The source has been identified and checked.
2. The data fields and geographic/time coverage are documented.
3. The retrieval method is known and permitted.
4. Intended research, commercial, storage, and redistribution uses have been reviewed.
5. A small sample can be retrieved and validated, where access allows.
6. A person responsible for source approval records the decision.

If no authorized transaction-price data is available, keep reference rates separate and use synthetic fixtures only for software testing. Do not manufacture real transaction labels.

## 4. Dataset Design

Use separate logical datasets and database tables. Do not combine all source types into a single training CSV.

### 4.1 `data_source`

Purpose: track provider identity, permission, and reliability.

Recommended fields:

- `source_id` (UUID primary key)
- `source_name`
- `state_code`
- `source_type` (government, authorized_provider, manual_authorized_import, synthetic_test)
- `official_url`
- `access_method`
- `license_scope`
- `approval_status` (pending_review, approved, suspended, rejected)
- `terms_url`
- `last_checked_at`
- `last_successful_sync_at`
- `created_at`
- `updated_at`

### 4.2 `property_record`

Purpose: store stable property identity and property attributes.

Recommended fields:

- `property_id` (stable internal UUID)
- `source_id`
- `source_record_id`
- `state_code`
- `district`
- `city`
- `locality`
- `pincode` (nullable)
- `property_type` (apartment, independent_house, villa, residential_plot, other_residential)
- `area_value_raw`
- `area_unit_raw`
- `area_sqft` (nullable)
- `area_type` (carpet, built_up, super_built_up, plot, unknown)
- `bedrooms` (nullable)
- `bathrooms` (nullable)
- `construction_year` (nullable)
- `location` (PostGIS geography point, nullable when unavailable)
- `source_authenticity_status`
- `attribute_verification_status`
- `source_url`
- `source_record_hash`
- `raw_payload` (only where storage is permitted)
- `retrieved_at`
- `published_at` (nullable)
- `created_at`
- `updated_at`

Use a unique constraint on `(source_id, source_record_id)` where stable source IDs exist. Do not create false property identities when records cannot be matched reliably.

### 4.3 `property_transaction`

Purpose: store individual sale or transfer evidence.

Recommended fields:

- `transaction_id` (UUID primary key)
- `property_id` (nullable if the property match is uncertain)
- `source_id`
- `source_transaction_id`
- `transaction_date`
- `transaction_price_raw`
- `transaction_price_unit_raw`
- `transaction_price_inr` (nullable)
- `price_type` (sale_consideration, reported_sale_price, unknown)
- `transaction_verification_status` (unverified, verified, rejected)
- `source_url`
- `source_record_hash`
- `retrieved_at`
- `raw_payload` (only if permitted)

Use a unique constraint on `(source_id, source_transaction_id)` when stable transaction IDs exist. Do not treat a registration fee, stamp-duty value, circle rate, or asking price as sale consideration unless the source explicitly establishes that meaning.

### 4.4 `property_listing`

Purpose: store asking-price evidence separately from transactions.

Recommended fields:

- `listing_id`
- `property_id` (nullable if identity is uncertain)
- `source_id`
- `source_listing_id`
- `asking_price_raw`
- `asking_price_inr`
- `listing_date`
- `listing_status`
- `source_url`
- `retrieved_at`
- `source_record_hash`

Only ingest listings from providers whose applicable terms permit the intended collection and use.

### 4.5 `reference_rate`

Purpose: store official circle rates, guidance values, ready-reckoner rates, or similar administrative benchmarks.

Recommended fields:

- `rate_id`
- `source_id`
- `state_code`
- `district`
- `locality`
- `property_category`
- `rate_raw`
- `rate_unit_raw`
- `rate_inr_normalized` (nullable; contract/schema exposed as `rate_inr_per_sqft` per F-17, INR per square foot; physical DB column maintains historical `rate_inr_normalized` name)
- `effective_from`
- `effective_to`
- `published_at`
- `source_url`
- `retrieved_at`
- `source_record_hash`

Never use this table as if it were a verified sale-transaction table.

### 4.6 `ingestion_run`

Recommended fields:

- `run_id`
- `source_id`
- `started_at`
- `finished_at`
- `run_status`
- `rows_received`
- `rows_accepted`
- `rows_quarantined`
- `rows_duplicate`
- `rows_rejected`
- `build_version`
- `source_snapshot_hash`
- `error_summary`

Every ingestion run must account for all received rows. Define mutually understandable row-count semantics and test the accounting invariant.

### 4.7 `valuation_run` and `valuation_comparable`

`valuation_run` should store:

- `valuation_id`
- `subject_property_input`
- `estimate_inr`
- `lower_bound_inr` (nullable)
- `upper_bound_inr` (nullable)
- `status` (completed, abstained, needs_human_review, failed)
- `reason_codes`
- `method_version`
- `dataset_cutoff`
- `created_at`

`valuation_comparable` should store:

- `valuation_id`
- `transaction_id`
- `distance_m`
- `similarity_score` (if defined and validated)
- `adjusted_price_per_sqft`
- `selection_reason`

Every estimate must be traceable to the eligible evidence used.

## 5. Unit Conversion and Normalization

Preserve raw values and units. Apply versioned, tested conversions:

- ₹1 lakh = ₹100,000
- ₹1 crore = ₹10,000,000
- 1 square metre = approximately 10.7639104167 square feet
- 1 square yard = 9 square feet

Rules:

1. Do not infer an unknown unit from the numeric value alone.
2. Do not equate carpet, built-up, super built-up, and plot area.
3. Do not calculate price per square foot if the price or compatible area basis is missing or invalid.
4. Calculate normalized price per square foot from validated price and area; do not blindly trust a provider's supplied figure.
5. Store the conversion version and original source values.
6. Add tests for rounding, boundary values, malformed numbers, lakh/crore formats, and unit conversion.
7. Keep unknown area type as `unknown`; never silently assign a likely area type.

## 6. Data Cleaning, Duplicates, and Outliers

### Rejection and quarantine

Do not silently drop invalid records. Write invalid rows to a quarantine dataset with:

- `run_id`
- `source_id`
- `source_record_id` when available
- `reason_code`
- `reason_detail`
- `rejected_at`
- a safe reference to the raw row, subject to source permissions

Typical reason codes include:

- `MISSING_PRICE`
- `MISSING_AREA`
- `INVALID_UNIT`
- `INVALID_DATE`
- `INVALID_COORDINATES`
- `UNSUPPORTED_PROPERTY_TYPE`
- `DUPLICATE_RECORD`
- `SOURCE_NOT_APPROVED`
- `PRICE_TYPE_NOT_ELIGIBLE`
- `AREA_BASIS_INCOMPATIBLE`
- `PROVENANCE_MISSING`

A row can be retained for audit but excluded from valuation eligibility. Clearly distinguish rejected, quarantined, duplicate, and accepted counts.

### Deduplication

- Use stable source IDs whenever available.
- Use cautious fingerprint matching only as a secondary method.
- Do not merge records solely because their prices, locality names, or approximate coordinates match.
- Preserve repeat sales as separate transactions.
- Make imports idempotent: importing the same snapshot twice must not create duplicate records.

### Outlier flags

Use locality-aware robust checks only when group size is sufficient. A possible robust score is:

`robust_z = 0.67449 * (value - median) / MAD`

where `MAD` is the median absolute deviation.

- Handle zero MAD and small groups explicitly.
- Flag outliers for review rather than automatically deleting them.
- Keep the original value and record the rule/version that generated the flag.
- Do not treat every expensive or inexpensive property as erroneous.

## 7. Geographic and Evaluation Leakage Prevention

A fixed random seed gives reproducibility but does not prevent leakage.

Implement split logic that:

1. Keeps records belonging to the same known property in one partition.
2. Keeps linked listings and transactions for the same property in one partition where appropriate.
3. Uses a temporal holdout to simulate valuation on later transactions.
4. Uses locality-level or geographic holdouts when sample sizes permit.
5. Fits any data-derived preprocessing only on training data.
6. Records the split manifest, seed, algorithm version, dates, and geographic groups.
7. Reports performance separately by state, city/locality, and property type when sample size permits.

If there are too few localities or verified transactions for a reliable holdout, report that limitation rather than claiming strong generalization.

## 8. Valuation Eligibility and Abstention

A record is not eligible as a comparable merely because it contains a price.

Eligibility should consider:

- approved source and permitted use
- verified or appropriately qualified transaction-price evidence
- residential property type
- valid transaction date
- valid price and compatible area basis
- valid coordinates or sufficiently reliable location
- duplicate status
- source and attribute verification status
- relevant market period and geographic proximity

The valuation agent should:

1. Identify comparable residential transactions.
2. Filter by property type and compatible area basis.
3. Search nearby properties and expand distance/time windows only when justified.
4. Record each filter and expansion.
5. Calculate adjusted price-per-square-foot values only from eligible evidence.
6. Use a transparent robust estimator, such as a weighted median, where appropriate.
7. Calculate uncertainty intervals only when the number and quality of comparables support them.
8. Abstain or request human review when comparable evidence is insufficient, highly dispersed, stale, inconsistent, or poorly located.

Do not claim an 80% interval is calibrated unless it has been tested against an independent evaluation set.

## 9. Recommended Project Structure

```text
property-valuation-agent/
├── backend/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── schemas/
│       │   ├── property.py
│       │   ├── transaction.py
│       │   ├── source.py
│       │   └── valuation.py
│       ├── ingestion/
│       │   ├── provider.py
│       │   ├── registry.py
│       │   ├── normalize.py
│       │   ├── validate.py
│       │   ├── deduplicate.py
│       │   └── quarantine.py
│       ├── providers/
│       │   ├── up/
│       │   ├── maharashtra/
│       │   ├── karnataka/
│       │   └── telangana/
│       ├── database/
│       │   ├── models.py
│       │   ├── connection.py
│       │   └── repository.py
│       └── valuation/
│           ├── comps.py
│           ├── estimate.py
│           └── confidence.py
├── data/
│   ├── raw/
│   ├── processed/
│   ├── quarantine/
│   ├── reference_rates/
│   ├── synthetic/
│   ├── source_readiness.csv
│   ├── schema.md
│   └── DATA_CARD.md
├── scripts/
│   ├── check_sources.py
│   ├── import_dataset.py
│   ├── validate_dataset.py
│   └── build_dataset.py
├── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── evaluation/
├── reports/
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

State provider folders may remain empty until authorized data access is confirmed. Do not create fake adapters that pretend an API is available.

## 10. Implementation Sequence and Definition of Done

### Step 1: Source-readiness audit

Tasks:
- Create the source register for Uttar Pradesh, Maharashtra, Karnataka, and Telangana.
- Verify current official URLs and available services.
- Record whether API access, bulk files, historical coverage, transaction price, and reuse permissions are confirmed.
- Record evidence and the next action for every source.

Done when:
- Every candidate source has a documented status.
- Unknown values remain explicitly unknown.
- No data source is marked approved without a recorded permission decision.

### Step 2: Canonical schema and validators

Tasks:
- Implement strict Pydantic v2 schemas.
- Define enumerations and database constraints.
- Add unit conversion helpers.
- Implement provenance requirements and reason-coded validation.

Done when:
- Invalid values fail predictably.
- Unknown optional attributes remain nullable or explicitly unknown.
- Unit conversion and price-per-square-foot tests pass.

### Step 3: One approved ingestion path

Tasks:
- Choose the first source that passes the access and permission gate.
- Implement an API, permitted file importer, or authorized manual import.
- Store source metadata and a hash of each permitted source snapshot.
- Write rejected records to quarantine.
- Add repeat-import/idempotency handling.

Done when:
- A real, permitted sample can be imported reproducibly.
- All received rows are accounted for.
- A second import does not create duplicates.

### Step 4: PostgreSQL and PostGIS

Tasks:
- Implement database models and migrations.
- Add unique constraints and spatial indexes.
- Validate coordinates and state/locality mappings.
- Test transaction rollback and spatial queries.

Done when:
- Schema migrations succeed on a clean database.
- Duplicate and invalid records are handled safely.
- Spatial comparable searches return expected test results.

### Step 5: Multi-state expansion

Tasks:
- Apply the same provider interface and schema to the remaining states.
- Add a state only after its source passes the readiness gate.
- Keep source-specific raw fields and transformations documented.

Done when:
- Each enabled state has evidence of source permission and data coverage.
- Unsupported states return an explicit data-unavailable result rather than fabricated records.

### Step 6: Valuation and evaluation

Tasks:
- Implement comparable selection, robust estimation and abstention.
- Build tests for insufficient comparables, stale data, area incompatibility, outliers, and poor geographic coverage.
- Use time-based and locality-based holdouts where possible.
- Publish evaluation results and limitations.

Done when:
- Every estimate is reproducible from stored evidence.
- Unsupported cases abstain or require human review.
- Performance claims match the actual quality and coverage of the evaluation data.

## 11. Testing Checklist

### Unit tests

- Strict schema validation
- Lakh/crore conversion
- Square metre/square yard conversion
- Compatible-area checks
- Price-per-square-foot calculation
- Missing and malformed values
- Invalid dates and coordinates
- Duplicate detection
- Outlier handling with zero MAD and small groups
- Provenance enforcement
- Reference-rate and transaction separation
- Deterministic build and split manifests

### Integration tests

- PostgreSQL constraints
- PostGIS distance queries
- Migrations from an empty database
- Transaction rollback
- Idempotent imports
- Source approval checks
- Quarantine persistence
- Valuation evidence traceability

### Evaluation tests

- Temporal holdout
- Locality holdout where feasible
- Performance by state and property type
- Coverage and abstention rate
- Error distribution and large-error cases
- Confidence-interval calibration, if intervals are produced
- Data leakage checks

Use synthetic fixtures for deterministic tests, but label them clearly and never include them in reported real-world accuracy metrics.

## 12. Data Card Requirements

Create `data/DATA_CARD.md` and maintain it as the dataset changes.

Include:

- Purpose and intended users
- Source names and official URLs
- Licence and permission status
- Collection timestamps and source snapshot hashes
- Geographic and temporal coverage
- Counts by state, locality, property type, and price type
- Source and transaction verification levels
- Accepted, duplicate, quarantined, and rejected counts
- Unit conversions and transformations
- Asking-price versus transaction-price limitations
- Government reference-rate limitations
- Evaluation split methodology
- Known biases and missing coverage
- Update schedule and source failure policy
- Privacy and retention controls

## 13. Suggested Dependencies

Use a minimal Python backend stack. Pin exact versions in a lockfile after testing the target environment.

```text
fastapi
uvicorn[standard]
pydantic>=2.9,<3.0
pydantic-settings
sqlalchemy>=2.0,<3.0
alembic
psycopg[binary]
geoalchemy2
pandas
numpy
pyarrow
httpx
tenacity
python-dateutil
scipy
scikit-learn
pytest
pytest-cov
hypothesis
ruff
mypy
pre-commit
```

Notes:
- PostgreSQL and PostGIS are server components and must be installed/configured separately.
- `python-multipart` is needed only if the API accepts multipart file uploads.
- `geopy` is optional; do not geocode addresses through a service unless its terms, rate limits, and privacy implications are acceptable.
- Do not add LangChain, LangGraph, vector databases, embedding models, or an LLM solely for this phase. Plain Python functions are sufficient for deterministic ingestion and comparable-based valuation.

## 14. Final Development Rules for Gemini

When modifying this repository:

1. Read the current code and tests before proposing changes.
2. Implement one phase at a time.
3. Do not fabricate API endpoints, source availability, datasets, or credentials.
4. Do not scrape a source until its access rules and intended use are reviewed.
5. Keep provider adapters separate from normalization and valuation logic.
6. Keep reference rates, listings, transactions, and synthetic fixtures separate.
7. Add tests for every data transformation and important failure case.
8. Never silently drop rows or silently impute key valuation fields.
9. Keep database migrations and `.env.example` in sync with code changes.
10. Do not put secrets, personal data, or licensed raw datasets into Git.
11. Use parameterized SQL and validate file paths and source-controlled inputs.
12. Do not report an estimate as verified market value. Describe it as an estimate and expose its evidence, limitations, and review status.
13. If a task depends on a source that is not yet approved or available, stop that adapter implementation and document the blocker rather than inventing a workaround.
14. Prefer simple, auditable Python over unnecessary agent frameworks.
15. Update the data card, tests, and README when the schema or pipeline behavior changes.

# 15. Mandatory Implementation and Dataset Verification

## 15.1 Objective

Do not consider the project complete merely because Python files, CSV datasets, database models, or API routes have been created.

The implementation must demonstrate that:
1. PostgreSQL/PostGIS can be configured and connected.
2. Database migrations execute successfully.
3. The ingestion pipeline can import, validate, and store records.
4. Every record has traceable provenance.
5. Synthetic data is distinguishable from real source data.
6. Dataset freshness and source verification can be checked.
7. Valuation results can be reproduced from eligible evidence.
8. All verification results are recorded in a report.

## 15.2 Inspect Before Changing Code

Before implementing anything:
- Inspect the existing repository, Python files, tests, configuration, migrations, and datasets.
- Identify which components are implemented, partially implemented, missing, or untested.
- Determine whether PostgreSQL is actually configured and whether a connection has ever been verified.
- Check whether any generated dataset comes from a genuine source or is only synthetic.
- Do not claim that a feature works merely because its code exists.
- Do not overwrite working code unnecessarily.

Create `reports/implementation_audit.md` documenting the findings.

## 15.3 Database Connection and Migration Verification

Configure PostgreSQL with PostGIS.

Provide:
- `.env.example` with placeholder database settings.
- `docker-compose.yml` for a local PostgreSQL/PostGIS development environment, if Docker is the selected setup.
- `backend/app/database/connection.py` for database connectivity.
- SQLAlchemy models and Alembic migrations.
- `scripts/check_database.py` to test the connection and required database extensions.
- `scripts/check_migrations.py` or equivalent migration verification.
- Automated integration tests.

Never commit passwords, API keys, or real credentials.

The database verification script must:
1. Read connection settings from environment variables.
2. Connect to the configured database.
3. execute a simple query such as `SELECT 1`.
4. Verify the PostGIS extension when geographic queries are required.
5. Report the database connection result and migration status.
6. Exit with a non-zero status when a required check fails.

Do not silently switch to an in-memory database or CSV when PostgreSQL is unavailable.

## 15.4 Separate Synthetic and Real Datasets

Maintain distinct datasets and provenance classifications.

Allowed source categories:
- `synthetic_test`
- `government`
- `authorized_provider`
- `manual_authorized_import`

Every ingestion run must record its source category and dataset origin.

Synthetic fixtures must:
- Be explicitly labelled as synthetic.
- Use clearly identified test fixtures.
- Never be described as genuine property transactions.
- Never be included in real-world valuation accuracy metrics.
- Be excluded from production valuation queries by default.

Do not create fake government records, fake transaction IDs, fake source URLs, or fake provider responses.

## 15.5 Source and Freshness Verification

Create `scripts/check_sources.py` and maintain `data/source_readiness.csv`.

For Uttar Pradesh, Maharashtra, Karnataka, and Telangana, record:
- Official source URL.
- Data category.
- API or permitted retrieval method.
- Availability of a sample.
- Availability of transaction prices.
- Historical and geographic coverage.
- License and intended-use permission status.
- Last verification timestamp.
- Evidence supporting the decision.
- Next action and approval decision.

Use `unknown` when a fact has not been verified.

For every imported dataset, record separately:
- Original transaction or effective date, where applicable.
- Source publication/update date, where available.
- Retrieval timestamp.
- Ingestion timestamp.
- Last successful synchronization timestamp.
- Source snapshot hash.
- Source record identifier and source URL, where available.

Do not describe a dataset as real-time merely because it was recently downloaded.

Use an explicit freshness policy based on the source's documented update frequency. Report the age of the data and flag stale or unavailable sources.

If a source does not provide real-time data, describe it accurately as historical, periodically updated, or of unknown freshness.

## 15.6 Dataset Validation

Implement `scripts/validate_dataset.py`.

Validate:
- Required fields and schema.
- Valid prices, dates, area values, units, and geographic coordinates.
- Compatible area types.
- Valid property and transaction categories.
- Source approval and provenance.
- Duplicate source IDs.
- Transaction-price eligibility.
- Missing and contradictory values.
- State, district, and locality coverage.
- Unit conversions and normalized price-per-square-foot calculations.

Never silently discard or impute records.

Persist or export rejected and quarantined records with reason codes, subject to source permissions.

Every ingestion report must reconcile received, accepted, quarantined, rejected, and duplicate records according to documented counting rules.

## 15.7 Automated End-to-End Verification

Create `scripts/run_verification.py` to execute the required checks and generate `reports/verification_report.md`.

The verification suite must test:

1. Database connectivity.
2. Migration success on a clean test database.
3. Record insertion and retrieval.
4. Schema and unit validation.
5. Source provenance enforcement.
6. Duplicate import handling.
7. Quarantine persistence.
8. Transaction rollback.
9. PostGIS geographic queries.
10. Synthetic-versus-real data separation.
11. Freshness reporting.
12. Valuation evidence traceability.
13. Abstention when eligible evidence is insufficient.

Run unit tests and integration tests separately.

Integration tests must use a real PostgreSQL/PostGIS test instance, not a mocked database connection alone.

Use synthetic fixtures for deterministic testing. Use an authorized real sample for source-to-database verification only when one is available and its use is permitted.

If real data access is unavailable, report that limitation. Do not fabricate a successful source integration.

## 15.8 Verification Report

The report must contain:
- Execution timestamp.
- Code version or commit identifier.
- Environment and database status.
- Migration status.
- Test results and failures.
- Source readiness by state.
- Dataset origin and source verification level.
- Retrieval and synchronization timestamps.
- Accepted, rejected, quarantined, and duplicate counts.
- Missing-field and duplicate summaries.
- Geographic and time coverage.
- Synthetic and real record counts reported separately.
- Valuation evaluation results, if a suitable independent real dataset exists.
- Known limitations and recommended next actions.

Use explicit statuses such as:
- `PASS`
- `FAIL`
- `BLOCKED`
- `NOT_VERIFIED`
- `NOT_APPLICABLE`

Do not report a blocked or unexecuted check as passed.

## 15.9 Definition of Done

The development pipeline is verified only when database integration, migrations, data validation, ingestion accounting, and automated tests pass.

Real-source integration is verified only when an authorized source has actually returned a sample, the sample's provenance has been retained, the records have been validated, and the permitted records have been successfully stored and queried.

Real-time capability is verified only if the source supports the required update frequency and synchronization behavior has been demonstrated.

Real-world valuation performance is verified only with a suitable independent evaluation dataset containing appropriately verified transaction evidence.

If any requirement cannot be demonstrated, mark it as `BLOCKED` or `NOT_VERIFIED` and explain why.

Do not mark the entire project complete merely because synthetic-data tests pass.