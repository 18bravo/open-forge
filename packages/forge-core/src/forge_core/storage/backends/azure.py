"""
Azure Blob Storage Backend

This module implements the storage backend for Azure Blob Storage.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, AsyncIterator

from forge_core.storage.abstraction import (
    BaseStorageBackend,
    ObjectNotFoundError,
    StorageConfig,
    StorageError,
    StorageObject,
)

if TYPE_CHECKING:
    from azure.storage.blob import BlobServiceClient, ContainerClient

logger = logging.getLogger(__name__)


class AzureStorageBackend(BaseStorageBackend):
    """
    Storage backend for Azure Blob Storage.

    Example usage:
        >>> config = StorageConfig(
        ...     provider=StorageProvider.AZURE,
        ...     bucket="my-container",
        ...     connection_string="DefaultEndpointsProtocol=https;...",
        ... )
        >>> storage = AzureStorageBackend(config)
        >>> await storage.connect()
        >>> await storage.put("key", b"data")
    """

    def __init__(self, config: StorageConfig) -> None:
        """Initialize the Azure storage backend."""
        super().__init__(config)
        self._service_client: "BlobServiceClient | None" = None
        self._container_client: "ContainerClient | None" = None

    async def connect(self) -> None:
        """Connect to Azure Blob Storage."""
        try:
            from azure.storage.blob import BlobServiceClient

            if self.config.connection_string:
                self._service_client = BlobServiceClient.from_connection_string(
                    self.config.connection_string
                )
            else:
                raise StorageError(
                    "Azure storage requires connection_string in config"
                )

            self._container_client = self._service_client.get_container_client(
                self.config.bucket
            )
            self._connected = True
            logger.info(f"Connected to Azure container: {self.config.bucket}")

        except ImportError:
            raise ImportError(
                "azure-storage-blob package required. "
                "Install with: pip install azure-storage-blob"
            )
        except Exception as e:
            raise StorageError(f"Failed to connect to Azure: {e}")

    async def disconnect(self) -> None:
        """Disconnect from Azure Blob Storage."""
        self._container_client = None
        self._service_client = None
        self._connected = False
        logger.info("Disconnected from Azure Blob Storage")

    async def put(
        self,
        key: str,
        data: bytes,
        metadata: dict[str, str] | None = None,
        content_type: str = "application/octet-stream",
    ) -> None:
        """Store an object in Azure Blob Storage."""
        if self._container_client is None:
            raise StorageError("Not connected to Azure")

        full_key = self._full_key(key)

        try:
            from azure.storage.blob import ContentSettings

            blob_client = self._container_client.get_blob_client(full_key)
            blob_client.upload_blob(
                data,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type),
                metadata=metadata,
            )
            logger.debug(f"Uploaded blob: {full_key}")

        except Exception as e:
            raise StorageError(f"Failed to put object {key}: {e}")

    async def get(self, key: str) -> tuple[bytes, dict[str, str]]:
        """Retrieve an object from Azure Blob Storage."""
        if self._container_client is None:
            raise StorageError("Not connected to Azure")

        full_key = self._full_key(key)

        try:
            blob_client = self._container_client.get_blob_client(full_key)
            download = blob_client.download_blob()
            data = download.readall()
            properties = blob_client.get_blob_properties()
            metadata = properties.metadata or {}
            return data, metadata

        except Exception as e:
            if "BlobNotFound" in str(e) or "404" in str(e):
                raise ObjectNotFoundError(key)
            raise StorageError(f"Failed to get object {key}: {e}")

    async def delete(self, key: str) -> None:
        """Delete an object from Azure Blob Storage."""
        if self._container_client is None:
            raise StorageError("Not connected to Azure")

        full_key = self._full_key(key)

        try:
            blob_client = self._container_client.get_blob_client(full_key)
            blob_client.delete_blob()
            logger.debug(f"Deleted blob: {full_key}")

        except Exception as e:
            raise StorageError(f"Failed to delete object {key}: {e}")

    async def exists(self, key: str) -> bool:
        """Check if an object exists in Azure Blob Storage."""
        if self._container_client is None:
            raise StorageError("Not connected to Azure")

        full_key = self._full_key(key)

        try:
            blob_client = self._container_client.get_blob_client(full_key)
            return blob_client.exists()
        except Exception:
            return False

    async def list(
        self,
        prefix: str = "",
        max_keys: int = 1000,
    ) -> AsyncIterator[str]:
        """List objects in Azure Blob Storage."""
        if self._container_client is None:
            raise StorageError("Not connected to Azure")

        full_prefix = self._full_key(prefix)
        keys_returned = 0

        blobs = self._container_client.list_blobs(name_starts_with=full_prefix)

        for blob in blobs:
            if keys_returned >= max_keys:
                break

            key = blob.name
            # Remove base path from key
            if self.config.base_path:
                key = key[len(self.config.base_path) + 1 :]
            yield key
            keys_returned += 1

    async def get_metadata(self, key: str) -> StorageObject:
        """Get object metadata from Azure Blob Storage."""
        if self._container_client is None:
            raise StorageError("Not connected to Azure")

        full_key = self._full_key(key)

        try:
            blob_client = self._container_client.get_blob_client(full_key)
            properties = blob_client.get_blob_properties()

            return StorageObject(
                key=key,
                size=properties.size,
                content_type=properties.content_settings.content_type
                or "application/octet-stream",
                last_modified=properties.last_modified,
                etag=properties.etag,
                metadata=properties.metadata or {},
            )

        except Exception as e:
            if "BlobNotFound" in str(e) or "404" in str(e):
                raise ObjectNotFoundError(key)
            raise StorageError(f"Failed to get metadata for {key}: {e}")

    async def get_presigned_url(
        self,
        key: str,
        expires_in: timedelta = timedelta(hours=1),
        method: str = "GET",
    ) -> str:
        """Generate a presigned URL for Azure Blob Storage."""
        if self._container_client is None:
            raise StorageError("Not connected to Azure")

        full_key = self._full_key(key)

        try:
            from azure.storage.blob import BlobSasPermissions, generate_blob_sas

            blob_client = self._container_client.get_blob_client(full_key)
            account_name = blob_client.account_name

            # Determine permissions based on method
            if method == "GET":
                permissions = BlobSasPermissions(read=True)
            else:
                permissions = BlobSasPermissions(write=True, create=True)

            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=self.config.bucket,
                blob_name=full_key,
                permission=permissions,
                expiry=datetime.now(timezone.utc) + expires_in,
            )

            return f"{blob_client.url}?{sas_token}"

        except Exception as e:
            raise StorageError(f"Failed to generate presigned URL: {e}")

    async def copy(self, source_key: str, dest_key: str) -> None:
        """Copy an object within Azure Blob Storage."""
        if self._container_client is None:
            raise StorageError("Not connected to Azure")

        full_source = self._full_key(source_key)
        full_dest = self._full_key(dest_key)

        try:
            source_blob = self._container_client.get_blob_client(full_source)
            dest_blob = self._container_client.get_blob_client(full_dest)

            dest_blob.start_copy_from_url(source_blob.url)
            logger.debug(f"Copied {full_source} to {full_dest}")

        except Exception as e:
            if "BlobNotFound" in str(e) or "404" in str(e):
                raise ObjectNotFoundError(source_key)
            raise StorageError(f"Failed to copy {source_key} to {dest_key}: {e}")
