"""
S3 Storage Backend

This module implements the storage backend for Amazon S3 and S3-compatible
services like MinIO and LocalStack.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING, AsyncIterator

from forge_core.storage.abstraction import (
    BaseStorageBackend,
    ObjectNotFoundError,
    StorageConfig,
    StorageError,
    StorageObject,
)

if TYPE_CHECKING:
    import boto3
    from botocore.client import BaseClient

logger = logging.getLogger(__name__)


class S3StorageBackend(BaseStorageBackend):
    """
    Storage backend for Amazon S3 and S3-compatible services.

    Supports:
    - Amazon S3
    - MinIO
    - LocalStack
    - Any S3-compatible storage

    Example usage:
        >>> config = StorageConfig(
        ...     provider=StorageProvider.S3,
        ...     bucket="my-bucket",
        ...     region="us-east-1",
        ... )
        >>> storage = S3StorageBackend(config)
        >>> await storage.connect()
        >>> await storage.put("key", b"data")
    """

    def __init__(self, config: StorageConfig) -> None:
        """Initialize the S3 storage backend."""
        super().__init__(config)
        self._client: "BaseClient | None" = None

    async def connect(self) -> None:
        """Connect to S3."""
        try:
            import boto3
            from botocore.config import Config

            boto_config = Config(
                region_name=self.config.region,
                signature_version="s3v4",
            )

            client_kwargs = {
                "config": boto_config,
            }

            # Custom endpoint for MinIO/LocalStack
            if self.config.endpoint:
                client_kwargs["endpoint_url"] = self.config.endpoint

            # Explicit credentials
            if self.config.access_key and self.config.secret_key:
                client_kwargs["aws_access_key_id"] = self.config.access_key
                client_kwargs["aws_secret_access_key"] = self.config.secret_key

            self._client = boto3.client("s3", **client_kwargs)
            self._connected = True
            logger.info(f"Connected to S3 bucket: {self.config.bucket}")

        except ImportError:
            raise ImportError(
                "boto3 package required. Install with: pip install boto3"
            )
        except Exception as e:
            raise StorageError(f"Failed to connect to S3: {e}")

    async def disconnect(self) -> None:
        """Disconnect from S3."""
        self._client = None
        self._connected = False
        logger.info("Disconnected from S3")

    async def put(
        self,
        key: str,
        data: bytes,
        metadata: dict[str, str] | None = None,
        content_type: str = "application/octet-stream",
    ) -> None:
        """Store an object in S3."""
        if self._client is None:
            raise StorageError("Not connected to S3")

        full_key = self._full_key(key)

        try:
            put_kwargs = {
                "Bucket": self.config.bucket,
                "Key": full_key,
                "Body": data,
                "ContentType": content_type,
            }

            if metadata:
                put_kwargs["Metadata"] = metadata

            self._client.put_object(**put_kwargs)
            logger.debug(f"Uploaded object: {full_key}")

        except Exception as e:
            raise StorageError(f"Failed to put object {key}: {e}")

    async def get(self, key: str) -> tuple[bytes, dict[str, str]]:
        """Retrieve an object from S3."""
        if self._client is None:
            raise StorageError("Not connected to S3")

        full_key = self._full_key(key)

        try:
            response = self._client.get_object(
                Bucket=self.config.bucket,
                Key=full_key,
            )
            data = response["Body"].read()
            metadata = response.get("Metadata", {})
            return data, metadata

        except self._client.exceptions.NoSuchKey:
            raise ObjectNotFoundError(key)
        except Exception as e:
            if "NoSuchKey" in str(e) or "404" in str(e):
                raise ObjectNotFoundError(key)
            raise StorageError(f"Failed to get object {key}: {e}")

    async def delete(self, key: str) -> None:
        """Delete an object from S3."""
        if self._client is None:
            raise StorageError("Not connected to S3")

        full_key = self._full_key(key)

        try:
            self._client.delete_object(
                Bucket=self.config.bucket,
                Key=full_key,
            )
            logger.debug(f"Deleted object: {full_key}")

        except Exception as e:
            raise StorageError(f"Failed to delete object {key}: {e}")

    async def exists(self, key: str) -> bool:
        """Check if an object exists in S3."""
        if self._client is None:
            raise StorageError("Not connected to S3")

        full_key = self._full_key(key)

        try:
            self._client.head_object(
                Bucket=self.config.bucket,
                Key=full_key,
            )
            return True
        except Exception:
            return False

    async def list(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> AsyncIterator[str]:
        """List objects in S3."""
        if self._client is None:
            raise StorageError("Not connected to S3")

        full_prefix = self._full_key(prefix)
        continuation_token = None
        keys_returned = 0

        while keys_returned < max_keys:
            list_kwargs = {
                "Bucket": self.config.bucket,
                "Prefix": full_prefix,
                "MaxKeys": min(1000, max_keys - keys_returned),
            }

            if continuation_token:
                list_kwargs["ContinuationToken"] = continuation_token

            response = self._client.list_objects_v2(**list_kwargs)

            for obj in response.get("Contents", []):
                key = obj["Key"]
                # Remove base path from key
                if self.config.base_path:
                    key = key[len(self.config.base_path) + 1 :]
                yield key
                keys_returned += 1

            if not response.get("IsTruncated"):
                break

            continuation_token = response.get("NextContinuationToken")

    async def get_metadata(self, key: str) -> StorageObject:
        """Get object metadata from S3."""
        if self._client is None:
            raise StorageError("Not connected to S3")

        full_key = self._full_key(key)

        try:
            response = self._client.head_object(
                Bucket=self.config.bucket,
                Key=full_key,
            )

            return StorageObject(
                key=key,
                size=response.get("ContentLength", 0),
                content_type=response.get("ContentType", "application/octet-stream"),
                last_modified=response.get("LastModified"),
                etag=response.get("ETag", "").strip('"'),
                metadata=response.get("Metadata", {}),
            )

        except Exception as e:
            if "404" in str(e) or "NoSuchKey" in str(e):
                raise ObjectNotFoundError(key)
            raise StorageError(f"Failed to get metadata for {key}: {e}")

    async def get_presigned_url(
        self,
        key: str,
        expires_in: timedelta = timedelta(hours=1),
        method: str = "GET",
    ) -> str:
        """Generate a presigned URL for S3."""
        if self._client is None:
            raise StorageError("Not connected to S3")

        full_key = self._full_key(key)
        operation = "get_object" if method == "GET" else "put_object"

        url = self._client.generate_presigned_url(
            operation,
            Params={
                "Bucket": self.config.bucket,
                "Key": full_key,
            },
            ExpiresIn=int(expires_in.total_seconds()),
        )

        return url

    async def copy(self, source_key: str, dest_key: str) -> None:
        """Copy an object within S3."""
        if self._client is None:
            raise StorageError("Not connected to S3")

        full_source = self._full_key(source_key)
        full_dest = self._full_key(dest_key)

        try:
            self._client.copy_object(
                Bucket=self.config.bucket,
                CopySource={"Bucket": self.config.bucket, "Key": full_source},
                Key=full_dest,
            )
            logger.debug(f"Copied {full_source} to {full_dest}")

        except Exception as e:
            if "404" in str(e) or "NoSuchKey" in str(e):
                raise ObjectNotFoundError(source_key)
            raise StorageError(f"Failed to copy {source_key} to {dest_key}: {e}")
