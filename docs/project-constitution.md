# ADDMAI Project Constitution & Engineering Rules

## 1. Project Identity & Overview

- **Project Name:** ADDMAI
- **Full Name:** AI-Powered Deepfake Detection & Media Authenticity Intelligence
- **Current Stage:** Stage 0 — Project Constitution & Engineering Rules

ADDMAI is a production-oriented, AI-assisted media authenticity analysis platform designed to evaluate facial images and short facial videos using multiple independent evidence sources rather than relying on a single deepfake classifier.

---

## 2. Project Vision

Deepfake creation techniques evolve rapidly, making monolithic single-model classifiers brittle, prone to adversarial failure, and vulnerable to distribution shifts. ADDMAI's vision is to build an evidence-based authenticity intelligence platform that treats media authentication as a multi-signal forensic problem.

The system synthesizes:
1. Deepfake AI detection (facial manipulation features)
2. Image forensic analysis
3. Video and frame-level analysis
4. Temporal consistency analysis
5. Media forensic signals (compression, boundary anomalies, frequency artifacts)
6. Container and file metadata analysis
7. Cryptographic integrity tracking
8. C2PA / Content Credentials provenance inspection (when available)
9. Transparent evidence fusion
10. Explainable risk assessment
11. Historical analysis auditing
12. Operational observability and health monitoring

The final system delivers an **evidence-based assessment** with clear uncertainty bounds rather than claiming absolute certainty.

---

## 3. Core Problem & Multi-Signal Philosophy

### The Flaw of Traditional Systems
Traditional deepfake detection systems simplify the problem into a brittle binary pipeline:
```
Media ──► Single AI Model ──► REAL / FAKE
```
This fails in real-world scenarios due to compression artifacts, lighting differences, unseen generator architectures, and ambiguous inputs.

### The ADDMAI Multi-Signal Architecture
ADDMAI approaches authenticity through independent signal streams:
```
                     Media
                       │
       ┌───────────────┼───────────────┬────────────────┬───────────────┐
       ▼               ▼               ▼                ▼               ▼
  AI Detection     Temporal        Forensic         Metadata      Cryptographic
  (Frame/Face)     Analysis         Signals        Inspection       Integrity
       │               │               │                │           (SHA-256)
       └───────────────┼───────────────┴────────────────┼───────────────┘
                       │                                │
                       │                     Provenance (C2PA)
                       │                                │
                       └───────────────┬────────────────┘
                                       ▼
                                Evidence Fusion
                                       │
                                       ▼
                                Risk Assessment
                                       │
                                       ▼
                               Explainable Result
```

### Handling Conflicting Evidence
Real-world evidence frequently conflicts. For example:
- An AI classifier predicts a high probability of manipulation,
- BUT verifiable C2PA hardware provenance is present and valid,
- AND forensic compression signals show no boundary splicing.

In such cases, ADDMAI must **never** force a binary `FAKE` classification. Instead, it must synthesize the conflict and output:
```
INCONCLUSIVE
```
accompanied by granular explanations detailing which signals conflicted and why.

---

## 4. System Objectives

The long-term engineering objectives of ADDMAI are to:
- Ingest supported media formats (images and short videos).
- Validate uploaded media against strict security, MIME, size, and duration constraints.
- Securely persist raw media and intermediate inspection artifacts into S3-compatible object storage.
- Calculate and verify cryptographic integrity hashes (SHA-256).
- Detect, isolate, crop, and normalize human faces across frames.
- Run deepfake feature extraction and inference using validated computer-vision backbones.
- Analyze video sequences for temporal anomalies (blinking inconsistencies, facial jitter, landmark drift).
- Extract independent media forensic signals (frequency domain artifacts, noise patterns, double-compression traces).
- Inspect and parse C2PA / Content Authenticity Initiative (CAI) manifests when embedded.
- Fuse multi-source evidence using deterministic, transparent rules.
- Produce an explainable, audit-ready authenticity assessment.
- Expose typed, versioned REST API endpoints (`/api/v1`).
- Provide an interactive, responsive React dashboard for analyst exploration.
- Maintain immutable analysis logs and audit histories in PostgreSQL.
- Maintain production observability across queues, model inference latencies, and service health.

