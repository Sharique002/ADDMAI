"""Unit tests for Media Ingestion Service and Repository persistence (Stage 2).

Conforms to Sections 24, 25, 26.D of Stage 2 specifications.
Tests database persistence, retrieval by ID, unique SHA-256 deduplication,
and failure cleanup without requiring external Docker services.
"""

import asyncio
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch
import uuid

# Ensure apps/api is on sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
api_dir = root_dir / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.media import MediaRecord
from app.repositories.media import media_repository
from app.services.media_ingestion import MediaIngestionService
from app.services.storage import InMemoryStorageBackend, StorageService


class TestMediaServiceAndRepository(unittest.IsolatedAsyncioTestCase):
    """Test suite covering database persistence, deduplication, and service workflows."""

    async def asyncSetUp(self) -> None:
        # Isolated in-memory SQLite engine
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Isolated in-memory storage backend
        self.storage_backend = InMemoryStorageBackend()
        self.storage_service = StorageService(backend=self.storage_backend)

        # Ingestion service
        self.ingestion_service = MediaIngestionService()

        # Generate sample PNG
        buf = io.BytesIO()
        Image.new("RGB", (20, 20), color="yellow").save(buf, format="PNG")
        self.png_bytes = buf.getvalue()

    async def asyncTearDown(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()

    async def test_media_repository_create_and_get_by_id(self) -> None:
        """Verify standard media record creation and retrieval by UUID."""
        async with self.session_maker() as session:
            record_id = uuid.uuid4()
            digest = "a" * 64
            record = MediaRecord(
                id=record_id,
                sha256_digest=digest,
                media_category="image",
                mime_type="image/png",
                original_filename="test.png",
                size_bytes=len(self.png_bytes),
                storage_key=f"media/original/{digest}",
                validation_status="accepted",
            )
            await media_repository.create(session, record)
            await session.commit()

            fetched = await media_repository.get_by_id(session, record_id)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.id, record_id)
            self.assertEqual(fetched.sha256_digest, digest)
            self.assertEqual(fetched.media_category, "image")
            self.assertEqual(fetched.size_bytes, len(self.png_bytes))

    async def test_media_repository_get_by_sha256(self) -> None:
        """Verify retrieval of existing media record by SHA-256 digest."""
        async with self.session_maker() as session:
            record_id = uuid.uuid4()
            digest = "b" * 64
            record = MediaRecord(
                id=record_id,
                sha256_digest=digest,
                media_category="image",
                mime_type="image/png",
                original_filename="photo.png",
                size_bytes=512,
                storage_key=f"media/original/{digest}",
                validation_status="accepted",
            )
            await media_repository.create(session, record)
            await session.commit()

            fetched = await media_repository.get_by_sha256(session, digest)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.id, record_id)

    async def test_full_ingestion_pipeline_new_media(self) -> None:
        """End-to-end ingestion of a new asset stores bytes and creates DB record."""
        with patch("app.services.media_ingestion.storage_service", self.storage_service):
            async with self.session_maker() as session:
                record, analysis, is_duplicate = await self.ingestion_service.ingest_media(
                    content=self.png_bytes,
                    raw_filename="sample.png",
                    declared_content_type="image/png",
                    session=session,
                )

                self.assertFalse(is_duplicate)
                self.assertIsNotNone(record.id)
                self.assertEqual(record.validation_status, "accepted")
                self.assertEqual(record.media_category, "image")

                # Verify object exists in storage
                self.assertTrue(await self.storage_service.object_exists(record.storage_key))

                # Verify AnalysisRecord structured observations
                self.assertEqual(analysis.media_id, str(record.id))
                self.assertEqual(analysis.integrity.sha256_digest, record.sha256_digest)
                self.assertEqual(analysis.container["width"], 20)
                self.assertEqual(analysis.container["height"], 20)
                self.assertGreaterEqual(len(analysis.evidence), 3)

    async def test_deduplication_invariant_identical_bytes(self) -> None:
        """Uploading identical bytes a second time reuses existing record and avoids duplicate storage."""
        with patch("app.services.media_ingestion.storage_service", self.storage_service):
            async with self.session_maker() as session:
                # 1. Initial ingestion
                rec1, anal1, is_dup1 = await self.ingestion_service.ingest_media(
                    content=self.png_bytes,
                    raw_filename="first_upload.png",
                    declared_content_type="image/png",
                    session=session,
                )
                self.assertFalse(is_dup1)

                # Count storage objects
                initial_storage_keys = list(self.storage_backend._storage.keys())
                self.assertEqual(len(initial_storage_keys), 1)

                # 2. Duplicate ingestion with different filename but identical bytes
                rec2, anal2, is_dup2 = await self.ingestion_service.ingest_media(
                    content=self.png_bytes,
                    raw_filename="second_upload_different_name.png",
                    declared_content_type="image/png",
                    session=session,
                )

                # Enforce deduplication invariant (Section 12 & 16)
                self.assertTrue(is_dup2)
                self.assertEqual(rec1.id, rec2.id)
                self.assertEqual(rec1.sha256_digest, rec2.sha256_digest)

                # Verify no second storage object was created
                self.assertEqual(len(self.storage_backend._storage.keys()), 1)

    async def test_storage_rollback_on_database_failure(self) -> None:
        """If database persistence fails, storage object is deleted to prevent orphans (Section 24)."""
        with patch("app.services.media_ingestion.storage_service", self.storage_service):
            async with self.session_maker() as session:
                # Force database create method to raise an error
                with patch.object(media_repository, "create", side_effect=RuntimeError("DB write failure")):
                    with self.assertRaises(RuntimeError):
                        await self.ingestion_service.ingest_media(
                            content=self.png_bytes,
                            raw_filename="fail.png",
                            declared_content_type="image/png",
                            session=session,
                        )

                    # Verify no orphan storage object was left behind
                    digest = self.ingestion_service.calculate_sha256(self.png_bytes)
                    key = StorageService.get_deterministic_key(digest)
                    self.assertFalse(await self.storage_service.object_exists(key))


if __name__ == "__main__":
    unittest.main()
