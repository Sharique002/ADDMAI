"""Typed configuration management for ADDMAI API.

Conforms to Stage 1 requirements (Section 6) and Stage 0 Constitution.
Reads environment variables with support for .env files.
"""

from functools import lru_cache
import json
import os
from typing import Any, List, Union

try:
    from pydantic import Field, field_validator
    from pydantic_settings import BaseSettings, SettingsConfigDict
    HAS_PYDANTIC = True
except ImportError:  # pragma: no cover
    HAS_PYDANTIC = False


if HAS_PYDANTIC:
    class Settings(BaseSettings):
        """Typed backend settings conforming to Stage 1 specifications."""

        # Application Identity
        APP_NAME: str = "ADDMAI API"
        APP_ENV: str = "development"
        APP_VERSION: str = "0.1.0"
        API_V1_STR: str = "/api/v1"
        LOG_LEVEL: str = "INFO"

        # Database Configuration
        DATABASE_URL: str = "postgresql+asyncpg://addmai:addmai_dev_password@localhost:5432/addmai"

        # Redis Task Broker & Cache
        REDIS_URL: str = "redis://localhost:6379/0"

        # MinIO S3-Compatible Object Storage
        MINIO_ENDPOINT: str = "http://localhost:9000"
        MINIO_ACCESS_KEY: str = "minioadmin"
        MINIO_SECRET_KEY: str = "minioadmin"
        MINIO_BUCKET: str = "addmai-uploads"
        MINIO_CONSOLE_URL: str = "http://localhost:9001"

        # CORS Configuration
        CORS_ALLOWED_ORIGINS: List[str] = [
            "http://localhost:3000",
            "http://localhost:5173",
        ]

        @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
        @classmethod
        def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
            if isinstance(v, str):
                v_clean = v.strip()
                if v_clean.startswith("[") and v_clean.endswith("]"):
                    try:
                        return json.loads(v_clean)
                    except json.JSONDecodeError:
                        pass
                return [origin.strip() for origin in v_clean.split(",") if origin.strip()]
            return v

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=True,
            extra="ignore",
        )

else:  # Fallback for lightweight / pre-pip environments
    class Settings:  # type: ignore
        """Fallback settings implementation using Python standard library."""

        def __init__(self) -> None:
            self.APP_NAME = os.getenv("APP_NAME", "ADDMAI API")
            self.APP_ENV = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development"))
            self.APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
            self.API_V1_STR = os.getenv("API_V1_STR", "/api/v1")
            self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

            self.DATABASE_URL = os.getenv(
                "DATABASE_URL",
                "postgresql+asyncpg://addmai:addmai_dev_password@localhost:5432/addmai",
            )
            self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

            self.MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", os.getenv("S3_ENDPOINT_URL", "http://localhost:9000"))
            self.MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", os.getenv("S3_ACCESS_KEY", "minioadmin"))
            self.MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", os.getenv("S3_SECRET_KEY", "minioadmin"))
            self.MINIO_BUCKET = os.getenv("MINIO_BUCKET", os.getenv("S3_BUCKET_UPLOADS", "addmai-uploads"))
            self.MINIO_CONSOLE_URL = os.getenv("MINIO_CONSOLE_URL", "http://localhost:9001")

            raw_cors = os.getenv("CORS_ALLOWED_ORIGINS", '["http://localhost:3000","http://localhost:5173"]')
            if raw_cors.strip().startswith("[") and raw_cors.strip().endswith("]"):
                try:
                    self.CORS_ALLOWED_ORIGINS = json.loads(raw_cors)
                except Exception:
                    self.CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:5173"]
            else:
                self.CORS_ALLOWED_ORIGINS = [i.strip() for i in raw_cors.split(",") if i.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Return cached instance of application settings."""
    return Settings()


settings = get_settings()
