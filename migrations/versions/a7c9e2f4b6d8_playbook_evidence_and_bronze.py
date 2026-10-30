"""playbook evidence, jurisdiction, market and bronze tables

Revision ID: a7c9e2f4b6d8
Revises: e35561efe721
Create Date: 2026-10-25 00:00:00.000000

This revision adds the playbook-required evidence, compliance, jurisdiction,
market-indicator, and bronze-layer tables. It also adds source approval and
freshness records.

Safety notes
------------
* Source approvals are fail-closed. Any pre-existing ``approved`` row that does
  not already carry a complete approval record is downgraded to
  ``pending_review`` before the new check constraint is created.
* ``vector`` is created defensively; the host image must ship the extension.
* No regulatory document, market fact, or threshold is inserted here.
"""

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a7c9e2f4b6d8"
down_revision: str | None = "e35561efe721"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Jurisdiction packs -------------------------------------------------
    op.create_table(
        "jurisdiction",
        sa.Column("state_code", sa.String(length=2), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="planned",
            nullable=False,
        ),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("config_version", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('planned','pilot','live','paused')",
            name="ck_jurisdiction_status",
        ),
        sa.PrimaryKeyConstraint("state_code"),
    )
    op.create_index(
        op.f("ix_jurisdiction_status"), "jurisdiction", ["status"], unique=False
    )

    # --- Source approval record and freshness ------------------------------
    op.add_column(
        "data_sources",
        sa.Column(
            "access_mode",
            sa.String(length=30),
            server_default="access_pending",
            nullable=False,
        ),
    )
    op.add_column(
        "data_sources", sa.Column("supports_transactions", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "data_sources",
        sa.Column("supports_guideline_values", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "data_sources", sa.Column("supports_land_records", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "data_sources", sa.Column("refresh_interval_days", sa.Integer(), nullable=True)
    )
    op.add_column(
        "data_sources",
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "data_sources",
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("data_sources", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column("data_sources", sa.Column("approved_by", sa.Text(), nullable=True))
    op.add_column(
        "data_sources",
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "data_sources",
        sa.Column("terms_snapshot_sha256", sa.String(length=64), nullable=True),
    )
    op.add_column("data_sources", sa.Column("review_due", sa.Date(), nullable=True))
    op.add_column("data_sources", sa.Column("decision_note", sa.Text(), nullable=True))
    op.create_index(
        op.f("ix_data_sources_access_mode"),
        "data_sources",
        ["access_mode"],
        unique=False,
    )

    # Fail closed before enforcing the approval-record constraint. Existing
    # approved rows without a complete record are not evidence of approval.
    op.execute(
        """
        UPDATE data_sources
        SET approval_status = 'pending_review'
        WHERE approval_status = 'approved'
          AND (
              approved_by IS NULL
              OR approved_at IS NULL
              OR terms_snapshot_sha256 IS NULL
              OR review_due IS NULL
              OR access_mode IN ('access_pending', 'not_permitted')
          )
        """
    )
    op.create_check_constraint(
        "ck_data_source_access_mode",
        "data_sources",
        "access_mode IN ('access_pending','official_api','official_download',"
        "'portal_manual','licensed_feed','not_permitted')",
    )
    op.create_check_constraint(
        "ck_data_source_terms_sha256",
        "data_sources",
        "terms_snapshot_sha256 IS NULL OR "
        "terms_snapshot_sha256 ~ '^[a-f0-9]{64}$'",
    )
    op.create_check_constraint(
        "ck_data_source_approved_needs_record",
        "data_sources",
        "approval_status <> 'approved' OR (approved_by IS NOT NULL "
        "AND approved_at IS NOT NULL AND terms_snapshot_sha256 IS NOT NULL "
        "AND review_due IS NOT NULL AND access_mode NOT IN "
        "('access_pending','not_permitted'))",
    )

    # --- Regulatory documents and chunks -----------------------------------
    op.create_table(
        "reg_document",
        sa.Column("doc_id", sa.UUID(), nullable=False),
        sa.Column("source_name", sa.Text(), nullable=False),
        sa.Column("authority", sa.Text(), nullable=False),
        sa.Column(
            "category", sa.String(length=100), server_default="general", nullable=False
        ),
        sa.Column("version_or_date", sa.Text(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "retrieved_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "approved", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("approved_by", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_due", sa.Date(), nullable=True),
        sa.Column("terms_snapshot_sha256", sa.String(length=64), nullable=True),
        sa.Column(
            "license_scope",
            sa.Text(),
            server_default="unverified",
            nullable=False,
        ),
        sa.Column(
            "scope", sa.String(length=20), server_default="national", nullable=False
        ),
        sa.Column("state_code", sa.String(length=2), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "scope IN ('national','state')", name="ck_reg_document_scope"
        ),
        sa.CheckConstraint(
            "(scope = 'national' AND state_code IS NULL) OR "
            "(scope = 'state' AND state_code IS NOT NULL)",
            name="ck_reg_document_scope_state",
        ),
        sa.CheckConstraint(
            "sha256 ~ '^[a-f0-9]{64}$'", name="ck_reg_document_sha256"
        ),
        sa.CheckConstraint(
            "terms_snapshot_sha256 IS NULL OR "
            "terms_snapshot_sha256 ~ '^[a-f0-9]{64}$'",
            name="ck_reg_document_terms_sha256",
        ),
        sa.CheckConstraint(
            "effective_from IS NULL OR effective_to IS NULL OR "
            "effective_from <= effective_to",
            name="ck_reg_document_effective_dates",
        ),
        sa.CheckConstraint(
            "NOT approved OR (approved_by IS NOT NULL AND approved_at IS NOT NULL "
            "AND review_due IS NOT NULL AND terms_snapshot_sha256 IS NOT NULL)",
            name="ck_reg_document_approved_needs_record",
        ),
        sa.ForeignKeyConstraint(
            ["state_code"], ["jurisdiction.state_code"], name="fk_reg_document_jurisdiction"
        ),
        sa.PrimaryKeyConstraint("doc_id"),
        sa.UniqueConstraint("sha256", name="uq_reg_document_sha256"),
    )
    op.create_index(
        op.f("ix_reg_document_approved"), "reg_document", ["approved"], unique=False
    )
    op.create_index(op.f("ix_reg_document_sha256"), "reg_document", ["sha256"], unique=False)
    op.create_index(op.f("ix_reg_document_scope"), "reg_document", ["scope"], unique=False)
    op.create_index(
        op.f("ix_reg_document_state_code"),
        "reg_document",
        ["state_code"],
        unique=False,
    )

    # The image must provide pgvector. Creating the extension here is idempotent
    # and keeps a clean database bootstrappable from Alembic alone.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "reg_chunk",
        sa.Column("chunk_id", sa.UUID(), nullable=False),
        sa.Column("doc_id", sa.UUID(), nullable=False),
        sa.Column("source_name", sa.Text(), nullable=False),
        sa.Column("authority", sa.Text(), nullable=False),
        sa.Column("section_ref", sa.Text(), nullable=True),
        sa.Column("page_ref", sa.Text(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(dim=384), nullable=False),
        sa.Column(
            "tsv",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', text)", persisted=True),
            nullable=True,
        ),
        sa.Column(
            "scope", sa.String(length=20), server_default="national", nullable=False
        ),
        sa.Column("state_code", sa.String(length=2), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("version_or_date", sa.Text(), nullable=False),
        sa.Column(
            "approved", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "license_scope",
            sa.Text(),
            server_default="unverified",
            nullable=False,
        ),
        sa.Column("index_version", sa.String(length=50), nullable=False),
        sa.CheckConstraint("scope IN ('national','state')", name="ck_reg_chunk_scope"),
        sa.CheckConstraint(
            "(scope = 'national' AND state_code IS NULL) OR "
            "(scope = 'state' AND state_code IS NOT NULL)",
            name="ck_reg_chunk_scope_state",
        ),
        sa.CheckConstraint(
            "effective_from IS NULL OR effective_to IS NULL OR "
            "effective_from <= effective_to",
            name="ck_reg_chunk_effective_dates",
        ),
        sa.ForeignKeyConstraint(
            ["doc_id"],
            ["reg_document.doc_id"],
            name="fk_reg_chunk_document",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["state_code"], ["jurisdiction.state_code"], name="fk_reg_chunk_jurisdiction"
        ),
        sa.PrimaryKeyConstraint("chunk_id"),
        sa.UniqueConstraint(
            "doc_id",
            "section_ref",
            "index_version",
            name="uq_reg_chunk_doc_section_version",
        ),
    )
    op.create_index(op.f("ix_reg_chunk_approved"), "reg_chunk", ["approved"], unique=False)
    op.create_index(op.f("ix_reg_chunk_doc_id"), "reg_chunk", ["doc_id"], unique=False)
    op.create_index(
        op.f("ix_reg_chunk_index_version"),
        "reg_chunk",
        ["index_version"],
        unique=False,
    )
    op.create_index(op.f("ix_reg_chunk_scope"), "reg_chunk", ["scope"], unique=False)
    op.create_index(
        op.f("ix_reg_chunk_state_code"), "reg_chunk", ["state_code"], unique=False
    )
    op.create_index(
        "idx_reg_chunk_embedding_hnsw",
        "reg_chunk",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "idx_reg_chunk_tsv_gin",
        "reg_chunk",
        ["tsv"],
        unique=False,
        postgresql_using="gin",
    )

    # --- Compliance findings ------------------------------------------------
    op.create_table(
        "compliance_finding",
        sa.Column("finding_id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("state_code", sa.String(length=2), nullable=True),
        sa.Column("rule_id", sa.String(length=50), nullable=False),
        sa.Column("rule_set_version", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=True),
        sa.Column("affected_requirement", sa.Text(), nullable=False),
        sa.Column(
            "evidence_refs",
            postgresql.ARRAY(postgresql.UUID(as_uuid=True)),
            server_default=sa.text("'{}'::uuid[]"),
            nullable=False,
        ),
        sa.Column(
            "missing_information",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column(
            "human_review_required",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('no_issue_detected','potential_issue','cannot_verify')",
            name="ck_compliance_finding_status",
        ),
        sa.CheckConstraint(
            "severity IS NULL OR severity IN ('low','medium','high')",
            name="ck_compliance_finding_severity",
        ),
        sa.CheckConstraint(
            "status = 'cannot_verify' OR cardinality(evidence_refs) > 0",
            name="ck_compliance_finding_evidence_required",
        ),
        sa.CheckConstraint(
            "status <> 'cannot_verify' OR human_review_required",
            name="ck_compliance_finding_cannot_verify_review",
        ),
        sa.ForeignKeyConstraint(
            ["state_code"],
            ["jurisdiction.state_code"],
            name="fk_compliance_finding_jurisdiction",
        ),
        sa.PrimaryKeyConstraint("finding_id"),
    )
    op.create_index(
        op.f("ix_compliance_finding_case_id"),
        "compliance_finding",
        ["case_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_compliance_finding_rule_id"),
        "compliance_finding",
        ["rule_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_compliance_finding_state_code"),
        "compliance_finding",
        ["state_code"],
        unique=False,
    )
    op.create_index(
        op.f("ix_compliance_finding_status"),
        "compliance_finding",
        ["status"],
        unique=False,
    )

    # --- Market facts -------------------------------------------------------
    op.create_table(
        "market_indicator",
        sa.Column("geo_key", sa.String(length=200), nullable=False),
        sa.Column("period", sa.Date(), nullable=False),
        sa.Column("metric", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column(
            "retrieved_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("value = value", name="ck_market_indicator_value_not_nan"),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["data_sources.source_id"],
            name="fk_market_indicator_source",
        ),
        sa.PrimaryKeyConstraint(
            "geo_key", "period", "metric", "source_id", name="pk_market_indicator"
        ),
    )

    # --- Bronze layer -------------------------------------------------------
    op.create_table(
        "raw_record",
        sa.Column("raw_id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("file_sha256", sa.String(length=64), nullable=True),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "status", sa.String(length=30), server_default="new", nullable=False
        ),
        sa.Column(
            "record_type",
            sa.String(length=30),
            server_default="registered_transaction",
            nullable=False,
        ),
        sa.Column("record_fingerprint", sa.String(length=64), nullable=False),
        sa.CheckConstraint(
            "record_type IN ('registered_transaction','guideline_value',"
            "'land_record','listing','survey')",
            name="ck_raw_record_type",
        ),
        sa.CheckConstraint(
            "record_fingerprint ~ '^[a-f0-9]{64}$'",
            name="ck_raw_record_fingerprint_sha256",
        ),
        sa.CheckConstraint(
            "file_sha256 IS NULL OR file_sha256 ~ '^[a-f0-9]{64}$'",
            name="ck_raw_record_file_sha256",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"], ["data_sources.source_id"], name="fk_raw_record_source"
        ),
        sa.PrimaryKeyConstraint("raw_id"),
        sa.UniqueConstraint(
            "source_id",
            "record_type",
            "record_fingerprint",
            name="raw_record_dedupe",
        ),
    )
    op.create_index(
        op.f("ix_raw_record_record_type"),
        "raw_record",
        ["record_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_raw_record_source_id"), "raw_record", ["source_id"], unique=False
    )
    op.create_index(op.f("ix_raw_record_status"), "raw_record", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_raw_record_status"), table_name="raw_record")
    op.drop_index(op.f("ix_raw_record_source_id"), table_name="raw_record")
    op.drop_index(op.f("ix_raw_record_record_type"), table_name="raw_record")
    op.drop_table("raw_record")

    op.drop_table("market_indicator")

    op.drop_index(
        op.f("ix_compliance_finding_status"), table_name="compliance_finding"
    )
    op.drop_index(
        op.f("ix_compliance_finding_state_code"), table_name="compliance_finding"
    )
    op.drop_index(
        op.f("ix_compliance_finding_rule_id"), table_name="compliance_finding"
    )
    op.drop_index(
        op.f("ix_compliance_finding_case_id"), table_name="compliance_finding"
    )
    op.drop_table("compliance_finding")

    op.drop_index("idx_reg_chunk_tsv_gin", table_name="reg_chunk")
    op.drop_index("idx_reg_chunk_embedding_hnsw", table_name="reg_chunk")
    op.drop_index(op.f("ix_reg_chunk_state_code"), table_name="reg_chunk")
    op.drop_index(op.f("ix_reg_chunk_scope"), table_name="reg_chunk")
    op.drop_index(op.f("ix_reg_chunk_index_version"), table_name="reg_chunk")
    op.drop_index(op.f("ix_reg_chunk_doc_id"), table_name="reg_chunk")
    op.drop_index(op.f("ix_reg_chunk_approved"), table_name="reg_chunk")
    op.drop_table("reg_chunk")

    op.drop_index(op.f("ix_reg_document_state_code"), table_name="reg_document")
    op.drop_index(op.f("ix_reg_document_scope"), table_name="reg_document")
    op.drop_index(op.f("ix_reg_document_sha256"), table_name="reg_document")
    op.drop_index(op.f("ix_reg_document_approved"), table_name="reg_document")
    op.drop_table("reg_document")

    op.drop_constraint(
        "ck_data_source_approved_needs_record", "data_sources", type_="check"
    )
    op.drop_constraint("ck_data_source_terms_sha256", "data_sources", type_="check")
    op.drop_constraint("ck_data_source_access_mode", "data_sources", type_="check")
    op.drop_index(op.f("ix_data_sources_access_mode"), table_name="data_sources")
    op.drop_column("data_sources", "decision_note")
    op.drop_column("data_sources", "review_due")
    op.drop_column("data_sources", "terms_snapshot_sha256")
    op.drop_column("data_sources", "approved_at")
    op.drop_column("data_sources", "approved_by")
    op.drop_column("data_sources", "last_error")
    op.drop_column("data_sources", "last_success_at")
    op.drop_column("data_sources", "last_attempt_at")
    op.drop_column("data_sources", "refresh_interval_days")
    op.drop_column("data_sources", "supports_land_records")
    op.drop_column("data_sources", "supports_guideline_values")
    op.drop_column("data_sources", "supports_transactions")
    op.drop_column("data_sources", "access_mode")

    op.drop_index(op.f("ix_jurisdiction_status"), table_name="jurisdiction")
    op.drop_table("jurisdiction")
