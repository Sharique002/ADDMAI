"""Unit tests for typed configuration management (Section 6)."""

import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

# Ensure apps/api is on sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
api_dir = root_dir / "apps" / "api"
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from app.core.config import Settings, get_settings


class TestConfig(unittest.TestCase):
    """Test configuration defaults and environment overrides."""

    def test_default_settings(self) -> None:
        """Verify baseline Stage 1 configuration defaults."""
        settings = Settings()
        self.assertEqual(settings.APP_NAME, "ADDMAI API")
        self.assertEqual(settings.APP_VERSION, "0.1.0")
        self.assertEqual(settings.API_V1_STR, "/api/v1")

        # Infrastructure defaults
        self.assertIn("postgresql", settings.DATABASE_URL)
        self.assertIn("redis", settings.REDIS_URL)
        self.assertEqual(settings.MINIO_BUCKET, "addmai-uploads")

    def test_environment_override(self) -> None:
        """Verify environment variable overrides."""
        with patch.dict(
            os.environ,
            {
                "APP_NAME": "ADDMAI Custom API",
                "APP_ENV": "testing",
                "MINIO_BUCKET": "custom-uploads",
            },
            clear=False,
        ):
            settings = Settings()
            self.assertEqual(settings.APP_NAME, "ADDMAI Custom API")
            self.assertEqual(settings.APP_ENV, "testing")
            self.assertEqual(settings.MINIO_BUCKET, "custom-uploads")

    def test_cors_origins_parsing(self) -> None:
        """Verify CORS origins string and list parsing."""
        settings = Settings()
        self.assertIsInstance(settings.CORS_ALLOWED_ORIGINS, list)
        self.assertTrue(len(settings.CORS_ALLOWED_ORIGINS) >= 1)


if __name__ == "__main__":
    unittest.main()
