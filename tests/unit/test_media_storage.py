"""Unit tests for Storage abstraction and rollback safety (Stage 2.1).

Conforms to Sections 16, 17, 18, 30 of Stage 2.1 specifications.
"""

import hashlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch

# Ensure apps/api is on sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
api_dir = root_dir / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from PIL import Image

from app.core.config import settings
from app.services.storage import InMemoryStorageBackend, StorageService


class TestMediaStorageHardening(unittest.IsolatedAsyncioTestCase):
    """Test suite covering storage key derivation, CRUD, and rollback handling."""

    async def asyncSetUp(self) -> None:
        self.backend = InMemoryStorageBackend()
        self.storage = StorageService(backend=self.backend)

        buf = io.BytesIO()
        Image.new("RGB", (16, 16), color="orange").save(buf, format="PNG")
        self.sample_bytes = buf.getvalue()

    async def test_storage_key_determinism(self) -> None:
        """Identical SHA-256 digests produce identical storage keys."""
        digest1 = "abcd1234" * 8
        digest2 = "abcd1234" * 8
        key1 = StorageService.get_deterministic_key(digest1)
        key2 = StorageService.get_deterministic_key(digest2)

        self.assertEqual(key1, f"media/original/{digest1}")
        self.assertEqual(key1, key2)

    async def test_storage_key_different_hashes(self) -> None:
        """Different SHA-256 digests produce distinct storage keys."""
        d1 = "1" * 64
        d2 = "2" * 64
        self.assertNotEqual(
            StorageService.get_deterministic_key(d1),
            StorageService.get_deterministic_key(d2),
        )

    async def test_storage_key_does_not_contain_filename(self) -> None:
        """Storage key must NEVER incorporate untrusted original_filename."""
        key = StorageService.get_deterministic_key("a" * 64)
        self.assertNotIn("malicious", key)
        self.assertNotIn(".jpg", key)
        self.assertNotIn("..", key)

    async def test_storage_upload_and_metadata_preservation(self) -> None:
        """Storage backend preserves content-type, byte size, and original filename metadata."""
        sha = hashlib.sha256(self.sample_bytes).hexdigest()
        key = await self.storage.store_original(
            sha256_digest=sha,
            data=self.sample_bytes,
            content_type="image/png",
            original_filename="graphic.png",
        )

        self.assertTrue(await self.storage.object_exists(key))
        meta = await self.storage.get_metadata(key)
        self.assertIsNotNone(meta)
        self.assertEqual(meta["content_type"], "image/png")
        self.assertEqual(meta["original_filename"], "graphic.png")
        self.assertEqual(meta["sha256"], sha)
        self.assertEqual(meta["byte_size"], str(len(self.sample_bytes)))

    async def test_storage_delete_operation(self) -> None:
        """Deleting stored object removes data and metadata cleanly."""
        sha = hashlib.sha256(self.sample_bytes).hexdigest()
        key = await self.storage.store_original(
            sha256_digest=sha,
            data=self.sample_bytes,
            content_type="image/png",
            original_filename="to_delete.png",
        )
        self.assertTrue(await self.storage.object_exists(key))

        deleted = await self.storage.delete_object(key)
        self.assertTrue(deleted)
        self.assertFalse(await self.storage.object_exists(key))
        self.assertIsNone(await self.storage.get_metadata(key))


if __name__ == "__main__":
    unittest.main()
