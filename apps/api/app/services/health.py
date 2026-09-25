"""Dependency readiness logic conforming to Section 7 & 8 of Stage 1.1.

Truthfully probes infrastructure services (PostgreSQL, Redis, MinIO) via TCP.
Unit tests mock the probe function; the service itself never reports 'ready'
unless connectivity is verified or mocked.
Never exposes credentials, secrets, or internal connection strings.
"""

from datetime import datetime, timezone
import logging
import socket
from typing import Any, Dict, Tuple
from urllib.parse import urlparse

from app.core.config import Settings

logger = logging.getLogger("addmai.health_service")


def check_tcp_connection(host: str, port: int, timeout: float = 0.5) -> bool:
    """Check TCP connectivity to an infrastructure service host and port."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


class HealthService:
    """Service encapsulating liveness and readiness logic."""

    @staticmethod
    def get_liveness() -> Dict[str, str]:
        """Return truthful liveness probe response."""
        return {"status": "healthy"}

    @staticmethod
    def check_readiness(settings: Settings) -> Tuple[bool, Dict[str, Dict[str, Any]]]:
        """Truthfully evaluate connectivity to all configured infrastructure services.

        Returns:
            Tuple of (all_ready: bool, dependencies: Dict[str, Dict[str, Any]])
        """
        dependencies: Dict[str, Dict[str, Any]] = {}

        # 1. PostgreSQL Probe
        try:
            db_raw = settings.DATABASE_URL
            if not (db_raw.startswith("postgresql://") or db_raw.startswith("postgresql+asyncpg://")):
                raise ValueError("Invalid PostgreSQL URL scheme")

            cleaned_url = db_raw.replace("postgresql+asyncpg://", "http://").replace("postgresql://", "http://")
            parsed_db = urlparse(cleaned_url)
            if not parsed_db.hostname:
                raise ValueError("Missing PostgreSQL hostname in configuration")

            db_host = parsed_db.hostname
            db_port = parsed_db.port or 5432

            is_db_ready = check_tcp_connection(db_host, db_port)
            dependencies["postgres"] = {
                "configured": True,
                "status": "ready" if is_db_ready else "not_ready",
            }
        except Exception:
            logger.warning("PostgreSQL configuration invalid or unreachable", exc_info=False)
            dependencies["postgres"] = {
                "configured": bool(settings.DATABASE_URL),
                "status": "not_ready",
            }

        # 2. Redis Probe
        try:
            redis_raw = settings.REDIS_URL
            if not (redis_raw.startswith("redis://") or redis_raw.startswith("rediss://")):
                raise ValueError("Invalid Redis URL scheme")

            parsed_redis = urlparse(redis_raw)
            if not parsed_redis.hostname:
                raise ValueError("Missing Redis hostname in configuration")

            redis_host = parsed_redis.hostname
            redis_port = parsed_redis.port or 6379

            is_redis_ready = check_tcp_connection(redis_host, redis_port)
            dependencies["redis"] = {
                "configured": True,
                "status": "ready" if is_redis_ready else "not_ready",
            }
        except Exception:
            logger.warning("Redis configuration invalid or unreachable", exc_info=False)
            dependencies["redis"] = {
                "configured": bool(settings.REDIS_URL),
                "status": "not_ready",
            }

        # 3. MinIO Probe
        try:
            minio_raw = settings.MINIO_ENDPOINT
            if not (minio_raw.startswith("http://") or minio_raw.startswith("https://")):
                raise ValueError("Invalid MinIO endpoint scheme")

            parsed_minio = urlparse(minio_raw)
            if not parsed_minio.hostname:
                raise ValueError("Missing MinIO hostname in configuration")

            minio_host = parsed_minio.hostname
            default_port = 443 if parsed_minio.scheme == "https" else 80
            minio_port = parsed_minio.port or default_port

            is_minio_ready = check_tcp_connection(minio_host, minio_port)
            dependencies["minio"] = {
                "configured": True,
                "status": "ready" if is_minio_ready else "not_ready",
            }
        except Exception:
            logger.warning("MinIO configuration invalid or unreachable", exc_info=False)
            dependencies["minio"] = {
                "configured": bool(settings.MINIO_ENDPOINT),
                "status": "not_ready",
            }

        all_ready = all(dep["status"] == "ready" for dep in dependencies.values())
        return all_ready, dependencies


health_service = HealthService()
