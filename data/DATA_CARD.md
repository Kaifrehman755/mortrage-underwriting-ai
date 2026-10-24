# Data Card: Indian Residential Property Valuation Dataset

## 1. Dataset Purpose & Intended Users
This dataset infrastructure powers the backend for an Indian residential property valuation agent.
- **Intended Users:** Mortgage underwriters, risk officers, and automated valuation engines requiring transparent, auditable market evidence.
- **Scope:** Estimates market value using eligible comparable property transactions, distinct administrative reference rates (circle rates / guidance values / ready-reckoners), and robust uncertainty handling.

## 2. Candidate Sources & Readiness Status

As audited in `data/source_readiness.csv`:

| State | Source Name | Category | Access Method | Transaction Price Available | Decision |
|---|---|---|---|---|---|
| **Uttar Pradesh** | IGRSUP Circle Rates (`https://igrsup.gov.in/`) | `reference_rate` | Downloadable file | No | `pending_review` (provenance unverified — F-03) |
| **Uttar Pradesh** | IGRSUP Deed Search (`https://igrsup.gov.in/`) | `property_transaction` | Unknown (login/CAPTCHA gated) | No | `rejected` (no scraping) |
| **Maharashtra** | IGR Maharashtra eASR (`https://easr.igrmaharashtra.gov.in/`) | `reference_rate` | Manual export | No | `pending_review` (provenance unverified — F-03) |
| **Maharashtra** | IGR Maharashtra eSearch (`https://esearchigr.maharashtra.gov.in/`) | `property_transaction` | Unknown | Yes (search-only) | `rejected` (no bulk API) |
| **Karnataka** | Kaveri 2.0 Guidance Values (`https://kaveri.karnataka.gov.in/`) | `reference_rate` | Manual export | No | `pending_review` (provenance unverified — F-03) |
| **Karnataka** | Kaveri 2.0 Document Services (`https://kaveri.karnataka.gov.in/`) | `property_transaction` | Unknown | Yes (search-only) | `rejected` (restricted) |
| **Telangana** | IGRS Market Value Services (`https://registration.telangana.gov.in/`) | `reference_rate` | Manual export | No | `pending_review` (provenance unverified — F-03) |
| **Telangana** | IGRS Registered Deeds (`https://registration.telangana.gov.in/`) | `property_transaction` | Unknown | Yes (search-only) | `rejected` (restricted) |
| **All States (Dev)** | Synthetic Property Test Fixture Generator (`local://test-fixtures/synthetic`) | `property_transaction` | Fixture code | Yes (simulated) | `approved` (tests only) |

## 2.1 Unverified Multi-State Reference Rate Fixtures (Development Only — NOT approved)

> **Provenance status (F-03, verified 2026-10-17): UNVERIFIED.**
> These local files are **synthetic development fixtures** created to exercise the ingestion and
> unit-normalisation pipeline. They are **not** verified downloads from the state portals and must
> never be reported as official reference-rate evidence. Authorized external verification on
> 2026-10-17 could not resolve the deep snapshot URLs previously cited as provenance (UP: portal
> error page; MH: timeout; KA: landing page only; TS: HTTP 404), so the datasets remain pending
> review. The corresponding `data/source_readiness.csv` rows are `pending_review`, and the source
> approval gate therefore blocks ingestion until an authorized export is obtained, its SHA-256
> recorded (`terms_snapshot_sha256`), and a named verifier signs off.
> Every fixture row carries `source_url=local://synthetic/reference_rates/<file>` and a
> `[SYNTHETIC DEV FIXTURE - UNVERIFIED PROVENANCE]` marker in `notes`.

- **Uttar Pradesh (UP):**
  - Fixture: `data/reference_rates/up_lucknow_circle_rates_2024.csv`
  - SHA-256: `1ef78d3bac7809fbf9af68ceed5aa686a2fea7a79b96dd4b04bece92ec6acf09`
  - Rows: 12 received, 12 accepted, 0 quarantined, 0 duplicate (Pass 1). Invariant: `12 == 12` (PASSED).
- **Maharashtra (MH):**
  - Fixture: `data/reference_rates/mh_mumbai_ready_reckoner_2024.csv`
  - SHA-256: `4c9ba460e9fd97a6f5bc5fcfc9657d66f09d0bd1b9f3c75a43a930fd678fc3d3`
  - Rows: 7 received, 7 accepted, 0 quarantined, 0 duplicate (Pass 1). Invariant: `7 == 7` (PASSED).
