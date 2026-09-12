# AI Mortgage Underwriting Automation System

[![Backend Status](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Frontend Status](https://img.shields.io/badge/Frontend-Next.js%2014-black.svg)](https://nextjs.org)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%2016-336791.svg)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com)
[![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-black.svg)](https://github.com/astral-sh/ruff)

A modular, production-style automated mortgage underwriting engine built with clean architecture principles.

---

## 1. Project Name & Description
**Mortgage Underwriting AI** is an intelligent underwriting platform designed to streamline end-to-end mortgage risk evaluation, regulatory compliance verification, deterministic financial calculations, document processing, and human-in-the-loop decision recommendations.

---

## 2. Project Objective
The full system will eventually automate mortgage underwriting through:
1. **Document Ingestion**: Multi-modal upload and storage boundaries.
2. **OCR & Document Classification**: Automated classification of W-2s, 1040s, paystubs, bank statements, and appraisals.
3. **Structured Field Extraction**: Extraction of borrower income, assets, liabilities, and collateral details.
4. **Document Validation**: Cross-verification of dates, employers, wages, and signatures.
5. **Credit Analysis**: Tri-merge credit profile analysis and derogatory mark detection.
6. **DTI Calculation**: Deterministic front-end and back-end debt-to-income ratios.
7. **LTV Calculation**: Deterministic loan-to-value (LTV) and combined loan-to-value (CLTV).
8. **DSCR Calculation**: Debt service coverage ratios for investment properties.
9. **FICO Interpretation**: Representative qualifying credit score selection.
10. **Property Valuation**: Appraisal reconciliation and comparable sales analysis.
11. **Regulatory Compliance Checking**: Programmatic compliance enforcement (RESPA, TILA, HMDA, Fair Lending).
12. **FNMA / FHLMC Guideline RAG**: Retrieval-Augmented Generation for Fannie Mae / Freddie Mac selling guidelines.
13. **Fair Lending & HMDA Flag Detection**: Automated disparate impact and LAR reporting checks.
14. **Risk Scoring**: Multi-factor composite risk index.
15. **Decision Recommendation**: Automated underwriting recommendation (Approve, Deny, Suspend).
16. **Human-in-the-Loop Review**: Underwriter review, condition sign-off, and override workflows.
17. **Natural-Language Underwriting Report**: Synthesized executive underwriting narrative.
18. **PDF Generation**: Standardized Fannie Mae Form 1008 Transmittal Summary generation.
19. **Audit Logging**: Immutable event trails for regulatory compliance.
20. **Evaluation & Testing**: Golden dataset benchmarking for extraction and decision accuracy.
21. **LangGraph Workflow Orchestration**: State-driven multi-agent coordination.

---

## 3. Current Phase 0 Scope
> **IMPORTANT NOTE**: Phase 0 establishes **strictly the foundation, directory hierarchy, configuration skeleton, documentation, development environment, and tests**. 
> No business logic, AI agents, OCR pipelines, RAG systems, financial math, or compliance rules are active yet. All future domain modules exist as clean, decoupled placeholders ready for incremental development.

---

## 4. Architecture Overview
The system follows a strict layered separation:
```text
Frontend (Next.js 14 / Tailwind CSS)
   ↓ [HTTP / JSON REST]
API Gateway (FastAPI / Pydantic v2 / Exception Handlers)
   ↓
Service & Orchestration Layer (LangGraph State Machine / Agents)
   ↓
Domain Logic (Deterministic Calculations / Compliance Rule Engines)
   ↓
Persistence & Storage (PostgreSQL / Local File System Boundaries)
```

Detailed architectural blueprints are documented in [`docs/architecture/overview.md`](docs/architecture/overview.md).

---

## 5. Folder Structure
```text
mortgage-underwriting-ai/
│
├── backend/
│   ├── app/
│   │   ├── api/                  # API routers (health, auth, applications, etc.)
│   │   ├── agents/               # Multi-agent placeholders (document, credit, property, etc.)
│   │   ├── workflows/            # LangGraph state machine & workflow graphs
│   │   ├── document_processing/  # OCR, classification, extraction, validation
│   │   ├── calculations/         # Deterministic financial math (DTI, LTV, DSCR, FICO)
│   │   ├── rag/                  # Regulatory guideline RAG pipeline
│   │   ├── compliance/           # RESPA, TILA, HMDA, Fair Lending rules
│   │   ├── property/             # Valuation, comps, and property data adapters
│   │   ├── reports/              # Underwriting narrative & PDF generation
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── database/             # Database connection, base model, migrations
│   │   ├── security/             # Authentication, RBAC permissions, encryption
│   │   ├── core/                 # Config (Pydantic Settings), logging, exceptions
│   │   └── main.py               # FastAPI application entry point
│   │
│   ├── tests/
│   │   ├── unit/                 # Unit tests (health, config, exceptions)
│   │   ├── integration/          # Database & service integration tests
│   │   └── evaluation/           # AI accuracy benchmarks (Phase 1+)
│   │
│   ├── requirements.txt          # Production dependencies
│   ├── requirements-dev.txt      # Dev / test dependencies (pytest, ruff, mypy)
│   ├── Dockerfile                # Multi-stage Python 3.11 container
│   ├── .dockerignore
│   └── pyproject.toml            # Tool configurations (Ruff, Pytest)
│
├── frontend/
│   ├── app/                      # Next.js App Router (layout.tsx, page.tsx, globals.css)
│   ├── components/               # Header, Sidebar, Dashboard, HealthStatus
│   ├── hooks/                    # Custom React hooks
│   ├── lib/                      # API client and helper functions
│   ├── services/                 # Health check and domain API services
│   ├── types/                    # TypeScript interfaces
│   ├── public/                   # Static assets
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── postcss.config.mjs
│   ├── next.config.mjs
│   ├── Dockerfile                # Multi-stage Node.js container
│   └── .dockerignore
│
├── data/
│   ├── sample_documents/         # Synthetic sample borrower documents (no PII)
│   ├── regulatory_docs/          # FNMA, FHLMC, CFPB reference guideline manuals
│   ├── test_cases/               # Structured test case loan profiles
│   └── ground_truth/             # Golden evaluation benchmark datasets
│
├── scripts/                      # Setup and utility automation scripts
│   ├── setup_dev.py
│   └── README.md
│
├── docs/                         # System documentation
│   ├── architecture/overview.md  # Architectural blueprint
│   ├── api/overview.md           # API endpoints and schema registry
│   ├── compliance/overview.md    # Regulatory statutes and rule mappings
│   └── evaluation/overview.md    # Benchmark methodologies and metrics
│
├── storage/                      # Secure file storage boundaries (gitignored)
│   ├── uploads/                  # Raw document uploads
│   ├── processed/                # Normalized / OCR-processed files
│   └── reports/                  # Generated underwriting PDFs
│
├── docker-compose.yml            # PostgreSQL + Backend + Frontend orchestration
├── .env.example                  # Environment variable template
├── .gitignore                    # Git exclusions
├── README.md                     # Project documentation
└── Makefile                      # Automation commands
```

---

## 6. Technology Stack

### Backend
- **Python 3.11+**
- **FastAPI**: Modern, high-performance web framework.
- **Pydantic v2 & Pydantic Settings**: Data validation and type-safe environment configuration.
- **SQLAlchemy 2.0 (Async)**: ORM and database abstraction.
- **PostgreSQL 16**: Relational data persistence.
- **Alembic**: Database migrations.

### Frontend
- **Next.js 14+ (App Router)**: Modern React full-stack framework.
- **React 18 & TypeScript**: Component-driven typed user interface.
- **Tailwind CSS**: Utility-first styling with dark mode support.
- **Lucide Icons**: Comprehensive iconography.

### DevOps & Code Quality
- **Docker & Docker Compose**: Containerized multi-service orchestration.
- **Pytest & Pytest-Asyncio**: Asynchronous unit and integration testing.
- **Ruff**: Fast Python linter and formatter.

---

## 7. Local Setup Instructions

### Prerequisites
- Python 3.11+ (Python 3.14 compatible)
- Node.js 18+ & npm
- Docker & Docker Compose (Optional for containerized mode)
- Git

### Step 1: Clone and Enter Repository
```bash
git clone <repo-url>
cd mortgage-underwriting-ai
```

### Step 2: Initialize Environment File
```bash
# Windows PowerShell
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

### Step 3: Run Dev Setup Script
```bash
python scripts/setup_dev.py
```

---

## 8. Environment Variable Setup
Inspect `.env` and verify key settings:
```ini
APP_NAME="Mortgage Underwriting AI"
APP_ENV=development
DEBUG=true
API_PORT=8000
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/mortgage_underwriting
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 9. Docker Commands
Start all services (PostgreSQL, FastAPI Backend, Next.js Frontend) in isolated containers:

```bash
# Build and launch all services in the background
docker compose up --build -d

# View real-time logs
docker compose logs -f

# Check container health status
docker compose ps

# Stop all services
docker compose down
```

---

## 10. Backend Run Instructions (Standalone)

```bash
# 1. Create and activate Python virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 2. Install dependencies
pip install -r backend/requirements.txt -r backend/requirements-dev.txt

# 3. Start the FastAPI development server
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Health: `http://localhost:8000/api/v1/health`
- Interactive API Docs: `http://localhost:8000/docs`

---

## 11. Frontend Run Instructions (Standalone)

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install npm packages
npm install

# 3. Start Next.js development server
npm run dev
```
- Web Application: `http://localhost:3000`

---

## 12. Test & Linting Commands

```bash
# Run backend unit and integration test suite
cd backend
pytest tests/ -v

# Run Python linting with Ruff
ruff check .

# Run Frontend build and linting check
cd ../frontend
npm run lint
npm run build
```

---

## 13. Future Development Roadmap

- **Phase 1**: Application Intake & Data Models (Loan Application Schema, DB Repositories, Authentication).
- **Phase 2**: Document Ingestion, OCR Pipeline, and Information Extraction.
- **Phase 3**: Deterministic Financial Calculation Engine (DTI, LTV, CLTV, DSCR, Qualifying FICO).
- **Phase 4**: Regulatory Guidelines RAG Pipeline (FNMA/FHLMC selling guide embeddings & reranking).
- **Phase 5**: Statutory Compliance Engine (RESPA disclosure timing, TILA APR rules, HMDA LAR, Fair Lending).
- **Phase 6**: LangGraph Multi-Agent Orchestration & Human-in-the-loop (HITL) review.
- **Phase 7**: Underwriting Findings Synthesis, Fannie Mae Form 1008 PDF Generator, and Golden-set Evaluation.
