# ADDMAI Development Guide (Stage 1)

This guide provides instructions for setting up, running, and verifying the **ADDMAI** development environment.

> [!NOTE]
> **Stage 1 Scope:** This guide covers repository layout, local infrastructure (Docker Compose), backend API foundations, and frontend shell development. Deepfake AI models, media ingestion pipelines, and forensic algorithms will be introduced in subsequent stages.

---

## 1. Prerequisites

Before running the platform, ensure the following tooling is installed:

- **Python:** 3.11 or higher
- **Node.js:** v18.0 or higher (v20+ recommended) with `npm`
- **Docker & Docker Compose:** v2.20+ (for containerized stack execution)
- **Git:** Version 2.40+

---

## 2. Repository Layout

```
ADDMAI/
├── apps/
│   ├── api/             # FastAPI backend service
│   │   ├── app/         # Application modules (api, core, schemas)
│   │   └── tests/       # Backend unit test suite
│   └── web/             # React + TypeScript frontend dashboard
│       └── src/         # UI components & apiService abstraction
├── ml/                  # Machine learning models (Stage 3 & 4)
├── forensic/            # Forensic signal extractors (Stage 5)
├── provenance/          # C2PA provenance parser (Stage 5)
├── worker/              # Background analysis task workers (Stage 8)
├── database/            # Relational database schemas & migrations (Stage 3)
├── tests/               # Multi-module and end-to-end test runners
├── infra/               # Deployment and container orchestration manifests
├── scripts/             # Developer automation utilities
├── docs/                # Architecture and design documentation
├── docker-compose.yml   # Multi-service development stack
├── Makefile             # Automation commands
├── pyproject.toml       # Python package configuration
└── README.md            # Project introduction and roadmap status
```

---

## 3. Environment Configuration

1. Copy the environment configuration template:
   ```bash
   cp .env.example .env
   ```

2. Review the configured variables in `.env`:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `APP_NAME` | `"ADDMAI API"` | Backend service name |
| `APP_ENV` | `development` | Environment mode (`development`, `testing`, `production`) |
| `API_PORT` | `8000` | Host port for FastAPI REST API |
| `FRONTEND_PORT` | `5173` | Host port for React Vite dev server |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Connection URI for PostgreSQL 16 |
| `REDIS_URL` | `redis://localhost:6379/0` | Connection URI for Redis task broker |
| `MINIO_ENDPOINT` | `http://localhost:9000` | S3 API endpoint for MinIO object storage |
| `MINIO_CONSOLE_URL` | `http://localhost:9001` | Browser console for MinIO management |
| `CORS_ALLOWED_ORIGINS` | `["http://localhost:5173"]` | Explicit CORS allowed origins (no wildcard `*`) |

---

## 4. Running the Application

### Option A: Complete Docker Compose Stack
To start all 5 services simultaneously:
```bash
docker compose up -d
```

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

## 5. Testing & Verification

### Running Automated Backend Tests
Run the unit test suite:
```bash
python -m unittest discover -s apps/api/tests
python -m unittest discover -s tests
```
Or via `pytest` (if installed):
```bash
pytest
```

### Verifying Frontend Compilation
To run TypeScript checks and compile the production bundle:
```bash
cd apps/web
npm run build
```

---

## 6. Service Ports Reference

| Service | Internal Port | Host Port | Protocol | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **API** | `8000` | `8000` | HTTP | FastAPI REST Gateway |
| **Frontend** | `5173` | `5173` | HTTP | React Web Shell |
| **PostgreSQL** | `5432` | `5432` | TCP | Relational metadata persistence |
| **Redis** | `6379` | `6379` | TCP | Task queue broker & state cache |
| **MinIO API** | `9000` | `9000` | HTTP | S3 Object storage API |
| **MinIO Console** | `9001` | `9001` | HTTP | Web storage management UI |

---

## 7. Troubleshooting Common Problems

1. **Port Conflicts (`Address already in use`):**
   - Check if existing services are listening on 8000, 5432, 6379, or 9000 using `netstat -ano` (Windows) or `lsof -i :<port>` (macOS/Linux).
   - Change the port mappings in `.env` (e.g. `API_PORT=8001`).

2. **Readiness Probe Reports `not_ready`:**
   - In development mode (`APP_ENV=development`), the `/api/v1/ready` probe verifies TCP connectivity to PostgreSQL, Redis, and MinIO. If the external Docker containers are not running, this is expected behavior.
   - For isolated test runs, ensure `APP_ENV=testing` is set.

3. **CORS Errors in Browser:**
   - Verify `CORS_ALLOWED_ORIGINS` in `.env` includes the origin where your frontend is running (default: `http://localhost:5173`). Wildcard `*` is prohibited for security compliance.
