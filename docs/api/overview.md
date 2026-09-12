# API Specification Overview

> **Current Status**: **Phase 0 Active**. Health check endpoint `/api/v1/health` is live. Future mortgage underwriting endpoints are defined in the schema registry and structured for phased implementation.

---

## Base URL & Prefix

- **Base URL**: `http://localhost:8000`
- **Prefix**: `/api/v1`
- **Interactive Documentation**:
  - Swagger UI: `http://localhost:8000/docs`
  - ReDoc: `http://localhost:8000/redoc`
  - OpenAPI Spec: `http://localhost:8000/openapi.json`

---

## Phase 0 Active Endpoints

### 1. Health Check
- **Endpoint**: `GET /api/v1/health`
- **Summary**: Returns system operational status and database connection liveness.
- **Response Format**:
```json
{
  "status": "healthy",
  "service": "mortgage-underwriting-api",
  "version": "0.1.0",
  "environment": "development",
  "database": "connected"
}
```

### 2. Root Status
- **Endpoint**: `GET /`
- **Summary**: Returns root descriptor and links to documentation.

---

## Planned Endpoints (Phase 1+)

| Method | Endpoint | Description | Target Phase |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | User authentication & JWT issuance | Phase 1 |
| `POST` | `/api/v1/applications` | Create new mortgage application | Phase 1 |
| `GET` | `/api/v1/applications/{id}` | Retrieve application details & status | Phase 1 |
| `POST` | `/api/v1/documents/upload` | Upload borrower income/asset document | Phase 2 |
| `POST` | `/api/v1/documents/{id}/process` | Trigger OCR & field extraction | Phase 2 |
| `POST` | `/api/v1/underwriting/analyze` | Execute LangGraph workflow | Phase 3-6 |
| `GET` | `/api/v1/compliance/check/{id}` | Run statutory compliance audit | Phase 5 |
| `GET` | `/api/v1/reports/{id}/pdf` | Export Fannie Mae Form 1008 / PDF | Phase 7 |

---

## Standard Error Response Format

All error responses return a uniform JSON structure:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Detailed error message description",
    "details": {
      "field": "income",
      "reason": "Must be greater than 0"
    }
  }
}
```
