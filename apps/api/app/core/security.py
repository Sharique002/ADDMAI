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


def sanitize_filename(filename: str) -> str:
    """Sanitize user-provided filename to prevent path traversal and null-byte injection.

    Ensures:
    - Null bytes are stripped.
    - Directory separators and path traversal are removed via basename extraction.
    - Only safe alphanumeric, underscore, hyphen, and period characters are kept.
    - Multiple consecutive dots are collapsed.
    - Empty, space-only, or dot/underscore-only strings safely default to 'unnamed_asset'.
    """
    if not filename or not isinstance(filename, str) or not filename.strip():
        return "unnamed_asset"

    # 1. Strip null bytes
    clean = filename.replace("\x00", "")

    # 2. Extract basename to defeat path traversal (e.g., ../ or C:\)
    clean = os.path.basename(clean.strip())

    # 3. Filter non-whitelisted characters
    clean = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", clean)

    # 4. Collapse consecutive dots
    clean = re.sub(r"\.{2,}", ".", clean)

    # 5. Strip leading/trailing dots, underscores, and whitespace
    clean_stripped = clean.strip(". _")
    if not clean_stripped:
        return "unnamed_asset"

    return clean.strip(". ") or "unnamed_asset"