- **Karnataka (KA):**
  - Fixture: `data/reference_rates/ka_bengaluru_guidance_values_2024.csv`
  - SHA-256: `677d2b94b473b4f2e520dcdfe0459fd2014f19169874fa3dfad4424156a262c7`
  - Rows: 7 received, 7 accepted, 0 quarantined, 0 duplicate (Pass 1). Invariant: `7 == 7` (PASSED).
- **Telangana (TS):**
  - Fixture: `data/reference_rates/ts_hyderabad_market_values_2024.csv`
  - SHA-256: `26e0f9079bf690abb47f562b23b22fc763c0db2ae0f7f963377da283b024ae01`
  - Rows: 7 received, 7 accepted, 0 quarantined, 0 duplicate (Pass 1). Invariant: `7 == 7` (PASSED).

All fixtures guarantee 100% idempotency (zero net duplicates added on second pass).

## 2.2 Multi-State Provider Architecture (Phase 5)
- **Supported State Adapters:**
  - `UttarPradeshProvider` (`UP`): IGRSUP Circle Rates (unverified synthetic dev fixture). Native unit: `per_sqm` (factor: 10.7639104167). Transaction deed access restricted.
  - `MaharashtraProvider` (`MH`): IGR Maharashtra eASR Ready Reckoner (unverified synthetic dev fixture). Native unit: `per_sqm` (factor: 10.7639104167). Transaction deed access restricted.
  - `KarnatakaProvider` (`KA`): Kaveri 2.0 Guidance Values (unverified synthetic dev fixture). Native unit: `per_sqft`. Transaction deed access restricted.
  - `TelanganaProvider` (`TS`): IGRS Telangana Market Values (unverified synthetic dev fixture). Native unit: `per_sqyd` (factor: 9.0). Transaction deed access restricted.
- **Unsupported State Handling:**
  - Any state outside {`UP`, `MH`, `KA`, `TS`} (e.g. `DL`, `TN`, `GJ`, `RJ`) is explicitly blocked by `StateProviderRegistry` and `ValuationEngine`.
  - Raises `UnsupportedStateError` or returns `ABSTAINED` with reason code `STATE_NOT_SUPPORTED`. No records are ever fabricated.
- **Deed Access Restriction:**
  - In all four candidate states, automated bulk scraping of public deed search portals is prohibited under government terms and technical security controls (CAPTCHA/OTP).
  - Calling `provider.require_transaction_data()` explicitly raises `TransactionDataUnavailableError`.

## 2.3 Reference-Rate Provenance Verification (F-03)

Authorized external verification performed 2026-10-17. Each dataset's previously-claimed snapshot URL
was fetched directly and recorded:

| Dataset | Previously-claimed snapshot URL | Verification result |
|---|---|---|
| UP Lucknow circle rates | `https://igrsup.gov.in/igrsup/rates/lucknow/2024` | Not resolved (generic portal error page) — UNVERIFIED |
| MH Mumbai ready reckoner | `https://easr.igrmaharashtra.gov.in/easr/rates/mumbai/2024` | Not resolved (request timed out) — UNVERIFIED |
| KA Bengaluru guidance values | `https://kaveri.karnataka.gov.in/rates/bengaluru/2024` | Not resolved (portal landing page only) — UNVERIFIED |
| TS Hyderabad market values | `https://registration.telangana.gov.in/rates/hyderabad/2024` | HTTP 404 — UNVERIFIED |

**Approval rule enforced:** a reference-rate dataset may only be marked `approved` once an authorized
export has been obtained, its SHA-256 recorded (`terms_snapshot_sha256`), and a named verifier recorded.
Until then it must remain `pending_review`, and the source approval gate must block ingestion
(`scripts/check_sources.py --verify-fixtures`, `backend/tests/unit/test_f03_data_provenance.py`).

## 2.4 Market-Index Provenance (F-02)

> **Provenance status (F-02, checked 2026-10-17): UNVERIFIED.**
> The HPI time-adjustment series is no longer hard-coded inside the valuation engine. It now
> lives in a versioned file, `data/market_indices/rbi_hpi_urban_lucknow.json`, which carries
> the series source, publication date, units, base year and an explicit `verification_status`.
> The shipped fixture is `unverified`, so the engine **abstains from the HPI time adjustment**
> rather than inventing a value, and the affected output is flagged `human_review_required`.
> The previously hard-coded `rbi_hpi_yoy_growth_percent = 8.2` constant and the `100.0`
> fallback level have both been removed. To promote the series: obtain an authorized DBIE
> export, record its SHA-256 and the exact `source_url`/`publication_date`, update each value,
> then set `verification_status` to `verified`. Until then the `data/source_readiness.csv`
> row remains `pending_review` and the runtime gate keeps the adjustment abstained
> (`backend/tests/unit/test_f02_market_index.py`).

