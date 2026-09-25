"""Data-access repository for MediaRecord entities (Section 13 & 25).

Maintains clean separation between SQL queries and application logic.
Transactions are bounded explicitly by callers or session context.
"""

from typing import Optional, Union
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import MediaRecord


class MediaRepository:
    """Repository handling CRUD persistence for MediaRecord."""

    async def get_by_id(
        self, session: AsyncSession, media_id: Union[uuid.UUID, str]
    ) -> Optional[MediaRecord]:
        """Fetch media record by its unique UUID."""
        if isinstance(media_id, str):
            try:
                media_id = uuid.UUID(media_id)
            except ValueError:
                return None

        stmt = select(MediaRecord).where(MediaRecord.id == media_id)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_sha256(
        self, session: AsyncSession, sha256_digest: str
    ) -> Optional[MediaRecord]:
        """Fetch media record by exact SHA-256 byte digest."""
        stmt = select(MediaRecord).where(
            MediaRecord.sha256_digest == sha256_digest.lower()
        )
        result = await session.execute(stmt)
        return result.scalars().first()

    async def create(
        self, session: AsyncSession, record: MediaRecord
    ) -> MediaRecord:
        """Persist a new media record."""
        session.add(record)
        await session.flush()
        return record


media_repository = MediaRepository()
