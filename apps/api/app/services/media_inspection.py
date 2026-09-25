"""Container and basic media inspection conforming to Sections 12, 14, 15 of Stage 2.1.

Safely extracts dimensions, container properties, color modes, and duration
without altering bytes or executing untrusted media files.
Enforces resource safety (decompression bomb protection, box boundary limits).
Does NOT perform forensic analysis, ML inference, or authenticity grading.
"""

from io import BytesIO
import struct
from typing import Any, Dict

from PIL import Image, ImageFile

from app.core.media_types import MalformedMediaError

# Enforce strict rejection of truncated images (Section 12)
ImageFile.LOAD_TRUNCATED_IMAGES = False


def inspect_image(content: bytes) -> Dict[str, Any]:
    """Inspect basic image properties using Pillow with resource and parser hardening.

    Extracts width, height, format, and color mode safely.
    Fails cleanly on malformed, corrupted, truncated, or pathological decompression bomb images.
    """
    try:
        # First pass: read headers and properties
        with Image.open(BytesIO(content)) as img:
            width, height = img.size
            img_format = img.format or "UNKNOWN"
            color_mode = img.mode or "UNKNOWN"

            if width <= 0 or height <= 0:
                raise MalformedMediaError("Malformed image: Invalid non-positive dimensions.")

            # Check for EXIF presence safely without modifying content
            has_exif = False
            try:
                exif_data = img.getexif()
                has_exif = bool(exif_data and len(exif_data) > 0)
            except Exception:
                has_exif = False

        # Second pass: verify stream integrity without decoding raster pixels to memory
        with Image.open(BytesIO(content)) as verify_img:
            verify_img.verify()

        return {
            "media_category": "image",
            "format": img_format,
            "width": width,
            "height": height,
            "color_mode": color_mode,
            "exif_present": has_exif,
        }
    except MalformedMediaError:
        raise
    except Image.DecompressionBombError as exc:
        raise MalformedMediaError(
            f"Image dimensions exceed safe resource limits (decompression bomb protection): {exc}"
        ) from exc
    except Exception as exc:
        raise MalformedMediaError(f"Malformed image: Failed to parse image structure ({str(exc)})") from exc


