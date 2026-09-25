"""Unit tests for security utilities and logging redaction (Stage 1.1).

Conforms to Section 14, 15, 17C of Stage 1.1 specification.
"""

import logging
from pathlib import Path
import sys
import unittest

# Ensure apps/api is on sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
api_dir = root_dir / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from app.core.logging import SafeFormatter
from app.core.security import generate_request_id, sanitize_filename


class TestSecurityUtilities(unittest.TestCase):
    """Test security utilities conforming to Section 14 & 17C."""

    def test_request_id_format(self) -> None:
        """Verify request ID prefix and structure."""
        req_id = generate_request_id()
        self.assertTrue(req_id.startswith("req_"))
        self.assertTrue(len(req_id) > 10)

    def test_request_id_uniqueness(self) -> None:
        """Verify successive request IDs are unique."""
        ids = {generate_request_id() for _ in range(100)}
        self.assertEqual(len(ids), 100)

    def test_filename_path_traversal(self) -> None:
        """Verify directory traversal sequences are stripped to base name."""
        self.assertEqual(sanitize_filename("../../etc/passwd"), "passwd")
        self.assertEqual(sanitize_filename("..\\..\\windows\\system32\\cmd.exe"), "cmd.exe")

    def test_filename_null_byte_handling(self) -> None:
        """Verify null bytes are stripped cleanly."""
        self.assertEqual(sanitize_filename("test\x00image.png"), "testimage.png")
        self.assertEqual(sanitize_filename("payload\x00.jpg"), "payload.jpg")

    def test_filename_empty_and_dot_handling(self) -> None:
        """Verify empty and dot-only filenames default to unnamed_asset."""
        self.assertEqual(sanitize_filename(""), "unnamed_asset")
        self.assertEqual(sanitize_filename(None), "unnamed_asset")  # type: ignore
        self.assertEqual(sanitize_filename("..."), "unnamed_asset")
        self.assertEqual(sanitize_filename("   "), "unnamed_asset")

    def test_filename_special_character_filtering(self) -> None:
        """Verify dangerous characters are replaced with underscores."""
        self.assertEqual(sanitize_filename("foo$bar;rm.png"), "foo_bar_rm.png")
        self.assertEqual(sanitize_filename("avatar (1).jpeg"), "avatar__1_.jpeg")


class TestLoggingRedaction(unittest.TestCase):
    """Test logging credential redaction conforming to Section 15 & 17."""

    def setUp(self) -> None:
        self.formatter = SafeFormatter(service_name="TEST-API")

    def test_uri_password_redaction(self) -> None:
        """Verify database credentials in connection URIs are masked."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Connected to postgresql+asyncpg://addmai:supersecret123@localhost:5432/addmai",
            args=(),
            exc_info=None,
        )
        formatted = self.formatter.format(record)
        self.assertNotIn("supersecret123", formatted)
        self.assertIn("addmai:[REDACTED]@", formatted)

    def test_key_value_secret_redaction(self) -> None:
        """Verify sensitive key-value pairs are masked in log messages."""
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="User supplied password=TopSecretValue! and api_key: Key999",
            args=(),
            exc_info=None,
        )
        formatted = self.formatter.format(record)
        self.assertNotIn("TopSecretValue!", formatted)
        self.assertNotIn("Key999", formatted)
        self.assertIn("password=[REDACTED]", formatted)
        self.assertIn("api_key: [REDACTED]", formatted)

    def test_utc_timestamp_format(self) -> None:
        """Verify log messages contain formatted UTC timestamps."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Normal operational log message",
            args=(),
            exc_info=None,
        )
        formatted = self.formatter.format(record)
        self.assertIn("UTC", formatted)
        self.assertIn("[INFO   ]", formatted)
        self.assertIn("[TEST-API]", formatted)


if __name__ == "__main__":
    unittest.main()
