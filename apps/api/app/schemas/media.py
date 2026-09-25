"""Schemas for Media Ingestion, Integrity, Evidence, and Analysis Records (Sections 10, 21, 22)."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class MediaResponse(BaseModel):
    """Structured media ingestion record representation (Section 10 & 14)."""
    media_id: str = Field(..., description="Unique system media UUID identifier")
    sha256_digest: str = Field(..., description="Immutable 64-character hex SHA-256 byte digest")
    media_category: str = Field(..., description="Media category: 'image' or 'video'")
    mime_type: str = Field(..., description="Standard MIME format string")
    original_filename: str = Field(..., description="Sanitized original upload filename")
    size_bytes: int = Field(..., description="File size in bytes")
    validation_status: str = Field(default="accepted", description="Validation status: 'accepted'")
    created_at: str = Field(..., description="ISO 8601 UTC creation timestamp")


class IntegrityRecord(BaseModel):
    """Cryptographic byte integrity verification data (Section 8)."""
    sha256_digest: str = Field(..., description="Exact SHA-256 calculated from raw bytes")
    algorithm: str = Field(default="SHA-256", description="Digest cryptographic algorithm")
    size_bytes: int = Field(..., description="Original asset size in bytes")
    verified: bool = Field(default=True, description="Byte sequence integrity verified")
    note: str = Field(
        default="SHA-256 identifies the exact byte sequence but does not establish authenticity.",
        description="Constitutional disclaimer",
    )


class EvidenceItem(BaseModel):
    """Neutral forensic evidence observation (Section 21).

    Used as an extensible contract across Stage 2 and future stages.
    Does not assign authenticity verdicts or manipulation probabilities.
    """
    evidence_type: str = Field(..., description="Category: CRYPTOGRAPHIC_HASH, MEDIA_TYPE, CONTAINER_INFO, METADATA_OBSERVATION")
    source: str = Field(..., description="Subsystem that generated observation")
    value: Any = Field(..., description="Observation payload")
    observed_at: str = Field(..., description="ISO 8601 UTC timestamp of observation")


class AnalysisRecord(BaseModel):
    """Comprehensive analysis and evidence record for ingested media (Section 22)."""
    media_id: str = Field(..., description="Target media asset identifier")
    ingestion: MediaResponse = Field(..., description="Ingestion metadata")
    integrity: IntegrityRecord = Field(..., description="Cryptographic integrity verification")
    container: Dict[str, Any] = Field(..., description="Container and dimensional properties")
    metadata: Dict[str, Any] = Field(..., description="Neutral metadata observations")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Extensible evidence list")


class MediaErrorResponse(BaseModel):
    """RFC-7807 compliant error response schema."""
    type: str = Field(..., description="URI identifying error type")
    title: str = Field(..., description="Short summary of error")
    status: int = Field(..., description="HTTP status code")
    detail: str = Field(..., description="Human-readable explanation of error")
    instance: str = Field(..., description="URI of request endpoint")


class MediaIngestionResponse(BaseModel):
    """Unified API response for media ingestion and retrieval (Sections 14, 15, 22)."""
    media_id: str = Field(..., description="Unique system media UUID identifier")
    sha256_digest: str = Field(..., description="Immutable 64-character hex SHA-256 byte digest")
    media_category: str = Field(..., description="Media category: 'image' or 'video'")
    mime_type: str = Field(..., description="Standard MIME format string")
    original_filename: str = Field(..., description="Sanitized original upload filename")
    size_bytes: int = Field(..., description="File size in bytes")
    validation_status: str = Field(default="accepted", description="Validation status: 'accepted'")
    created_at: str = Field(..., description="ISO 8601 UTC creation timestamp")
    is_duplicate: bool = Field(default=False, description="Indicates if asset was previously ingested")
    analysis: Optional[AnalysisRecord] = Field(default=None, description="Structured analysis and evidence record")

