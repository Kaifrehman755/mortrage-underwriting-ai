# Rule: Security Remediation and Provenance Governance

## 1. Status Log Invariant
- A finding in `SECURITY_AUDIT_REPORT.md` must NEVER be marked REMEDIATED in summaries or documentation unless an authoritative `## F-XX ... REMEDIATED` entry exists in the status log with executed command outputs, exit codes, and regression test proofs.
- Pre-existing or uncommitted working tree modifications must be treated as "unconfirmed attribution" until explicitly verified against the audit baseline.

## 2. Governing Spec vs Active Code Synchronization
- When a remediation alters a schema field name or contract (e.g., `rate_inr_normalized` -> `rate_inr_per_sqft`), the governing specification (`CLAUDE.md`/`GEMINI.md`) must be kept in sync via explicit amendments or documented mapping tables in `data/schema.md`.
- Never silently diverge the physical database column, ORM model, and API schema without recording the mapping.

## 3. Strict Scope & Operation Boundary Gates
- Destructive DB actions, Alembic autogenerations, package installations, and Docker builds must remain flagged as `BLOCKED / NOT RUN` until explicit user authorization is granted.
- Never substitute synthetic data for real sources or manufacture credentials to satisfy tests.
