"""Media ingestion and retrieval API router (Stage 2).

Conforms to Sections 14, 15, 16, 21, 22, 23 of Stage 2 specifications.
Exposes POST /api/v1/media and GET /api/v1/media/{media_id}.
"""

import logging
from typing import Any
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.media_types import (
    EmptyMediaError,
    FileTooLargeError,
    MalformedMediaError,
    UnsupportedMediaTypeError,
)
from app.db.session import get_db
from app.repositories.media import media_repository
from app.schemas.media import (
    EvidenceItem,
    IntegrityRecord,
    MediaErrorResponse,
    MediaIngestionResponse,
    MediaResponse,
)
from app.schemas.prediction import ModelPredictionResponse
from app.services.detection import (
    DetectionError,
    IntegrityVerificationError,
    MediaNotFoundError,
    StorageObjectNotFoundError,
    UnsupportedMediaCategoryError,
    detection_service,
)
from app.services.media_ingestion import media_ingestion_service
from ml.inference.model_loader import ModelSecurityError
from ml.preprocessing.preprocessor import PreprocessingError

logger = logging.getLogger("addmai.api.media")

router = APIRouter()


def _build_error_response(
    request: Request,
    status_code: int,
    error_type: str,
    title: str,
    detail: str,
) -> JSONResponse:
    """Construct RFC-7807 compliant structured error response (Section 23)."""
    return JSONResponse(
        status_code=status_code,
        content={
            "type": f"https://api.addmai.local/errors/{error_type}",
            "title": title,
            "status": status_code,
            "detail": detail,
            "instance": request.url.path,
        },
    )


