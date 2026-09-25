"""Data-access repository for ModelPredictionRecord entities (Section 15).

Maintains clean separation between SQL queries and application logic.
Transactions are bounded explicitly by callers or session context.
"""

from typing import List, Optional, Union
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import ModelPredictionRecord


class PredictionRepository:
    """Repository handling CRUD persistence for ModelPredictionRecord."""

    async def get_by_id(
        self, session: AsyncSession, prediction_id: Union[uuid.UUID, str]
    ) -> Optional[ModelPredictionRecord]:
        """Fetch model prediction by unique UUID."""
        if isinstance(prediction_id, str):
            try:
                prediction_id = uuid.UUID(prediction_id)
            except ValueError:
                return None

        stmt = select(ModelPredictionRecord).where(ModelPredictionRecord.id == prediction_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_media_id(
        self, session: AsyncSession, media_id: Union[uuid.UUID, str]
    ) -> List[ModelPredictionRecord]:
        """Fetch all model predictions associated with a media asset, sorted newest first."""
        if isinstance(media_id, str):
            try:
                media_id = uuid.UUID(media_id)
            except ValueError:
                return []

        stmt = (
            select(ModelPredictionRecord)
            .where(ModelPredictionRecord.media_id == media_id)
            .order_by(ModelPredictionRecord.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self, session: AsyncSession, record: ModelPredictionRecord
    ) -> ModelPredictionRecord:
        """Persist a new model prediction record."""
        session.add(record)
        await session.flush()
        return record


prediction_repository = PredictionRepository()
