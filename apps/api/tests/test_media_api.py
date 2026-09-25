"""API endpoint tests for media ingestion and retrieval conforming to Sections 14, 15, 23, 26.F, 26.G."""

import asyncio
from datetime import datetime, timezone
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import uuid

# Ensure apps/api is on sys.path
api_dir = Path(__file__).resolve().parent.parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.media import MediaRecord
from app.services.storage import InMemoryStorageBackend, StorageService


class TestMediaAPIEndpoints(unittest.TestCase):
    """Test suite covering POST /api/v1/media and GET /api/v1/media/{media_id}."""

    @classmethod
    def setUpClass(cls) -> None:
        # Create an in-memory SQLite async engine for tests
        cls.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

        # Create all tables synchronously within async run
        async def init_tables() -> None:
            async with cls.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        asyncio.run(init_tables())

        cls.session_maker = async_sessionmaker(
            bind=cls.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # In-memory storage backend
        cls.storage_backend = InMemoryStorageBackend()
        cls.mock_storage_service = StorageService(backend=cls.storage_backend)

        # Generate sample valid JPEG and PNG
        buf_jpg = io.BytesIO()
        Image.new("RGB", (30, 30), color="blue").save(buf_jpg, format="JPEG")
        cls.jpg_bytes = buf_jpg.getvalue()

        buf_png = io.BytesIO()
        Image.new("RGB", (30, 30), color="red").save(buf_png, format="PNG")
        cls.png_bytes = buf_png.getvalue()

    @classmethod
    def tearDownClass(cls) -> None:
        async def drop_tables() -> None:
            async with cls.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await cls.engine.dispose()

        asyncio.run(drop_tables())

    def setUp(self) -> None:
        # Reset database tables and in-memory storage for each test
        async def reset_db() -> None:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)

        asyncio.run(reset_db())
        self.storage_backend._storage.clear()
        self.storage_backend._metadata.clear()

        # Dependency override for database session
        async def override_get_db():
            async with self.session_maker() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db

        # Patch storage_service in media_ingestion module
        self.storage_patcher = patch(
            "app.services.media_ingestion.storage_service",
            self.mock_storage_service,
        )
        self.storage_patcher.start()

        self.client = TestClient(app)


    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.storage_patcher.stop()

    # ============================================================
    # POST /api/v1/media TESTS (Section 14 & 26.F)
    # ============================================================

    def test_post_media_successful_upload(self) -> None:
        """Uploading valid JPEG returns HTTP 201 Created and structured ingestion record."""
        files = {"file": ("test_upload.jpg", io.BytesIO(self.jpg_bytes), "image/jpeg")}
        response = self.client.post("/api/v1/media", files=files)

        self.assertEqual(response.status_code, 201)
        data = response.json()

        self.assertIn("media_id", data)
        self.assertIn("sha256_digest", data)
        self.assertEqual(data["media_category"], "image")
        self.assertEqual(data["mime_type"], "image/jpeg")
        self.assertEqual(data["size_bytes"], len(self.jpg_bytes))
        self.assertEqual(data["validation_status"], "accepted")
        self.assertEqual(data["is_duplicate"], False)
        self.assertIn("analysis", data)
        self.assertEqual(data["analysis"]["container"]["width"], 30)
        self.assertEqual(data["analysis"]["container"]["height"], 30)

    def test_post_media_duplicate_ingestion(self) -> None:
        """Uploading identical bytes returns HTTP 200 with duplicate flag without second storage."""
        files1 = {"file": ("orig.png", io.BytesIO(self.png_bytes), "image/png")}
        resp1 = self.client.post("/api/v1/media", files=files1)
        self.assertEqual(resp1.status_code, 201)
        orig_id = resp1.json()["media_id"]

        files2 = {"file": ("copy.png", io.BytesIO(self.png_bytes), "image/png")}
        resp2 = self.client.post("/api/v1/media", files=files2)
        self.assertEqual(resp2.status_code, 200)
        dup_data = resp2.json()

        self.assertEqual(dup_data["media_id"], orig_id)
        self.assertEqual(dup_data["is_duplicate"], True)

    def test_post_media_unsupported_media_type(self) -> None:
        """Uploading unsupported format (e.g. .txt) returns HTTP 415 RFC-7807 error."""
        files = {"file": ("document.txt", io.BytesIO(b"Hello plain text file"), "text/plain")}
        response = self.client.post("/api/v1/media", files=files)

        self.assertEqual(response.status_code, 415)
        data = response.json()
        self.assertEqual(data["status"], 415)
        self.assertEqual(data["title"], "Unsupported Media Type")
        self.assertIn("type", data)
        self.assertIn("detail", data)

    def test_post_media_empty_content(self) -> None:
        """Uploading empty 0-byte file returns HTTP 422 RFC-7807 error."""
        files = {"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")}
        response = self.client.post("/api/v1/media", files=files)

        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertEqual(data["status"], 422)
        self.assertEqual(data["title"], "Malformed Media")

    def test_post_media_malformed_content(self) -> None:
        """Uploading corrupt/spoofed image content returns HTTP 422 RFC-7807 error."""
        corrupt_bytes = b"NOT_A_VALID_HEADER" + (b"\x00" * 40)
        files = {"file": ("corrupt.jpg", io.BytesIO(corrupt_bytes), "image/jpeg")}
        response = self.client.post("/api/v1/media", files=files)

        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertEqual(data["status"], 422)

    def test_post_media_oversized_file(self) -> None:
        """Uploading payload larger than MEDIA_MAX_UPLOAD_SIZE_MB returns HTTP 413 error."""
        # Temporarily patch configured max size to small value
        with patch.object(settings, "MEDIA_MAX_UPLOAD_SIZE_MB", 0.0001):
            large_bytes = b"\xff\xd8\xff\xe0" + (b"\x00" * 2000)
            files = {"file": ("large.jpg", io.BytesIO(large_bytes), "image/jpeg")}
            response = self.client.post("/api/v1/media", files=files)

            self.assertEqual(response.status_code, 413)
            data = response.json()
            self.assertEqual(data["status"], 413)
            self.assertEqual(data["title"], "File Too Large")

    def test_post_media_content_length_early_guard(self) -> None:
        """Requests with Content-Length exceeding max upload limit are rejected early with HTTP 413."""
        with patch.object(settings, "MEDIA_MAX_UPLOAD_SIZE_MB", 0.001):
            headers = {"Content-Length": "9999999"}
            files = {"file": ("large.jpg", io.BytesIO(self.jpg_bytes), "image/jpeg")}
            response = self.client.post("/api/v1/media", files=files, headers=headers)
            self.assertEqual(response.status_code, 413)
            self.assertEqual(response.json()["title"], "File Too Large")

    def test_post_media_missing_file_field(self) -> None:
        """Posting multipart data without 'file' field returns HTTP 422 error."""
        response = self.client.post("/api/v1/media", data={"other_field": "val"})
        self.assertEqual(response.status_code, 422)


    # ============================================================
    # GET /api/v1/media/{media_id} TESTS (Section 15 & 26.F)
    # ============================================================

    def test_get_media_existing_record(self) -> None:
        """Querying an existing media_id returns HTTP 200 and structured record without binary bytes."""
        files = {"file": ("test_get.jpg", io.BytesIO(self.jpg_bytes), "image/jpeg")}
        post_resp = self.client.post("/api/v1/media", files=files)
        media_id = post_resp.json()["media_id"]

        get_resp = self.client.get(f"/api/v1/media/{media_id}")
        self.assertEqual(get_resp.status_code, 200)
        data = get_resp.json()

        self.assertEqual(data["media_id"], media_id)
        self.assertEqual(data["validation_status"], "accepted")
        self.assertIn("analysis", data)
        # Ensure binary file content is NOT returned
        self.assertNotIn("content", data)
        self.assertNotIn("bytes", data)

    def test_get_media_unknown_id(self) -> None:
        """Querying nonexistent UUID returns HTTP 404 RFC-7807 error."""
        random_uuid = str(uuid.uuid4())
        response = self.client.get(f"/api/v1/media/{random_uuid}")

        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["status"], 404)
        self.assertEqual(data["title"], "Media Not Found")

    def test_get_media_invalid_uuid_string(self) -> None:
        """Querying malformed non-UUID string safely returns HTTP 404 RFC-7807 error."""
        response = self.client.get("/api/v1/media/not-a-valid-uuid-string")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["status"], 404)

    # ============================================================
    # 26.G: SECURITY VERIFICATION
    # ============================================================

    def test_api_responses_never_expose_secrets(self) -> None:
        """Responses must never contain secrets, internal DB urls, passwords, or MinIO keys."""
        files = {"file": ("security_check.png", io.BytesIO(self.png_bytes), "image/png")}
        resp = self.client.post("/api/v1/media", files=files)
        raw_text = resp.text

        # Verify forbidden strings
        self.assertNotIn("minioadmin", raw_text)
        self.assertNotIn(settings.MINIO_SECRET_KEY, raw_text)
        self.assertNotIn(settings.POSTGRES_PASSWORD, raw_text)
        self.assertNotIn("postgresql://", raw_text)
        self.assertNotIn("sqlite://", raw_text)
        self.assertNotIn("Traceback", raw_text)


if __name__ == "__main__":
    unittest.main()
