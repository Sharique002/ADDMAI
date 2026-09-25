"""Integration tests for POST /api/v1/media/{media_id}/detect API endpoint (Stage 3).

Conforms to Sections 16, 17, 18, 20, 24 of Stage 3 specifications.
"""

from datetime import datetime, timezone
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
api_dir = Path(__file__).resolve().parent.parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.media import MediaRecord
from app.repositories.media import media_repository
from app.services.detection import detection_service
from app.services.storage import InMemoryStorageBackend, StorageService


class TestMediaDetectAPI(unittest.TestCase):
    """Test suite covering the AI detection HTTP endpoint contracts and error states."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(cls.temp_dir, "test_api_detect.db")
        cls.engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)

        cls.session_maker = async_sessionmaker(
            bind=cls.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        cls.storage_backend = InMemoryStorageBackend()
        cls.storage_service = StorageService(backend=cls.storage_backend)

        # Generate sample PNG fixture
        buf = io.BytesIO()
        Image.new("RGB", (100, 100), color="orange").save(buf, format="PNG")
        cls.png_bytes = buf.getvalue()

        # Generate sample MP4 dummy fixture
        cls.mp4_bytes = b"\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41\x00\x00\x00\x08free"

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def setUp(self) -> None:
        import asyncio
        async def init_tables():
            async with self.engine.begin() as conn:
                await conn.execute(text("PRAGMA journal_mode=WAL;"))
                await conn.run_sync(Base.metadata.create_all)
        asyncio.run(init_tables())

        async def override_get_db():
            async with self.session_maker() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        import asyncio
        async def drop_tables():
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
        asyncio.run(drop_tables())
        app.dependency_overrides.clear()

    def test_detect_valid_image_success(self) -> None:
        """POST /media/{id}/detect for valid image returns 200 with structured ModelPredictionResponse."""
        import asyncio
        media_id = uuid.uuid4()
        storage_key = f"media/original/{'a' * 64}"

        async def setup_data():
            await self.storage_backend.upload(storage_key, self.png_bytes, "image/png")
            import hashlib
            digest = hashlib.sha256(self.png_bytes).hexdigest()
            async with self.session_maker() as session:
                record = MediaRecord(
                    id=media_id,
                    sha256_digest=digest,
                    media_category="image",
                    mime_type="image/png",
                    original_filename="test.png",
                    size_bytes=len(self.png_bytes),
                    storage_key=storage_key,
                    validation_status="accepted",
                )
                await media_repository.create(session, record)
                await session.commit()

        asyncio.run(setup_data())

        with patch.object(detection_service, "storage", self.storage_service):
            response = self.client.post(f"/api/v1/media/{media_id}/detect")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["media_id"], str(media_id))
        self.assertIn("model", data)
        self.assertEqual(data["model"]["model_id"], "addmai-deepfake-detector")
        self.assertIn(data["prediction"], ["REAL", "DEEPFAKE"])
        self.assertGreaterEqual(data["confidence"], 0.0)
        self.assertLessEqual(data["confidence"], 1.0)
        self.assertIn("inference_timestamp", data)
        self.assertIn("preprocessing_version", data)

        # CRITICAL CONSTITUTIONAL BOUNDARY ASSERTION:
        # Zero final authenticity claims permitted in Stage 3 response
        self.assertNotIn("verdict", data)
        self.assertNotIn("LIKELY_AUTHENTIC", str(data))
        self.assertNotIn("LIKELY_MANIPULATED", str(data))
        self.assertNotIn("INCONCLUSIVE", str(data))

    def test_detect_unknown_media_id_returns_404(self) -> None:
        """POST /media/{id}/detect for non-existent media_id returns 404 with RFC-7807 problem details."""
        random_id = uuid.uuid4()
        response = self.client.post(f"/api/v1/media/{random_id}/detect")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("type", data)
        self.assertEqual(data["status"], 404)
        self.assertIn("not found", data["detail"].lower())

    def test_detect_invalid_uuid_returns_404(self) -> None:
        """POST /media/{id}/detect with malformed UUID string returns 404."""
        response = self.client.post("/api/v1/media/not-a-valid-uuid/detect")
        self.assertEqual(response.status_code, 404)

    def test_detect_video_returns_415_unsupported_media_type(self) -> None:
        """POST /media/{id}/detect for video asset returns 415 stating Stage 3 supports images only."""
        import asyncio
        video_id = uuid.uuid4()
        storage_key = f"media/original/{'b' * 64}"

        async def setup_video():
            await self.storage_backend.upload(storage_key, self.mp4_bytes, "video/mp4")
            import hashlib
            digest = hashlib.sha256(self.mp4_bytes).hexdigest()
            async with self.session_maker() as session:
                record = MediaRecord(
                    id=video_id,
                    sha256_digest=digest,
                    media_category="video",  # Video category
                    mime_type="video/mp4",
                    original_filename="sample.mp4",
                    size_bytes=len(self.mp4_bytes),
                    storage_key=storage_key,
                    validation_status="accepted",
                )
                await media_repository.create(session, record)
                await session.commit()

        asyncio.run(setup_video())

        with patch("app.services.detection.storage_service", self.storage_service):
            response = self.client.post(f"/api/v1/media/{video_id}/detect")

        self.assertEqual(response.status_code, 415)
        data = response.json()
        self.assertEqual(data["status"], 415)
        self.assertIn("video", data["detail"].lower())
        self.assertIn("Stage 3", data["detail"])

    def test_detect_corrupted_media_returns_422(self) -> None:
        """POST /media/{id}/detect where stored media bytes are unparseable returns 422."""
        import asyncio
        bad_id = uuid.uuid4()
        storage_key = f"media/original/{'c' * 64}"
        corrupt_bytes = b"CORRUPTED_NOT_AN_IMAGE_PAYLOAD"

        async def setup_corrupted():
            await self.storage_backend.upload(storage_key, corrupt_bytes, "image/png")
            import hashlib
            digest = hashlib.sha256(corrupt_bytes).hexdigest()
            async with self.session_maker() as session:
                record = MediaRecord(
                    id=bad_id,
                    sha256_digest=digest,
                    media_category="image",
                    mime_type="image/png",
                    original_filename="bad.png",
                    size_bytes=len(corrupt_bytes),
                    storage_key=storage_key,
                    validation_status="accepted",
                )
                await media_repository.create(session, record)
                await session.commit()

        asyncio.run(setup_corrupted())

        with patch.object(detection_service, "storage", self.storage_service):
            response = self.client.post(f"/api/v1/media/{bad_id}/detect")

        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertEqual(data["status"], 422)
        self.assertIn("malformed", data["type"].lower())


if __name__ == "__main__":
    unittest.main()