---

## 5. Result Terminology & Trust Model

### Distinction Between Model Prediction and System Assessment
To avoid misleading users and stakeholders, ADDMAI enforces a strict semantic boundary between raw machine learning output and the comprehensive system verdict:

| Concept | Possible Values | Meaning |
| :--- | :--- | :--- |
| **Model Prediction** | `REAL`, `DEEPFAKE` | Raw probabilistic output from the AI classifier. Represents statistical feature correlation only. |
| **Final System Assessment** | `LIKELY_AUTHENTIC`, `LIKELY_MANIPULATED`, `INCONCLUSIVE` | Comprehensive verdict synthesized from AI detection, temporal analysis, forensics, metadata, integrity, and provenance. |

### Prohibited Terminology
The system, documentation, and user interfaces must **never** use absolute language such as:
- ❌ *"Guaranteed Fake"*
- ❌ *"100% Authentic"*
- ❌ *"Proven Fake"*
- ❌ *"Infallible Detection"*

Such claims are scientifically invalid for statistical inference. Definite claims are only permissible when presenting an externally verified cryptographic proof (e.g., *"SHA-256 hash matches the provided digest exactly"*).

### Trust Model & Evidence Classification
Each signal category represents a distinct evidence class with specific limitations:

| Signal Category | Evidence Nature | Interpretation Rule |
| :--- | :--- | :--- |
| **AI Detection** | Statistical machine learning evidence | Susceptible to adversarial perturbation, distribution shift, and compression noise. |
| **Temporal Analysis** | Inter-frame consistency evidence | Evaluates physiological and physical continuity across video frames. |
| **Forensic Signals** | Signal processing / media evidence | Uncovers physical/compression anomalies (PRNU, error level analysis, frequency spectrum). |
| **Metadata** | Descriptive container information | Useful context, but easily stripped or spoofed; low evidentiary weight on its own. |
| **Cryptographic Hash** | Byte-level integrity data | Proves the file was not altered in transit/storage; proves nothing about original authenticity. |
| **C2PA / Provenance** | Cryptographic assertion chain | Strong authenticity indicator when valid; absence does **not** indicate manipulation. |

> [!IMPORTANT]
> **Absence of Evidence is Not Evidence of Absence:**
> The absence of a C2PA manifest or metadata does NOT imply that a media file is manipulated. It simply signifies:
> `NO_VERIFIABLE_PROVENANCE_AVAILABLE`.

---

## 6. Core Engineering Principles

1. **Modularity**:
   Distinct boundaries exist between API, business services, database repositories, object storage, media pre-processing, ML inference, forensic extractors, provenance parsing, evidence fusion, worker queues, and frontend dashboards.
2. **Separation of Concerns**:
   HTTP route handlers must never contain machine learning code, database queries, raw OpenCV pipelines, or fusion formulas. Route handlers delegate strictly to orchestrator services.
3. **Testability**:
   Every service, calculator, and extractor must be testable in complete isolation through dependency injection and decoupled interfaces.
4. **Configuration Management**:
   All dynamic configuration must be loaded from validated environment variables via typed settings (e.g., Pydantic `BaseSettings`). Secrets, credentials, and internal endpoints are never hardcoded.
5. **Reproducibility**:
   Every ML experiment, evaluation benchmark, and processing job must record random seeds, dataset versions, preprocessing parameters, model architecture identifiers, and metric definitions.
6. **Observability**:
   Core workflows emit structured JSON logs, trace contexts, performance metrics, and error classifications. Secrets and raw media bytes must never leak into log streams.
7. **Security by Design**:
   All user-provided media files are treated as untrusted, hostile input. Strict MIME inspection, size caps, duration limits, path sanitization, and isolated processing environments are mandatory.
8. **Simple Before Complex**:
   Do not introduce architectural complexity (e.g., Kafka, Kubernetes, microservice splits) prematurely. Build the cleanest, most maintainable modular monolithic architecture that satisfies the operational requirements.

---

## 7. Technology Direction

The long-term technological foundation consists of the following components:

