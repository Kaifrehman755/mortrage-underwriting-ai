# Canonical Valuation Pipeline & ORM Tree (F-10 decision record)

**Status:** Decided — Phase-2 remediation, Priority 5 (F-10).
**Date:** 2026-10-17
**Owner decision:** `app/property` is canonical (see §3).
**Related:** `SECURITY_AUDIT_REPORT.md` (finding F-10), `REMEDIATION_SUMMARY.md`.

F-10 reported two parallel valuation pipelines and two ORM trees with no declared source of
truth. This document records the evidence and the resulting designation. It is **documentation
only** — nothing is deleted, and no runtime behaviour changes.

---

## 1. The two valuation trees

| Tree | Origin | Estimator / controls | Live consumers |
|---|---|---|---|
| `backend/app/property/*` (`valuation.py`, `comps.py`, `gate.py`, `market_index.py`, …) | Playbook AVM | Weighted-median estimator + **F-01 synthetic-exclusion gate** + **F-02 market-index gating/abstention** + guardrail gate | **`PropertyAgent`** (`app/agents/property_agent.py`) and `app/property/__init__.py` |
| `backend/app/valuation/*` (`estimate.py`, `comps.py`, `confidence.py`, `outliers.py`, `evaluation.py`) | GEMINI engine | MAD outlier detection, confidence bounds, reason-coded abstention (`INSUFFICIENT_COMPARABLES`, `MISSING_COORDINATES`, …), leakage-free evaluation harness | Only unit tests (`test_valuation_engine.py`, `tests/evaluation/*`); **no live entry point** |

## 2. The two ORM trees

| Tree | Status | Live consumers |
|---|---|---|
| `backend/app/database/models/*` | **Canonical** (India scope): `CircleRate`, `DataSource`, `PropertyRecord`, `PropertyTransaction`, `PropertyListing`, `ReferenceRate`, `IngestionRun`, `QuarantineRecordModel`, `ValuationRun`, `ValuationComparable` | `migrations/env.py` (`target_metadata = Base.metadata`), repositories |
| `backend/app/models/*` | **Legacy** (out-of-scope US-mortgage stubs): `Application`, `Applicant`, `Document`, `Property`, `CreditProfile`, `RiskAssessment`, `UnderwritingDecision`, `AuditLog` | Only itself — no live or migration reference |

Evidence method: AST scan of every module under `backend/app`, `migrations/`, `backend/tests`,
and `scripts/` for `import app.valuation` / `from app.valuation …` and `import app.models` /
`from app.models …`. The result is asserted by
`backend/tests/unit/test_f10_canonical_pipeline.py`.

## 3. Decision

1. **Valuation engine — canonical: `app/property/*`.**
   It is the only path wired into a live entry point (`PropertyAgent`), and it is where the
   CRITICAL F-01 synthetic gate and the F-02 market-index gating/abstention live. Promoting the
   other tree would mean the live estimate temporarily loses those controls, which is not
   acceptable for a security remediation.
2. **`app/valuation/*` is the stricter GEMINI engine and the migration *target*, not the
   current canon.** It is retained, is **not** marked deprecated, and is the intended destination
   once the F-01/F-02 controls are ported into it.
3. **ORM tree — canonical: `app/database/models/*`.** `app/models/*` is marked deprecated
   (a `DeprecationWarning` is emitted on import of the package) and must not be used by new code.

## 4. Consequences and follow-ups

* **Exactly one engine is wired at a time.** A guard test (`test_f10_canonical_pipeline.py`)
  fails if a live entry point imports `app.valuation` while `app/property.valuation` is the wired
  engine — so switching engines must be a deliberate, accompanied change.
* **Migration path (future, not this phase):** to make `app/valuation` canonical, first port the
  F-01 synthetic-exclusion gate and the F-02 index gating/abstention into it, then move
  `PropertyAgent` and update the `app.property`/`app.valuation` test suites. Only then flip this
  record and the guard test.
* **No deletion.** Per the Priority-5 instruction ("avoid deleting legacy files until their
  references and compatibility implications are understood"), `app/models/*` and
  `app/valuation/*` are retained.
* **`app/models/*` compatibility:** because nothing imports it today, the added
  `DeprecationWarning` cannot break a live path; it will surface any future accidental use.
