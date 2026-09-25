"""Unit tests for typed configuration management (Stage 1.1 Hardened).

Conforms to Section 10 & 17A of Stage 1.1 specification.
Tests defaults, overrides, CORS parsing, wildcard CORS prohibition,
and production credential rejection.
"""

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

from app.core.config import Settings


class TestConfig(unittest.TestCase):
    """Test configuration defaults, environment overrides, and security validations."""

    def test_default_development_settings(self) -> None:
        """Verify baseline Stage 1 development defaults."""
        settings = Settings()
        self.assertEqual(settings.APP_NAME, "ADDMAI API")
        self.assertEqual(settings.APP_ENV, "development")
        self.assertEqual(settings.APP_VERSION, "0.1.0")
        self.assertEqual(settings.API_V1_STR, "/api/v1")

        # Infrastructure defaults
        self.assertIn("postgresql", settings.DATABASE_URL)
        self.assertIn("redis", settings.REDIS_URL)
        self.assertEqual(settings.MINIO_BUCKET, "addmai-uploads")

    def test_environment_override(self) -> None:
        """Verify environment variable overrides take precedence."""
        with patch.dict(
            os.environ,
            {
                "APP_NAME": "ADDMAI Hardened API",
                "APP_ENV": "development",
                "MINIO_BUCKET": "custom-uploads",
            },
            clear=False,
        ):
            settings = Settings()
            self.assertEqual(settings.APP_NAME, "ADDMAI Hardened API")
            self.assertEqual(settings.MINIO_BUCKET, "custom-uploads")

    def test_cors_origins_parsing(self) -> None:
        """Verify CORS origins string and list parsing."""
        settings = Settings(CORS_ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:5173"])
        self.assertIsInstance(settings.CORS_ALLOWED_ORIGINS, list)
        self.assertEqual(len(settings.CORS_ALLOWED_ORIGINS), 2)

    def test_wildcard_cors_prohibition(self) -> None:
        """Verify wildcard CORS origin '*' is strictly rejected."""
        with self.assertRaises(ValueError) as ctx:
            Settings(CORS_ALLOWED_ORIGINS=["*"])
        self.assertIn("Wildcard CORS origin '*' is strictly prohibited", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            Settings(CORS_ALLOWED_ORIGINS='["http://localhost:3000", "*"]')
        self.assertIn("Wildcard CORS origin '*' is strictly prohibited", str(ctx.exception))

    def test_production_insecure_db_password_rejection(self) -> None:
        """Verify production mode rejects default development database password."""
        with self.assertRaises(ValueError) as ctx:
            Settings(
                APP_ENV="production",
                POSTGRES_PASSWORD="addmai_dev_password",
                MINIO_ACCESS_KEY="secure_prod_key",
                MINIO_SECRET_KEY="secure_prod_secret",
            )
        self.assertIn("Insecure development PostgreSQL password detected", str(ctx.exception))

    def test_production_insecure_minio_credentials_rejection(self) -> None:
        """Verify production mode rejects default development MinIO credentials."""
        with self.assertRaises(ValueError) as ctx:
            Settings(
                APP_ENV="production",
                POSTGRES_PASSWORD="secure_prod_password",
                DATABASE_URL="postgresql+asyncpg://addmai:secure_prod_password@localhost:5432/addmai",
                MINIO_ACCESS_KEY="minioadmin",
                MINIO_SECRET_KEY="minioadmin",
            )
        self.assertIn("Insecure development MinIO credentials detected", str(ctx.exception))

    def test_production_valid_configuration(self) -> None:
        """Verify production mode succeeds with explicit secure credentials."""
        settings = Settings(
            APP_ENV="production",
            POSTGRES_PASSWORD="SuperSecretProdPassword!123",
            DATABASE_URL="postgresql+asyncpg://addmai:SuperSecretProdPassword!123@prod-db:5432/addmai",
            MINIO_ACCESS_KEY="ProdMinioAccessKey987",
            MINIO_SECRET_KEY="ProdMinioSecretKey654",
            CORS_ALLOWED_ORIGINS=["https://addmai.org"],
        )
        self.assertEqual(settings.APP_ENV, "production")
        self.assertEqual(settings.POSTGRES_PASSWORD, "SuperSecretProdPassword!123")
        self.assertEqual(settings.MINIO_ACCESS_KEY, "ProdMinioAccessKey987")


if __name__ == "__main__":
    unittest.main()
