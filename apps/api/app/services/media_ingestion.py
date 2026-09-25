"""Media Ingestion Service orchestrating validation, integrity, storage, and persistence (Stage 2).

Conforms to Sections 3, 7, 8, 11, 16, 24, 25 of Stage 2 specifications.
Guarantees byte preservation, deterministic SHA-256 computation,
duplicate deduplication, and transactional consistency.
"""

from datetime import datetime, timezone
import hashlib
import logging
from typing import Any, Dict, Tuple
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.media_types import (
    EmptyMediaError,
    FileTooLargeError,
    MalformedMediaError,
    UnsupportedMediaTypeError,
    validate_media_type,
)
from app.core.security import sanitize_filename
from app.models.media import MediaRecord
from app.repositories.media import media_repository
from app.schemas.media import AnalysisRecord, IntegrityRecord, MediaResponse
from app.services.media_inspection import inspect_media_container
from app.services.metadata import metadata_service
from app.services.storage import storage_service

logger = logging.getLogger("addmai.media_ingestion")


class MediaIngestionService:
    """Service encapsulating end-to-end media ingestion workflows."""

    @staticmethod
    def calculate_sha256(content: bytes) -> str:
        """Calculate deterministic 64-character lowercase hexadecimal SHA-256 digest."""
        digest = hashlib.sha256(content).hexdigest().lower()
        if len(digest) != 64:
            raise RuntimeError("Internal hashing error: Calculated digest length is not 64 characters.")
        return digest

    async def ingest_media(
        self,
        content: bytes,
        raw_filename: str,
        declared_content_type: str,
        session: AsyncSession,
    ) -> Tuple[MediaRecord, AnalysisRecord, bool]:
        """Ingest, validate, hash, store, and persist an untrusted media file.

        Returns:
            Tuple of (MediaRecord, AnalysisRecord, is_duplicate: bool)
        """
        # 1. Validation (Section 5 & 6)
        if not content or len(content) == 0:
            raise EmptyMediaError("Uploaded media file is empty (0 bytes).")

        max_bytes = settings.media_max_upload_size_bytes
        if len(content) > max_bytes:
            raise FileTooLargeError(
                f"File size ({len(content)} bytes) exceeds configured maximum allowed limit of {max_bytes} bytes."
            )

        clean_filename = sanitize_filename(raw_filename)
        media_def = validate_media_type(clean_filename, content, declared_content_type)

        # 2. Cryptographic Integrity: SHA-256 (Section 8)
        sha256_digest = self.calculate_sha256(content)

        # 3. Deduplication Check (Section 12 & 16: ONE SHA-256 -> ONE canonical original object)
        existing_record = await media_repository.get_by_sha256(session, sha256_digest)
        if existing_record:
            logger.info(
                f"Duplicate media detected for SHA-256 {sha256_digest}. Reusing existing record {existing_record.id}."
            )
            container_info = inspect_media_container(existing_record.media_category, content)
            evidence = metadata_service.build_evidence_items(
                sha256_digest=sha256_digest,
                size_bytes=existing_record.size_bytes,
                mime_type=existing_record.mime_type,
                category=existing_record.media_category,
                container_info=container_info,
                is_duplicate=True,
            )
            analysis = self.build_analysis_record(existing_record, container_info, evidence)
            return existing_record, analysis, True

        # 4. Container Inspection (Section 17, 18, 19)
        container_info = inspect_media_container(media_def.category.value, content)

        # 5. Store Original in Object Storage (Section 9)
        storage_key = storage_service.get_deterministic_key(sha256_digest)
        await storage_service.store_original(
            sha256_digest=sha256_digest,
            data=content,
            content_type=media_def.mime_type,
            original_filename=clean_filename,
        )

        # 6. Database Persistence within explicit transaction boundary (Section 24 & 25)
        media_id = uuid.uuid4()
        record = MediaRecord(
            id=media_id,
            sha256_digest=sha256_digest,
            media_category=media_def.category.value,
            mime_type=media_def.mime_type,
            original_filename=clean_filename,
            size_bytes=len(content),
            storage_key=storage_key,
            validation_status="accepted",
            created_at=datetime.now(timezone.utc),
        )

        from sqlalchemy.exc import IntegrityError

        try:
            await media_repository.create(session, record)
            await session.commit()
        except IntegrityError:

            # Concurrent duplicate race: another simultaneous request committed the same SHA-256 first
            logger.info(
                f"Concurrent duplicate race detected for SHA-256 {sha256_digest}. Reusing winner's record."
            )
            await session.rollback()
            import asyncio
            existing_winner = None
            for _ in range(10):
                existing_winner = await media_repository.get_by_sha256(session, sha256_digest)
                if existing_winner:
                    break
                await asyncio.sleep(0.02)

            if existing_winner:
                # Do NOT delete storage object as the winner is using it
                evidence = metadata_service.build_evidence_items(
                    sha256_digest=sha256_digest,
                    size_bytes=existing_winner.size_bytes,
                    mime_type=existing_winner.mime_type,
                    category=existing_winner.media_category,
                    container_info=container_info,
                    is_duplicate=True,
                )
                analysis = self.build_analysis_record(existing_winner, container_info, evidence)
                return existing_winner, analysis, True
            raise RuntimeError("Database integrity error encountered during media ingestion.")

        except Exception as exc:
            logger.error(f"Database persistence failed for media {media_id}. Rolling back: {str(exc)}")
            await session.rollback()
            # Clean up uploaded storage object to prevent orphan storage artifacts (Section 24)
            try:
                await storage_service.delete_object(storage_key)
            except Exception as cleanup_err:
                logger.error(
                    f"Rollback cleanup failed for storage key {storage_key}: {str(cleanup_err)}"
                )
            raise RuntimeError("Failed to persist media ingestion record to database.") from exc


        # 7. Synthesize Evidence and Structured Analysis Record (Section 21 & 22)
        evidence = metadata_service.build_evidence_items(
            sha256_digest=sha256_digest,
            size_bytes=len(content),
            mime_type=media_def.mime_type,
            category=media_def.category.value,
            container_info=container_info,
            is_duplicate=False,
        )
        analysis = self.build_analysis_record(record, container_info, evidence)
        return record, analysis, False

    @staticmethod
    def build_analysis_record(
        record: MediaRecord,
        container_info: Dict[str, Any],
        evidence: list,
    ) -> AnalysisRecord:
        """Construct structured AnalysisRecord from media record and observations."""
        media_resp = MediaResponse(
            media_id=str(record.id),
            sha256_digest=record.sha256_digest,
            media_category=record.media_category,
            mime_type=record.mime_type,
            original_filename=record.original_filename,
            size_bytes=record.size_bytes,
            validation_status=record.validation_status,
            created_at=record.created_at.isoformat() if hasattr(record.created_at, "isoformat") else str(record.created_at),
        )
        integrity = IntegrityRecord(
            sha256_digest=record.sha256_digest,
            algorithm="SHA-256",
            size_bytes=record.size_bytes,
            verified=True,
        )
        metadata_obs = {
            "exif_present": container_info.get("exif_present", False),
            "media_category": record.media_category,
            "format": container_info.get("format") or container_info.get("container_format", "unknown"),
        }

        return AnalysisRecord(
            media_id=str(record.id),
            ingestion=media_resp,
            integrity=integrity,
            container=container_info,
            metadata=metadata_obs,
            evidence=evidence,
        )


media_ingestion_service = MediaIngestionService()
