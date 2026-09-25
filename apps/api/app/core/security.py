"""Core security utilities and validation helpers."""

import os
import re
import uuid
from typing import Set

ALLOWED_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".mp4"}


def generate_request_id() -> str:
    """Generate a unique request tracking ID."""
    return f"req_{uuid.uuid4().hex[:12]}"


def sanitize_filename(filename: str) -> str:
    """Sanitize user-provided filename to prevent path traversal."""
    if not filename:
        return "unnamed_asset"
    basename = os.path.basename(filename)
    clean_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", basename)
    return re.sub(r"\.{2,}", ".", clean_name) or "unnamed_asset"
