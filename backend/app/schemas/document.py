"""Pydantic schemas for document ingestion and metadata (Reserved for Phase 1+)."""

from pydantic import BaseModel


class DocumentBase(BaseModel):
    """Placeholder schema for document metadata."""
    pass


class DocumentUploadResponse(DocumentBase):
    """Placeholder schema for document upload acknowledgment."""
    pass
