"""Object Storage abstraction layer conforming to Section 9 of Stage 2.

Handles deterministic object-key generation, uploading original bytes,
and metadata persistence without exposing MinIO/S3 credentials to callers.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import logging
from typing import Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("addmai.storage")


class StorageBackend(ABC):
    """Abstract object storage interface."""

    @abstractmethod
    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Upload raw byte data to the storage backend."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check whether an object exists at the specified key."""
        pass

    @abstractmethod
    async def get_metadata(self, key: str) -> Optional[Dict[str, str]]:
        """Retrieve stored object metadata."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete an object by key."""
        pass


class InMemoryStorageBackend(StorageBackend):
    """Deterministic in-memory storage backend for isolated unit testing."""

    def __init__(self) -> None:
        self._storage: Dict[str, bytes] = {}
        self._metadata: Dict[str, Dict[str, str]] = {}

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        self._storage[key] = data
        meta = metadata.copy() if metadata else {}
        meta["content_type"] = content_type
        meta["size_bytes"] = str(len(data))
        meta["uploaded_at"] = datetime.now(timezone.utc).isoformat()
        self._metadata[key] = meta

    async def exists(self, key: str) -> bool:
        return key in self._storage

    async def get_metadata(self, key: str) -> Optional[Dict[str, str]]:
        return self._metadata.get(key)

    async def delete(self, key: str) -> bool:
        if key in self._storage:
            del self._storage[key]
            self._metadata.pop(key, None)
            return True
        return False


class S3MinIOStorageBackend(StorageBackend):
    """S3/MinIO compatible HTTP object storage backend."""

    def __init__(
        self,
        endpoint_url: str,
        bucket_name: str,
        access_key: str,
        secret_key: str,
    ) -> None:
        self.endpoint_url = endpoint_url.rstrip("/")
        self.bucket_name = bucket_name
        self.access_key = access_key
        self.secret_key = secret_key

    def _get_url(self, key: str) -> str:
        return f"{self.endpoint_url}/{self.bucket_name}/{key.lstrip('/')}"

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        headers = {"Content-Type": content_type}
        if metadata:
            for k, v in metadata.items():
                headers[f"x-amz-meta-{k}"] = str(v)

        async with httpx.AsyncClient() as client:
            resp = await client.put(self._get_url(key), content=data, headers=headers)
            if resp.status_code not in (200, 201):
                logger.error(
                    f"MinIO storage upload failed: HTTP {resp.status_code}",
                    extra={"key": key, "status": resp.status_code},
                )
                raise RuntimeError(f"Storage upload failed with HTTP status {resp.status_code}")

    async def exists(self, key: str) -> bool:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.head(self._get_url(key))
                return resp.status_code == 200
            except httpx.RequestError:
                return False

    async def get_metadata(self, key: str) -> Optional[Dict[str, str]]:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.head(self._get_url(key))
                if resp.status_code == 200:
                    meta = {}
                    for h_name, h_val in resp.headers.items():
                        if h_name.startswith("x-amz-meta-"):
                            meta[h_name[len("x-amz-meta-") :]] = h_val
                    meta["content_type"] = resp.headers.get("content-type", "application/octet-stream")
                    meta["size_bytes"] = resp.headers.get("content-length", "0")
                    return meta
                return None
            except httpx.RequestError:
                return None

    async def delete(self, key: str) -> bool:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.delete(self._get_url(key))
                return resp.status_code in (200, 204)
            except httpx.RequestError:
                return False


class StorageService:
    """Service orchestrating object storage operations with deterministic keying."""

    def __init__(self, backend: Optional[StorageBackend] = None) -> None:
        if backend:
            self._backend = backend
        elif settings.APP_ENV == "testing":
            self._backend = InMemoryStorageBackend()
        else:
            self._backend = S3MinIOStorageBackend(
                endpoint_url=settings.MINIO_ENDPOINT,
                bucket_name=settings.MINIO_BUCKET,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
            )

    @staticmethod
    def get_deterministic_key(sha256_digest: str) -> str:
        """Construct canonical object storage key based on immutable byte hash (Section 9)."""
        clean_digest = sha256_digest.strip().lower()
        return f"media/original/{clean_digest}"

    async def store_original(
        self,
        sha256_digest: str,
        data: bytes,
        content_type: str,
        original_filename: str,
    ) -> str:
        """Store original bytes with deterministic keying and metadata."""
        key = self.get_deterministic_key(sha256_digest)
        metadata = {
            "sha256": sha256_digest.lower(),
            "original_filename": original_filename,
            "byte_size": str(len(data)),
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        }
        await self._backend.upload(key, data, content_type, metadata)
        return key

    async def object_exists(self, key: str) -> bool:
        """Verify whether an object exists in storage."""
        return await self._backend.exists(key)

    async def get_metadata(self, key: str) -> Optional[Dict[str, str]]:
        """Retrieve stored object metadata."""
        return await self._backend.get_metadata(key)

    async def delete_object(self, key: str) -> bool:
        """Delete an object for transaction rollback / cleanup."""
        return await self._backend.delete(key)


storage_service = StorageService()
