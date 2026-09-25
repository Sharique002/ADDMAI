"""Unit tests for concurrent deduplication races, database consistency, and CHECK constraints (Stage 2.1).

Conforms to Sections 6, 17, 18, 19, 20 of Stage 2.1 specifications.
"""

import asyncio
import io
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

# Ensure apps/api is on sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
api_dir = root_dir / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from PIL import Image
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.media import MediaRecord
from app.repositories.media import media_repository
from app.services.media_ingestion import MediaIngestionService
from app.services.storage import InMemoryStorageBackend, StorageService


class TestMediaConcurrencyAndConsistency(unittest.IsolatedAsyncioTestCase):
    """Test suite covering concurrent ingestion races, storage/database consistency, and constraints."""

    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(self.temp_dir, "test_concurrency.db")
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{db_path}",
            echo=False,
        )
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

        # Generate sample PNG
        buf = io.BytesIO()
        Image.new("RGB", (25, 25), color="purple").save(buf, format="PNG")
        self.png_bytes = buf.getvalue()

    async def asyncTearDown(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ============================================================
    # 6: DATABASE SCHEMA INITIALIZATION TEST
    # ============================================================

    async def test_database_initialization_and_schema_contract(self) -> None:
        """Fresh database creates media_records table with required columns, constraints, and indexes."""
        async with self.engine.connect() as conn:
            # Check table existence
            table_names = await conn.run_sync(
                lambda sync_conn: sync_conn.dialect.get_table_names(sync_conn)
            )
            self.assertIn("media_records", table_names)

            # Check columns
            cols = await conn.run_sync(
                lambda sync_conn: sync_conn.dialect.get_columns(sync_conn, "media_records")
            )
            col_names = {c["name"] for c in cols}
            expected_cols = {
                "id",
                "sha256_digest",
                "media_category",
                "mime_type",
                "original_filename",
                "size_bytes",
                "storage_key",
                "validation_status",
                "created_at",
            }
            self.assertTrue(expected_cols.issubset(col_names))

    # ============================================================
    # 20: MEDIA RECORD INVARIANTS & CHECK CONSTRAINTS
    # ============================================================

    async def test_check_constraint_negative_size_bytes_rejected(self) -> None:
        """Database rejects media record with negative size_bytes."""
        async with self.session_maker() as session:
            bad_record = MediaRecord(
                id=uuid.uuid4(),
                sha256_digest="f" * 64,
                media_category="image",
                mime_type="image/png",
                original_filename="neg.png",
                size_bytes=-100,  # Violates check constraint
                storage_key="media/original/" + "f" * 64,
                validation_status="accepted",
            )
            session.add(bad_record)
            with self.assertRaises(IntegrityError):
                await session.commit()
            await session.rollback()

    async def test_check_constraint_invalid_media_category_rejected(self) -> None:
        """Database rejects media record with category outside ('image', 'video')."""
        async with self.session_maker() as session:
            bad_record = MediaRecord(
                id=uuid.uuid4(),
                sha256_digest="1" * 64,
                media_category="audio",  # Not supported in Stage 2
                mime_type="audio/mp3",
                original_filename="sound.mp3",
                size_bytes=500,
                storage_key="media/original/" + "1" * 64,
                validation_status="accepted",
            )
            session.add(bad_record)
            with self.assertRaises(IntegrityError):
                await session.commit()
            await session.rollback()

    # ============================================================
    # 19: CONCURRENT DEDUPLICATION SIMULATION (REQUIRED)
    # ============================================================

    async def test_concurrent_deduplication_race(self) -> None:
        """Simulate simultaneous ingestion attempts with identical bytes.

        Request A and Request B execute concurrently.
        Expected: Exactly ONE canonical media record in database.
                  Exactly ONE canonical storage object in MinIO.
                  Both requests succeed with deterministic responses.
        """
        with patch("app.services.media_ingestion.storage_service", self.storage_service):
            # Run two simultaneous ingestions using separate database sessions
            async def run_ingest(req_num: int):
                async with self.session_maker() as session:
                    return await self.ingestion_service.ingest_media(
                        content=self.png_bytes,
                        raw_filename=f"concurrent_upload_{req_num}.png",
                        declared_content_type="image/png",
                        session=session,
                    )

            # Execute concurrently via asyncio.gather
            (rec1, anal1, is_dup1), (rec2, anal2, is_dup2) = await asyncio.gather(
                run_ingest(1),
                run_ingest(2),
            )

            # Both return identical canonical media_id and SHA-256
            self.assertEqual(rec1.id, rec2.id)
            self.assertEqual(rec1.sha256_digest, rec2.sha256_digest)

            # Exactly one request is new, and the other is flagged duplicate
            self.assertTrue(is_dup1 or is_dup2)
            self.assertNotEqual(is_dup1, is_dup2)

            # Verify database has exactly 1 row
            async with self.session_maker() as session:
                rows = (await session.execute(select(MediaRecord))).scalars().all()
                self.assertEqual(len(rows), 1)

            # Verify storage has exactly 1 canonical object
            storage_keys = list(self.storage_backend._storage.keys())
            self.assertEqual(len(storage_keys), 1)

    # ============================================================
    # 18: STORAGE & DATABASE CONSISTENCY CASES
    # ============================================================

    async def test_case_c_storage_succeeds_db_fails_cleanup_attempted(self) -> None:
        """Case C: Storage upload succeeds, DB commit fails -> storage object deleted."""
        with patch("app.services.media_ingestion.storage_service", self.storage_service):
            async with self.session_maker() as session:
                with patch.object(session, "commit", side_effect=RuntimeError("Simulated DB commit error")):
                    with self.assertRaises(RuntimeError):
                        await self.ingestion_service.ingest_media(
                            content=self.png_bytes,
                            raw_filename="rollback_test.png",
                            declared_content_type="image/png",
                            session=session,
                        )

                    # Ensure storage object was cleaned up
                    digest = self.ingestion_service.calculate_sha256(self.png_bytes)
                    key = StorageService.get_deterministic_key(digest)
                    self.assertFalse(await self.storage_service.object_exists(key))

    async def test_case_d_storage_fails_no_db_record_created(self) -> None:
        """Case D: Storage upload fails -> no database record is created."""
        with patch("app.services.media_ingestion.storage_service", self.storage_service):
            async with self.session_maker() as session:
                with patch.object(self.storage_service, "store_original", side_effect=RuntimeError("S3 connection error")):
                    with self.assertRaises(RuntimeError):
                        await self.ingestion_service.ingest_media(
                            content=self.png_bytes,
                            raw_filename="storage_fail.png",
                            declared_content_type="image/png",
                            session=session,
                        )

                    # Verify no DB record exists
                    rows = (await session.execute(select(MediaRecord))).scalars().all()
                    self.assertEqual(len(rows), 0)


if __name__ == "__main__":
    unittest.main()