def inspect_mp4_video(content: bytes) -> Dict[str, Any]:
    """Parse ISO Base Media File Format (MP4) container boxes with parser hardening.

    Extracts container format, duration, dimensions, and timescale safely
    without decoding video frames or invoking native FFmpeg binaries.
    Guarantees:
    - Bounded iteration (max 500 boxes) to prevent infinite loops.
    - Strict box size validation (rejects invalid sizes, negative offsets, or buffer overruns).
    - Safe skipping of unknown/unrelated boxes.
    - Requires valid 'ftyp' container box.
    """
    if len(content) < 16:
        raise MalformedMediaError("Malformed MP4: Content is too small to contain a valid container header.")

    offset = 0
    content_len = len(content)
    major_brand = "mp4"
    duration_seconds: float = 0.0
    width: int = 0
    height: int = 0
    timescale: int = 1000
    found_ftyp = False
    found_moov = False
    box_count = 0

    try:
        while offset + 8 <= content_len:
            box_count += 1
            if box_count > 500:
                raise MalformedMediaError("Malformed MP4: Exceeded maximum allowed box count.")

            box_size, box_type = struct.unpack(">I4s", content[offset : offset + 8])
            box_type_str = box_type.decode("latin1", errors="replace")

            if box_size < 8 and box_size not in (0, 1):
                raise MalformedMediaError(f"Malformed MP4: Invalid box size {box_size} in container header.")

            header_size = 8
            if box_size == 1:
                # 64-bit extended box size
                if offset + 16 > content_len:
                    raise MalformedMediaError("Malformed MP4: Truncated 64-bit box header.")
                actual_size = struct.unpack(">Q", content[offset + 8 : offset + 16])[0]
                header_size = 16
                if actual_size < 16:
                    raise MalformedMediaError("Malformed MP4: Invalid 64-bit box size.")
            elif box_size == 0:
                # Extends to end of file
                actual_size = content_len - offset
            else:
                actual_size = box_size

            if offset + actual_size > content_len:
                raise MalformedMediaError("Malformed MP4: Declared box size exceeds content length.")

            payload = content[offset + header_size : offset + actual_size]

            if box_type_str == "ftyp":
                found_ftyp = True
                if len(payload) < 4:
                    raise MalformedMediaError("Malformed MP4: Truncated 'ftyp' box payload.")
                major_brand = payload[:4].decode("latin1", errors="replace").strip()

            elif box_type_str == "moov":
                found_moov = True
                sub_offset = 0
                while sub_offset + 8 <= len(payload):
                    sub_size, sub_type = struct.unpack(">I4s", payload[sub_offset : sub_offset + 8])
                    sub_type_str = sub_type.decode("latin1", errors="replace")

                    if sub_size < 8:
                        raise MalformedMediaError("Malformed MP4: Invalid sub-box size inside 'moov'.")
                    if sub_offset + sub_size > len(payload):
                        raise MalformedMediaError("Malformed MP4: Sub-box in 'moov' exceeds payload length.")

                    sub_payload = payload[sub_offset + 8 : sub_offset + sub_size]

                    if sub_type_str == "mvhd":
                        if len(sub_payload) < 4:
                            raise MalformedMediaError("Malformed MP4: Truncated 'mvhd' header.")
                        version = sub_payload[0]
                        if version == 0:
                            if len(sub_payload) < 20:
                                raise MalformedMediaError("Malformed MP4: Truncated version 0 'mvhd' box.")
                            timescale, raw_dur = struct.unpack(">II", sub_payload[12:20])
                        elif version == 1:
                            if len(sub_payload) < 32:
                                raise MalformedMediaError("Malformed MP4: Truncated version 1 'mvhd' box.")
                            timescale, raw_dur = struct.unpack(">IQ", sub_payload[20:32])
                        if timescale > 0:
                            duration_seconds = round(raw_dur / timescale, 2)

                    elif sub_type_str == "trak":
                        # Search for tkhd inside trak to extract video track dimensions
                        trak_offset = 0
                        while trak_offset + 8 <= len(sub_payload):
                            t_size, t_type = struct.unpack(">I4s", sub_payload[trak_offset : trak_offset + 8])
                            t_type_str = t_type.decode("latin1", errors="replace")

                            if t_size < 8:
                                raise MalformedMediaError("Malformed MP4: Invalid sub-box size inside 'trak'.")
                            if trak_offset + t_size > len(sub_payload):
                                raise MalformedMediaError("Malformed MP4: Sub-box in 'trak' exceeds payload length.")

                            if t_type_str == "tkhd":
                                tkhd_data = sub_payload[trak_offset + 8 : trak_offset + t_size]
                                if len(tkhd_data) < 4:
                                    raise MalformedMediaError("Malformed MP4: Truncated 'tkhd' header.")
                                tkhd_ver = tkhd_data[0]
                                if tkhd_ver == 0 and len(tkhd_data) >= 84:
                                    w_fixed, h_fixed = struct.unpack(">II", tkhd_data[76:84])
                                    track_w, track_h = int(w_fixed >> 16), int(h_fixed >> 16)
                                    if track_w > 0 and track_h > 0:
                                        width, height = track_w, track_h
                                elif tkhd_ver == 1 and len(tkhd_data) >= 96:
                                    w_fixed, h_fixed = struct.unpack(">II", tkhd_data[88:96])
                                    track_w, track_h = int(w_fixed >> 16), int(h_fixed >> 16)
                                    if track_w > 0 and track_h > 0:
                                        width, height = track_w, track_h

                            trak_offset += t_size

                    sub_offset += sub_size

            # Safely advance offset to next box (unknown boxes like 'free', 'mdat', etc. skipped cleanly)
            offset += actual_size

    except MalformedMediaError:
        raise
    except Exception as exc:
        raise MalformedMediaError(f"Malformed MP4: Corrupted box structure ({str(exc)})") from exc

    if not found_ftyp:
        raise MalformedMediaError("Malformed MP4: Missing required 'ftyp' container box.")

    return {
        "media_category": "video",
        "container_format": "mp4",
        "major_brand": major_brand,
        "width": width,
        "height": height,
        "duration_seconds": duration_seconds,
        "timescale": timescale,
    }


def inspect_media_container(category: str, content: bytes) -> Dict[str, Any]:
    """Route container inspection based on media category."""
    if category == "image":
        return inspect_image(content)
    elif category == "video":
        return inspect_mp4_video(content)
    else:
        raise MalformedMediaError(f"Unknown media category '{category}'")
