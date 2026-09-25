"""Typed configuration management for ADDMAI API (Stage 1.1 Hardened).

Conforms to Section 10 (Configuration Hardening) of Stage 1.1 specification.
Enforces typed settings, prevents wildcard CORS, and prohibits insecure default
development credentials in production mode.
"""

from functools import lru_cache
import json
import os
from typing import List, Union

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_DEV_DB_PASSWORD = "addmai_dev_password"
INSECURE_DEV_MINIO_CRED = "minioadmin"


class Settings(BaseSettings):
    """Typed backend settings conforming to Stage 1.1 specifications."""

    # Application Identity
    APP_NAME: str = Field(default="ADDMAI API", description="Service display name")
    APP_ENV: str = Field(default="development", description="Runtime environment: development | testing | production")
    APP_VERSION: str = Field(default="0.1.0", description="Semver release")
    API_V1_STR: str = Field(default="/api/v1", description="API version prefix")
    LOG_LEVEL: str = Field(default="INFO", description="Standard logging level")

    # PostgreSQL Relational Database Configuration
    POSTGRES_USER: str = Field(default="addmai", description="PostgreSQL database user")
    POSTGRES_PASSWORD: str = Field(default="addmai_dev_password", description="PostgreSQL database password")
    POSTGRES_DB: str = Field(default="addmai", description="PostgreSQL database name")
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://addmai:addmai_dev_password@localhost:5432/addmai",
        description="Async connection URI for PostgreSQL",
    )

    # Redis Task Queue & Cache
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Connection URI for Redis")

    # MinIO / S3 Object Storage
    MINIO_ENDPOINT: str = Field(default="http://localhost:9000", description="MinIO/S3 API endpoint URL")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin", description="MinIO access key")
    MINIO_SECRET_KEY: str = Field(default="minioadmin", description="MinIO secret key")
    MINIO_BUCKET: str = Field(default="addmai-uploads", description="Default bucket for media uploads")
    MINIO_CONSOLE_URL: str = Field(default="http://localhost:9001", description="MinIO Web Console URL")

    # CORS Configuration
    CORS_ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed web origins. Wildcard '*' is strictly prohibited.",
    )

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def validate_and_parse_cors(cls, v: Union[str, List[str]]) -> List[str]:
        origins: List[str] = []
        if isinstance(v, str):
            v_clean = v.strip()
            if v_clean.startswith("[") and v_clean.endswith("]"):
                try:
                    origins = json.loads(v_clean)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Malformed JSON in CORS_ALLOWED_ORIGINS: {exc}") from exc
            else:
                origins = [origin.strip() for origin in v_clean.split(",") if origin.strip()]
        elif isinstance(v, list):
            origins = v
        else:
            raise ValueError(f"Invalid type for CORS_ALLOWED_ORIGINS: {type(v)}")

        # Hardened security check: Wildcard '*' is prohibited in all environments (Section 10)
        if any(origin.strip() == "*" for origin in origins):
            raise ValueError("Wildcard CORS origin '*' is strictly prohibited for security compliance.")

        return origins

    @model_validator(mode="after")
    def validate_production_credentials(self) -> "Settings":
        """Disallow default development credentials in production environment (Section 10)."""
        if self.APP_ENV.lower() == "production":
            # Check database credentials
            if (
                self.POSTGRES_PASSWORD == INSECURE_DEV_DB_PASSWORD
                or INSECURE_DEV_DB_PASSWORD in self.DATABASE_URL
            ):
                raise ValueError(
                    "Production configuration error: Insecure development PostgreSQL password detected. "
                    "Explicit, secure credentials are required in production."
                )

            # Check MinIO storage credentials
            if (
                self.MINIO_ACCESS_KEY == INSECURE_DEV_MINIO_CRED
                or self.MINIO_SECRET_KEY == INSECURE_DEV_MINIO_CRED
            ):
                raise ValueError(
                    "Production configuration error: Insecure development MinIO credentials detected. "
                    "Explicit, secure credentials are required in production."
                )

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached instance of application settings."""
    return Settings()


settings = get_settings()