## 3. Strict Boundary Rules & Invariants
1. **Separation of Evidence:**
   - Transaction records (`property_transaction`), asking listings (`property_listing`), and administrative reference rates (`reference_rate`) are stored in distinct tables.
   - Government circle rates / guidance values are **never** treated as sale prices.
   - Asking prices from listings are **never** treated as verified transaction prices.
2. **Provenance Tracking:** Every record must track `source_id`, `source_record_id`, `retrieval_time`, `effective_date`, `source_url`, and `license_scope`. Records derived from synthetic fixtures must carry `source_url=local://synthetic/...` (never a fabricated official URL) and a synthetic provenance marker; they are never counted as real market evidence.
3. **No Unrecorded Dropping or Imputation:** Any invalid row must be preserved in `quarantine` with standard reason codes (e.g. `MISSING_PRICE`, `MISSING_AREA`, `MISSING_REQUIRED_FIELD`, `INVALID_DATE`, `UNSUPPORTED_PROPERTY_TYPE`, `SOURCE_NOT_APPROVED`). This applies to **both** ingestion paths: the canonical provider importers and the `CircleRateIngestor` HTML/CSV/Excel/PDF path (F-04), which now emit a `QuarantineRecord` per rejected row plus an `IngestionRunAccounting` record.
4. **Synthetic Data Policy:** Synthetic fixtures are strictly for software testing and pipeline validation. They are explicitly tagged with `source_type=synthetic_test` and never counted as real market evidence.

## 4. Normalization & Conversion Standards
- **Currency:** Normalized to Indian Rupee (INR).
  - 1 Lakh = 100,000 INR
  - 1 Crore = 10,000,000 INR
- **Area:** Normalized to square feet (`sqft`).
  - 1 sq. metre = 10.7639104167 sqft
  - 1 sq. yard = 9.0 sqft
- **Area Basis Isolation:** Carpet area, built-up area, super built-up area, and plot area are kept distinct and never conflated. Price-per-sqft is only computed when price and compatible area basis are both present and verified.

## 5. Valuation Engine & Abstention Principles (Phase 6)
- **Robust Estimation:** Point estimate is derived using a transparent 50th percentile weighted median over adjusted price-per-square-foot of eligible comparables.
- **Locality-Aware Outlier Detection:** Evaluates comparables using Median Absolute Deviation (MAD):
  `robust_z = 0.67449 * (value - median) / MAD`
  - Handles zero MAD and small groups (< 4) explicitly.
  - Outliers (|robust_z| >= 3.5) are flagged with provenance reasons and given reduced weights rather than silently dropped.
- **Strict Reason-Coded Abstention:**
  - `STATE_NOT_SUPPORTED`: Request in unsupported state.
  - `MISSING_COORDINATES`: Subject lacks geographic latitude/longitude.
  - `AREA_BASIS_INCOMPATIBLE`: Subject has unknown area type.
  - `INSUFFICIENT_COMPARABLES`: Fewer than 3 eligible comps found within max radius (5.0 km).
  - `EXCESSIVE_DISPERSION`: Price dispersion across comps exceeds tolerance (CV > 0.35).
  - `STALE_EVIDENCE`: Comps exceed maximum recency window (median age > 450 days).
  - `OUTLIERS_DETECTED`: Comps trigger robust MAD outlier flags, routing to `needs_human_review`.
- **Empirical Uncertainty Bounds:**
  - Lower and upper bounds are derived from 15th and 85th weighted percentiles.
  - Withheld (`None`) when fewer than 5 eligible comps are available or dispersion is excessive.
  - Clearly tagged as uncalibrated heuristic bounds; never claimed as calibrated probabilities.

## 6. Evaluation Split Methodology & Leakage Prevention
- **Group Isolation:** All transactions, listings, and updates for the same physical property remain strictly in the same split partition.
- **Temporal Holdout:** Simulates valuation strictly on subsequent market periods using time-based cutoffs. Training data contains no future transactions relative to `split_date`.
- **Locality Holdout:** Unseen localities held out completely to evaluate geographic transferability without locality leakage.
- **Split Manifests:** Every split generates a deterministic `SplitManifest` with parameters and SHA-256 hash.
- **Performance Reporting:** MdAPE, MAPE, coverage rate, abstention rate, large-error rate (>20%), and state-stratified metrics.

## 7. Privacy & Personal Data
- No personally identifiable information (PII) regarding buyers, sellers, or owners is ingested or stored.
- Protected-class attributes or demographic proxies are strictly barred from the valuation feature set.

