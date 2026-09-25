# ADDMAI

**AI-Powered Deepfake Detection & Media Authenticity Intelligence**

[![Stage](https://img.shields.io/badge/Stage-0%3A%20Constitution-blue.svg)](#)
[![License](https://img.shields.io/badge/License-Proprietary-lightgrey.svg)](#)

---

## Overview

ADDMAI is an engineering platform designed for robust, explainable media authenticity analysis. Rather than relying on a single deepfake classification model, ADDMAI treats media verification as a multi-signal forensic discipline by synthesizing:

1. **AI Detection:** Deep learning facial manipulation detection
2. **Temporal Consistency:** Inter-frame continuity and physiological coherence
3. **Forensic Signals:** Compression anomalies, frequency domain analysis, and blending artifacts
4. **Metadata & Container Inspection:** File structure and camera/encoding profile validation
5. **Cryptographic Integrity:** Immutable SHA-256 byte tracking
6. **Provenance:** C2PA / Content Authenticity Initiative credential verification (when available)
7. **Evidence Fusion:** Deterministic, multi-evidence synthesis capable of resolving conflicting signals

---

## Project Status: Stage 0

The project is currently at **Stage 0 — Project Constitution & Engineering Rules**.

In accordance with strict stage-by-stage engineering boundaries:
- Application functionality, models, and databases are deliberately deferred to subsequent stages.
- Core architectural standards, trust models, security boundaries, and evaluation protocols have been ratified.

The foundational project constitution is documented in:
📄 **[`docs/project-constitution.md`](docs/project-constitution.md)**

---

## Core Trust Model & Terminology

ADDMAI distinguishes strictly between machine learning inference and final platform assessments:

- **Model Prediction:** `REAL` or `DEEPFAKE` (raw statistical inference)
- **Final System Assessment:** `LIKELY_AUTHENTIC`, `LIKELY_MANIPULATED`, or `INCONCLUSIVE`

> Absolute claims (e.g. *"100% Authentic"*, *"Guaranteed Fake"*) are strictly prohibited unless presenting externally verified cryptographic proofs. The absence of provenance metadata never implies manipulation.

---

## Technology Roadmap

- **Frontend:** React, TypeScript, Tailwind CSS
- **Backend:** Python (FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic)
- **Storage & State:** PostgreSQL, Redis, MinIO / S3-compatible storage
- **AI / Computer Vision:** PyTorch, OpenCV, NumPy, scikit-learn
- **Infrastructure & Monitoring:** Docker, Docker Compose, Prometheus, Grafana

---

## Engineering Rules

All project contributors and automation agents must adhere to the 32 principles specified in the [Project Constitution](docs/project-constitution.md), including:
- **Modular Isolation:** Zero business or ML logic in HTTP presentation layers.
- **Strict Data Partitioning:** Video-level and identity-level separation to eliminate data leakage.
- **Security by Design:** All media uploads are treated as hostile, untrusted inputs.
- **Transparent Fusion:** Deterministic evidence synthesis handling signal conflict gracefully.
