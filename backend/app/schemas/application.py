"""Pydantic schemas for mortgage applications (Reserved for Phase 1+)."""

from pydantic import BaseModel


class ApplicationBase(BaseModel):
    """Placeholder schema for mortgage loan application data."""
    pass


class ApplicationCreate(ApplicationBase):
    """Placeholder schema for application submission."""
    pass


class ApplicationResponse(ApplicationBase):
    """Placeholder schema for application retrieval response."""
    pass
