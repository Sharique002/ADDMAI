"""AI Detection Orchestration Service (Stage 3).

Coordinates media retrieval, cryptographic verification, deterministic preprocessing,
model inference, prediction persistence, and byte immutability verification.
"""

from datetime import datetime, timezone
import hashlib
import logging
from typing import Optional, Union
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import MediaRecord
from app.models.prediction import ModelPredictionRecord
from app.repositories.media import media_repository
from app.repositories.prediction import prediction_repository
from app.schemas.prediction import ModelInfo, ModelPredictionResponse, PredictionEnum
from app.services.storage import storage_service
from ml.inference.engine import inference_engine
from ml.inference.model_loader import ModelSecurityError
from ml.preprocessing.preprocessor import PreprocessingError

logger = logging.getLogger("addmai.services.detection")


class DetectionError(Exception):
    """Base exception for detection service operations."""
    pass


class MediaNotFoundError(DetectionError):
    """Raised when the requested media record does not exist."""
    pass


class UnsupportedMediaCategoryError(DetectionError):
    """Raised when media format is not supported by the model (e.g. video in Stage 3)."""
    pass


class StorageObjectNotFoundError(DetectionError):
    """Raised when canonical bytes cannot be retrieved from storage."""
    pass


class IntegrityVerificationError(DetectionError):
    """Raised when stored byte digest fails verification against recorded digest."""
    pass


class DetectionService:
    """Service orchestrating AI deepfake detection on canonical media assets."""

    def __init__(self, engine=inference_engine, storage=storage_service) -> None:
        self.engine = engine
        self.storage = storage

    async def detect(
        self,
        media_id: Union[uuid.UUID, str],
        session: AsyncSession,
    ) -> ModelPredictionResponse:
        """Execute AI deepfake detection on a canonical media asset.

        Args:
            media_id: UUID of the ingested media asset.
            session: Active database session for persistence.

        Returns:
            ModelPredictionResponse with model-level classification ('REAL' or 'DEEPFAKE').

        Raises:
            MediaNotFoundError: If media record does not exist.
            UnsupportedMediaCategoryError: If media category is not 'image'.
            StorageObjectNotFoundError: If original bytes are missing from storage.
            IntegrityVerificationError: If byte digest fails verification.
            PreprocessingError: If media fails decoding / preprocessing.
            ModelSecurityError: If model artifact fails security checks.
        """
        # 1. Retrieve Media Record from Database
        record = await media_repository.get_by_id(session, media_id)
        if not record:
            raise MediaNotFoundError(f"Media asset with ID '{media_id}' was not found.")

        # 2. Check Category Compatibility (Stage 3 supports images only)
        if record.media_category != "image":
            raise UnsupportedMediaCategoryError(
                f"Media category '{record.media_category}' is not supported by model "
                f"'{self.engine.config.model_id}' in Stage 3. Stage 3 supports static images (JPEG, PNG). "
                f"Video frame analysis is scheduled for future stages."
            )

        # 3. Retrieve Canonical Original Bytes from Storage
        content = await self.storage.get_object(record.storage_key)
        if content is None:
            raise StorageObjectNotFoundError(
                f"Canonical media asset for storage key '{record.storage_key}' could not be retrieved."
            )

        # 4. Verify Cryptographic Integrity BEFORE Inference
        sha256_before = hashlib.sha256(content).hexdigest().lower()
        if sha256_before != record.sha256_digest.lower():
            raise IntegrityVerificationError(
                f"Integrity violation: Stored object SHA-256 ({sha256_before}) does not match "
                f"canonical database digest ({record.sha256_digest})."
            )

        # 5. Execute Model Inference
        model_output = self.engine.predict(content)

        # 6. Verify Cryptographic Integrity AFTER Inference (Immutability Invariant)
        sha256_after = hashlib.sha256(content).hexdigest().lower()
        if sha256_before != sha256_after:
            raise IntegrityVerificationError(
                "CRITICAL: Media content was mutated during inference pipeline. "
                "Aborting prediction persistence."
            )

        # 7. Persist Prediction Record in Database
        prediction_id = uuid.uuid4()
        pred_record = ModelPredictionRecord(
            id=prediction_id,
            media_id=record.id,
            model_id=model_output.model_id,
            model_version=model_output.model_version,
            prediction=model_output.prediction.value,
            confidence=model_output.confidence,
            preprocessing_version=model_output.preprocessing_version,
            model_artifact_sha256=model_output.artifact_sha256,
            created_at=model_output.inference_timestamp,
        )

        try:
            await prediction_repository.create(session, pred_record)
            await session.commit()
        except Exception as exc:
            logger.error(f"Failed to persist prediction record {prediction_id}: {exc}")
            await session.rollback()
            raise RuntimeError(f"Database persistence failed for prediction: {exc}") from exc

        # 8. Construct Response
        return ModelPredictionResponse(
            media_id=str(record.id),
            model=ModelInfo(
                model_id=model_output.model_id,
                version=model_output.model_version,
            ),
            prediction=PredictionEnum(model_output.prediction.value),
            confidence=model_output.confidence,
            preprocessing_version=model_output.preprocessing_version,
            inference_timestamp=model_output.inference_timestamp.isoformat(),
            prediction_id=str(prediction_id),
            model_artifact_sha256=model_output.artifact_sha256,
        )


detection_service = DetectionService()