@router.post(
    "",
    response_model=MediaIngestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest untrusted media asset",
    description="Validate, compute SHA-256 digest, store canonical bytes, and record media asset.",
    responses={
        201: {"model": MediaIngestionResponse, "description": "Media accepted and ingested"},
        200: {"model": MediaIngestionResponse, "description": "Duplicate media detected; existing record returned"},
        413: {"model": MediaErrorResponse, "description": "File too large"},
        415: {"model": MediaErrorResponse, "description": "Unsupported media type"},
        422: {"model": MediaErrorResponse, "description": "Empty or malformed media content"},
        500: {"model": MediaErrorResponse, "description": "Internal server error"},
    },
)
async def ingest_media(
    request: Request,
    response: Response,
    file: UploadFile = File(..., description="Multipart binary media file (JPEG, PNG, MP4)"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Ingest uploaded media file, preserving bytes and computing SHA-256 (Section 14 & 23)."""
    max_bytes = settings.media_max_upload_size_bytes

    # 1. Early request-level size guard via Content-Length header (Section 10)
    content_length_header = request.headers.get("content-length")
    if content_length_header:
        try:
            declared_len = int(content_length_header)
            if declared_len > max_bytes:
                return _build_error_response(
                    request,
                    status.HTTP_413_CONTENT_TOO_LARGE,
                    "file-too-large",
                    "File Too Large",
                    f"Request payload size ({declared_len} bytes) exceeds maximum allowed limit of {max_bytes} bytes (25 MB inclusive).",
                )
        except ValueError:
            pass

    try:
        # 2. Bounded chunked streaming read to prevent unbounded memory allocation
        chunks = []
        bytes_read = 0
        chunk_size = 1024 * 1024  # 1 MB chunk

        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            bytes_read += len(chunk)
            if bytes_read > max_bytes:
                raise FileTooLargeError(
                    f"File size exceeds maximum allowed upload limit of {max_bytes} bytes (25 MB inclusive)."
                )
            chunks.append(chunk)

        content = b"".join(chunks)
        raw_filename = file.filename or "unnamed_upload"
        declared_content_type = file.content_type or "application/octet-stream"

        record, analysis, is_duplicate = await media_ingestion_service.ingest_media(
            content=content,
            raw_filename=raw_filename,
            declared_content_type=declared_content_type,
            session=db,
        )


        response.status_code = status.HTTP_200_OK if is_duplicate else status.HTTP_201_CREATED
        return MediaIngestionResponse(
            media_id=str(record.id),
            sha256_digest=record.sha256_digest,
            media_category=record.media_category,
            mime_type=record.mime_type,
            original_filename=record.original_filename,
            size_bytes=record.size_bytes,
            validation_status=record.validation_status,
            created_at=record.created_at.isoformat() if hasattr(record.created_at, "isoformat") else str(record.created_at),
            is_duplicate=is_duplicate,
            analysis=analysis,
        )

    except UnsupportedMediaTypeError as err:
        return _build_error_response(
            request,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "unsupported-media-type",
            "Unsupported Media Type",
            str(err),
        )
    except FileTooLargeError as err:
        return _build_error_response(
            request,
            status.HTTP_413_CONTENT_TOO_LARGE,
            "file-too-large",
            "File Too Large",
            str(err),
        )
    except (EmptyMediaError, MalformedMediaError) as err:
        return _build_error_response(
            request,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "malformed-media",
            "Malformed Media",
            str(err),
        )

    except Exception as exc:
        logger.error(f"Unexpected media ingestion failure: {exc}", exc_info=False)
        return _build_error_response(
            request,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal-error",
            "Internal Server Error",
            "An unexpected error occurred during media ingestion. Original bytes were not persisted.",
        )


@router.get(
    "/{media_id}",
    response_model=MediaIngestionResponse,
    summary="Retrieve structured media ingestion record",
    description="Retrieve structured ingestion and evidence record by system media_id (Section 15).",
    responses={
        200: {"model": MediaIngestionResponse, "description": "Media record retrieved successfully"},
        404: {"model": MediaErrorResponse, "description": "Media not found"},
    },
)
async def get_media_record(
    media_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve structured ingestion record by media_id without exposing original bytes."""
    try:
        media_uuid = uuid.UUID(media_id)
    except (ValueError, AttributeError):
        return _build_error_response(
            request,
            status.HTTP_404_NOT_FOUND,
            "media-not-found",
            "Media Not Found",
            f"Media with ID '{media_id}' was not found in the ingestion catalog.",
        )

    record = await media_repository.get_by_id(db, media_uuid)
    if not record:
        return _build_error_response(
            request,
            status.HTTP_404_NOT_FOUND,
            "media-not-found",
            "Media Not Found",
            f"Media with ID '{media_id}' was not found in the ingestion catalog.",
        )

    # Reconstruct container and neutral evidence observations
    container_info = {
        "media_category": record.media_category,
        "format": record.mime_type.split("/")[-1].upper(),
        "mime_type": record.mime_type,
        "size_bytes": record.size_bytes,
    }
    evidence = [
        EvidenceItem(
            evidence_type="CRYPTOGRAPHIC_HASH",
            source="addmai.ingestion.hasher",
            value={"algorithm": "SHA-256", "digest": record.sha256_digest},
            observed_at=record.created_at.isoformat() if hasattr(record.created_at, "isoformat") else str(record.created_at),
        ),
        EvidenceItem(
            evidence_type="MEDIA_TYPE",
            source="addmai.ingestion.validator",
            value={"mime_type": record.mime_type, "category": record.media_category},
            observed_at=record.created_at.isoformat() if hasattr(record.created_at, "isoformat") else str(record.created_at),
        ),
    ]

    analysis = media_ingestion_service.build_analysis_record(record, container_info, evidence)

    return MediaIngestionResponse(
        media_id=str(record.id),
        sha256_digest=record.sha256_digest,
        media_category=record.media_category,
        mime_type=record.mime_type,
        original_filename=record.original_filename,
        size_bytes=record.size_bytes,
        validation_status=record.validation_status,
        created_at=record.created_at.isoformat() if hasattr(record.created_at, "isoformat") else str(record.created_at),
        is_duplicate=False,
        analysis=analysis,
    )


@router.post(
    "/{media_id}/detect",
    response_model=ModelPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute AI deepfake detection model on media asset (Stage 3)",
    description="Retrieve canonical media asset, execute deterministic preprocessing and AI inference, and return structured model prediction.",
    responses={
        200: {"model": ModelPredictionResponse, "description": "AI model prediction computed successfully"},
        404: {"model": MediaErrorResponse, "description": "Media not found"},
        415: {"model": MediaErrorResponse, "description": "Unsupported media category for detection (e.g. video in Stage 3)"},
        422: {"model": MediaErrorResponse, "description": "Malformed or unprocessable media content"},
        500: {"model": MediaErrorResponse, "description": "Internal model, storage, or integrity error"},
    },
)
async def detect_media(
    request: Request,
    media_id: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Execute AI deepfake detection on a canonical media asset (Section 16 & 17)."""
    try:
        prediction_resp = await detection_service.detect(media_id, db)
        return prediction_resp
    except MediaNotFoundError as err:
        return _build_error_response(
            request,
            status.HTTP_404_NOT_FOUND,
            "media-not-found",
            "Media Not Found",
            str(err),
        )
    except UnsupportedMediaCategoryError as err:
        return _build_error_response(
            request,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "unsupported-media-type",
            "Unsupported Media Type for AI Detection",
            str(err),
        )
    except PreprocessingError as err:
        return _build_error_response(
            request,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "malformed-media-content",
            "Malformed Media Content",
            f"Media asset could not be preprocessed for inference: {str(err)}",
        )
    except (StorageObjectNotFoundError, IntegrityVerificationError) as err:
        logger.error(f"Integrity/storage failure during detection on media '{media_id}': {err}")
        return _build_error_response(
            request,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "storage-integrity-error",
            "Storage Integrity Failure",
            str(err),
        )
    except ModelSecurityError as err:
        logger.error(f"Model security failure during detection on media '{media_id}': {err}")
        return _build_error_response(
            request,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "model-security-error",
            "Model Security Failure",
            "The detection model could not be loaded due to an artifact security or configuration error.",
        )
    except Exception as exc:
        logger.error(f"Unexpected internal failure during detection on media '{media_id}': {exc}")
        return _build_error_response(
            request,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal-detection-error",
            "Internal Detection Error",
            "An unexpected error occurred while executing the AI detection engine.",
        )

