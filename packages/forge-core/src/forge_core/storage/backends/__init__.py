"""
Storage Backends

This module provides different backend implementations for object storage:

- **s3**: Amazon S3 and S3-compatible services (MinIO, LocalStack)
- **azure**: Azure Blob Storage
- **local**: Local filesystem for development and testing
"""

from forge_core.storage.backends.azure import AzureStorageBackend
from forge_core.storage.backends.local import LocalStorageBackend
from forge_core.storage.backends.s3 import S3StorageBackend

__all__ = [
    "S3StorageBackend",
    "AzureStorageBackend",
    "LocalStorageBackend",
]
