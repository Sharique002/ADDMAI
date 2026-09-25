# ADDMAI Development Guide (Stage 3: AI Detection Engine)

This guide provides instructions for setting up, running, testing, and verifying the **ADDMAI** development environment.

> [!NOTE]
> **Stage 3 Scope:** This guide covers repository layout, local infrastructure (Docker Compose), backend API foundations, Alembic database migrations (`media_records`, `model_predictions`), media ingestion and integrity hardening, and the Stage 3 AI Deepfake Detection Engine with React analyst dashboard. Forensic analysis (ELA/FFT), temporal consistency, and multi-signal evidence fusion will be introduced in subsequent stages.

---

## 1. Prerequisites

Before running the platform, ensure the following tooling is installed:

- **Python:** 3.11 or higher (3.11.9 recommended)
- **Node.js:** v18.0 or higher (v20+ recommended) with `npm`
- **Docker & Docker Compose:** v2.20+ (for containerized stack execution)
- **Git:** Version 2.40+

---

## 2. Dependency Management Strategy

ADDMAI enforces a clear source-of-truth hierarchy across dependency files:

1. **`pyproject.toml` (Authoritative):**
   - The single authoritative source for project metadata, Python version constraints (`>=3.11`), core runtime dependencies, and development tools.
2. **`requirements.txt` (Production & Docker):**
   - Derived directly from `pyproject.toml`. Maintained for container build compatibility (`apps/api/Dockerfile`) and standard deployment environments.
3. **`requirements-dev.txt` (Local Development):**
   - References `requirements.txt` and adds developer test harnesses (`pytest`, `ruff`, `pytest-cov`).

### Local Python Environment Setup
```bash
python -m venv .venv
# Activate on Windows:
.venv\Scripts\Activate.ps1
# Activate on Linux/macOS:
source .venv/bin/activate

# Install dependencies:
pip install -r requirements-dev.txt
# Or in editable mode via pyproject:
pip install -e .[dev]
```

---

## 3. Environment & Credential Policy

### Development vs Production Credentials
- **Development Mode (`APP_ENV=development`):**
  - Safe, local development defaults are provided (e.g., `addmai_dev_password` and `minioadmin`).
  - Marked clearly in `.env.example` as `DEVELOPMENT ONLY`.
- **Production Mode (`APP_ENV=production`):**
  - The application strictly refuses to start if default development passwords or MinIO keys are detected.
  - Explicit, unique, cryptographically strong credentials must be provided.
- **CORS Security:**
  - Wildcard origin (`*`) is strictly rejected across all environments. Explicit origins must be declared in `CORS_ALLOWED_ORIGINS`.

---

## 4. Repository Layout

```
ADDMAI/
├── apps/
│   ├── api/             # FastAPI backend service
│   │   ├── app/         # Application modules
│   │   │   ├── api/v1/  # Health and Media REST routes
│   │   │   │   ├── health.py
│   │   │   │   └── media.py
│   │   │   ├── core/    # Config, logging, security, media_types registry
│   │   │   ├── db/      # Async database engine & session dependency
│   │   │   ├── models/  # SQLAlchemy models (media_records)
│   │   │   ├── repositories/ # Media data access repositories
│   │   │   ├── schemas/ # Pydantic schemas (MediaIngestionResponse, etc.)
│   │   │   ├── services/# Domain services:
│   │   │   │   ├── health.py
│   │   │   │   ├── media_ingestion.py
│   │   │   │   ├── media_inspection.py
│   │   │   │   ├── metadata.py
│   │   │   │   └── storage.py
│   │   │   └── main.py  # FastAPI entrypoint
│   │   ├── tests/       # Health & Media API integration tests
│   │   └── Dockerfile   # Pinned Python 3.11.9-slim container
│   └── web/             # React + TypeScript frontend dashboard
│       ├── src/         # UI components, Ingestion UI & apiService abstraction
│       └── Dockerfile   # Pinned Node 20.12.2-alpine container
├── ml/                  # Machine learning models (Stage 3 & 4)
├── forensic/            # Forensic signal extractors (Stage 5)
├── provenance/          # C2PA provenance parser (Stage 5)
├── worker/              # Background analysis task workers (Stage 8)
├── database/            # Database schema & migrations
│   ├── migrations/      # Alembic migration versions
│   └── schema.sql       # Reference SQL schema (media_records)
├── tests/               # Unit and integrity test suites
│   ├── unit/            # Media integrity, validation, and service tests
│   └── api/             # Route integration tests
├── infra/               # Deployment and container orchestration manifests
├── scripts/             # Developer automation utilities
├── docs/                # Architecture and design documentation
├── docker-compose.yml   # Multi-service development stack (pinned versions)
├── alembic.ini          # Database migration configuration
├── Makefile             # Automation commands
├── pyproject.toml       # Python package configuration (Authoritative)
└── README.md            # Project introduction and roadmap status
```


