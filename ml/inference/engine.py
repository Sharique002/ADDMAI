"""Model inference engine coordinating preprocessing, forward pass, and prediction contracts."""

from datetime import datetime, timezone
import logging
from typing import Optional

import torch

from ml.config.model_config import model_config
from ml.inference.model_loader import model_loader
from ml.preprocessing.preprocessor import image_preprocessor
from ml.schemas.prediction import ModelOutput, PredictionEnum

logger = logging.getLogger("addmai.ml.engine")


class InferenceEngine:
    """Coordinates deterministic preprocessing and model inference for deepfake detection."""

    def __init__(
        self,
        config=model_config,
        preprocessor=image_preprocessor,
        loader=model_loader,
    ) -> None:
        self.config = config
        self.preprocessor = preprocessor
        self.loader = loader

    def predict(self, content: bytes) -> ModelOutput:
        """Execute end-to-end deepfake detection on raw in-memory media bytes.

        Args:
            content: Raw immutable bytes of an ingested media asset.

        Returns:
            Structured ModelOutput containing discrete prediction ('REAL' or 'DEEPFAKE')
            and associated model confidence metadata.
        """
        # 1. Deterministic Preprocessing
        tensor = self.preprocessor.preprocess(content)

        # 2. Safe Model Loading & Checksum Verification
        model, artifact_sha256 = self.loader.load_model()

        # 3. Model Inference (no gradient tracking, deterministic eval)
        with torch.no_grad():
            logit = model(tensor)
            raw_score = torch.sigmoid(logit).squeeze().item()

        # 4. Binary Decision Boundary Mapping
        # If score >= threshold -> DEEPFAKE; else -> REAL
        threshold = self.config.decision_threshold
        if raw_score >= threshold:
            prediction = PredictionEnum.DEEPFAKE
            # Confidence is model certainty in the assigned class
            confidence = raw_score
        else:
            prediction = PredictionEnum.REAL
            confidence = 1.0 - raw_score

        # Bound confidence strictly to [0.0, 1.0] and round for stability
        bounded_confidence = max(0.0, min(1.0, float(confidence)))

        return ModelOutput(
            prediction=prediction,
            confidence=round(bounded_confidence, 4),
            raw_score=round(raw_score, 6),
            model_id=self.config.model_id,
            model_version=self.config.model_version,
            preprocessing_version=self.config.preprocessing_version,
            artifact_sha256=artifact_sha256,
            inference_timestamp=datetime.now(timezone.utc),
        )


inference_engine = InferenceEngine()
