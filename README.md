# ADDMAI

**AI-Powered Deepfake Detection & Media Authenticity Intelligence**

[![Stage](https://img.shields.io/badge/Stage-2.1%3A%20Media%20Ingestion%20%26%20Integrity%20Hardening-green.svg)](#)
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

## 2. Current Status: Stage 2.1 (Media Ingestion & Integrity Hardening)

The project has completed **Stage 2.1 — Media Ingestion & Cryptographic Integrity Hardening**.

> [!IMPORTANT]
> **Stage 2.1 Scope:** Hardens the media ingestion layer with schema-level check constraints (`size_bytes >= 0`, `media_category IN ('image', 'video')`), strict single-source Alembic migration authority, hostile filename sanitization (directory traversal, null bytes, unicode stripping), Pillow resource safety (`LOAD_TRUNCATED_IMAGES = False`, `DecompressionBombError` handling), bounded MP4 box parsing (loop limits, size verification), concurrent duplicate race recovery without storage deletion, early `Content-Length` and bounded chunked streaming (25 MB inclusive limit), and transactional consistency rollback.
>
> **Constitutional Boundary:** In accordance with the ADDMAI Engineering Constitution, Stage 2.1 does **NOT** include deepfake detection models, AI inference, face detection, facial landmarks, temporal analysis, forensic algorithms (ELA, FFT), C2PA verification, evidence fusion scoring, or authenticity verdicts (`REAL`, `FAKE`, `LIKELY_AUTHENTIC`, `LIKELY_MANIPULATED`). Stage 2.1 outputs strictly: `MEDIA INGESTED + INTEGRITY VERIFIED + STRUCTURED OBSERVATIONS`.


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

## 9. Media Ingestion & Integrity Endpoints (Stage 2)

- **Ingest Untrusted Media:**
  ```http
  POST http://localhost:8000/api/v1/media
  Content-Type: multipart/form-data
  ```
  **Parameters:** `file` (Multipart file upload; accepted formats: `.jpg`, `.jpeg`, `.png`, `.mp4` up to 25 MB).
  **Behavior:**
  - Validates magic bytes against declared extension and MIME.
  - Generates immutable 64-character lowercase hex SHA-256 digest from original bytes.
  - Deduplicates: Identical SHA-256 reuses existing canonical asset without duplicate storage.
  - Stores raw bytes in MinIO at `media/original/{sha256}`.
  - Persists structured record in PostgreSQL `media_records` table.
  - Extracts container dimensions and metadata neutrally without authenticity verdicts.
  **Response:** `HTTP 201 Created` (new) or `HTTP 200 OK` (deduplicated)
  ```json
  {
    "media_id": "89f82b94-4bf6-4e03-b957-3a4a9497fe2f",
    "sha256_digest": "4a5b6c...",
    "media_category": "image",
    "mime_type": "image/jpeg",
    "original_filename": "sample.jpg",
    "size_bytes": 123456,
    "validation_status": "accepted",
    "created_at": "2026-09-25T13:00:00Z",
    "is_duplicate": false,
    "analysis": {
      "container": { "format": "JPEG", "width": 1920, "height": 1080, "exif_present": false },
      "integrity": { "sha256_digest": "4a5b6c...", "algorithm": "SHA-256", "verified": true }
    }
  }
  ```

- **Retrieve Ingestion Record:**
  ```http
  GET http://localhost:8000/api/v1/media/{media_id}
  ```
  Returns `HTTP 200 OK` with structured metadata record. Never returns the original binary bytes or raw storage credentials.

- **Error Contract (RFC-7807):**
  - `HTTP 413`: Payload Too Large (> 25 MB inclusive limit, checked via early `Content-Length` header and bounded 1MB chunked streaming)
  - `HTTP 415`: Unsupported Media Type (magic-byte / extension mismatch or unsupported format)
  - `HTTP 422`: Malformed / Empty Media Content (truncated file, decompression bomb, corrupted container)
  - `HTTP 404`: Media Not Found

---

## 10. Database Schema Authority & Check Constraints

1. **Schema Authority:**
   - **Alembic Migrations (`database/migrations/`):** The **single authoritative source of truth** for database schemas and evolution.
   - **`database/schema.sql`:** Maintained as a bootstrap script for fresh Docker initialization.
2. **Table Constraints (`media_records`):**
   - `ck_media_records_size_bytes_non_negative`: `size_bytes >= 0`
   - `ck_media_records_media_category`: `media_category IN ('image', 'video')`
   - `uq_media_records_sha256_digest`: `UNIQUE (sha256_digest)`
3. **Concurrent Duplicate Race Handling:**
   - If two concurrent requests upload identical media bytes simultaneously, the unique constraint prevents duplicate rows.
   - The losing transaction catches `IntegrityError`, rolls back, retrieves the winner's canonical record, and reuses the stored object without deleting it.

---

## 11. Testing & Verification

All test suites run deterministically in local environments without requiring an active Docker daemon by utilizing isolated in-memory/SQLite WAL and mock storage backends.

### Run All Backend Tests (90 Tests):
```bash
python -m unittest tests/api/test_health.py tests/unit/test_config.py tests/unit/test_security_logging.py tests/unit/test_media_service.py tests/unit/test_media_storage.py tests/unit/test_media_integrity.py tests/unit/test_media_concurrency.py apps/api/tests/test_health.py apps/api/tests/test_media_api.py
```

### Run Frontend Typecheck & Build:
```bash
cd apps/web
npm run build
```

---

## 12. Repository Documentation Index

- [Project Constitution & Principles](docs/project-constitution.md)
- [System Architecture](docs/architecture.md)
- [Developer Onboarding & Troubleshooting Guide](docs/development.md)

