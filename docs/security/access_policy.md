# API Access Policy (India property-valuation backend)

**Status:** **Ratified** — owner sign-off (Phase-2 remediation F-05). Authoritative for the current API surface.
**Scope:** The FastAPI surface mounted at `API_PREFIX` (`/api/v1`), see `backend/app/api/router.py`.

This document is the authoritative, explicit decision about which endpoints are public and
which require authentication. It exists because Phase-0 shipped with **no** authentication on
any endpoint (F-05), which is acceptable only as a *documented public-data decision* for the
current surface — not as a default for future endpoints.

## 1. Endpoint classification

| Endpoint | Status | Reason | Controls |
|---|---|---|---|
| `GET /health` | **Public** | Liveness/readiness probe; returns only service status and a boolean DB probe | None required |
| `GET /circle-rates/lookup` | **Public reference data** | Returns government-notified circle rates only; no personal, confidential, or restricted information | Input validation, safe (non-reflecting) error handling, best-effort rate limit |
| `GET /` | **Public** | Static service descriptor (name/version/docs links) | None required |
| `/auth/*` | **Protected** | Reserved for Phase 1+ | `require_api_key` |
| `/applications/*` | **Protected** | Borrower-adjacent data | `require_api_key` |
| `/documents/*` | **Protected** | Borrower documents | `require_api_key` |
| `/underwriting/*` | **Protected** | Underwriting outcomes | `require_api_key` |
| `/compliance/*` | **Protected** | Compliance results | `require_api_key` |
| `/reports/*` | **Protected** | Generated reports | `require_api_key` |

The protected routers are **empty placeholders in Phase 0**; the policy exists so that an
endpoint added to any of them inherits authentication rather than shipping unauthenticated.

## 2. How protection is enforced

* `require_api_key` (`backend/app/security/auth.py`) is attached to each protected router's
  constructor (`APIRouter(..., dependencies=[Depends(require_api_key)])`), so *every* route
  added later is authenticated unless the router is deliberately moved into the public set and
  documented in this file.
* The dependency **fails closed**:
  * `API_KEY` unset ⇒ `503 Service Unavailable` ("authentication is not configured").
  * Missing or invalid credential ⇒ `401 Unauthorized`.
  * Valid credential (via `Authorization: Bearer <key>` or `X-API-Key`) ⇒ allowed.
* There is deliberately **no user-management system**: a single operator-provisioned
  `API_KEY`, compared with `hmac.compare_digest`, authenticates non-public callers. Replace it
  with a real identity provider before exposing borrower-adjacent or personal data.

## 3. Public-endpoint controls

* **Rate limiting** — `enforce_rate_limit` (`backend/app/security/rate_limit.py`) is attached to
  `/circle-rates/lookup`. It is a best-effort, per-process sliding window
  (`RATE_LIMIT_PER_MINUTE`, default 120; `0` disables). Production deployments should *also*
  enforce a limit at the edge/gateway; this is not a substitute.
* **Input validation** — query parameters are length- and pattern-constrained in the endpoint
  signature.
* **Safe error handling** — error responses do not reflect raw caller input.

## 4. Accepted risk (Phase 0)

`GET /health` and `GET /circle-rates/lookup` return `200` without credentials. This is an
**accepted, documented risk** because they expose only non-sensitive reference data and the
circle-rate row still requires ingestion to have populated it. The finding F-05 remediation
allows this provided the decision is explicit and future data endpoints are protected — which
is what this document and the router wiring enforce.

## 5. Outbound-request policy (F-08)

Ingestion is a separate trust boundary and is **allowlist-driven**, not authenticated:

* Outbound fetches must be HTTPS, must target a host on `CIRCLE_RATE_ALLOWED_HOSTS`, must not
  be an IP literal in an internal/reserved range, and **redirects are not followed**.
* Local file ingestion is confined to `CIRCLE_RATE_INTAKE_DIR` with path-traversal rejection.

See `backend/app/ingestion/circle_rates.py` (`validate_ingestion_url`, `resolve_intake_path`).
