# Progress — India Property-Valuation Backend

**Scope:** India property-valuation backend only. No RAG, compliance, frontend or US-mortgage work.
**Governing instructions (not edited):** `CLAUDE.md` / `GEMINI.md`, `backend/app/property/playbook.md`,
`data/regulatory_docs/.clinerules/*`.
**Authoritative brief + per-finding status log:** `SECURITY_AUDIT_REPORT.md`.
**Roll-up report:** `REMEDIATION_SUMMARY.md`.

This file is the R21 `docs/PROGRESS.md` deliverable (F-18). It records where the remediation stands,
the required scripts/reports, and the documented deviations.

---

## 1. Finding status

| Finding | Severity | Status |
|---|---|---|
| F-01 synthetic comps reach production valuation | CRITICAL | REMEDIATED |
| F-02 unprovenanced hard-coded market index | HIGH | REMEDIATED |
| F-03 reference-rate fixtures labelled as government data | HIGH | REMEDIATED (relabelled as unverified dev fixtures; sources `pending_review`) |
| F-04 circle-rate ingestion silently drops rows | HIGH | REMEDIATED |
| F-05 no authentication on any endpoint | HIGH | REMEDIATED |
| F-06 CORS wildcard fallback + credentials | MEDIUM | REMEDIATED |
| F-07 default DB creds / insecure default secret | MEDIUM | REMEDIATED |
| F-08 SSRF / arbitrary local file read | MEDIUM | REMEDIATED |
| F-09 `.env.example` out of sync + embedding-model mismatch | MEDIUM | REMEDIATED |
| F-10 two parallel valuation pipelines / ORM trees | MEDIUM | REMEDIATED (canonical designation) |
| F-11 duplicated dependency declarations | MEDIUM | REMEDIATED (static verification) |
| F-12 no Alembic revision files | MEDIUM | **BLOCKED** (needs an authorised disposable PostGIS DB) |
| F-13 RAG out-of-scope with fabricated content | MEDIUM | OPEN — out of scope (documented) |
| F-14 broad exception handling / leaked error text | LOW | REMEDIATED |
| F-15 `rows_rejected` accounting unreachable | LOW | REMEDIATED |
| F-16 fabricated fallback source URL | LOW | REMEDIATED |
| F-17 reference-rate unit semantics inconsistent | LOW | REMEDIATED |
| F-18 instruction/artifact conflicts; missing deliverables | INFO | IN PROGRESS (this file + R21 scripts; conflicts documented below) |
| F-19 no Flask frontend / no ML model | INFO | NO ACTION (informational, out of scope) |
| F-20 positive controls observed | INFO | NO ACTION (recorded) |

---

## 2. Required scripts and reports (R21)

| Deliverable | Status | Purpose |
|---|---|---|
| `scripts/check_sources.py` | present | Source-readiness checks; `--verify-fixtures` verifies reference-rate + market-index provenance |
| `scripts/check_migrations.py` | present | Static Alembic readiness (config, canonical ORM target, revisions/heads); reports F-12 open |
| `scripts/check_database.py` | present | PostGIS config check (static by default) and `--connect` read-only probe |
| `scripts/validate_dataset.py` | present | Validates on-disk processed rows, manifests and quarantine records |
| `scripts/build_dataset.py` | present | Gated dataset builder (dry-run by default; fails closed on unapproved sources) |
| `scripts/run_verification.py` | present | Runs the approved local checks; can write `reports/verification_report.md` |
| `reports/implementation_audit.md` | present | What changed and why |
| `reports/verification_report.md` | present | Generated from real command output |
| `docs/PROGRESS.md` | present | This file |

Reproduce:

```bash
./.venv/Scripts/python.exe scripts/run_verification.py            # all approved checks
./.venv/Scripts/python.exe scripts/validate_dataset.py            # dataset only
./.venv/Scripts/python.exe scripts/check_migrations.py            # F-12 readiness
./.venv/Scripts/python.exe scripts/check_database.py              # DB config (no connection)
./.venv/Scripts/python.exe scripts/build_dataset.py              # dry-run; fails closed (F-03)
```

---

## 3. Documented blockers and gate consequences

* **F-12 (Alembic).** `migrations/versions/` has no revision file. Generating and testing the initial
  revision requires a live disposable PostGIS database (autogenerate + `upgrade head` /
  `downgrade base`), which is **not authorised**. `scripts/check_migrations.py` reports this explicitly
  and exits non-zero, so the gap is never silent.
* **F-03 (source approval gate).** The four reference-rate fixture sources are `pending_review`, so the
  canonical, gated ingestion refuses them. Consequently `scripts/build_dataset.py` currently reports all
  four states as `BLOCKED` and exits `2`. That is the intended, fail-closed behaviour — the existing
  `data/processed/**` files remain labelled synthetic dev fixtures and are **not** rebuilt.
* **Not authorised / not run:** dependency vulnerability scan, Docker build, live DB migrations, live
  fetch of government sources (RBI DBIE HPI values were not fetched; the market-index series stays an
  unverified fixture).

---

## 4. Deviations and conflicts (F-18)

| Item | Resolution |
|---|---|
| `.clinerules/*` located under `data/regulatory_docs/` rather than the repo root | **Not moved.** The governing instructions reference this path; relocating it would contradict the instructions. Recorded here instead. |
| `README.md` and `docs/*` describe a US full-stack system | **Not rewritten** (out of India scope and it is unrelated user content). The India scope is stated at the top of this file and in `SECURITY_AUDIT_REPORT.md`. |
| `AGENTS.md` and `.clineignore` absent | Recorded as absent. No file invented; the governing instructions are `CLAUDE.md`/`GEMINI.md`. |
| `docs/playbook/` absent | Recorded. The playbook lives at `backend/app/property/playbook.md`. |
| `frontend/`, `rag/`, compliance stubs exist although "not this phase" | Left untouched (R22). F-13 (RAG fabricated content) stays an out-of-scope documented residual. |
| `scripts/import_dataset.py` writes unconditionally | Superseded in practice by the safer, gated `scripts/build_dataset.py` (dry-run by default). `import_dataset.py` is retained to avoid deleting user work. |

---

## 5. Remaining open decisions

1. Ratify `docs/security/access_policy.md` as the F-05 access-policy location (instead of the README).
2. Ratify the `rate_inr_normalized` → `rate_inr_per_sqft` rename in the governing docs (`CLAUDE.md` /
   `GEMINI.md` §4.5 still name the old field; the governing docs were not edited).
