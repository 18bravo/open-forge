"""
Storage Abstraction

This module defines the storage backend protocol and common types for
object storage across the Open Forge platform.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncIterator, Protocol, runtime_checkable


class StorageProvider(str, Enum):
    """Supported storage providers."""

    S3 = "s3"
    MINIO = "minio"
    AZURE = "azure"
    GCS = "gcs"
    LOCAL = "local"


@dataclass
class StorageConfig:
    """
    Configuration for a storage backend.

    Attributes:
        provider: Storage provider type
        bucket: Bucket/container name
        endpoint: Custom endpoint URL (for MinIO, LocalStack, etc.)
        region: Cloud region
        access_key: Access key ID (for S3-compatible)
        secret_key: Secret access key (for S3-compatible)
        connection_string: Connection string (for Azure)
        base_path: Base path prefix for all operations
        public_url_base: Base URL for public access
    """

    provider: StorageProvider
    bucket: str
    endpoint: str | None = None
    region: str = "us-east-1"
    access_key: str | None = None
    secret_key: str | None = None
    connection_string: str | None = None
    base_path: str = ""
    public_url_base: str | None = None


@dataclass
class StorageObject:
    """
    Represents an object in storage.

    Attributes:
        key: Object key/path
        size: Size in bytes
        content_type: MIME type
        last_modified: Last modification timestamp
        etag: Entity tag for versioning
        metadata: Custom metadata
    """

    key: str
    size: int = 0
    content_type: str = "application/octet-stream"
    last_modified: datetime | None = None
    etag: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


class StorageError(Exception):
    """Base exception for storage errors."""

    pass


class ObjectNotFoundError(StorageError):
    """Raised when an object is not found."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"Object not found: {key}")


class BucketNotFoundError(StorageError):
    """Raised when a bucket is not found."""

    def __init__(self, bucket: str) -> None:
        self.bucket = bucket
        super().__init__(f"Bucket not found: {bucket}")


@runtime_checkable
class StorageBackend(Protocol):
    """
    Protocol for storage backend implementations.

    Provides a consistent interface for object storage operations
    across different cloud providers and local filesystems.

    Example usage:
        >>> storage = S3StorageBackend(config)
        >>> await storage.connect()
        >>>
        >>> # Upload an object
        >>> await storage.put(
        ...     key="data/file.csv",
        ...     data=b"col1,col2\\n1,2\\n",
        ...     metadata={"content-type": "text/csv"},
        ... )
        >>>
        >>> # Download an object
        >>> data, metadata = await storage.get("data/file.csv")
        >>>
        >>> # List objects
        >>> async for key in storage.list("data/"):
        ...     print(key)
    """

    async def connect(self) -> None:
        """
        Connect to the storage backend.

        Validates configuration and establishes connection.
        """
        ...

    async def disconnect(self) -> None:
        """
        Disconnect from the storage backend.

        Releases any resources held by the connection.
        """
        ...

    async def put(
        self,
        key: str,
        data: bytes,
        metadata: dict[str, str] | None = None,
        content_type: str = "application/octet-stream",
    ) -> None:
        """
        Store an object.

        Args:
            key: Object key/path
            data: Object data as bytes
            metadata: Custom metadata to store with the object
            content_type: MIME type of the object

        Raises:
            StorageError: If the operation fails
        """
        ...

    async def get(self, key: str) -> tuple[bytes, dict[str, str]]:
        """
        Retrieve an object.

        Args:
            key: Object key/path

        Returns:
            Tuple of (data bytes, metadata dict)

        Raises:
            ObjectNotFoundError: If the object doesn't exist
            StorageError: If the operation fails
        """
        ...

    async def delete(self, key: str) -> None:
        """
        Delete an object.

        Args:
            key: Object key/path

        Raises:
            ObjectNotFoundError: If the object doesn't exist
            StorageError: If the operation fails
        """
        ...

    async def exists(self, key: str) -> bool:
        """
        Check if an object exists.

        Args:
            key: Object key/path

        Returns:
            True if the object exists
        """
        ...

    async def list(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> AsyncIterator[str]:
        """
        List objects with a given prefix.

        Args:
            prefix: Key prefix to filter by
            max_keys: Maximum number of keys to return

        Yields:
            Object keys matching the prefix
        """
        ...

    async def get_metadata(self, key: str) -> StorageObject:
        """
        Get object metadata without downloading the data.

        Args:
            key: Object key/path

        Returns:
            StorageObject with metadata

        Raises:
            ObjectNotFoundError: If the object doesn't exist
        """
        ...

    async def get_presigned_url(
        self,
        key: str,
        expires_in: timedelta = timedelta(hours=1),
        method: str = "GET",
    ) -> str:
        """
        Generate a presigned URL for direct client access.

        Args:
            key: Object key/path
            expires_in: URL expiration time
            method: HTTP method (GET for download, PUT for upload)

        Returns:
            Presigned URL string
        """
        ...

    async def copy(self, source_key: str, dest_key: str) -> None:
        """
        Copy an object within the storage backend.

        Args:
            source_key: Source object key
            dest_key: Destination object key

        Raises:
            ObjectNotFoundError: If the source object doesn't exist
        """
        ...


class BaseStorageBackend(ABC):
    """
    Abstract base class for storage backends.

    Provides common functionality that concrete implementations can use.
    """

    def __init__(self, config: StorageConfig) -> None:
        """Initialize the storage backend with configuration."""
        self.config = config
        self._connected = False

    @abstractmethod
    async def connect(self) -> None:
        """Connect to the storage backend."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the storage backend."""
        ...

    @abstractmethod
    async def put(
        self,
        key: str,
        data: bytes,
        metadata: dict[str, str] | None = None,
        content_type: str = "application/octet-stream",
    ) -> None:
        """Store an object."""
        ...

    @abstractmethod
    async def get(self, key: str) -> tuple[bytes, dict[str, str]]:
        """Retrieve an object."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete an object."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if an object exists."""
        ...

    @abstractmethod
    async def list(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> AsyncIterator[str]:
        """List objects with a given prefix."""
        ...

    @abstractmethod
    async def get_metadata(self, key: str) -> StorageObject:
        """Get object metadata."""
        ...

    @abstractmethod
    async def get_presigned_url(
        self,
        key: str,
        expires_in: timedelta = timedelta(hours=1),
        method: str = "GET",
    ) -> str:
        """Generate a presigned URL."""
        ...

    @abstractmethod
    async def copy(self, source_key: str, dest_key: str) -> None:
        """Copy an object."""
        ...

    def _full_key(self, key: str) -> str:
        """Get the full key including base path."""
        if self.config.base_path:
            return f"{self.config.base_path.rstrip('/')}/{key}"
        return key
