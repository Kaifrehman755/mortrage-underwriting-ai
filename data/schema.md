# Canonical Database & Dataset Schema

This schema documents the structured database tables and datasets defined in `GEMINI.md` (Section 4) for the Indian Residential Property Valuation backend.

---

## 1. `data_source`
Tracks provider identity, permission, terms, and approval status.

| Field Name | Type | Constraints / Description |
|---|---|---|
| `source_id` | UUID | Primary Key |
| `source_name` | String(100) | Unique descriptive name |
| `state_code` | String(10) | State code (UP, MH, KA, TS, or ALL) |
| `source_type` | Enum | `government`, `authorized_provider`, `manual_authorized_import`, `synthetic_test` |
| `official_url` | Text | Base official URL of the provider |
| `access_method` | String(50) | `API`, `downloadable file`, `manual authorized export`, `licensed provider` |
| `license_scope` | Text | Specific license and permitted usage description |
| `approval_status` | Enum | `pending_review`, `approved`, `suspended`, `rejected` |
| `terms_url` | Text | Link to terms of use / licensing document |
| `last_checked_at` | DateTime (UTC) | Last verification timestamp |
| `last_successful_sync_at` | DateTime (UTC) | Nullable |
| `created_at` | DateTime (UTC) | Default now() |
| `updated_at` | DateTime (UTC) | Default now() |

---

## 2. `property_record`
Stores physical property identity and stable attributes.

| Field Name | Type | Constraints / Description |
|---|---|---|
| `property_id` | UUID | Primary Key |
| `source_id` | UUID | Foreign Key -> `data_source.source_id` |
| `source_record_id` | String(100) | ID from source provider; Unique with `source_id` |
| `state_code` | String(10) | Indexed |
| `district` | String(100) | Indexed |
| `city` | String(100) | Indexed |
| `locality` | String(150) | Indexed |
| `pincode` | String(10) | Nullable, validated 6 digits for India |
| `property_type` | Enum | `apartment`, `independent_house`, `villa`, `residential_plot`, `other_residential` |
| `area_value_raw` | Numeric | Original value as reported by source |
| `area_unit_raw` | String(30) | sqft, sqm, sqyd, etc. |
| `area_sqft` | Numeric | Normalized area in square feet; Nullable if conversion not possible |
| `area_type` | Enum | `carpet`, `built_up`, `super_built_up`, `plot`, `unknown` |
| `bedrooms` | Integer | Nullable |
| `bathrooms` | Integer | Nullable |
| `construction_year`| Integer | Nullable |
| `location` | PostGIS Point | `Point(lon, lat, srid=4326)` - Nullable |
| `source_authenticity_status` | Enum | `verified_official`, `secondary_provider`, `unverified` |
| `attribute_verification_status` | Enum | `verified`, `unverified`, `disputed` |
| `source_url` | Text | Provenance link |
| `source_record_hash` | String(64) | SHA-256 hash of original record |
| `raw_payload` | JSONB | Nullable; only if storage terms permit |
| `retrieved_at` | DateTime (UTC) | Retrieval timestamp |
| `published_at` | DateTime (UTC) | Nullable |
| `created_at` | DateTime (UTC) | Default now() |
| `updated_at` | DateTime (UTC) | Default now() |

---

## 3. `property_transaction`
Stores verified or reported transaction and consideration evidence. Kept strictly distinct from listings and circle rates.

| Field Name | Type | Constraints / Description |
|---|---|---|
| `transaction_id` | UUID | Primary Key |
| `property_id` | UUID | Foreign Key -> `property_record.property_id` (Nullable if match uncertain) |
| `source_id` | UUID | Foreign Key -> `data_source.source_id` |
| `source_transaction_id` | String(100) | ID from source; Unique with `source_id` |
| `transaction_date` | Date | Date of sale deed / registration |
| `transaction_price_raw` | Numeric | Raw price consideration |
| `transaction_price_unit_raw` | String(20) | INR, Lakh, Crore, etc. |
| `transaction_price_inr` | Numeric | Price normalized to INR |
| `price_type` | Enum | `sale_consideration`, `reported_sale_price`, `unknown` |
| `transaction_verification_status` | Enum | `unverified`, `verified`, `rejected` |
| `source_url` | Text | Provenance URL |
| `source_record_hash` | String(64) | SHA-256 hash |
| `retrieved_at` | DateTime (UTC) | Timestamp |
| `raw_payload` | JSONB | Nullable |

---

## 4. `property_listing`
Stores asking-price evidence. Never treated as verified sales.

| Field Name | Type | Constraints / Description |
|---|---|---|
| `listing_id` | UUID | Primary Key |
| `property_id` | UUID | Foreign Key -> `property_record.property_id` (Nullable) |
| `source_id` | UUID | Foreign Key -> `data_source.source_id` |
| `source_listing_id` | String(100) | Unique with `source_id` |
| `asking_price_raw` | Numeric | Raw asking price |
| `asking_price_inr` | Numeric | Normalized to INR |
| `listing_date` | Date | Date listing was posted |
| `listing_status` | Enum | `active`, `pending`, `sold`, `withdrawn` |
| `source_url` | Text | Listing URL |
| `retrieved_at` | DateTime (UTC) | Timestamp |
| `source_record_hash` | String(64) | SHA-256 hash |

