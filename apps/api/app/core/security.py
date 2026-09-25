"""Core security utilities and validation helpers (Stage 1.1 Hardened).

Conforms to Section 14 (Security Utility Review) of Stage 1.1 specification.
Provides robust filename sanitization against path traversal, null bytes,
and malformed input, as well as unique request tracking.
"""

import os
import re
import uuid
from typing import Set

ALLOWED_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".mp4"}


def generate_request_id() -> str:
    """Generate a unique request tracking ID."""
    return f"req_{uuid.uuid4().hex[:16]}"


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize user-provided filename to prevent path traversal and null-byte injection.

    Ensures:
    - Null bytes are stripped.
    - Directory separators and path traversal are removed across Unix and Windows.
    - Drive letters (e.g., C:) are stripped.
    - Safe alphanumeric, unicode word characters, underscores, hyphens, and periods are kept.
    - Multiple consecutive dots are collapsed.
    - Empty, space-only, or dot/underscore-only strings safely default to 'unnamed_asset'.
    - Stored length is strictly bounded to max_length (default 255) while preserving extension.
    """
    if not filename or not isinstance(filename, str) or not filename.strip():
        return "unnamed_asset"

    # 1. Strip null bytes
    clean = filename.replace("\x00", "").strip()

    # 2. Normalize Windows drive letters and separators
    clean = re.sub(r"^[a-zA-Z]:", "", clean)
    clean = clean.replace("\\", "/")

    # 3. Extract basename (last path component)
    clean = clean.split("/")[-1]

    # 4. Filter disallowed characters while preserving Unicode words
    clean = re.sub(r"[^\w\-\.]", "_", clean, flags=re.UNICODE)

    # 5. Collapse consecutive dots
    clean = re.sub(r"\.{2,}", ".", clean)

    # 6. Strip leading/trailing dots, underscores, and whitespace
    clean_stripped = clean.strip(". _")
    if not clean_stripped:
        return "unnamed_asset"

    clean = clean_stripped

    # 7. Bound length to max_length preserving extension
    if len(clean) > max_length:
        parts = clean.rsplit(".", 1)
        if len(parts) == 2 and len(parts[1]) <= 10:
            ext = "." + parts[1]
            stem = parts[0][: max_length - len(ext)]
            clean = stem.rstrip(". _") + ext
        else:
            clean = clean[:max_length].rstrip(". _")

    return clean or "unnamed_asset"

