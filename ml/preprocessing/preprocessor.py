"""Deterministic image preprocessing pipeline conforming to Section 9 of Stage 3."""

import io
import logging
from typing import Tuple

import numpy as np
from PIL import Image, ImageFile
import torch

from ml.config.model_config import model_config

logger = logging.getLogger("addmai.ml.preprocessor")


class PreprocessingError(Exception):
    """Raised when preprocessing encounters malformed or oversized input."""
    pass


class ImagePreprocessor:
    """Deterministic image preprocessing for deepfake model inference.

    Executes decode -> resize -> center-crop -> RGB conversion -> normalization -> tensor conversion.
    Strictly preserves in-memory byte immutability of the source payload.
    """

    def __init__(
        self,
        target_size: Tuple[int, int] = (model_config.input_height, model_config.input_width),
        resize_dim: int = model_config.resize_dimension,
        max_pixels: int = model_config.max_image_pixels,
    ) -> None:
        self.target_height, self.target_width = target_size
        self.resize_dim = resize_dim
        self.max_pixels = max_pixels

        # Standard ImageNet normalization coefficients
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32)

    def preprocess(self, content: bytes) -> torch.Tensor:
        """Process raw image bytes into a normalized (1, 3, H, W) PyTorch tensor.

        Args:
            content: Raw immutable bytes of an ingested image asset.

        Returns:
            torch.FloatTensor of shape (1, 3, target_height, target_width).

        Raises:
            PreprocessingError: If media is empty, truncated, decompression bomb, or unreadable.
        """
        if not content or len(content) == 0:
            raise PreprocessingError("Input content is empty (0 bytes).")

        # Configure Pillow security invariants
        Image.MAX_IMAGE_PIXELS = self.max_pixels
        ImageFile.LOAD_TRUNCATED_IMAGES = False

        try:
            # 1. Decode & Verify
            stream = io.BytesIO(content)
            with Image.open(stream) as img:
                img.verify()

            # Reopen after verify to load image data
            stream.seek(0)
            with Image.open(stream) as img:
                # 2. Convert to RGB color-space
                rgb_img = img.convert("RGB")

                # 3. Resize to intermediate dimension (bicubic)
                resized_img = rgb_img.resize(
                    (self.resize_dim, self.resize_dim),
                    resample=Image.Resampling.BICUBIC,
                )

                # 4. Deterministic Center-Crop
                left = (self.resize_dim - self.target_width) // 2
                top = (self.resize_dim - self.target_height) // 2
                right = left + self.target_width
                bottom = top + self.target_height
                cropped_img = resized_img.crop((left, top, right, bottom))

                # 5. Convert to normalized NumPy array in range [0.0, 1.0]
                img_np = np.asarray(cropped_img, dtype=np.float32) / 255.0

                # 6. Apply Channel Normalization: (x - mean) / std
                norm_np = (img_np - self.mean) / self.std

                # 7. Convert from (H, W, C) to (C, H, W)
                chw_np = np.transpose(norm_np, (2, 0, 1))

                # 8. Add Batch Dimension -> (1, C, H, W)
                batch_np = np.expand_dims(chw_np, axis=0)

                # 9. Convert to PyTorch Tensor
                tensor = torch.from_numpy(batch_np).contiguous().float()

                return tensor

        except Image.DecompressionBombError as dbe:
            logger.warning(f"Decompression bomb detected during preprocessing: {dbe}")
            raise PreprocessingError(f"Image exceeds safe dimension threshold: {dbe}") from dbe
        except (OSError, SyntaxError, ValueError) as err:
            logger.warning(f"Malformed image encountered during preprocessing: {err}")
            raise PreprocessingError(f"Failed to decode valid image stream: {err}") from err
        except Exception as exc:
            logger.error(f"Unexpected error during image preprocessing: {exc}")
            raise PreprocessingError(f"Unexpected image preprocessing failure: {exc}") from exc


image_preprocessor = ImagePreprocessor()
