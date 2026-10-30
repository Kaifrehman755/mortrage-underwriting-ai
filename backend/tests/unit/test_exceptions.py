"""Unit tests for exception hierarchy and error handling."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel, ValidationError, model_validator

from app.core.exceptions import (
    AppException,
    ComplianceException,
    DocumentProcessingException,
    ValidationException,
    WorkflowException,
    register_exception_handlers,
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


def test_custom_validator_error_returns_serializable_422() -> None:
    """A ValueError in a Pydantic model_validator must not become a 500."""
    class RejectsEverything(BaseModel):
        value: int

        @model_validator(mode="after")
        def reject(self) -> None:
            raise ValueError("raw identifier is not accepted")

    try:
        RejectsEverything(value=1)
    except ValidationError as exc:
        request_error = RequestValidationError(exc.errors(), body={})
    else:  # pragma: no cover - defensive
        raise AssertionError("validator did not reject")

    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/raise-validation")
    def raise_validation() -> None:
        raise request_error

    response = TestClient(test_app, raise_server_exceptions=False).get(
        "/raise-validation"
    )
    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "REQUEST_VALIDATION_ERROR"
    assert "raw identifier" in str(payload)
