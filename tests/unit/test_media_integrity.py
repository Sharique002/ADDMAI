"""Hardened Unit Tests for media hashing, filename sanitization, validation, container security, and neutral evidence (Stage 2.1).

Conforms to Sections 7, 8, 9, 11, 12, 13, 14, 15, 25, 30 of Stage 2.1 specifications.
All tests run deterministically in-memory without external services.
"""

import hashlib
import io
import os
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

# Ensure apps/api is on sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
api_dir = root_dir / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from PIL import Image

from app.core.config import settings
from app.core.media_types import (
    EmptyMediaError,
    FileTooLargeError,
    MalformedMediaError,
    UnsupportedMediaTypeError,
    validate_media_type,
)
from app.core.security import sanitize_filename
from app.services.media_ingestion import MediaIngestionService
from app.services.media_inspection import inspect_image, inspect_media_container, inspect_mp4_video
from app.services.metadata import MetadataService
from app.services.storage import InMemoryStorageBackend, StorageService


class TestMediaIntegrityAndValidation(unittest.TestCase):
    """Test suite covering Stage 2.1 hashing, filename, hostile validation, image, and MP4 security."""

    def setUp(self) -> None:
        self.ingestion_service = MediaIngestionService()
        self.metadata_service = MetadataService()

        # Generate minimal valid test images
        png_buf = io.BytesIO()
        Image.new("RGB", (32, 32), color="green").save(png_buf, format="PNG")
        self.valid_png_bytes = png_buf.getvalue()

        jpg_buf = io.BytesIO()
        Image.new("RGB", (32, 32), color="blue").save(jpg_buf, format="JPEG")
        self.valid_jpg_bytes = jpg_buf.getvalue()

        # Minimal valid MP4 container: 24B ftyp box + 8B free box = 32B total
        self.valid_mp4_bytes = (
            b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isommp41\x00\x00\x00\x08free"
        )

    # ============================================================
    # 7 & 30: HASHING TESTS
    # ============================================================

    def test_sha256_known_empty_vector(self) -> None:
        """Known test vector: empty byte string sha256."""
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        digest = self.ingestion_service.calculate_sha256(b"")
        self.assertEqual(digest, expected)

    def test_sha256_known_string_vector(self) -> None:
        """Known test vector: deterministic string input."""
        sample_bytes = b"ADDMAI-STAGE-2.1-HARDENING-TEST-VECTOR"
        expected = hashlib.sha256(sample_bytes).hexdigest().lower()
        digest = self.ingestion_service.calculate_sha256(sample_bytes)
        self.assertEqual(digest, expected)

    def test_sha256_format_strictly_64_lowercase_hex(self) -> None:
        """SHA-256 digest format must be exactly 64 lowercase hexadecimal characters."""
        digest = self.ingestion_service.calculate_sha256(self.valid_png_bytes)
        self.assertEqual(len(digest), 64)
        self.assertTrue(bool(re.fullmatch(r"^[0-9a-f]{64}$", digest)))

    def test_sha256_determinism(self) -> None:
        """Repeated computation over identical bytes must yield identical hash every time."""
        digest_1 = self.ingestion_service.calculate_sha256(self.valid_jpg_bytes)
        digest_2 = self.ingestion_service.calculate_sha256(self.valid_jpg_bytes)
        self.assertEqual(digest_1, digest_2)

    def test_sha256_avalanche_effect(self) -> None:
        """A single bit flip must produce a completely different hash digest."""
        b1 = b"Sample video or image payload version A"
        b2 = b"Sample video or image payload version B"
        d1 = self.ingestion_service.calculate_sha256(b1)
        d2 = self.ingestion_service.calculate_sha256(b2)
        self.assertNotEqual(d1, d2)

    def test_sha256_binary_and_null_bytes(self) -> None:
        """Hashing bytes containing binary nulls and arbitrary bytes works deterministically."""
        null_bytes = b"\x00\x01\x02\x00\x00\xff\xfe\x00\xaa\xbb"
        expected = hashlib.sha256(null_bytes).hexdigest().lower()
        self.assertEqual(self.ingestion_service.calculate_sha256(null_bytes), expected)

    def test_sha256_large_payload(self) -> None:
        """Hashing a 2 MB byte stream calculates exact expected hash."""
        large_bytes = b"X" * (2 * 1024 * 1024)
        expected = hashlib.sha256(large_bytes).hexdigest().lower()
        self.assertEqual(self.ingestion_service.calculate_sha256(large_bytes), expected)

    def test_sha256_unicode_bytes(self) -> None:
        """Unicode characters encoded as UTF-8 bytes are hashed deterministically."""
        unicode_bytes = "Изображение 2026 🔒".encode("utf-8")
        expected = hashlib.sha256(unicode_bytes).hexdigest().lower()
        self.assertEqual(self.ingestion_service.calculate_sha256(unicode_bytes), expected)

    # ============================================================
    # 9 & 30: FILENAME TESTS
    # ============================================================

    def test_filename_normal(self) -> None:
        """Normal alphanumeric filename with extension is preserved."""
        cleaned = sanitize_filename("sample_photo.jpg")
        self.assertEqual(cleaned, "sample_photo.jpg")

    def test_filename_path_traversal_unix(self) -> None:
        """Directory traversal sequences (../) are neutralized."""
        cleaned = sanitize_filename("../../../etc/passwd.png")
        self.assertNotIn("/", cleaned)
        self.assertNotIn("..", cleaned)
        self.assertTrue(cleaned.endswith(".png"))

    def test_filename_path_traversal_windows(self) -> None:
        """Directory traversal sequences (..\\) are neutralized."""
        cleaned = sanitize_filename("..\\..\\Windows\\System32\\cmd.jpg")
        self.assertNotIn("\\", cleaned)
        self.assertNotIn("..", cleaned)
        self.assertTrue(cleaned.endswith(".jpg"))

    def test_filename_absolute_unix_path(self) -> None:
        """Absolute Unix paths (/var/uploads/secret.jpg) have directory components removed."""
        cleaned = sanitize_filename("/var/uploads/secret.jpg")
        self.assertEqual(cleaned, "secret.jpg")

    def test_filename_absolute_windows_path(self) -> None:
        """Absolute Windows drive paths (C:\\Windows\\system32\\file.jpg) have drive & dirs removed."""
        cleaned = sanitize_filename("C:\\Windows\\system32\\file.jpg")
        self.assertEqual(cleaned, "file.jpg")

    def test_filename_null_byte_injection(self) -> None:
        """Null byte injection is stripped from filename."""
        cleaned = sanitize_filename("innocent.jpg\x00.exe")
        self.assertNotIn("\x00", cleaned)
        self.assertTrue(cleaned.endswith(".exe"))

    def test_filename_empty_fallback(self) -> None:
        """Empty or whitespace-only filename falls back to default safe name."""
        self.assertEqual(sanitize_filename(""), "unnamed_asset")
        self.assertEqual(sanitize_filename("   "), "unnamed_asset")

    def test_filename_unicode(self) -> None:
        """Unicode filenames are safely handled and preserved."""
        cleaned = sanitize_filename("фотография_2026.png")
        self.assertIsInstance(cleaned, str)
        self.assertIn("2026.png", cleaned)

    def test_filename_very_long_bounded_length(self) -> None:
        """Filenames exceeding 255 characters are safely bounded to <= 255 characters."""
        long_stem = "a" * 300
        cleaned = sanitize_filename(f"{long_stem}.jpg")
        self.assertLessEqual(len(cleaned), 255)
        self.assertTrue(cleaned.endswith(".jpg"))

    # ============================================================
    # 8 & 30: HOSTILE MEDIA VALIDATION TESTS
    # ============================================================

    def test_upload_valid_jpeg_accepted(self) -> None:
        """Valid JPEG image passes format and magic-byte inspection."""
        media_def = validate_media_type("sample.jpg", self.valid_jpg_bytes, "image/jpeg")
        self.assertEqual(media_def.mime_type, "image/jpeg")
        self.assertEqual(media_def.category.value, "image")

    def test_upload_valid_png_accepted(self) -> None:
        """Valid PNG image passes format and magic-byte inspection."""
        media_def = validate_media_type("graphic.png", self.valid_png_bytes, "image/png")
        self.assertEqual(media_def.mime_type, "image/png")
        self.assertEqual(media_def.category.value, "image")

    def test_upload_valid_mp4_accepted(self) -> None:
        """Valid MP4 container passes format and ftyp inspection."""
        media_def = validate_media_type("clip.mp4", self.valid_mp4_bytes, "video/mp4")
        self.assertEqual(media_def.mime_type, "video/mp4")
        self.assertEqual(media_def.category.value, "video")

    def test_upload_extension_spoofing_rejected(self) -> None:
        """file.exe containing valid JPEG bytes is rejected due to disallowed extension."""
        with self.assertRaises(UnsupportedMediaTypeError):
            validate_media_type("malicious.exe", self.valid_jpg_bytes, "application/octet-stream")

    def test_upload_content_mismatch_png_with_jpeg_bytes(self) -> None:
        """file.png containing JPEG bytes is rejected with MalformedMediaError."""
        with self.assertRaises(MalformedMediaError):
            validate_media_type("spoofed.png", self.valid_jpg_bytes, "image/png")

    def test_upload_content_mismatch_jpg_with_random_bytes(self) -> None:
        """file.jpg containing random non-JPEG bytes is rejected with MalformedMediaError."""
        random_bytes = b"RANDOM_EXECUTABLE_PAYLOAD_NOT_IMAGE" + (b"\x00" * 30)
        with self.assertRaises(MalformedMediaError):
            validate_media_type("fake.jpg", random_bytes, "image/jpeg")

    def test_upload_content_mismatch_mp4_with_random_bytes(self) -> None:
        """file.mp4 containing random bytes without ftyp is rejected with MalformedMediaError."""
        with self.assertRaises(MalformedMediaError):
            validate_media_type("fake.mp4", b"NOT_AN_MP4_FILE_AT_ALL_1234567890", "video/mp4")

    def test_upload_empty_bytes_rejected(self) -> None:
        """Zero-length payload is rejected with EmptyMediaError."""
        with self.assertRaises(EmptyMediaError):
            validate_media_type("empty.jpg", b"", "image/jpeg")

    # ============================================================
    # 12 & 30: IMAGE SECURITY TESTS
    # ============================================================

    def test_image_corrupted_jpeg_rejected(self) -> None:
        """Corrupted JPEG bytes fail cleanly with MalformedMediaError."""
        corrupt_jpg = b"\xff\xd8\xff\xe0" + (b"\x00" * 20)
        with self.assertRaises(MalformedMediaError):
            inspect_image(corrupt_jpg)

    def test_image_corrupted_png_rejected(self) -> None:
        """Corrupted PNG stream fails cleanly with MalformedMediaError."""
        corrupt_png = b"\x89PNG\r\n\x1a\n" + (b"\xff" * 20)
        with self.assertRaises(MalformedMediaError):
            inspect_image(corrupt_png)

    def test_image_truncated_jpeg_rejected(self) -> None:
        """Truncated JPEG file stream is rejected by inspect_image."""
        half_jpg = self.valid_jpg_bytes[: len(self.valid_jpg_bytes) // 2]
        with self.assertRaises(MalformedMediaError):
            inspect_image(half_jpg)

    def test_image_decompression_bomb_safety(self) -> None:
        """Decompression bomb error in Pillow is caught and raised as MalformedMediaError."""
        with patch("PIL.Image.open") as mock_open:
            mock_open.side_effect = Image.DecompressionBombError("Decompression bomb protection triggered.")
            with self.assertRaises(MalformedMediaError) as ctx:
                inspect_image(self.valid_png_bytes)
            self.assertIn("decompression bomb", str(ctx.exception).lower())

    # ============================================================
    # 14 & 30: MP4 PARSER SECURITY TESTS
    # ============================================================

    def test_mp4_missing_ftyp_rejected(self) -> None:
        """MP4 without ftyp box raises MalformedMediaError."""
        no_ftyp = b"\x00\x00\x00\x10free12345678" + (b"\x00" * 16)
        with self.assertRaises(MalformedMediaError) as ctx:
            inspect_mp4_video(no_ftyp)
        self.assertIn("ftyp", str(ctx.exception).lower())

    def test_mp4_truncated_ftyp_rejected(self) -> None:
        """MP4 with declared ftyp box smaller than required payload raises MalformedMediaError."""
        truncated_ftyp = b"\x00\x00\x00\x09ftypX" + (b"\x00" * 16)
        with self.assertRaises(MalformedMediaError):
            inspect_mp4_video(truncated_ftyp)

    def test_mp4_invalid_box_size_rejected(self) -> None:
        """MP4 box declaring size < 8 (e.g. 4) raises MalformedMediaError."""
        bad_box = b"\x00\x00\x00\x04ftyp" + (b"\x00" * 20)
        with self.assertRaises(MalformedMediaError):
            inspect_mp4_video(bad_box)

    def test_mp4_oversized_box_declaration_rejected(self) -> None:
        """MP4 box declaring size larger than available content raises MalformedMediaError."""
        oversized = b"\x00\x00\xff\x00ftyp" + (b"\x00" * 20)
        with self.assertRaises(MalformedMediaError):
            inspect_mp4_video(oversized)

    def test_mp4_unknown_boxes_safely_skipped(self) -> None:
        """Unknown boxes (free, skip, wide, etc.) are safely skipped without errors."""
        # 24B ftyp + 8B free + 8B skip = 40B total
        multi_box = (
            b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isommp41"
            b"\x00\x00\x00\x08free"
            b"\x00\x00\x00\x08skip"
        )
        info = inspect_mp4_video(multi_box)
        self.assertEqual(info["major_brand"], "isom")
        self.assertEqual(info["container_format"], "mp4")

    # ============================================================
    # 13 & 30: ORIGINAL-BYTE INTEGRITY & EQUALITY TEST
    # ============================================================

    def test_original_byte_and_hash_equality(self) -> None:
        """Original upload bytes == stored bytes, and sha256(upload) == sha256(stored)."""
        import asyncio

        async def run_integrity_check() -> None:
            backend = InMemoryStorageBackend()
            storage = StorageService(backend=backend)

            original_bytes = bytes(self.valid_png_bytes)
            computed_sha = self.ingestion_service.calculate_sha256(original_bytes)

            # Store in backend
            key = await storage.store_original(
                sha256_digest=computed_sha,
                data=original_bytes,
                content_type="image/png",
                original_filename="test_integrity.png",
            )

            # Retrieve stored bytes directly from backend
            stored_bytes = backend._storage[key]

            # Invariant validation
            self.assertEqual(original_bytes, stored_bytes)
            self.assertEqual(
                hashlib.sha256(original_bytes).hexdigest().lower(),
                hashlib.sha256(stored_bytes).hexdigest().lower(),
            )
            self.assertEqual(computed_sha, hashlib.sha256(stored_bytes).hexdigest().lower())

        asyncio.run(run_integrity_check())

    # ============================================================
    # 25 & 30: METADATA NEUTRALITY TEST
    # ============================================================

    def test_absence_of_exif_never_produces_manipulation_verdicts(self) -> None:
        """Missing EXIF must remain a neutral observation, never flagged suspicious/manipulated."""
        evidence = self.metadata_service.build_evidence_items(
            sha256_digest="e" * 64,
            size_bytes=1000,
            mime_type="image/jpeg",
            category="image",
            container_info={"format": "JPEG", "width": 800, "height": 600, "exif_present": False},
            is_duplicate=False,
        )

        for item in evidence:
            dumped = item.model_dump()
            for forbidden in ["suspicious", "manipulated", "fake", "score", "verdict"]:
                self.assertNotIn(forbidden, dumped)
                if isinstance(dumped.get("value"), dict):
                    self.assertNotIn(forbidden, dumped["value"])


if __name__ == "__main__":
    unittest.main()
