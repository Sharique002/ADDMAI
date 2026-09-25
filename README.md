# ADDMAI

**AI-Powered Deepfake Detection & Media Authenticity Intelligence**

[![Stage](https://img.shields.io/badge/Stage-1%3A%20Infrastructure-blue.svg)](#)
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

## 2. Current Status: Stage 1

The project is currently at **Stage 1 — Repository & Development Infrastructure**.

> [!IMPORTANT]
> **Stage 1 Scope:** This stage establishes the local development environment, containerized infrastructure, backend API foundations, and frontend application shell.
> **No deepfake models, video/audio extraction pipelines, database schemas, or forensic algorithms are implemented yet.** Those belong to subsequent stages.

---

## 3. Technology Foundation

- **Backend:** Python 3.11+, FastAPI, Pydantic v2
- **Frontend:** React 18, TypeScript 5, Vite
- **Database:** PostgreSQL 16
- **Task Queue & Cache:** Redis 7
- **Object Storage:** MinIO (local S3-compatible)
- **Containerization:** Docker, Docker Compose
- **Testing:** Python `unittest` / `pytest`

---

## 4. Prerequisites

- Python 3.11+
- Node.js v18+ & npm
- Docker & Docker Compose (optional for containerized stack)
- Git

---

## 5. Local Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Sharique002/ADDMAI.git
   cd ADDMAI
   ```

2. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```

3. **Install Frontend Dependencies:**
   ```bash
   cd apps/web
   npm install
   cd ../..
   ```

---

## 6. Starting the Stack Locally

### Option A: Docker Compose (All Services)
```bash
docker compose up -d
```
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

## 8. Health & Verification Endpoints

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

- **Readiness Probe:**
  ```http
  GET http://localhost:8000/api/v1/ready
  ```
  Returns readiness status of configured infrastructure dependencies (PostgreSQL, Redis, MinIO).

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
