"""
Storage Abstraction Module

This module provides a unified interface for object storage across different backends:

- **S3**: Amazon S3 and compatible services (MinIO)
- **Azure**: Azure Blob Storage
- **Local**: Local filesystem (for development and testing)

The storage abstraction supports:
- Put/get/delete operations
- Metadata management
- Presigned URLs for direct client access
- Streaming for large files
"""

from forge_core.storage.abstraction import (
    StorageBackend,
    StorageConfig,
    StorageError,
    StorageObject,
)

__all__ = [
    "StorageBackend",
    "StorageConfig",
    "StorageObject",
    "StorageError",
]
