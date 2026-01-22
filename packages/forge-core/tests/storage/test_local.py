"""Tests for the local storage backend."""

import pytest

from forge_core.storage.abstraction import ObjectNotFoundError
from forge_core.storage.backends.local import LocalStorageBackend


class TestLocalStorageBackend:
    """Tests for LocalStorageBackend."""

    @pytest.mark.asyncio
    async def test_put_get(self, local_storage: LocalStorageBackend) -> None:
        """Test putting and getting objects."""
        await local_storage.put("test-key", b"test-data")

        data, metadata = await local_storage.get("test-key")

        assert data == b"test-data"

    @pytest.mark.asyncio
    async def test_put_with_metadata(self, local_storage: LocalStorageBackend) -> None:
        """Test putting objects with metadata."""
        await local_storage.put(
            "test-key",
            b"test-data",
            metadata={"custom": "value"},
            content_type="text/plain",
        )

        data, metadata = await local_storage.get("test-key")

        assert data == b"test-data"
        assert metadata.get("custom") == "value"

    @pytest.mark.asyncio
    async def test_get_not_found(self, local_storage: LocalStorageBackend) -> None:
        """Test getting a non-existent object."""
        with pytest.raises(ObjectNotFoundError):
            await local_storage.get("non-existent-key")

    @pytest.mark.asyncio
    async def test_delete(self, local_storage: LocalStorageBackend) -> None:
        """Test deleting objects."""
        await local_storage.put("test-key", b"test-data")
        assert await local_storage.exists("test-key")

        await local_storage.delete("test-key")
        assert not await local_storage.exists("test-key")

    @pytest.mark.asyncio
    async def test_exists(self, local_storage: LocalStorageBackend) -> None:
        """Test checking object existence."""
        assert not await local_storage.exists("test-key")

        await local_storage.put("test-key", b"test-data")

        assert await local_storage.exists("test-key")

    @pytest.mark.asyncio
    async def test_list(self, local_storage: LocalStorageBackend) -> None:
        """Test listing objects."""
        await local_storage.put("prefix/a.txt", b"data-a")
        await local_storage.put("prefix/b.txt", b"data-b")
        await local_storage.put("other/c.txt", b"data-c")

        keys = [key async for key in local_storage.list("prefix/")]

        assert len(keys) == 2
        assert "prefix/a.txt" in keys
        assert "prefix/b.txt" in keys

    @pytest.mark.asyncio
    async def test_get_metadata(self, local_storage: LocalStorageBackend) -> None:
        """Test getting object metadata."""
        await local_storage.put(
            "test-key",
            b"test-data",
            metadata={"custom": "value"},
            content_type="application/json",
        )

        obj = await local_storage.get_metadata("test-key")

        assert obj.key == "test-key"
        assert obj.size == len(b"test-data")
        assert obj.content_type == "application/json"
        assert obj.metadata.get("custom") == "value"

    @pytest.mark.asyncio
    async def test_copy(self, local_storage: LocalStorageBackend) -> None:
        """Test copying objects."""
        await local_storage.put("source-key", b"source-data")

        await local_storage.copy("source-key", "dest-key")

        source_data, _ = await local_storage.get("source-key")
        dest_data, _ = await local_storage.get("dest-key")

        assert source_data == dest_data

    @pytest.mark.asyncio
    async def test_copy_not_found(self, local_storage: LocalStorageBackend) -> None:
        """Test copying a non-existent object."""
        with pytest.raises(ObjectNotFoundError):
            await local_storage.copy("non-existent", "dest")

    @pytest.mark.asyncio
    async def test_nested_paths(self, local_storage: LocalStorageBackend) -> None:
        """Test working with nested paths."""
        await local_storage.put("a/b/c/deep-file.txt", b"deep-data")

        assert await local_storage.exists("a/b/c/deep-file.txt")

        data, _ = await local_storage.get("a/b/c/deep-file.txt")
        assert data == b"deep-data"
