"""Storage adapter that integrates with forge-core storage backends."""

from __future__ import annotations

from typing import TYPE_CHECKING, AsyncIterator, Protocol, runtime_checkable

if TYPE_CHECKING:
    from forge_media.core.media_set import MediaItem


@runtime_checkable
class StorageBackend(Protocol):
    """
    Protocol for storage backends (from forge-core).

    This protocol defines the interface that forge-media expects from
    storage backends. Implementations are provided by forge-core.
    """

    async def put(self, key: str, data: bytes, metadata: dict[str, str] | None = None) -> None:
        """Store data at the given key."""
        ...

    async def get(self, key: str) -> tuple[bytes, dict[str, str]]:
        """Retrieve data and metadata from the given key."""
        ...

    async def delete(self, key: str) -> None:
        """Delete data at the given key."""
        ...

    async def list(self, prefix: str) -> AsyncIterator[str]:
        """List keys with the given prefix."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        ...


class MediaStorageAdapter:
    """
    Adapter for storing and retrieving media using forge-core storage.

    This adapter provides media-specific operations on top of the generic
    storage backend from forge-core, including:
    - Path generation for media items
    - Thumbnail storage
    - Presigned URL generation (when supported)

    Example:
        ```python
        from forge_core.storage import S3Backend
        from forge_media.core.storage import MediaStorageAdapter

        backend = S3Backend(bucket="my-media-bucket")
        storage = MediaStorageAdapter(backend)

        # Upload media
        await storage.upload_media(media_item, file_data)

        # Get download URL
        url = await storage.get_download_url(media_item)
        ```
    """

    def __init__(self, backend: StorageBackend, prefix: str = "media"):
        """
        Initialize the media storage adapter.

        Args:
            backend: A forge-core storage backend instance
            prefix: Path prefix for all media storage (default: "media")
        """
        self.backend = backend
        self.prefix = prefix

    def _media_path(self, media_set_id: str, media_id: str, filename: str) -> str:
        """Generate storage path for a media item."""
        return f"{self.prefix}/{media_set_id}/{media_id}/{filename}"

    def _thumbnail_path(
        self, media_set_id: str, media_id: str, width: int, height: int
    ) -> str:
        """Generate storage path for a thumbnail."""
        return f"{self.prefix}/{media_set_id}/{media_id}/thumbnails/{width}x{height}.jpg"

    async def upload_media(
        self,
        item: MediaItem,
        data: bytes,
        content_type: str | None = None,
    ) -> str:
        """
        Upload media data to storage.

        Args:
            item: The MediaItem to upload data for
            data: Raw file data
            content_type: Optional MIME type for the content

        Returns:
            The storage path where the data was stored
        """
        path = self._media_path(item.media_set_id, item.id, item.name)
        metadata = {"content_type": content_type} if content_type else {}
        await self.backend.put(path, data, metadata)
        return path

    async def download_media(self, item: MediaItem) -> bytes:
        """
        Download media data from storage.

        Args:
            item: The MediaItem to download

        Returns:
            Raw file data
        """
        data, _ = await self.backend.get(item.storage_path)
        return data

    async def delete_media(self, item: MediaItem) -> None:
        """
        Delete media and associated thumbnails from storage.

        Args:
            item: The MediaItem to delete
        """
        # Delete main file
        await self.backend.delete(item.storage_path)

        # Delete thumbnails
        for thumbnail_path in item.thumbnails:
            try:
                await self.backend.delete(thumbnail_path)
            except Exception:
                # Ignore errors deleting thumbnails
                pass

    async def upload_thumbnail(
        self,
        item: MediaItem,
        data: bytes,
        width: int,
        height: int,
    ) -> str:
        """
        Upload a thumbnail image.

        Args:
            item: The MediaItem this thumbnail belongs to
            data: JPEG image data
            width: Thumbnail width
            height: Thumbnail height

        Returns:
            The storage path where the thumbnail was stored
        """
        path = self._thumbnail_path(item.media_set_id, item.id, width, height)
        await self.backend.put(path, data, {"content_type": "image/jpeg"})
        return path

    async def get_thumbnail(
        self,
        item: MediaItem,
        width: int,
        height: int,
    ) -> bytes | None:
        """
        Get a thumbnail image.

        Args:
            item: The MediaItem
            width: Thumbnail width
            height: Thumbnail height

        Returns:
            JPEG image data or None if thumbnail doesn't exist
        """
        path = self._thumbnail_path(item.media_set_id, item.id, width, height)
        if not await self.backend.exists(path):
            return None
        data, _ = await self.backend.get(path)
        return data

    async def media_exists(self, item: MediaItem) -> bool:
        """Check if the media file exists in storage."""
        return await self.backend.exists(item.storage_path)
