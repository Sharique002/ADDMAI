"""Secure model artifact loading and validation conforming to Section 7 of Stage 3."""

import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple

from safetensors.torch import load_file
import torch

from ml.config.model_config import model_config
from ml.models.detector import ADDMAIDeepfakeDetector

logger = logging.getLogger("addmai.ml.loader")


class ModelSecurityError(Exception):
    """Raised when model artifact fails integrity, path, or format validation."""
    pass


class ModelNotFoundError(ModelSecurityError):
    """Raised when model weights file cannot be located."""
    pass


class ModelChecksumMismatchError(ModelSecurityError):
    """Raised when model artifact checksum does not match trusted configuration."""
    pass


class ModelLoader:
    """Safe model artifact loader enforcing path confinement, checksums, and safetensors deserialization."""

    def __init__(self, config=model_config) -> None:
        self.config = config
        self._cached_model: Optional[ADDMAIDeepfakeDetector] = None
        self._cached_sha256: Optional[str] = None

    def calculate_artifact_sha256(self, file_path: Path) -> str:
        """Compute deterministic 64-character lowercase hex SHA-256 of artifact."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest().lower()

    def load_model(
        self,
        artifact_path: Optional[Path] = None,
        expected_sha256: Optional[str] = None,
        force_reload: bool = False,
    ) -> Tuple[ADDMAIDeepfakeDetector, str]:
        """Safely load and verify model weights into ADDMAIDeepfakeDetector architecture.

        Args:
            artifact_path: Optional path override. Must resolve within trusted artifact directory.
            expected_sha256: Optional expected checksum override.
            force_reload: If True, bypasses internal cache.

        Returns:
            Tuple of (loaded ADDMAIDeepfakeDetector in eval mode, verified artifact SHA-256).

        Raises:
            ModelNotFoundError: If artifact does not exist on disk.
            ModelSecurityError: If artifact path is outside trusted directory or contains invalid format.
            ModelChecksumMismatchError: If file digest does not match expected checksum.
        """
        if self._cached_model is not None and not force_reload and artifact_path is None:
            return self._cached_model, self._cached_sha256  # type: ignore[return-value]

        target_path = (artifact_path or self.config.artifact_path).resolve()
        trusted_dir = self.config.artifact_dir.resolve()
        expected_digest = (expected_sha256 or self.config.expected_artifact_sha256).strip().lower()

        # 1. Path Confinement Check (Prevent Path Traversal)
        try:
            target_path.relative_to(trusted_dir)
        except ValueError as err:
            raise ModelSecurityError(
                f"Model artifact path '{target_path}' is outside trusted directory '{trusted_dir}'."
            ) from err

        # 2. Existence Check
        if not target_path.is_file():
            raise ModelNotFoundError(f"Model artifact not found at '{target_path}'.")

        # 3. Cryptographic Digest Verification
        actual_sha256 = self.calculate_artifact_sha256(target_path)
        if actual_sha256 != expected_digest:
            raise ModelChecksumMismatchError(
                f"Model artifact integrity check failed. Expected SHA-256 {expected_digest}, "
                f"calculated {actual_sha256}."
            )

        # 4. Safe Deserialization via Safetensors
        try:
            state_dict = load_file(str(target_path))
        except Exception as exc:
            raise ModelSecurityError(f"Failed to safely deserialize model artifact: {exc}") from exc

        # 5. Architecture Instantiation & Parameter Freezing
        model = ADDMAIDeepfakeDetector()
        try:
            model.load_state_dict(state_dict, strict=True)
        except Exception as exc:
            raise ModelSecurityError(f"State dict incompatible with ADDMAIDeepfakeDetector: {exc}") from exc

        model.eval()
        for param in model.parameters():
            param.requires_grad = False

        self._cached_model = model
        self._cached_sha256 = actual_sha256

        logger.info(
            f"Successfully loaded and verified model '{self.config.model_id}' "
            f"v{self.config.model_version} (SHA-256: {actual_sha256[:16]}...)"
        )
        return model, actual_sha256


model_loader = ModelLoader()
