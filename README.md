# ADDMAI

**AI-Powered Deepfake Detection & Media Authenticity Intelligence**

[![Stage](https://img.shields.io/badge/Stage-3%3A%20AI%20Detection%20Engine-green.svg)](#)
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

## 2. Current Status: Stage 3 (AI Detection Engine)

The project has achieved **Stage 3 — AI Detection Engine**.

> [!IMPORTANT]
> **Stage 3 Scope:** Introduces the AI deepfake detection model pipeline operating on canonical media ingested via Stage 2.1. Implements MesoNet-4 inspired CNN (`ADDMAIDeepfakeDetector`), safe artifact loading via native `safetensors` (`model.safetensors`), strict SHA-256 pre-inference checksum validation, deterministic resizing and center-cropping preprocessing (`224x224`), `model_predictions` relational persistence, mandatory byte-for-byte original media immutability verification, and REST inference endpoint (`POST /api/v1/media/{media_id}/detect`).
>
> **Constitutional Boundary:** In strict accordance with the ADDMAI Engineering Constitution, Stage 3 outputs ONLY: `MODEL PREDICTION` (`REAL` or `DEEPFAKE`). It does **NOT** produce final authenticity verdicts (`LIKELY_AUTHENTIC`, `LIKELY_MANIPULATED`, `INCONCLUSIVE`), multi-signal evidence fusion, temporal consistency analysis, forensic analysis (ELA, FFT), or C2PA verification. Stage 3 outputs: `MEDIA INGESTED + INTEGRITY VERIFIED + MODEL PREDICTION`.


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

- **Execute AI Deepfake Detection (Stage 3):**
  ```http
  POST http://localhost:8000/api/v1/media/{media_id}/detect
  ```
  **Behavior:**
  - Retrieves canonical media asset from object storage via immutable storage key.
  - Verifies cryptographic SHA-256 before inference.
  - Executes deterministic preprocessing (decoding, resizing to 256x256, center-cropping to 224x224, ImageNet normalization).
  - Runs forward inference via `ADDMAIDeepfakeDetector` in PyTorch eval mode (`torch.no_grad()`).
  - Verifies byte SHA-256 after inference is strictly unchanged (immutability guarantee).
  - Persists prediction in `model_predictions` relational table.
  - Returns structured `ModelPredictionResponse` with model ID, version, prediction (`REAL` or `DEEPFAKE`), confidence score, and timestamp. Zero final authenticity claims.
  **Response:** `HTTP 200 OK`
  ```json
  {
    "media_id": "89f82b94-4bf6-4e03-b957-3a4a9497fe2f",
    "model": {
      "model_id": "addmai-deepfake-detector",
      "version": "1.0.0"
    },
    "prediction": "DEEPFAKE",
    "confidence": 0.9124,
    "preprocessing_version": "1.0.0",
    "inference_timestamp": "2026-09-25T18:40:00Z",
    "prediction_id": "c1f7b889-1123-455b-b98a-2c8e23f00122"
  }
  ```

- **Error Contract (RFC-7807):**
  - `HTTP 413`: Payload Too Large (> 25 MB inclusive limit, checked via early `Content-Length` header and bounded 1MB chunked streaming)
  - `HTTP 415`: Unsupported Media Type (magic-byte / extension mismatch or unsupported format; video detection rejected in Stage 3)
  - `HTTP 422`: Malformed / Empty Media Content (truncated file, decompression bomb, corrupted container)
  - `HTTP 404`: Media Not Found
  - `HTTP 500`: Model Artifact or Storage Integrity Failure

---

## 10. Database Schema Authority & Check Constraints

1. **Schema Authority:**
   - **Alembic Migrations (`database/migrations/`):** The **single authoritative source of truth** for database schemas and evolution.
   - **`database/schema.sql`:** Maintained as a bootstrap script for fresh Docker initialization.
2. **Table Constraints (`media_records`):**
   - `ck_media_records_size_bytes_non_negative`: `size_bytes >= 0`
   - `ck_media_records_media_category`: `media_category IN ('image', 'video')`
   - `uq_media_records_sha256_digest`: `UNIQUE (sha256_digest)`
3. **Table Constraints (`model_predictions` — Stage 3):**
   - `fk_model_predictions_media_id`: `FOREIGN KEY (media_id) REFERENCES media_records(id) ON DELETE CASCADE`
   - `ck_model_predictions_prediction`: `prediction IN ('REAL', 'DEEPFAKE')`
   - `ck_model_predictions_confidence_range`: `confidence >= 0.0 AND confidence <= 1.0`
4. **Concurrent Duplicate Race Handling:**
   - If two concurrent requests upload identical media bytes simultaneously, the unique constraint prevents duplicate rows.
   - The losing transaction catches `IntegrityError`, rolls back, retrieves the winner's canonical record, and reuses the stored object without deleting it.

---

## 11. Testing & Verification

All test suites run deterministically in local environments without requiring an active Docker daemon by utilizing isolated in-memory/SQLite WAL and mock storage backends.

### Run All Backend Tests (121 Tests):
```bash
python -m unittest tests/api/test_health.py tests/unit/test_config.py tests/unit/test_security_logging.py tests/unit/test_media_service.py tests/unit/test_media_storage.py tests/unit/test_media_integrity.py tests/unit/test_media_concurrency.py apps/api/tests/test_health.py apps/api/tests/test_media_api.py tests/unit/test_ml_preprocessing.py tests/unit/test_ml_model.py tests/unit/test_ml_loader_security.py tests/unit/test_ml_database.py tests/unit/test_media_original_integrity.py apps/api/tests/test_media_detect_api.py
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
- [Stage 3 AI Detection Engine Completion Report](docs/stage-3-completion-report.md)


