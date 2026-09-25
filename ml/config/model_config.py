"""Model configuration and artifact security parameters conforming to Sections 6, 7, 14 of Stage 3."""

from pathlib import Path
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Configuration governing model identity, dimensions, thresholds, and artifact integrity."""

    model_id: str = Field(
        default="addmai-deepfake-detector",
        description="Immutable identifier for the deepfake detector model",
    )
    model_version: str = Field(
        default="1.0.0",
        description="Semantic version string of the model architecture and weights",
    )
    preprocessing_version: str = Field(
        default="1.0.0",
        description="Semantic version of the deterministic preprocessing pipeline",
    )
    input_height: int = Field(default=224, description="Model input image tensor height")
    input_width: int = Field(default=224, description="Model input image tensor width")
    resize_dimension: int = Field(default=256, description="Intermediate bicubic resize dimension")
    max_image_pixels: int = Field(
        default=100_000_000,
        description="Hard ceiling for total image pixels to prevent decompression bombs",
    )
    decision_threshold: float = Field(
        default=0.5,
        description="Validation-tuned decision boundary for binary classification",
    )
    inference_timeout_seconds: float = Field(
        default=10.0,
        description="Maximum wall-clock execution time for a single inference call",
    )
    artifact_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "artifacts" / "addmai_detector_v1",
        description="Controlled filesystem directory containing model artifacts",
    )
    artifact_filename: str = Field(
        default="model.safetensors",
        description="Expected model weights filename",
    )
    expected_artifact_sha256: str = Field(
        default="07059e483e4643b7d6c0e0b26948e5bbb209e4c5334f06f58eb4d90b7923f7da",
        description="Expected 64-char lowercase hex SHA-256 digest of trusted model artifact",
    )

    @property
    def artifact_path(self) -> Path:
        """Resolved absolute path to the model weights file."""
        return self.artifact_dir / self.artifact_filename


model_config = ModelConfig()
