"""Central Media-Type Registry conforming to Sections 4 & 5 of Stage 2.

Defines supported media formats, MIME types, categories, and magic-byte signatures.
Treats all uploaded media as untrusted input.
"""

from dataclasses import dataclass
from enum import Enum
import os
from typing import Dict, List, Optional, Set


class MediaCategory(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


@dataclass(frozen=True)
class MediaTypeDefinition:
    """Specification of a supported media format."""
    name: str
    category: MediaCategory
    mime_type: str
    extensions: Set[str]
    is_supported: bool
    magic_signature_description: str


# Initial Supported Media Registry (Section 4)
SUPPORTED_MEDIA_TYPES: Dict[str, MediaTypeDefinition] = {
    "image/jpeg": MediaTypeDefinition(
        name="JPEG Image",
        category=MediaCategory.IMAGE,
        mime_type="image/jpeg",
        extensions={".jpg", ".jpeg"},
        is_supported=True,
        magic_signature_description="Standard JPEG SOI marker (0xFFD8FF)",
    ),
    "image/png": MediaTypeDefinition(
        name="PNG Image",
        category=MediaCategory.IMAGE,
        mime_type="image/png",
        extensions={".png"},
        is_supported=True,
        magic_signature_description="Standard PNG 8-byte header (0x89504E470D0A1A0A)",
    ),
    "video/mp4": MediaTypeDefinition(
        name="MP4 Video",
        category=MediaCategory.VIDEO,
        mime_type="video/mp4",
        extensions={".mp4"},
        is_supported=True,
        magic_signature_description="ISO Base Media File Format with 'ftyp' box signature",
    ),
}

# Extension to MIME lookup
EXTENSION_TO_MIME: Dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".mp4": "video/mp4",
}


class MediaValidationError(Exception):
    """Base exception for media validation errors."""
    pass


class UnsupportedMediaTypeError(MediaValidationError):
    """Raised when the media extension or MIME type is unsupported (HTTP 415)."""
    pass


class EmptyMediaError(MediaValidationError):
    """Raised when an empty file (0 bytes) is uploaded (HTTP 422)."""
    pass


class MalformedMediaError(MediaValidationError):
    """Raised when media bytes are corrupted or fail magic byte validation (HTTP 422)."""
    pass


class FileTooLargeError(MediaValidationError):
    """Raised when the uploaded media exceeds configured size limit (HTTP 413)."""
    pass


def sniff_magic_bytes(content: bytes) -> Optional[str]:
    """Sniff content byte signature to verify actual media format."""
    if len(content) < 8:
        return None

    # JPEG signature: 0xFF, 0xD8, 0xFF
    if content.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"

    # PNG signature: 0x89, 'P', 'N', 'G', 0x0D, 0x0A, 0x1A, 0x0A
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"

    # MP4 ISO container signature: contains 'ftyp' in first 32 bytes (typically bytes 4-8)
    if len(content) >= 12 and (content[4:8] == b"ftyp" or b"ftyp" in content[:32]):
        return "video/mp4"

    return None


def validate_media_type(filename: str, content: bytes, declared_mime: Optional[str] = None) -> MediaTypeDefinition:
    """Validate media filename and byte content against the central registry.

    Enforces:
    - Non-empty content
    - Whitelisted extension
    - Content magic byte verification matching extension
    """
    if not content or len(content) == 0:
        raise EmptyMediaError("Uploaded media file is empty (0 bytes).")

    _, ext = os.path.splitext(filename.lower())
    if not ext or ext not in EXTENSION_TO_MIME:
        raise UnsupportedMediaTypeError(
            f"Unsupported file extension '{ext or 'unknown'}'. Supported: .jpg, .jpeg, .png, .mp4"
        )

    expected_mime = EXTENSION_TO_MIME[ext]
    media_def = SUPPORTED_MEDIA_TYPES.get(expected_mime)
    if not media_def or not media_def.is_supported:
        raise UnsupportedMediaTypeError(f"Media format for extension '{ext}' is not supported.")

    # Sniff magic bytes from actual content
    sniffed_mime = sniff_magic_bytes(content)
    if not sniffed_mime:
        raise MalformedMediaError(
            f"Malformed media file: Content does not possess valid magic byte signatures for '{ext}'."
        )

    if sniffed_mime != expected_mime:
        raise MalformedMediaError(
            f"MIME mismatch: File extension '{ext}' implies '{expected_mime}', "
            f"but content bytes match '{sniffed_mime}'."
        )

    return media_def
