"""Pydantic schemas for AI detection prediction API responses (Section 12 & 17)."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PredictionEnum(str, Enum):
    """Permitted model prediction values (Section 12 of Stage 3)."""
    REAL = "REAL"
    DEEPFAKE = "DEEPFAKE"


class ModelInfo(BaseModel):
    """Metadata regarding the executing detection model."""
    model_config = ConfigDict(from_attributes=True)

    model_id: str = Field(description="Unique identifier of the AI model")
    version: str = Field(description="Semantic version string of the model")


class ModelPredictionResponse(BaseModel):
    """Strongly typed response contract for POST /api/v1/media/{media_id}/detect."""
    model_config = ConfigDict(from_attributes=True)

    media_id: str = Field(description="Unique UUID identifier of the analyzed media asset")
    model: ModelInfo = Field(description="Executing model identification")
    prediction: PredictionEnum = Field(description="Model-level prediction: 'REAL' or 'DEEPFAKE'")
    confidence: float = Field(ge=0.0, le=1.0, description="Model prediction score/confidence in range [0.0, 1.0]")
    preprocessing_version: str = Field(description="Semantic version of deterministic preprocessing applied")
    inference_timestamp: str = Field(description="ISO 8601 timestamp of inference execution")
    prediction_id: Optional[str] = Field(default=None, description="Unique UUID of persisted prediction record")
    model_artifact_sha256: Optional[str] = Field(default=None, description="SHA-256 digest of verified model artifact")
