# Infrastructure & Deployment (`infra/`)

This directory contains infrastructure specifications and orchestration manifests.

## Current Setup (Stage 1)
- **Local Dev Stack:** Managed via root `docker-compose.yml`.
  - `postgres` (PostgreSQL 16)
  - `redis` (Redis 7)
  - `minio` (S3-compatible Object Storage)
  - `api` (FastAPI backend on port 8000)
  - `web` (React frontend on port 5173)

## Planned Additions (Later Stages)
- Production Kubernetes manifests / Helm charts
- Prometheus & Grafana telemetry dashboards (Stage 11)
