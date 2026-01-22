"""
Local Filesystem Storage Backend

This module implements the storage backend using the local filesystem.
Ideal for development and testing environments.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncIterator

from forge_core.storage.abstraction import (
    BaseStorageBackend,
    ObjectNotFoundError,
    StorageConfig,
    StorageError,
    StorageObject,
)

logger = logging.getLogger(__name__)


class LocalStorageBackend(BaseStorageBackend):
    """
    Storage backend using the local filesystem.

    This is useful for:
    - Local development
    - Unit and integration testing
    - Scenarios where cloud storage is not available

    Objects are stored as files with a companion .meta.json file for metadata.

    Example usage:
        >>> config = StorageConfig(
        ...     provider=StorageProvider.LOCAL,
        ...     bucket="/tmp/forge-storage",
        ... )
        >>> storage = LocalStorageBackend(config)
        >>> await storage.connect()
        >>> await storage.put("key", b"data")
    """

    def __init__(self, config: StorageConfig) -> None:
        """Initialize the local storage backend."""
        super().__init__(config)
        self._base_dir: Path | None = None

    async def connect(self) -> None:
        """Initialize the local storage directory."""
        try:
            self._base_dir = Path(self.config.bucket)

            if self.config.base_path:
                self._base_dir = self._base_dir / self.config.base_path

            self._base_dir.mkdir(parents=True, exist_ok=True)
            self._connected = True
            logger.info(f"Connected to local storage: {self._base_dir}")

        except Exception as e:
            raise StorageError(f"Failed to initialize local storage: {e}")

    async def disconnect(self) -> None:
        """Disconnect from local storage."""
        self._base_dir = None
        self._connected = False
        logger.info("Disconnected from local storage")

    def _get_path(self, key: str) -> Path:
        """Get the full filesystem path for a key."""
        if self._base_dir is None:
            raise StorageError("Not connected")
        return self._base_dir / key

    def _get_meta_path(self, key: str) -> Path:
        """Get the metadata file path for a key."""
        return self._get_path(key).with_suffix(
            self._get_path(key).suffix + ".meta.json"
        )

    async def put(
        self,
        key: str,
        data: bytes,
        metadata: dict[str, str] | None = None,
        content_type: str = "application/octet-stream",
    ) -> None:
        """Store an object locally."""
        if self._base_dir is None:
            raise StorageError("Not connected")

        file_path = self._get_path(key)
        meta_path = self._get_meta_path(key)

        try:
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write data
            file_path.write_bytes(data)

            # Write metadata
            meta = {
                "content_type": content_type,
                "size": len(data),
                "etag": hashlib.md5(data).hexdigest(),
                "last_modified": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }
            meta_path.write_text(json.dumps(meta, indent=2))

            logger.debug(f"Stored object: {key}")

        except Exception as e:
            raise StorageError(f"Failed to put object {key}: {e}")

    async def get(self, key: str) -> tuple[bytes, dict[str, str]]:
        """Retrieve an object from local storage."""
        file_path = self._get_path(key)
        meta_path = self._get_meta_path(key)

        if not file_path.exists():
            raise ObjectNotFoundError(key)

        try:
            data = file_path.read_bytes()

            metadata = {}
            if meta_path.exists():
                meta = json.loads(meta_path.read_text())
                metadata = meta.get("metadata", {})

            return data, metadata

        except Exception as e:
            raise StorageError(f"Failed to get object {key}: {e}")

    async def delete(self, key: str) -> None:
        """Delete an object from local storage."""
        file_path = self._get_path(key)
        meta_path = self._get_meta_path(key)

        try:
            if file_path.exists():
                file_path.unlink()
            if meta_path.exists():
                meta_path.unlink()

            logger.debug(f"Deleted object: {key}")

        except Exception as e:
            raise StorageError(f"Failed to delete object {key}: {e}")

    async def exists(self, key: str) -> bool:
        """Check if an object exists locally."""
        return self._get_path(key).exists()

    async def list(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> AsyncIterator[str]:
        """List objects in local storage."""
        if self._base_dir is None:
            raise StorageError("Not connected")

        base_path = self._base_dir
        if prefix:
            search_path = base_path / prefix
            if search_path.is_file():
                yield prefix
                return
            base_path = search_path.parent if not search_path.exists() else search_path

        keys_returned = 0

        for root, _, files in os.walk(base_path):
            for file in files:
                if file.endswith(".meta.json"):
                    continue

                if keys_returned >= max_keys:
                    return

                full_path = Path(root) / file
                key = str(full_path.relative_to(self._base_dir))

                if prefix and not key.startswith(prefix):
                    continue

                yield key
                keys_returned += 1

    async def get_metadata(self, key: str) -> StorageObject:
        """Get object metadata from local storage."""
        file_path = self._get_path(key)
        meta_path = self._get_meta_path(key)

        if not file_path.exists():
            raise ObjectNotFoundError(key)

        try:
            stat = file_path.stat()

            metadata = {}
            content_type = "application/octet-stream"
            etag = None

            if meta_path.exists():
                meta = json.loads(meta_path.read_text())
                metadata = meta.get("metadata", {})
                content_type = meta.get("content_type", content_type)
                etag = meta.get("etag")

            return StorageObject(
                key=key,
                size=stat.st_size,
                content_type=content_type,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                etag=etag,
                metadata=metadata,
            )

        except Exception as e:
            raise StorageError(f"Failed to get metadata for {key}: {e}")

    async def get_presigned_url(
        self,
        key: str,
        expires_in: timedelta = timedelta(hours=1),
        method: str = "GET",
    ) -> str:
        """
        Generate a URL for local storage.

        For local storage, this returns a file:// URL.
        Note: This is only useful for local development.
        """
        file_path = self._get_path(key)

        if self.config.public_url_base:
            return f"{self.config.public_url_base.rstrip('/')}/{key}"

        return f"file://{file_path.absolute()}"

    async def copy(self, source_key: str, dest_key: str) -> None:
        """Copy an object within local storage."""
        source_path = self._get_path(source_key)
        source_meta = self._get_meta_path(source_key)
        dest_path = self._get_path(dest_key)
        dest_meta = self._get_meta_path(dest_key)

        if not source_path.exists():
            raise ObjectNotFoundError(source_key)

        try:
            import shutil

            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dest_path)

            if source_meta.exists():
                shutil.copy2(source_meta, dest_meta)

            logger.debug(f"Copied {source_key} to {dest_key}")

        except Exception as e:
            raise StorageError(f"Failed to copy {source_key} to {dest_key}: {e}")

    def clear(self) -> None:
        """Clear all objects (useful for testing)."""
        if self._base_dir is None:
            return

        import shutil

        if self._base_dir.exists():
            shutil.rmtree(self._base_dir)
            self._base_dir.mkdir(parents=True, exist_ok=True)