- **Frontend:** React, TypeScript, Tailwind CSS
- **Backend:** Python (3.11+), FastAPI, Pydantic v2, SQLAlchemy 2.0 (asyncio), Alembic
- **Database:** PostgreSQL
- **Cache & Asynchronous Job Broker:** Redis
- **Object Storage:** MinIO (local development), AWS S3-compatible storage (production)
- **AI / Computer Vision:** PyTorch, OpenCV, NumPy, Pandas, scikit-learn
- **Infrastructure:** Docker, Docker Compose
- **Observability:** Prometheus, Grafana, structured JSON logging
- **Testing:** pytest, pytest-asyncio, HTTP test clients

*Note: Technologies are adopted incrementally as each stage demands; dependencies are never pre-installed without active usage.*

---

## 8. Logical System Architecture

```
                               ┌─────────────────────────┐
                               │  React Admin Dashboard  │
                               └────────────┬────────────┘
                                            │ HTTP / JSON
                                            ▼
                               ┌─────────────────────────┐
                               │   FastAPI Gateway API   │
                               │        (/api/v1)        │
                               └────────────┬────────────┘
                                            │
                 ┌──────────────────────────┼──────────────────────────┐
                 ▼                          ▼                          ▼
      ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
      │    Media Service    │    │  Analysis Service   │    │ Provenance Service  │
      └──────────┬──────────┘    └──────────┬──────────┘    └──────────┬──────────┘
                 │                          │                          │
                 └──────────────────────────┼──────────────────────────┘
                                            │ Enqueue Job
                                            ▼
                               ┌─────────────────────────┐
                               │   Redis Task Broker &   │
                               │   Background Workers    │
                               └────────────┬────────────┘
                                            │
                 ┌──────────────────────────┼──────────────────────────┐
                 ▼                          ▼                          ▼
      ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
      │   AI Face Detector  │    │   Forensic Engine   │    │  Temporal Analyzer  │
      │  (PyTorch Inference)│    │ (Artifact Analysis) │    │  (Frame Continuity) │
      └──────────┬──────────┘    └──────────┬──────────┘    └──────────┬──────────┘
                 │                          │                          │
                 └──────────────────────────┼──────────────────────────┘
                                            │ Feature Vectors & Scores
                                            ▼
                               ┌─────────────────────────┐
                               │ Evidence Fusion Engine  │
                               └────────────┬────────────┘
                                            │
                                            ▼
                               ┌─────────────────────────┐
                               │ Risk Assessment Engine  │
                               └────────────┬────────────┘
                                            │
                        ┌───────────────────┴───────────────────┐
                        ▼                                       ▼
            ┌───────────────────────┐               ┌───────────────────────┐
            │   PostgreSQL DB       │               │   MinIO / S3 Storage  │
            │ (Metadata, Audit,     │               │ (Media, Face Crops,   │
            │  Job State, Results)  │               │  Grad-CAM Artifacts)  │
            └───────────────────────┘               └───────────────────────┘
```

---

## 9. Media & Operational Scope

### In-Scope Media Formats
- **Static Images:** `JPEG`, `JPG`, `PNG`
- **Video Streams:** `MP4` (H.264 encoded)

### System Domain Boundaries
- **Target Analysis:** High-resolution and standard-resolution human facial images and short facial video clips (typically 5 to 60 seconds).
- **Explicit Non-Goals (Out of Scope):**
  - Universal detection of arbitrary generative media (e.g., synthetic landscape art, audio-only deepfakes, text synthesis).
  - Real-time live surveillance / continuous RTSP CCTV stream monitoring.
  - Unlimited-length feature film or broadcast analysis.
  - Legally binding authenticity guarantees or forensic legal certifications.
  - Browser extensions or mobile application native clients.
  - Training massive multimodal foundation models from scratch.

---

## 10. Machine Learning Strategy

1. **Problem Formulation:**
   Binary classification of detected and normalized facial crops:
   $$\text{Output} \in \{ \text{REAL}, \text{DEEPFAKE} \}$$
   alongside a calibrated probability score $P(\text{deepfake}) \in [0.0, 1.0]$.
