"""
Tests for checkpoint management.

Verifies checkpoint storage and retrieval functionality.
"""

from datetime import datetime

import pytest

from forge_transforms.incremental import (
    Checkpoint,
    CheckpointMetadata,
    MemoryCheckpointStore,
    FileCheckpointStore,
)


class TestCheckpointMetadata:
    """Test CheckpointMetadata serialization."""

    def test_to_dict(self):
        """Test metadata serialization."""
        now = datetime.utcnow()
        meta = CheckpointMetadata(
            created_at=now,
            rows_processed=1000,
            watermark="2024-01-15T10:00:00",
            custom={"batch_id": 42},
        )
        data = meta.to_dict()

        assert data["created_at"] == now.isoformat()
        assert data["rows_processed"] == 1000
        assert data["watermark"] == "2024-01-15T10:00:00"
        assert data["custom"]["batch_id"] == 42

    def test_from_dict(self):
        """Test metadata deserialization."""
        data = {
            "created_at": "2024-01-15T10:00:00",
            "rows_processed": 500,
            "watermark": "seq-100",
            "custom": {},
        }
        meta = CheckpointMetadata.from_dict(data)

        assert meta.rows_processed == 500
        assert meta.watermark == "seq-100"


class TestCheckpoint:
    """Test Checkpoint serialization."""

    def test_to_dict(self):
        """Test checkpoint serialization."""
        checkpoint = Checkpoint(
            checkpoint_id="cp-001",
            transform_id="my-transform",
            state={"watermark": "2024-01-15", "offset": 100},
        )
        data = checkpoint.to_dict()

        assert data["checkpoint_id"] == "cp-001"
        assert data["transform_id"] == "my-transform"
        assert data["state"]["offset"] == 100

    def test_from_dict(self):
        """Test checkpoint deserialization."""
        data = {
            "checkpoint_id": "cp-002",
            "transform_id": "other-transform",
            "state": {"key": "value"},
            "metadata": {
                "created_at": "2024-01-15T10:00:00",
                "rows_processed": 0,
                "watermark": None,
                "custom": {},
            },
            "version": 1,
        }
        checkpoint = Checkpoint.from_dict(data)

        assert checkpoint.checkpoint_id == "cp-002"
        assert checkpoint.state["key"] == "value"


class TestMemoryCheckpointStore:
    """Test in-memory checkpoint store."""

    @pytest.fixture
    def store(self):
        """Create a fresh store for each test."""
        return MemoryCheckpointStore()

    @pytest.mark.asyncio
    async def test_save_and_get(self, store):
        """Test saving and retrieving a checkpoint."""
        checkpoint = Checkpoint(
            checkpoint_id="cp-001",
            transform_id="transform-1",
            state={"key": "value"},
        )
        await store.save(checkpoint)
        retrieved = await store.get("cp-001")

        assert retrieved is not None
        assert retrieved.checkpoint_id == "cp-001"
        assert retrieved.state["key"] == "value"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, store):
        """Test getting a nonexistent checkpoint."""
        result = await store.get("does-not-exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest(self, store):
        """Test getting the latest checkpoint."""
        for i in range(3):
            checkpoint = Checkpoint(
                checkpoint_id=f"cp-{i:03d}",
                transform_id="transform-1",
                state={"index": i},
            )
            await store.save(checkpoint)

        latest = await store.get_latest("transform-1")
        assert latest is not None
        # Should be the most recently created

    @pytest.mark.asyncio
    async def test_get_latest_empty(self, store):
        """Test getting latest from empty store."""
        result = await store.get_latest("transform-1")
        assert result is None

    @pytest.mark.asyncio
    async def test_list_checkpoints(self, store):
        """Test listing checkpoints."""
        for i in range(5):
            checkpoint = Checkpoint(
                checkpoint_id=f"cp-{i:03d}",
                transform_id="transform-1",
                state={},
            )
            await store.save(checkpoint)

        checkpoints = await store.list("transform-1", limit=3)
        assert len(checkpoints) == 3

    @pytest.mark.asyncio
    async def test_delete_checkpoint(self, store):
        """Test deleting a checkpoint."""
        checkpoint = Checkpoint(
            checkpoint_id="to-delete",
            transform_id="transform-1",
            state={},
        )
        await store.save(checkpoint)

        assert await store.delete("to-delete") is True
        assert await store.get("to-delete") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, store):
        """Test deleting a nonexistent checkpoint."""
        result = await store.delete("does-not-exist")
        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup(self, store):
        """Test cleaning up old checkpoints."""
        for i in range(10):
            checkpoint = Checkpoint(
                checkpoint_id=f"cp-{i:03d}",
                transform_id="transform-1",
                state={},
            )
            await store.save(checkpoint)

        deleted = await store.cleanup("transform-1", keep_count=3)

        assert deleted == 7
        remaining = await store.list("transform-1", limit=100)
        assert len(remaining) == 3


class TestFileCheckpointStore:
    """Test file-based checkpoint store."""

    @pytest.fixture
    def store(self, tmp_path):
        """Create a store in a temp directory."""
        return FileCheckpointStore(tmp_path / "checkpoints")

    @pytest.mark.asyncio
    async def test_save_and_get(self, store):
        """Test saving and retrieving from files."""
        checkpoint = Checkpoint(
            checkpoint_id="file-cp-001",
            transform_id="transform-1",
            state={"persisted": True},
        )
        await store.save(checkpoint)
        retrieved = await store.get("file-cp-001")

        assert retrieved is not None
        assert retrieved.state["persisted"] is True

    @pytest.mark.asyncio
    async def test_get_latest(self, store):
        """Test getting the latest checkpoint from files."""
        for i in range(3):
            checkpoint = Checkpoint(
                checkpoint_id=f"file-cp-{i:03d}",
                transform_id="file-transform",
                state={"index": i},
            )
            await store.save(checkpoint)

        latest = await store.get_latest("file-transform")
        assert latest is not None

    @pytest.mark.asyncio
    async def test_list_and_cleanup(self, store):
        """Test listing and cleanup with files."""
        for i in range(5):
            checkpoint = Checkpoint(
                checkpoint_id=f"cleanup-{i:03d}",
                transform_id="cleanup-transform",
                state={},
            )
            await store.save(checkpoint)

        checkpoints = await store.list("cleanup-transform")
        assert len(checkpoints) == 5

        deleted = await store.cleanup("cleanup-transform", keep_count=2)
        assert deleted == 3

        remaining = await store.list("cleanup-transform")
        assert len(remaining) == 2
