"""Unit tests for deterministic image preprocessing pipeline (Stage 3).

Conforms to Section 9 of Stage 3 specifications.
"""

import io
from pathlib import Path
import sys
import unittest

# Ensure project root is on sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
api_dir = root_dir / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import numpy as np
from PIL import Image
import torch

from ml.preprocessing.preprocessor import ImagePreprocessor, PreprocessingError


class TestImagePreprocessing(unittest.TestCase):
    """Test suite verifying image decoding, resizing, cropping, normalization, and bounds."""

    def setUp(self) -> None:
        self.preprocessor = ImagePreprocessor(target_size=(224, 224), resize_dim=256)

        # Generate sample PNG
        buf_png = io.BytesIO()
        Image.new("RGB", (320, 240), color="blue").save(buf_png, format="PNG")
        self.png_bytes = buf_png.getvalue()

        # Generate sample JPEG
        buf_jpg = io.BytesIO()
        Image.new("RGB", (400, 300), color="red").save(buf_jpg, format="JPEG")
        self.jpg_bytes = buf_jpg.getvalue()

    def test_png_preprocessing_shape_and_type(self) -> None:
        """PNG input decodes, resizes, crops, and produces (1, 3, 224, 224) float32 tensor."""
        tensor = self.preprocessor.preprocess(self.png_bytes)
        self.assertIsInstance(tensor, torch.Tensor)
        self.assertEqual(tensor.shape, (1, 3, 224, 224))
        self.assertEqual(tensor.dtype, torch.float32)

    def test_jpeg_preprocessing_shape_and_type(self) -> None:
        """JPEG input decodes, resizes, crops, and produces (1, 3, 224, 224) float32 tensor."""
        tensor = self.preprocessor.preprocess(self.jpg_bytes)
        self.assertIsInstance(tensor, torch.Tensor)
        self.assertEqual(tensor.shape, (1, 3, 224, 224))
        self.assertEqual(tensor.dtype, torch.float32)

    def test_preprocessing_determinism(self) -> None:
        """Identical input bytes produce bit-for-bit identical tensor output."""
        tensor1 = self.preprocessor.preprocess(self.png_bytes)
        tensor2 = self.preprocessor.preprocess(self.png_bytes)
        self.assertTrue(torch.equal(tensor1, tensor2))

    def test_preprocessing_does_not_mutate_input_bytes(self) -> None:
        """Preprocessing operates in-memory and leaves source byte buffer completely unchanged."""
        original_copy = bytes(self.png_bytes)
        _ = self.preprocessor.preprocess(self.png_bytes)
        self.assertEqual(self.png_bytes, original_copy)

    def test_grayscale_image_converts_to_three_channels(self) -> None:
        """Grayscale ('L') images are converted to 3-channel RGB tensors."""
        buf = io.BytesIO()
        Image.new("L", (150, 150), color=128).save(buf, format="PNG")
        tensor = self.preprocessor.preprocess(buf.getvalue())
        self.assertEqual(tensor.shape, (1, 3, 224, 224))

    def test_rgba_image_converts_to_rgb(self) -> None:
        """RGBA images are converted to 3-channel RGB tensors without alpha channel error."""
        buf = io.BytesIO()
        Image.new("RGBA", (150, 150), color=(100, 150, 200, 128)).save(buf, format="PNG")
        tensor = self.preprocessor.preprocess(buf.getvalue())
        self.assertEqual(tensor.shape, (1, 3, 224, 224))

    def test_empty_content_rejected(self) -> None:
        """Empty byte payload (0 bytes) raises PreprocessingError."""
        with self.assertRaises(PreprocessingError):
            self.preprocessor.preprocess(b"")

    def test_corrupted_image_rejected(self) -> None:
        """Corrupted random byte stream raises PreprocessingError."""
        with self.assertRaises(PreprocessingError):
            self.preprocessor.preprocess(b"\x89PNG\r\n\x1a\nCorruptedRandomDataGarbage")

    def test_decompression_bomb_rejected(self) -> None:
        """Oversized image exceeding max_pixels raises PreprocessingError."""
        bomb_preprocessor = ImagePreprocessor(max_pixels=5000)
        # Create image with 10,000 pixels (exceeds 5,000 cap)
        buf = io.BytesIO()
        Image.new("RGB", (100, 100), color="white").save(buf, format="PNG")
        with self.assertRaises(PreprocessingError):
            bomb_preprocessor.preprocess(buf.getvalue())


if __name__ == "__main__":
    unittest.main()
