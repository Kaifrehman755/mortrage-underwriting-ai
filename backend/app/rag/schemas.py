"""Regulatory and RAG schemas and evidence data contracts.

Adheres strictly to Playbook Section 1, 4, 8, 14.1, 15.3:
- Invariant 3: A compliance finding requires an EvidenceItem reference.
- Invariant 7: Evidence provides factual quotes; findings state 'potential issue for review'.
- Invariant 8: State isolation - scope ('national' vs 'state') and state_code filtering.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class RegDocument(BaseModel):
    """Metadata for an approved regulatory source document."""

    doc_id: str = Field(default_factory=lambda: str(uuid4()))
    source_name: str
    authority: str
    category: str = "general"
    version_or_date: str
    scope: Literal["national", "state"] = "national"
    state_code: str | None = None
    effective_from: str = "2000-01-01"
    effective_to: str = "2099-12-31"
    url: str
    sha256: str
    retrieved_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    # Fail closed: a document is not trusted until an owner records an approval.
    approved: bool = False
    approved_by: str | None = None
    approved_at: str | None = None
    review_due: str | None = None
    terms_snapshot_sha256: str | None = None
    license_scope: str = "unverified"

    @model_validator(mode="after")
    def validate_approval_record(self) -> RegDocument:
        """An approved document must carry the playbook's approval record."""
        if self.approved:
            missing = [
                field
                for field in (
                    "approved_by",
                    "approved_at",
                    "review_due",
                    "terms_snapshot_sha256",
                )
                if not getattr(self, field)
            ]
            if missing:
                raise ValueError(
                    "approved documents require an approval record; missing: "
                    + ", ".join(missing)
                )
        return self


class RegChunk(BaseModel):
    """A single clause or section chunk of regulatory text."""

    chunk_id: str = Field(default_factory=lambda: str(uuid4()))
    doc_id: str
    source_name: str
    authority: str
    section_ref: str
    page_ref: str | None = None
    text: str
    embedding: list[float] = Field(default_factory=list)
    scope: Literal["national", "state"] = "national"
    state_code: str | None = None
    effective_from: str = "2000-01-01"
    effective_to: str = "2099-12-31"
    version_or_date: str = "unknown"
    approved: bool = False
    license_scope: str = "unverified"
    index_version: str = "idx_v1_2026_10"


class EvidenceItem(BaseModel):
    """Exact quoted regulatory evidence attached to compliance findings.

    Invariant 3: A flag without an evidence reference is rejected by validation.
    The snippet is verbatim retrieved text, never hallucinated or summarized.
    """

    evidence_id: str = Field(default_factory=lambda: str(uuid4()))
    retrieval_ref: str  # Matches chunk_id
    source_name: str
    authority: str
    version_or_date: str
    section_or_page: str
    scope: str = "national"
    state_code: str | None = None
    snippet: str
    score: float = Field(..., ge=0.0, le=1.0)
    retrieved_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    license_scope: str = "unverified"
    index_version: str = "idx_v1_2026_10"


class RetrievalQuery(BaseModel):
    """Structured query for hybrid retrieval."""

    query: str
    loan_date: str | None = None
    state_code: str | None = None
    top_k: int = 5
    score_threshold: float = 0.35
    scope_filter: str | None = None
