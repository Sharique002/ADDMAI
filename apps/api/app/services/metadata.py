"""Metadata extraction and neutral evidence synthesis (Sections 20, 21, 22).

Treats metadata strictly as neutral observations.
Absence of metadata never implies manipulation.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

from app.schemas.media import EvidenceItem, IntegrityRecord


class MetadataService:
    """Service producing neutral metadata observations and evidence records."""

    @staticmethod
    def build_evidence_items(
        sha256_digest: str,
        size_bytes: int,
        mime_type: str,
        category: str,
        container_info: Dict[str, Any],
        is_duplicate: bool = False,
    ) -> List[EvidenceItem]:
        """Synthesize neutral evidence items from ingestion observations."""
        now = datetime.now(timezone.utc).isoformat()
        evidence: List[EvidenceItem] = []

        # 1. Cryptographic Hash Evidence
        evidence.append(
            EvidenceItem(
                evidence_type="CRYPTOGRAPHIC_HASH",
                source="sha256_integrity_engine",
                value={
                    "algorithm": "SHA-256",
                    "digest": sha256_digest,
                    "byte_size": size_bytes,
                    "duplicate_canonical_reused": is_duplicate,
                },
                observed_at=now,
            )
        )

        # 2. Media Type & MIME Evidence
        evidence.append(
            EvidenceItem(
                evidence_type="MEDIA_TYPE",
                source="media_registry_validator",
                value={
                    "mime_type": mime_type,
                    "category": category,
                    "is_supported": True,
                },
                observed_at=now,
            )
        )

        # 3. Container & Structural Properties Evidence
        evidence.append(
            EvidenceItem(
                evidence_type="CONTAINER_INFO",
                source="media_inspection_engine",
                value=container_info,
                observed_at=now,
            )
        )

        # 4. Metadata Observations Evidence
        metadata_obs = {
            "exif_present": container_info.get("exif_present", False),
            "dimensions_available": bool(
                container_info.get("width", 0) > 0 and container_info.get("height", 0) > 0
            ),
            "duration_seconds": container_info.get("duration_seconds", 0.0),
        }
        evidence.append(
            EvidenceItem(
                evidence_type="METADATA_OBSERVATION",
                source="metadata_inspector",
                value=metadata_obs,
                observed_at=now,
            )
        )

        return evidence


metadata_service = MetadataService()
