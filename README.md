# ADDMAI

**AI-Powered Deepfake Detection & Media Authenticity Intelligence**

[![Stage](https://img.shields.io/badge/Stage-1.1%3A%20Foundation%20Hardened-blue.svg)](#)
[![License](https://img.shields.io/badge/License-Proprietary-lightgrey.svg)](#)

---

## 1. Project Overview

**ADDMAI** is a production-oriented AI-assisted media authenticity analysis platform. Rather than reducing verification to an error-prone binary classifier (`Media -> AI Model -> REAL/FAKE`), ADDMAI synthesizes multiple independent forensic evidence channels:

1. **AI Face Manipulation Detection:** Convolutional & vision transformer inference
2. **Temporal Consistency Analysis:** Inter-frame continuity, landmark stability, and blink cadence
3. **Media Forensic Signals:** Error Level Analysis (ELA), frequency artifacts (FFT), double quantization
4. **Metadata & Container Inspection:** Encoding profiles, EXIF integrity, container structures
5. **Cryptographic Integrity:** Immutable SHA-256 byte digest tracking
6. **Content Provenance:** C2PA / Content Authenticity Initiative signed assertion validation
7. **Deterministic Evidence Fusion:** Transparent evidence synthesis resolving contradictory signals into explainable assessments (`LIKELY_AUTHENTIC`, `LIKELY_MANIPULATED`, or `INCONCLUSIVE`)

---

## 2. Current Status: Stage 1.1 (Foundation Hardening)

The project has achieved **Stage 1.1 — Foundation Hardening**.

> [!IMPORTANT]
> **Stage 1.1 Scope:** Hardens Python packaging consistency, truthful health/readiness semantics, Pydantic typed settings validation, pinned Docker reproducibility, and security utilities.
> **No deepfake models, video/audio extraction pipelines, database schemas, or forensic algorithms are implemented yet.** Those belong to subsequent stages.

---

## 3. Technology Foundation

- **Backend:** Python 3.11+ (Pinned container: `python:3.11.9-slim`), FastAPI, Pydantic v2
- **Frontend:** React 18, TypeScript 5, Vite (Pinned container: `node:20.12.2-alpine`)
- **Database:** PostgreSQL 16 (Pinned container: `postgres:16.2-alpine`)
- **Task Queue & Cache:** Redis 7 (Pinned container: `redis:7.2.4-alpine`)
- **Object Storage:** MinIO (Pinned container: `minio/minio:RELEASE.2024-03-30T09-41-56Z`)
- **Testing:** Python `unittest` / `pytest`

---

## 4. Prerequisites

- Python 3.11+ (3.11.9 recommended)
- Node.js v18+ & npm
- Docker & Docker Compose (for containerized stack execution)
- Git

---

## 5. Dependency Management Strategy

- **`pyproject.toml` (Authoritative):** Single source of truth for dependencies, Python version (`>=3.11`), and test runner paths.
- **`requirements.txt` (Docker & Production):** Maintained for reproducible container builds and production deployments.
- **`requirements-dev.txt` (Local Dev):** Development test harnesses (`pytest`, `ruff`, `pytest-cov`).

### Local Environment Setup:
```bash
git clone https://github.com/Sharique002/ADDMAI.git
cd ADDMAI
cp .env.example .env

# Install backend dependencies:
pip install -r requirements-dev.txt

# Install frontend dependencies:
cd apps/web
npm install
cd ../..
```

---

## 6. Starting the Stack Locally

### Option A: Complete Docker Compose Stack
```bash
docker compose up -d
```
All container images are pinned to specific version tags to eliminate unexpected environment drift.
To view logs:
```bash
docker compose logs -f
```
To stop containers:
```bash
docker compose down
```

### Option B: Native Execution

1. **Start FastAPI Backend:**
   ```bash
   python -m uvicorn app.main:app --app-dir apps/api --reload --port 8000
   ```

2. **Start React Frontend:**
   ```bash
   cd apps/web
   npm run dev
   ```

---

## 7. Service Ports Reference

| Service | Host Port | Protocol | Purpose |
| :--- | :--- | :--- | :--- |
| **API Gateway** | `8000` | HTTP | FastAPI REST endpoints & Swagger docs |
| **Web Frontend** | `5173` | HTTP | React + TypeScript Dashboard |
| **PostgreSQL** | `5432` | TCP | Relational metadata persistence |
| **Redis** | `6379` | TCP | Task queue broker & state cache |
| **MinIO API** | `9000` | HTTP | S3-compatible object storage API |
| **MinIO Console** | `9001` | HTTP | Web management console for MinIO |

---

## 8. Health & Truthful Verification Endpoints

- **Liveness Probe:**
  ```http
  GET http://localhost:8000/api/v1/health
  ```
  Returns `HTTP 200`:
  ```json
  {
    "status": "healthy"
  }
  ```

- **Truthful Readiness Probe:**
  ```http
  GET http://localhost:8000/api/v1/ready
  ```
  Actively probes PostgreSQL, Redis, and MinIO connectivity via TCP.
  - Returns `HTTP 200` with `"status": "ready"` when all configured infrastructure dependencies are reachable.
  - Returns `HTTP 503` with `"status": "not_ready"` if any dependency is unreachable or malformed.
  - Never leaks passwords, credentials, or internal URIs.

- **Interactive Documentation:**
  `http://localhost:8000/api/v1/docs`

---

## 9. Testing Instructions

### Run Backend Unit Tests:
```bash
python -m unittest discover -s apps/api/tests
python -m unittest discover -s tests
```

### Run Frontend Typecheck & Build:
```bash
cd apps/web
npm run build
```

---

## 10. Repository Documentation Index

- [Project Constitution & Principles](docs/project-constitution.md)
- [System Architecture](docs/architecture.md)
- [Developer Onboarding & Troubleshooting Guide](docs/development.md)