---

## 5. Running the Application

### Option A: Complete Docker Compose Stack
To start all 5 services simultaneously:
```bash
docker compose up -d
```
All container images are pinned to specific version tags to eliminate unexpected environment drift:
- `postgres:16.2-alpine`
- `redis:7.2.4-alpine`
- `minio/minio:RELEASE.2024-03-30T09-41-56Z`

Verify service status:
```bash
docker compose ps
```
To stop the stack:
```bash
docker compose down
```

### Option B: Local Native Execution

#### 1. Backend (FastAPI)
Activate your Python virtual environment and start the API server:
```bash
python -m uvicorn app.main:app --app-dir apps/api --reload --port 8000
```
- Interactive Swagger API docs: `http://localhost:8000/api/v1/docs`
- Health probe endpoint: `http://localhost:8000/api/v1/health`
- Readiness probe endpoint: `http://localhost:8000/api/v1/ready`

#### 2. Frontend (React + TypeScript)
In a separate terminal, install dependencies and launch the dev server:
```bash
cd apps/web
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 6. Health & Truthful Readiness Semantics

- **Liveness Probe (`GET /api/v1/health`):**
  - Always returns `HTTP 200` with `{"status": "healthy"}` if the FastAPI process is responsive.
- **Readiness Probe (`GET /api/v1/ready`):**
  - Performs active TCP connectivity verification against PostgreSQL (`5432`), Redis (`6379`), and MinIO (`9000`).
  - Returns `HTTP 200` with `"status": "ready"` **only** if all configured dependencies are reachable.
  - Returns `HTTP 503` with `"status": "not_ready"` if any dependency is unreachable or malformed.
  - Never falsely reports "ready" due to environment flags.

---

## 7. Database Migrations & Schema Evolution

Alembic serves as the **sole authoritative mechanism** for database schema definition and migration.

- **Apply Migrations:**
  ```bash
  alembic upgrade head
  ```
- **Generate New Migration:**
  ```bash
  alembic revision --autogenerate -m "describe_change"
  ```
- **Table Invariants:**
  - `media_records`: `ck_media_records_size_bytes_non_negative` (`size_bytes >= 0`), `ck_media_records_media_category` (`media_category IN ('image', 'video')`).
  - `model_predictions`: `ck_model_predictions_prediction` (`prediction IN ('REAL', 'DEEPFAKE')`), `ck_model_predictions_confidence_range` (`confidence >= 0.0 AND confidence <= 1.0`).

---

## 8. Testing & Verification

### Running Automated Backend Tests (121 Tests)
Run the complete backend test suite across unit, integrity, storage, concurrency, ML model, loader security, database, and API integration:
```bash
python -m unittest tests/api/test_health.py tests/unit/test_config.py tests/unit/test_security_logging.py tests/unit/test_media_service.py tests/unit/test_media_storage.py tests/unit/test_media_integrity.py tests/unit/test_media_concurrency.py apps/api/tests/test_health.py apps/api/tests/test_media_api.py tests/unit/test_ml_preprocessing.py tests/unit/test_ml_model.py tests/unit/test_ml_loader_security.py tests/unit/test_ml_database.py tests/unit/test_media_original_integrity.py apps/api/tests/test_media_detect_api.py
```

### Verifying Frontend Compilation
To run TypeScript checks and compile the production bundle:
```bash
cd apps/web
npm run build
```

---

## 9. Service Ports Reference

| Service | Internal Port | Host Port | Protocol | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **API** | `8000` | `8000` | HTTP | FastAPI REST Gateway |
| **Frontend** | `5173` | `5173` | HTTP | React Web Shell |
| **PostgreSQL** | `5432` | `5432` | TCP | Relational metadata persistence |
| **Redis** | `6379` | `6379` | TCP | Task queue broker & state cache |
| **MinIO API** | `9000` | `9000` | HTTP | S3 Object storage API |
| **MinIO Console** | `9001` | `9001` | HTTP | Web storage management UI |
