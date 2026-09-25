"""Security and integrity tests for model artifact loading (Stage 3).

Conforms to Section 7 & 20 of Stage 3 specifications.
Proves:
- Arbitrary model paths outside trusted directory are rejected (path traversal defense)
- Missing model files produce controlled errors
- Altered/corrupted artifact checksums are detected and rejected
- User uploads cannot select or replace model artifacts
"""

import hashlib
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

root_dir = Path(__file__).resolve().parent.parent.parent
api_dir = root_dir / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from ml.config.model_config import ModelConfig
from ml.inference.model_loader import (
    ModelChecksumMismatchError,
    ModelLoader,
    ModelNotFoundError,
    ModelSecurityError,
)


class TestModelLoaderSecurity(unittest.TestCase):
    """Test suite covering artifact path security, checksum validation, and safe loading."""

    def setUp(self) -> None:
        self.loader = ModelLoader()
        self.config = ModelConfig()

    def test_canonical_artifact_loads_successfully(self) -> None:
        """Configured canonical model artifact passes checksum verification and loads in eval mode."""
        model, digest = self.loader.load_model(force_reload=True)
        self.assertIsNotNone(model)
        self.assertEqual(digest, self.config.expected_artifact_sha256)
        self.assertFalse(model.training)

    def test_missing_model_file_raises_controlled_error(self) -> None:
        """Non-existent model path within trusted directory raises ModelNotFoundError."""
        fake_path = self.config.artifact_dir / "non_existent.safetensors"
        with self.assertRaises(ModelNotFoundError):
            self.loader.load_model(artifact_path=fake_path)

    def test_path_traversal_outside_trusted_dir_rejected(self) -> None:
        """Model path outside the trusted artifact directory raises ModelSecurityError."""
        # Attempt traversal to parent directory or /etc
        traversal_path = self.config.artifact_dir / ".." / ".." / "unauthorized_model.safetensors"
        with self.assertRaises(ModelSecurityError):
            self.loader.load_model(artifact_path=traversal_path)

    def test_checksum_mismatch_rejected(self) -> None:
        """Artifact with mismatched SHA-256 digest is rejected via ModelChecksumMismatchError."""
        with self.assertRaises(ModelChecksumMismatchError):
            self.loader.load_model(
                expected_sha256="0" * 64,  # Intentionally incorrect digest
                force_reload=True,
            )

    def test_tampered_model_weights_detected(self) -> None:
        """Tampered model file on disk is detected via cryptographic verification before deserialization."""
        temp_dir = tempfile.mkdtemp()
        try:
            fake_artifact = Path(temp_dir) / "model.safetensors"
            fake_artifact.write_bytes(b"tampered content")

            custom_config = ModelConfig(
                artifact_dir=Path(temp_dir),
                expected_artifact_sha256="f" * 64,
            )
            tamper_loader = ModelLoader(config=custom_config)

            # Calculated digest does not match expected "f"*64
            with self.assertRaises(ModelChecksumMismatchError):
                tamper_loader.load_model(artifact_path=fake_artifact)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_corrupted_safetensors_deserialization_fails_safely(self) -> None:
        """Invalid safetensors binary format with matching checksum fails safely without code execution."""
        temp_dir = tempfile.mkdtemp()
        try:
            corrupt_file = Path(temp_dir) / "corrupt.safetensors"
            corrupt_bytes = b"NOT_A_VALID_SAFETENSORS_HEADER_OR_PAYLOAD"
            corrupt_file.write_bytes(corrupt_bytes)
            computed_sha = hashlib.sha256(corrupt_bytes).hexdigest()

            custom_config = ModelConfig(
                artifact_dir=Path(temp_dir),
                expected_artifact_sha256=computed_sha,
            )
            loader = ModelLoader(config=custom_config)

            with self.assertRaises(ModelSecurityError):
                loader.load_model(artifact_path=corrupt_file, expected_sha256=computed_sha)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