2. **Model Paradigm:**
   Transfer learning using established, robust computer vision architectures fine-tuned on standardized deepfake benchmark datasets.
3. **Candidate Backbones:**
   - EfficientNet (e.g., B4 / B7)
   - ResNet / ConvNeXt
   - Xception / Dual-branch architectures
4. **Empirical Model Selection:**
   No backbone will be assumed superior a priori. Selection will be dictated strictly by empirical benchmarks measuring ROC-AUC, F1-score, inference latency, parameter footprint, and robustness across diverse demographics and compressions.

---

## 11. Video Analysis Pipeline

Video authentication must never rely on a single arbitrarily selected frame. The standard video processing sequence is:

```
Video File
    │
    ▼
1. Uniform & Scene-Aware Frame Sampling
    │
    ▼
2. Facial Landmark & Face Boundary Detection
    │
    ▼
3. Alignment, Cropping, & Spatial Normalization
    │
    ▼
4. Frame-Level Inference (Per-frame manipulation scores)
    │
    ▼
5. Temporal Sequence Analysis (Inter-frame jitter, blink patterns, optical flow)
    │
    ▼
6. Aggregation & Anomaly Timeline Construction
```

Intermediate inspection data (e.g., timestamps of suspicious frames, distribution of per-frame scores, face bounding boxes) must be preserved in the analysis record to substantiate the final verdict.

---

## 12. Forensic Engine Principles

The Forensic Engine functions as an independent signal extractor. It does **not** output `REAL` or `FAKE`.

### Signal Categories
- **Compression & Double-Quantization:** Detecting discrepancies between image container compression markers and pixel-level blocking artifacts.
- **Error Level Analysis (ELA):** Identifying regions saved at different compression levels across the image canvas.
- **Frequency Domain Analysis:** Discrete Fourier Transform (DFT) / DCT spectrum inspection to detect periodic generative lattice patterns.
- **Facial Boundary Blending Inconsistencies:** Gradient discontinuities along face swap contours.
- **Metadata Anomaly Checks:** Discrepancies between EXIF camera profiles, lens specifications, and container creation dates.

Each signal must be implemented as an isolated, deterministic Python module with dedicated unit tests.

---

## 13. Provenance & C2PA Specification

- ADDMAI embraces open content provenance standards (C2PA / Content Authenticity Initiative).
- When a media file contains signed C2PA manifests:
  - Validate the certificate chain.
  - Inspect manifest claim history (editing applications, parent asset references).
  - Match signed asset hash with the calculated media hash.
- **Absence Rule:** If no C2PA manifest is detected, record `NO_VERIFIABLE_PROVENANCE_AVAILABLE`. The absence of provenance must never decrease the authenticity score of authentic unauthenticated legacy media.

---

## 14. Cryptographic Asset Integrity

- Upon ingest, every asset is hashed using **SHA-256**.
- The digest is stored alongside file size, MIME type, and upload timestamps.
- **Distinction:** A SHA-256 hash guarantees that the stored bits have not been tampered with or corrupted since upload. It does **not** prove that the content depicted in the media represents an untampered capture of physical reality.

---

## 15. Evidence Fusion Engine

The Evidence Fusion Engine resolves heterogeneous, multi-modal signal outputs into a unified risk rating.

### Fusion Requirements
- **Deterministic & Traceable:** Rules and weighting models must be mathematically transparent and explainable. No black-box secondary neural networks for fusion.
- **Handling Conflicting Evidence:**
  - High AI fake probability + Validated C2PA Hardware Provenance $\rightarrow$ Triggers `INCONCLUSIVE` flag with review advisory.
  - Borderline AI score + Strong forensic boundary artifact $\rightarrow$ Elevates risk profile to `LIKELY_MANIPULATED`.
- **Verdict Mapping:**
  - High cumulative authenticity confidence $\rightarrow$ `LIKELY_AUTHENTIC`
  - High cumulative manipulation confidence $\rightarrow$ `LIKELY_MANIPULATED`
  - Ambiguous, low-confidence, or contradictory evidence $\rightarrow$ `INCONCLUSIVE`

---

