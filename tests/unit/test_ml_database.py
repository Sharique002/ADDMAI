"""Unit tests for ModelPredictionRecord entity, check constraints, and repository (Stage 3).

Conforms to Section 15 of Stage 3 specifications.
"""

from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import uuid

root_dir = Path(__file__).resolve().parent.parent.parent
api_dir = root_dir / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.media import MediaRecord
from app.models.prediction import ModelPredictionRecord
from app.repositories.media import media_repository
from app.repositories.prediction import prediction_repository


class TestModelPredictionDatabase(unittest.IsolatedAsyncioTestCase):
    """Test suite covering model_predictions table, check constraints, foreign keys, and repository CRUD."""

    async def asyncSetUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(self.temp_dir, "test_pred.db")
        self.engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)
        async with self.engine.begin() as conn:
            await conn.execute(text("PRAGMA journal_mode=WAL;"))
            await conn.execute(text("PRAGMA foreign_keys=ON;"))
            await conn.run_sync(Base.metadata.create_all)

        self.session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create parent media record for foreign key testing
        self.media_id = uuid.uuid4()
        async with self.session_maker() as session:
            parent = MediaRecord(
                id=self.media_id,
                sha256_digest="e" * 64,
                media_category="image",
                mime_type="image/png",
                original_filename="test.png",
                size_bytes=1024,
                storage_key="media/original/" + "e" * 64,
                validation_status="accepted",
            )
            await media_repository.create(session, parent)
            await session.commit()

    async def asyncTearDown(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    async def test_schema_contains_model_predictions_columns(self) -> None:
        """Database schema contains model_predictions table with all required columns."""
        async with self.engine.connect() as conn:
            cols = await conn.run_sync(
                lambda sync_conn: sync_conn.dialect.get_columns(sync_conn, "model_predictions")
            )
            col_names = {c["name"] for c in cols}
            expected = {
                "id",
                "media_id",
                "model_id",
                "model_version",
                "prediction",
                "confidence",
                "preprocessing_version",
                "model_artifact_sha256",
                "created_at",
            }
            self.assertTrue(expected.issubset(col_names))

    async def test_successful_prediction_persistence_and_retrieval(self) -> None:
        """Model prediction record persists and can be queried by ID and media_id."""
        pred_id = uuid.uuid4()
        async with self.session_maker() as session:
            record = ModelPredictionRecord(
                id=pred_id,
                media_id=self.media_id,
                model_id="addmai-deepfake-detector",
                model_version="1.0.0",
                prediction="REAL",
                confidence=0.875,
                preprocessing_version="1.0.0",
                model_artifact_sha256="0" * 64,
                created_at=datetime.now(timezone.utc),
            )
            await prediction_repository.create(session, record)
            await session.commit()

        async with self.session_maker() as session:
            fetched = await prediction_repository.get_by_id(session, pred_id)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.prediction, "REAL")
            self.assertAlmostEqual(fetched.confidence, 0.875)

            by_media = await prediction_repository.get_by_media_id(session, self.media_id)
            self.assertEqual(len(by_media), 1)
            self.assertEqual(by_media[0].id, pred_id)

    async def test_check_constraint_invalid_prediction_rejected(self) -> None:
        """Prediction outside ('REAL', 'DEEPFAKE') violates check constraint."""
        async with self.session_maker() as session:
            invalid_record = ModelPredictionRecord(
                id=uuid.uuid4(),
                media_id=self.media_id,
                model_id="addmai-deepfake-detector",
                model_version="1.0.0",
                prediction="LIKELY_AUTHENTIC",  # PROHIBITED in Stage 3!
                confidence=0.9,
                preprocessing_version="1.0.0",
                model_artifact_sha256="0" * 64,
            )
            session.add(invalid_record)
            with self.assertRaises(IntegrityError):
                await session.commit()
            await session.rollback()

    async def test_check_constraint_confidence_out_of_bounds_rejected(self) -> None:
        """Confidence score outside [0.0, 1.0] violates check constraint."""
        async with self.session_maker() as session:
            # Over 1.0
            bad_record = ModelPredictionRecord(
                id=uuid.uuid4(),
                media_id=self.media_id,
                model_id="addmai-deepfake-detector",
                model_version="1.0.0",
                prediction="DEEPFAKE",
                confidence=1.5,  # Invalid
                preprocessing_version="1.0.0",
                model_artifact_sha256="0" * 64,
            )
            session.add(bad_record)
            with self.assertRaises(IntegrityError):
                await session.commit()
            await session.rollback()

            # Under 0.0
            bad_record2 = ModelPredictionRecord(
                id=uuid.uuid4(),
                media_id=self.media_id,
                model_id="addmai-deepfake-detector",
                model_version="1.0.0",
                prediction="REAL",
                confidence=-0.1,  # Invalid
                preprocessing_version="1.0.0",
                model_artifact_sha256="0" * 64,
            )
            session.add(bad_record2)
            with self.assertRaises(IntegrityError):
                await session.commit()
            await session.rollback()


if __name__ == "__main__":
    unittest.main()