---

## 5. `reference_rate`
Stores official circle rates, guidance values, or ready-reckoner rates. Never treated as sale transactions.

| Field Name | Type | Constraints / Description |
|---|---|---|
| `rate_id` | UUID | Primary Key |
| `source_id` | UUID | Foreign Key -> `data_source.source_id` |
| `state_code` | String(10) | UP, MH, KA, TS |
| `district` | String(100) | District name |
| `locality` | String(150) | Locality / Sub-zone / Mouza |
| `property_category` | String(50) | Residential plot, flat, independent house |
| `rate_raw` | Numeric | Original published rate |
| `rate_unit_raw` | String(30) | per sqm, per sqft, per sqyd |
| `rate_inr_per_sqft` | Numeric | Normalized reference rate in INR per **square foot** (never per square metre). Contract, ORM attribute and physical column all use this name (renamed from `rate_inr_normalized` under the ratified F-17/F-12 migration). |
| `effective_from` | Date | Effective notification start date |
| `effective_to` | Date | Nullable |
| `published_at` | Date | Notification publication date |
| `source_url` | Text | Official notification source |
| `retrieved_at` | DateTime (UTC) | Timestamp |
| `source_record_hash` | String(64) | SHA-256 hash |

---

## 6. `ingestion_run` & `quarantine`
Audit accounting and rejected record isolation.

### `ingestion_run`
| Field Name | Type | Description |
|---|---|---|
| `run_id` | UUID | Primary Key |
| `source_id` | UUID | Foreign Key -> `data_source.source_id` |
| `started_at` | DateTime (UTC) | Run start |
| `finished_at` | DateTime (UTC) | Run finish |
| `run_status` | Enum | `running`, `completed`, `failed` |
| `rows_received` | Integer | Total records received |
| `rows_accepted` | Integer | Valid records ingested |
| `rows_quarantined` | Integer | Records held for data issues |
| `rows_duplicate` | Integer | Idempotently skipped duplicates |
| `rows_rejected` | Integer | Permanently barred records |
| `build_version` | String(50) | Pipeline version |
| `source_snapshot_hash` | String(64) | SHA-256 of ingested raw payload/file |
| `error_summary` | Text | Nullable summary of warnings/failures |

### `quarantine`
| Field Name | Type | Description |
|---|---|---|
| `quarantine_id` | UUID | Primary Key |
| `run_id` | UUID | Foreign Key -> `ingestion_run.run_id` |
| `source_id` | UUID | Foreign Key -> `data_source.source_id` |
| `source_record_id` | String(100) | Source ID if available |
| `reason_code` | String(50) | `MISSING_PRICE`, `MISSING_AREA`, `MISSING_REQUIRED_FIELD`, `INVALID_UNIT`, `INVALID_DATE`, `INVALID_COORDINATES`, `UNSUPPORTED_PROPERTY_TYPE`, `DUPLICATE_RECORD`, `SOURCE_NOT_APPROVED`, `PRICE_TYPE_NOT_ELIGIBLE`, `AREA_BASIS_INCOMPATIBLE`, `PROVENANCE_MISSING` |
| `reason_detail` | Text | Specific failure detail |
| `rejected_at` | DateTime (UTC) | Timestamp |
| `raw_record_ref` | Text | Reference pointer / hashed raw row |

---

## 7. `valuation_run` & `valuation_comparable`
Stores auditable valuation outputs and comparable evidence trace.

### `valuation_run`
| Field Name | Type | Description |
|---|---|---|
| `valuation_id` | UUID | Primary Key |
| `subject_property_input` | JSONB | Subject attributes snapshot |
| `estimate_inr` | Numeric | Model point estimate (Nullable if abstained) |
| `lower_bound_inr` | Numeric | Lower uncertainty bound |
| `upper_bound_inr` | Numeric | Upper uncertainty bound |
| `status` | Enum | `completed`, `abstained`, `needs_human_review`, `failed` |
| `reason_codes` | Array[String] | Reason codes for adjustments or abstentions |
| `method_version` | String(50) | Valuation algorithm version |
| `dataset_cutoff` | Date | Temporal boundary for comps |
| `created_at` | DateTime (UTC) | Valuation execution timestamp |

### `valuation_comparable`
| Field Name | Type | Description |
|---|---|---|
| `valuation_id` | UUID | Foreign Key -> `valuation_run.valuation_id` |
| `transaction_id` | UUID | Foreign Key -> `property_transaction.transaction_id` |
| `distance_m` | Numeric | PostGIS calculated distance in metres |
| `similarity_score` | Numeric | Calculated similarity weight (0.0 to 1.0) |
| `adjusted_price_per_sqft` | Numeric | Normalized price per sqft after adjustments |
| `selection_reason` | String(255) | Justification code for inclusion |
