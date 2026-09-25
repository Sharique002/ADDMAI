"""Model Prediction entity conforming to Section 15 of Stage 3 specification."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ModelPredictionRecord(Base):
    """Relational model representing an AI model detection prediction.

    Maintains 1:N relationship with MediaRecord (media_records.id).
    Strictly records model-level predictions ('REAL' or 'DEEPFAKE')
    with zero final authenticity verdict claims.
    """
    __tablename__ = "model_predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        doc="System-level unique prediction identifier (UUID)",
    )
    media_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("media_records.id", ondelete="CASCADE"),
        nullable=False,
        doc="Foreign key referencing canonical media asset in media_records",
    )
    model_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Unique identifier of the AI detection model",
    )
    model_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Semantic version string of the model",
    )
    prediction: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        doc="Model-level classification output: 'REAL' or 'DEEPFAKE'",
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Model output confidence / score in range [0.0, 1.0]",
    )
    preprocessing_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Semantic version of the preprocessing pipeline applied",
    )
    model_artifact_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Cryptographic SHA-256 digest of the model artifact used for inference",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="ISO timestamp when prediction record was generated",
    )

    __table_args__ = (
        Index("ix_model_predictions_media_id", "media_id"),
        CheckConstraint("prediction IN ('REAL', 'DEEPFAKE')", name="ck_model_predictions_prediction"),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="ck_model_predictions_confidence_range"),
    )
