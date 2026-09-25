"""Internal schemas and enums for ML prediction outputs."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class PredictionEnum(str, Enum):
    """Permitted model prediction values (Section 12 of Stage 3)."""
    REAL = "REAL"
    DEEPFAKE = "DEEPFAKE"


class ModelOutput(BaseModel):
    """Validated raw model inference result."""

    prediction: PredictionEnum = Field(description="Discrete model classification ('REAL' or 'DEEPFAKE')")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence metric in [0.0, 1.0]")
    raw_score: float = Field(description="Uncalibrated sigmoid probability output")
    model_id: str = Field(description="Unique identifier of the executing model")
    model_version: str = Field(description="Version string of the model")
    preprocessing_version: str = Field(description="Version of preprocessing applied")
    artifact_sha256: str = Field(description="SHA-256 digest of the model artifact used")
    inference_timestamp: datetime = Field(description="UTC timestamp of inference execution")
