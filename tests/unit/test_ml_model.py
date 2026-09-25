"""Unit tests for ADDMAIDeepfakeDetector architecture and inference engine (Stage 3).

Conforms to Sections 5, 6, 12, 13, 22 of Stage 3 specifications.
"""

from pathlib import Path
import sys
import unittest

root_dir = Path(__file__).resolve().parent.parent.parent
api_dir = root_dir / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import torch

from ml.config.model_config import model_config
from ml.inference.engine import InferenceEngine
from ml.models.detector import ADDMAIDeepfakeDetector
from ml.schemas.prediction import ModelOutput, PredictionEnum


class TestMLModelAndInference(unittest.TestCase):
    """Test suite covering model architecture, output shapes, deterministic evaluation, and engine contracts."""

    def setUp(self) -> None:
        self.model = ADDMAIDeepfakeDetector()
        self.model.eval()

    def test_model_forward_pass_shape(self) -> None:
        """Batch of (B, 3, 224, 224) produces logit output of shape (B, 1)."""
        x = torch.randn(2, 3, 224, 224)
        with torch.no_grad():
            out = self.model(x)
        self.assertEqual(out.shape, (2, 1))

    def test_single_sample_inference_shape(self) -> None:
        """Single sample (1, 3, 224, 224) produces (1, 1) output."""
        x = torch.randn(1, 3, 224, 224)
        with torch.no_grad():
            out = self.model(x)
        self.assertEqual(out.shape, (1, 1))

    def test_deterministic_eval_mode(self) -> None:
        """Model forward pass in eval mode produces identical outputs for identical inputs."""
        x = torch.randn(1, 3, 224, 224)
        with torch.no_grad():
            out1 = self.model(x)
            out2 = self.model(x)
        self.assertTrue(torch.equal(out1, out2))

    def test_sigmoid_probability_range(self) -> None:
        """Sigmoid of raw model logit is bounded within [0.0, 1.0]."""
        x = torch.randn(5, 3, 224, 224)
        with torch.no_grad():
            logits = self.model(x)
            probs = torch.sigmoid(logits)
        self.assertTrue((probs >= 0.0).all())
        self.assertTrue((probs <= 1.0).all())

    def test_inference_engine_decision_boundary(self) -> None:
        """Score >= 0.5 maps to DEEPFAKE; score < 0.5 maps to REAL."""
        from unittest.mock import MagicMock
        mock_preprocessor = MagicMock()
        mock_preprocessor.preprocess.return_value = torch.zeros(1, 3, 224, 224)

        # Mock model returning high logit (deepfake)
        mock_model_fake = MagicMock()
        mock_model_fake.return_value = torch.tensor([[5.0]])  # sigmoid(5.0) ~ 0.9933
        mock_loader_fake = MagicMock()
        mock_loader_fake.load_model.return_value = (mock_model_fake, "a" * 64)

        engine = InferenceEngine(preprocessor=mock_preprocessor, loader=mock_loader_fake)
        out = engine.predict(b"dummy")
        self.assertEqual(out.prediction, PredictionEnum.DEEPFAKE)
        self.assertGreaterEqual(out.confidence, 0.5)

        # Mock model returning low logit (real)
        mock_model_real = MagicMock()
        mock_model_real.return_value = torch.tensor([[-5.0]])  # sigmoid(-5.0) ~ 0.0067
        mock_loader_real = MagicMock()
        mock_loader_real.load_model.return_value = (mock_model_real, "a" * 64)

        engine_real = InferenceEngine(preprocessor=mock_preprocessor, loader=mock_loader_real)
        out_real = engine_real.predict(b"dummy")
        self.assertEqual(out_real.prediction, PredictionEnum.REAL)
        self.assertGreaterEqual(out_real.confidence, 0.5)

    def test_prediction_output_contract_fields(self) -> None:
        """Inference returns valid ModelOutput with required metadata and bounds."""
        import io
        from PIL import Image
        buf = io.BytesIO()
        Image.new("RGB", (64, 64), color="green").save(buf, format="PNG")

        from ml.inference.engine import inference_engine
        res = inference_engine.predict(buf.getvalue())
        self.assertIsInstance(res, ModelOutput)
        self.assertIn(res.prediction, [PredictionEnum.REAL, PredictionEnum.DEEPFAKE])
        self.assertGreaterEqual(res.confidence, 0.0)
        self.assertLessEqual(res.confidence, 1.0)
        self.assertEqual(res.model_id, model_config.model_id)
        self.assertEqual(res.model_version, model_config.model_version)
        self.assertEqual(res.preprocessing_version, model_config.preprocessing_version)
        self.assertEqual(len(res.artifact_sha256), 64)


if __name__ == "__main__":
    unittest.main()
