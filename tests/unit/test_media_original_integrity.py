"""Mandatory regression test verifying byte-for-byte immutability of original media (Section 26).

Proves:
1. Ingest known fixture.
2. Record SHA-256 before inference.
3. Run AI detection on the media.
4. Retrieve original bytes from storage.
5. Calculate SHA-256 again after inference.
6. Compare: SHA256_before == SHA256_after.
7. Verify byte-for-byte equality: bytes_before == bytes_after.
"""

import hashlib
import io
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

from PIL import Image
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.services.detection import DetectionService
from app.services.media_ingestion import MediaIngestionService
from app.services.storage import InMemoryStorageBackend, StorageService
from ml.inference.engine import inference_engine


class TestOriginalMediaIntegrity(unittest.IsolatedAsyncioTestCase):
    """Mandatory test suite verifying that AI inference does not alter canonical media bytes."""

    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(self.temp_dir, "test_integrity.db")
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)
        async with self.engine.begin() as conn:
            await conn.execute(text("PRAGMA journal_mode=WAL;"))
            await conn.run_sync(Base.metadata.create_all)

        self.session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        self.storage_backend = InMemoryStorageBackend()
        self.storage_service = StorageService(backend=self.storage_backend)
        self.ingestion_service = MediaIngestionService()
        self.detection_service = DetectionService(
            engine=inference_engine,
            storage=self.storage_service,
        )

        # Generate sample PNG fixture
        buf = io.BytesIO()
        Image.new("RGB", (200, 200), color="indigo").save(buf, format="PNG")
        self.fixture_bytes = buf.getvalue()

    async def asyncTearDown(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    async def test_canonical_media_byte_immutability_through_ai_detection(self) -> None:
        """Original bytes and SHA-256 remain strictly unchanged before and after AI inference."""
        from unittest.mock import patch

        with patch("app.services.media_ingestion.storage_service", self.storage_service):
            # 1. Ingest media asset
            async with self.session_maker() as session:
                record, analysis, is_dup = await self.ingestion_service.ingest_media(
                    content=self.fixture_bytes,
                    raw_filename="integrity_verification.png",
                    declared_content_type="image/png",
                    session=session,
                )
                media_id = record.id
                storage_key = record.storage_key

            # 2. Record SHA-256 and bytes before inference
            bytes_before = await self.storage_service.get_object(storage_key)
            self.assertIsNotNone(bytes_before)
            sha256_before = hashlib.sha256(bytes_before).hexdigest().lower()
            self.assertEqual(sha256_before, record.sha256_digest.lower())

            # 3. Execute AI detection on the ingested media asset
            async with self.session_maker() as session:
                prediction_resp = await self.detection_service.detect(media_id, session)

            # Verify prediction output is valid
            self.assertIn(prediction_resp.prediction.value, ["REAL", "DEEPFAKE"])
            self.assertGreaterEqual(prediction_resp.confidence, 0.0)
            self.assertLessEqual(prediction_resp.confidence, 1.0)

            # 4. Retrieve original bytes from storage after inference
            bytes_after = await self.storage_service.get_object(storage_key)
            self.assertIsNotNone(bytes_after)

            # 5. Calculate SHA-256 after inference
            sha256_after = hashlib.sha256(bytes_after).hexdigest().lower()

            # 6. MANDATORY ASSERTION: SHA-256 equality
            self.assertEqual(
                sha256_before,
                sha256_after,
                "CRITICAL FAILURE: SHA-256 digest of media asset changed after AI inference!",
            )

            # 7. MANDATORY ASSERTION: Byte-for-byte equality
            self.assertEqual(
                bytes_before,
                bytes_after,
                "CRITICAL FAILURE: Canonical byte sequence mutated during AI inference pipeline!",
            )

            # Verify stored bytes match original fixture exactly
            self.assertEqual(bytes_after, self.fixture_bytes)


if __name__ == "__main__":
    unittest.main()
