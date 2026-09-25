-- ==============================================================================
-- ADDMAI Relational Schema (Stage 2.1 Hardened)
-- Table: media_records
-- ==============================================================================
-- SCHEMA OWNERSHIP:
-- Alembic migrations (database/migrations/) are the AUTHORITATIVE source of truth
-- for database evolution. This file is retained strictly for Docker bootstrap
-- container initialization (postgres entrypoint).
-- ==============================================================================

CREATE TABLE IF NOT EXISTS media_records (
    id UUID PRIMARY KEY,
    sha256_digest VARCHAR(64) NOT NULL,
    media_category VARCHAR(16) NOT NULL,
    mime_type VARCHAR(64) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    size_bytes BIGINT NOT NULL,
    storage_key VARCHAR(255) NOT NULL,
    validation_status VARCHAR(32) NOT NULL DEFAULT 'accepted',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_media_records_sha256 UNIQUE (sha256_digest),
    CONSTRAINT ck_media_records_size_bytes_non_negative CHECK (size_bytes >= 0),
    CONSTRAINT ck_media_records_media_category CHECK (media_category IN ('image', 'video'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_media_records_sha256 ON media_records (sha256_digest);

-- Table: model_predictions (Stage 3 AI Detection)
CREATE TABLE IF NOT EXISTS model_predictions (
    id UUID PRIMARY KEY,
    media_id UUID NOT NULL REFERENCES media_records(id) ON DELETE CASCADE,
    model_id VARCHAR(64) NOT NULL,
    model_version VARCHAR(32) NOT NULL,
    prediction VARCHAR(16) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    preprocessing_version VARCHAR(32) NOT NULL,
    model_artifact_sha256 VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_model_predictions_prediction CHECK (prediction IN ('REAL', 'DEEPFAKE')),
    CONSTRAINT ck_model_predictions_confidence_range CHECK (confidence >= 0.0 AND confidence <= 1.0)
);

CREATE INDEX IF NOT EXISTS ix_model_predictions_media_id ON model_predictions (media_id);


