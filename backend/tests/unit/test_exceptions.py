"""Unit tests for exception hierarchy and error handling."""

from app.core.exceptions import (
    AppException,
    ComplianceException,
    DocumentProcessingException,
    ValidationException,
    WorkflowException,
)


def test_base_app_exception():
    """Verify base application exception attributes."""
    exc = AppException("Custom system error", status_code=500, error_code="SYS_ERROR")
    assert exc.message == "Custom system error"
    assert exc.status_code == 500
    assert exc.error_code == "SYS_ERROR"


def test_validation_exception():
    """Verify validation exception default status code."""
    exc = ValidationException("Invalid borrower income", details={"field": "income"})
    assert exc.status_code == 422
    assert exc.error_code == "VALIDATION_ERROR"
    assert exc.details["field"] == "income"


def test_document_processing_exception():
    """Verify document processing exception default status code."""
    exc = DocumentProcessingException("Corrupted PDF uploaded")
    assert exc.status_code == 400
    assert exc.error_code == "DOCUMENT_PROCESSING_ERROR"


def test_compliance_exception():
    """Verify compliance exception default status code."""
    exc = ComplianceException("High-priced mortgage loan flag")
    assert exc.status_code == 400
    assert exc.error_code == "COMPLIANCE_ERROR"


def test_workflow_exception():
    """Verify workflow exception default status code."""
    exc = WorkflowException("Agent execution timeout")
    assert exc.status_code == 500
    assert exc.error_code == "WORKFLOW_ERROR"
