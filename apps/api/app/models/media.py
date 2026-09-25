"""Media Record entity conforming to Sections 10, 11, 12 of Stage 2 specification."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import BigInteger, CheckConstraint, DateTime, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MediaRecord(Base):
    """Relational model representing an ingested media asset.

    Stores byte-level integrity tracking (SHA-256), MIME classification,
    storage location, and ingestion timestamps.
    """
    __tablename__ = "media_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="System-level unique media identifier (UUID)",
    )
    sha256_digest: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
        doc="Immutable 64-character lowercase hex SHA-256 digest of original bytes",
    )
    media_category: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        doc="Media category: 'image' or 'video'",
    )
    mime_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Standard MIME type (e.g., image/jpeg, video/mp4)",
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Sanitized original filename at upload time",
    )
    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        doc="Exact size of original uploaded asset in bytes",
    )
    storage_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Deterministic object storage path (e.g. media/original/{sha256})",
    )
    validation_status: Mapped[str] = mapped_column(
        String(32),
        default="accepted",
        nullable=False,
        doc="Ingestion validation state (e.g., 'accepted')",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="ISO timestamp when record was persisted",
    )

    __table_args__ = (
        Index("ix_media_records_sha256", "sha256_digest", unique=True),
        CheckConstraint("size_bytes >= 0", name="ck_media_records_size_bytes_non_negative"),
        CheckConstraint("media_category IN ('image', 'video')", name="ck_media_records_media_category"),
    )

