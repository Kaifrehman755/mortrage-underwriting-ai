# System Architecture Overview

> **Current Status**: **Phase 0 (Foundation & Skeleton)**. All architectural boundaries and module layers are defined. Advanced AI, RAG, OCR, calculations, and compliance rules are represented by clean interfaces and scheduled for progressive implementation in subsequent phases.

---

## 1. High-Level Architectural Diagram

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                              │
│         Next.js 14+ (App Router) • React 18 • TypeScript • Tailwind     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST (JSON)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         API & SERVICE GATEWAY                          │
│          FastAPI • Pydantic v2 • Correlation IDs • CORS Middleware     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    ▼                                                               ▼
┌──────────────────────────────────────┐  ┌──────────────────────────────┐
│        WORKFLOW ORCHESTRATION        │  │     DETERMINISTIC ENGINES    │
│  LangGraph State Machine (Planned)   │  │  - DTI / LTV / DSCR Math     │
│  - Document Ingestion Node           │  │  - Mid-FICO Selection        │
│  - Financial Analysis Node           │  │  - Composite Risk Score      │
│  - Compliance Audit Node             │  │  - Programmatic Rules Engine │
│  - Decision Synthesis Node           │  └──────────────┬───────────────┘
│  - Human-in-the-Loop Review Node     │                 │
└──────────────────┬───────────────────┘                 │
                   │                                     │
    ┌──────────────┴───────────────┐                     │
    ▼                              ▼                     │
┌─────────────────────────┐  ┌────────────────────────┐  │
│    SPECIALIZED AGENTS   │  │     REGULATORY RAG     │  │
│ - Document Agent        │  │ - Sentence Transformers│  │
│ - Credit Agent          │  │ - FAISS / ChromaDB     │  │
│ - Property Agent        │  │ - Cross-Encoder Rerank │  │
│ - Compliance Agent      │  │ - FNMA / FHLMC Guides  │  │
│ - Decision Agent        │  └────────────────────────┘  │
└─────────────────────────┘                              │
                   │                                     │
                   └───────────────┬─────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        DATA PERSISTENCE & STORAGE                      │
│   PostgreSQL (SQLAlchemy 2.0 Async) • Alembic • Local File Storage     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layered Separation of Concerns

The architecture strictly adheres to clear boundaries between components:

```text
Frontend (Presentation Only)
   ↓
API Routes & Serializers (Request Parsing & Response Marshaling)
   ↓
Service / Orchestration Layer (LangGraph State Machine & Coordination)
   ↓
Domain Logic (Deterministic Calculations, Statutory Compliance Rules)
   ↓
Infrastructure / External (PostgreSQL, Vector DB, Local Storage, Open LLM Adapters)
```

### Architectural Rules
1. **Frontend Isolation**: The frontend UI never performs financial math or makes direct database queries.
2. **Deterministic Purity**: Financial calculations (DTI, LTV, DSCR, FICO) are pure deterministic Python functions, isolated from LLM hallucinations.
3. **Compliance Separation**: Statutory rule evaluations (RESPA disclosure timelines, APR limits, HMDA LAR checks) are programmatic rule trees, supplemented (not replaced) by RAG guidance.
4. **Agent Modularity**: AI agents act as specialized analyzers within LangGraph state nodes, communicating via typed state objects.
5. **Database Decoupling**: Database models (SQLAlchemy ORM) are separated from API request/response schemas (Pydantic).

---

## 3. Component Details

### 3.1 Frontend (`frontend/`)
- Built with **Next.js (App Router)**, **React**, **TypeScript**, and **Tailwind CSS**.
- Responsive dashboard shell with live health check connectivity to the backend.
- Modular component hierarchy (`Header`, `Sidebar`, `HealthStatus`, `Dashboard`).

### 3.2 Backend API (`backend/app/api/`)
- Built with **FastAPI**.
- Exposes structured RESTful endpoints with automatic OpenAPI / Swagger documentation.
- Centralized exception handling formatting standard error responses without leaking tracebacks.
- Request correlation ID (`X-Request-ID`) attached across logging and response headers.

### 3.3 Database Layer (`backend/app/database/` & `models/`)
- **PostgreSQL 16** via Docker container.
- **SQLAlchemy 2.0 Async** engine with connection pooling and `asyncpg` driver.
- Base declarative models with timestamp mixins (`created_at`, `updated_at`).
- Alembic database migration directory structure.

### 3.4 Future AI & Agent Layer (`backend/app/agents/`)
- **Document Agent**: Ingestion, OCR classification, and structured tabular extraction.
- **Credit Agent**: Credit profile parsing, derogatory mark detection, trade-line analysis.
- **Property Agent**: Appraisal analysis, comparable sale adjustments, collateral valuation reconciliation.
- **Compliance Agent**: Fair lending checks, disclosure timing audits, guideline compliance.
- **Decision Agent**: Holistic underwriter recommendation synthesis (Approve / Deny / Suspend with Conditions).

### 3.5 Future LangGraph Orchestration (`backend/app/workflows/`)
- State graph management with `UnderwritingState`.
- Conditional routing based on loan complexity and high-risk flags.
- Native Human-in-the-loop (HITL) checkpoints for underwriter approval or condition overrides.

### 3.6 Future Regulatory RAG Pipeline (`backend/app/rag/`)
- Semantic chunking of Fannie Mae (FNMA) Selling Guide and Freddie Mac (FHLMC) guidelines.
- Open-source dense embeddings via `sentence-transformers`.
- Vector indexing using ChromaDB / FAISS with hybrid keyword retrieval and cross-encoder reranking.

### 3.7 Storage Boundary (`storage/`)
- File system isolation for uploaded documents (`uploads/`), processed artifacts (`processed/`), and generated underwriting PDF reports (`reports/`).
- Enforces access control boundaries to safeguard sensitive borrower financial records.
