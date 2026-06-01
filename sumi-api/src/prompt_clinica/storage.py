from __future__ import annotations

import functools
import io
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    @abstractmethod
    def save(self, key: str, data: bytes) -> str:
        """Persist bytes at key and return the public URL."""

    @abstractmethod
    def read(self, key: str) -> bytes | None:
        """Return bytes at key, or None if not found."""


class LocalStorageBackend(StorageBackend):
    def __init__(self, images_dir: str) -> None:
        self._root = Path(images_dir)

    def save(self, key: str, data: bytes) -> str:
        dest = self._root / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return f"/static/images/{key}"

    def read(self, key: str) -> bytes | None:
        path = self._root / key
        return path.read_bytes() if path.exists() else None


class RailwayStorageBackend(StorageBackend):
    def __init__(
        self,
        bucket_name: str,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        region: str,
        public_url: str,
    ) -> None:
        import boto3  # type: ignore[import-untyped]

        self._bucket = bucket_name
        self._public_url = public_url.rstrip("/")
        self._s3: Any = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    def save(self, key: str, data: bytes) -> str:
        self._s3.upload_fileobj(
            io.BytesIO(data),
            self._bucket,
            key,
            ExtraArgs={"ContentType": "image/png"},
        )
        logger.info("Uploaded to Railway bucket: %s", key)
        return f"{self._public_url}/{key}"

    def read(self, key: str) -> bytes | None:
        try:
            buf = io.BytesIO()
            self._s3.download_fileobj(self._bucket, key, buf)
            return buf.getvalue()
        except Exception:  # noqa: BLE001
            return None


@functools.lru_cache(maxsize=1)
def get_storage() -> StorageBackend:
    from prompt_clinica.config import settings

    if settings.storage_backend == "railway":
        return RailwayStorageBackend(
            bucket_name=settings.railway_bucket_name,
            endpoint_url=settings.railway_bucket_endpoint_url,
            access_key=settings.railway_bucket_access_key,
            secret_key=settings.railway_bucket_secret_key,
            region=settings.railway_bucket_region,
            public_url=settings.railway_public_url,
        )
    return LocalStorageBackend(settings.images_dir)