## 16. Explainability Requirements

Every user-facing analysis report must supply contextual evidence:
- **Calibrated Confidence:** Clear percentage intervals avoiding overconfidence.
- **Suspicious Frame Timeline:** Interactive timeline highlighting the specific seconds and frames containing anomalies.
- **Visual Attention / Saliency Maps:** Grad-CAM or attention rollouts indicating which facial regions (eyes, mouth, boundary) triggered the model.
- **Signal Breakdown:** Independent scoring cards displaying the status of forensic, metadata, and temporal checks.

---

## 17. Data Storage Architecture

### PostgreSQL (Relational Metadata & Audit Store)
- Stores media metadata, user references, analysis job state, raw signal vectors, final assessment records, and model benchmark metadata.
- Large binary blobs (images, video streams, serialized model weights) are strictly forbidden in relational columns.

### Object Storage (MinIO / S3)
- Stores immutable original media uploads, extracted frame sequences, face crops, heatmap overlays, and generated PDF/JSON summary reports.
- Organized under structured key prefixes:
  ```
  uploads/{media_id}/original.{ext}
  artifacts/{job_id}/crops/{frame_idx}_{face_idx}.png
  artifacts/{job_id}/visualizations/gradcam_{frame_idx}.png
  ```

---

## 18. Asynchronous Processing Workflow

All media processing is asynchronous and decoupled from the HTTP request-response cycle:

```
[Client]
   │ POST /api/v1/media/analyze
   ▼
[API Gateway] ──► Validate Request & Upload to S3 ──► Persist Job (State: QUEUED)
   │                                                         │
   ◄── Return 202 Accepted (job_id)                          │
                                                             ▼
                                                    [Redis Task Queue]
                                                             │
                                                             ▼
                                                    [Worker Process]
                                                    (State: PROCESSING)
                                                             │
                                   ┌─────────────────────────┼─────────────────────────┐
                                   ▼                         ▼                         ▼
                              AI Inference           Forensic Analysis         Temporal Analysis
                                   │                         │                         │
                                   └─────────────────────────┼─────────────────────────┘
                                                             ▼
                                                   Evidence Fusion Engine
                                                             ▼
                                                   Persist Results in DB
                                                    (State: COMPLETED)
```

- Failed analyses transition to `FAILED` with sanitized error messages.
- Jobs failing due to transient infrastructure issues may be retried up to 3 times with exponential backoff.
- Jobs failing due to corrupt media or invalid headers must fail immediately without retry loops.

---

## 19. API Design Standards

- **Base Path:** `/api/v1`
- **Request & Response Contracts:** Enforced using strict Pydantic v2 schemas.
- **Error Responses:** Uniform RFC-7807 compliant JSON schemas:
  ```json
  {
    "type": "https://addmai.org/errors/invalid-media-type",
    "title": "Invalid Media Format",
    "status": 415,
    "detail": "Provided file type 'video/quicktime' is not supported. Supported: image/jpeg, image/png, video/mp4.",
    "instance": "/api/v1/media/analyze",
    "request_id": "req_01HPX7K..."
  }
  ```
- **Security:** Request IDs on all responses; stack traces and internal server paths are never exposed.

---

## 20. Security Principles

1. **Untrusted Input:** Every upload is untrusted. File headers, magic bytes, dimensions, and compression flags are validated before passing to decoding engines.
2. **Resource Boundaries:**
   - Maximum image upload size: 15 MB.
   - Maximum video upload size: 100 MB.
   - Maximum video duration: 60 seconds.
3. **Path Traversal Protection:** Random UUIDv4 / ULID keys for all storage operations. User-supplied filenames are sanitized and stored only as metadata.
4. **Temporary File Discipline:** Any temporary files created on disk during frame extraction must be wrapped in deterministic context managers that guarantee cleanup even upon unhandled exceptions.
5. **Secret Isolation:** API keys, database credentials, and storage secrets must be injected via environment variables.

---

## 21. Observability Principles

