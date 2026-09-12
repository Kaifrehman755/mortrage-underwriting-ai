# System Evaluation & Benchmark Methodology

> **Current Status**: **Phase 0 Test Suite Established**. Unit and integration test baselines are configured for health, configuration, and database connection. Evaluation suites for AI and RAG accuracy will be populated in subsequent phases.

---

## 1. Test Suite Classification

| Suite | Directory | Purpose | Tools |
|---|---|---|---|
| **Unit Tests** | `backend/tests/unit/` | Isolated tests for API endpoints, schemas, configurations, and exceptions | `pytest`, `pytest-asyncio` |
| **Integration Tests** | `backend/tests/integration/` | Multi-component tests for database sessions, file uploads, and middleware | `pytest`, `asyncpg`, `SQLAlchemy` |
| **Evaluation Benchmarks** | `backend/tests/evaluation/` | Golden dataset evaluation for OCR accuracy, RAG retrieval recall, and decision parity | Custom benchmark harness |

---

## 2. Evaluation Metrics (Phases 1-7)

### 2.1 OCR & Extraction Accuracy
- **Field Exact Match (EM)**: Accuracy of extracted borrower name, SSN, income, tax values.
- **Character Error Rate (CER)**: Robustness against noisy scans and document artifacts.

### 2.2 RAG Guideline Retrieval
- **Hit Rate @ K (K=3, 5)**: Proportion of queries where the true relevant guideline section appears in top K.
- **Context Precision & Recall**: Precision of chunk citations from Fannie Mae Selling Guide.

### 2.3 Financial Calculation Precision
- 100% exact mathematical match for DTI, LTV, CLTV, DSCR calculations against audited spreadsheet ground truth.

### 2.4 Underwriting Decision Parity
- Agreement rate between multi-agent recommendations and experienced human underwriter verdicts on historical test portfolios.