- **Structured Logging:** All logs emitted in standard JSON format containing `timestamp`, `level`, `service`, `job_id`, `request_id`, and `message`.
- **Metrics Tracking:**
  - API HTTP request rate, status code distribution, and latency percentiles (p50, p95, p99).
  - Queue depth and worker processing latency.
  - Model inference latency per face crop.
  - Video processing duration per second of media.
- **Privacy Rule:** PII, credentials, authentication tokens, and raw facial crops are strictly excluded from logs.

---

## 22. Testing Strategy

ADDMAI enforces a three-tiered testing hierarchy:

```
               ▲
              / \
             /   \     End-to-End Tests (Full pipeline: API -> Worker -> Result)
            / E2E \
           /───────\
          /         \   Integration Tests (DB, MinIO, Redis, Service integration)
         /   INTEG   \
        /─────────────\
       /               \ Unit Tests (Validators, Math, Forensic signals, Fusion logic)
      /      UNIT       \
     /───────────────────\
```

- **Target Coverage:** $\ge 85\%$ line coverage on core business logic, evidence fusion algorithms, and forensic extractors.

---

## 23. Machine Learning Evaluation Principles

- **Metric Standard:** Accuracy alone is forbidden as a success metric. All models must report:
  - Precision
  - Recall
  - F1-Score
  - ROC-AUC
  - Confusion Matrix (True Positives, False Positives, True Negatives, False Negatives)
- **Video-Level Evaluation:**
  - Video-level aggregation metrics
  - Fake frame ratio sensitivity curves
  - Average inference latency per frame
- **Robustness Benchmarks:** Models must be stress-tested against:
  - JPEG compression (quality factors 50, 70, 90)
  - Video re-encoding (H.264 CRF 23, 28, 32)
  - Spatial downscaling and resizing
  - Gaussian blur and noise perturbation
- **Integrity Rule:** Metrics must be computed strictly via reproducible evaluation scripts. Never fabricate or extrapolate results.

---

## 24. Mandatory Data Leakage Rule

> [!CAUTION]
> **Strict Source-Level Dataset Separation:**
> Frames originating from the same source video or the same subject identity must **never** appear in both training and test partitions.
> Cross-validation and train/validation/test splits must be strictly partitioned at the source video / identity level. All dataset partitioning manifests must be cryptographically hashed and checked into version control.

---

## 25. Engineering Lifecycle & Rules

### Stage-by-Stage Development Protocol
For every stage:
1. Inspect the current repository.
2. Read relevant existing code and architecture.
3. Identify reusable components and shared abstractions.
4. Implement only the requested stage deliverables.
5. Add comprehensive unit and integration tests.
6. Run the test suite and verify green status.
7. Remediate any introduced regressions.
8. Verify end-to-end integration.
9. Update architectural documentation.
10. Report changes with full transparency.
11. **STOP and wait for user review before proceeding.**

### Code Modification & Reuse Rule
- Never blindly overwrite working modules.
- Check callers, imports, and tests before modifying existing abstractions.
- Never create duplicate repositories, database access layers, or utility functions.

### Dependency Management Rule
- Every new third-party dependency must be strictly justified.
- Verify whether existing standard library or already-installed packages fulfill the need before adding new dependencies.

### Documentation Integrity
- Planned documentation files:
  - `docs/architecture.md`
  - `docs/api.md`
  - `docs/ml.md`
  - `docs/evaluation.md`
  - `docs/security.md`
  - `docs/deployment.md`
  - `docs/limitations.md`
- Documentation must always reflect the actual, running state of the code. Never document an unwritten feature as completed.

---

## 26. Project Definition of Done

A stage or the final project is defined as complete only when:
- [x] Code strictly adheres to the engineering constitution.
- [x] Pipeline operates end-to-end without unhandled exceptions.
- [x] Machine learning evaluation is verified and reproducible.
- [x] Object storage and database boundaries are respected.
- [x] Asynchronous worker flows and queues function with proper retry/failure policies.
- [x] Forensic signals, provenance checks, and fusion engines provide explainable outputs.
- [x] Comprehensive automated tests pass.
- [x] Logs and telemetry follow structured observability requirements.
- [x] Documentation accurately reflects the current implementation.

---
*End of Stage 0 Constitution — Established and Ratified.*
