"""
Checkpoint Management

Provides state checkpointing for incremental processing, allowing
transforms to resume from previous processing state.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class CheckpointMetadata:
    """Metadata associated with a checkpoint.

    Attributes:
        created_at: When the checkpoint was created.
        rows_processed: Total rows processed up to this checkpoint.
        processing_time_ms: Total processing time in milliseconds.
        watermark: The watermark value (e.g., timestamp high-water mark).
        custom: Custom metadata dictionary.
    """

    created_at: datetime = field(default_factory=datetime.utcnow)
    rows_processed: int = 0
    processing_time_ms: int = 0
    watermark: str | None = None
    custom: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "created_at": self.created_at.isoformat(),
            "rows_processed": self.rows_processed,
            "processing_time_ms": self.processing_time_ms,
            "watermark": self.watermark,
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CheckpointMetadata":
        """Create from dictionary."""
        return cls(
            created_at=datetime.fromisoformat(data["created_at"]),
            rows_processed=data.get("rows_processed", 0),
            processing_time_ms=data.get("processing_time_ms", 0),
            watermark=data.get("watermark"),
            custom=data.get("custom", {}),
        )


@dataclass
class Checkpoint:
    """Represents a processing checkpoint.

    A checkpoint captures the state of incremental processing at a point
    in time, allowing processing to resume from that state.

    Attributes:
        checkpoint_id: Unique identifier for this checkpoint.
        transform_id: The transform this checkpoint belongs to.
        state: The checkpoint state data.
        metadata: Associated metadata.
        version: Checkpoint format version.
    """

    checkpoint_id: str
    transform_id: str
    state: dict[str, Any]
    metadata: CheckpointMetadata = field(default_factory=CheckpointMetadata)
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "transform_id": self.transform_id,
            "state": self.state,
            "metadata": self.metadata.to_dict(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Checkpoint":
        """Create from dictionary."""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            transform_id=data["transform_id"],
            state=data.get("state", {}),
            metadata=CheckpointMetadata.from_dict(data.get("metadata", {})),
            version=data.get("version", 1),
        )


class CheckpointStore(ABC):
    """Abstract base class for checkpoint storage.

    Provides an interface for persisting and retrieving checkpoints.
    Implementations can use different backends (file, database, etc.).

    Example:
        ```python
        store = FileCheckpointStore("/path/to/checkpoints")
        await store.save(checkpoint)
        latest = await store.get_latest("my_transform")
        ```
    """

    @abstractmethod
    async def save(self, checkpoint: Checkpoint) -> None:
        """Save a checkpoint.

        Args:
            checkpoint: The checkpoint to save.
        """
        ...

    @abstractmethod
    async def get(self, checkpoint_id: str) -> Checkpoint | None:
        """Get a checkpoint by ID.

        Args:
            checkpoint_id: The checkpoint ID.

        Returns:
            The checkpoint if found, None otherwise.
        """
        ...

    @abstractmethod
    async def get_latest(self, transform_id: str) -> Checkpoint | None:
        """Get the latest checkpoint for a transform.

        Args:
            transform_id: The transform ID.

        Returns:
            The latest checkpoint if any, None otherwise.
        """
        ...

    @abstractmethod
    async def list(self, transform_id: str, limit: int = 10) -> list[Checkpoint]:
        """List checkpoints for a transform.

        Args:
            transform_id: The transform ID.
            limit: Maximum number of checkpoints to return.

        Returns:
            List of checkpoints, newest first.
        """
        ...

    @abstractmethod
    async def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint.

        Args:
            checkpoint_id: The checkpoint ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        ...

    @abstractmethod
    async def cleanup(self, transform_id: str, keep_count: int = 5) -> int:
        """Clean up old checkpoints, keeping only the most recent.

        Args:
            transform_id: The transform ID.
            keep_count: Number of checkpoints to keep.

        Returns:
            Number of checkpoints deleted.
        """
        ...


class MemoryCheckpointStore(CheckpointStore):
    """In-memory checkpoint store for testing and development.

    Stores checkpoints in memory. Data is lost when the process exits.
    """

    def __init__(self) -> None:
        """Initialize the in-memory store."""
        self._checkpoints: dict[str, Checkpoint] = {}
        self._by_transform: dict[str, list[str]] = {}

    async def save(self, checkpoint: Checkpoint) -> None:
        """Save a checkpoint to memory."""
        self._checkpoints[checkpoint.checkpoint_id] = checkpoint

        if checkpoint.transform_id not in self._by_transform:
            self._by_transform[checkpoint.transform_id] = []
        self._by_transform[checkpoint.transform_id].append(checkpoint.checkpoint_id)

    async def get(self, checkpoint_id: str) -> Checkpoint | None:
        """Get a checkpoint by ID."""
        return self._checkpoints.get(checkpoint_id)

    async def get_latest(self, transform_id: str) -> Checkpoint | None:
        """Get the latest checkpoint for a transform."""
        checkpoint_ids = self._by_transform.get(transform_id, [])
        if not checkpoint_ids:
            return None

        # Get the most recent by creation time
        checkpoints = [
            self._checkpoints[cid]
            for cid in checkpoint_ids
            if cid in self._checkpoints
        ]
        if not checkpoints:
            return None

        return max(checkpoints, key=lambda c: c.metadata.created_at)

    async def list(self, transform_id: str, limit: int = 10) -> list[Checkpoint]:
        """List checkpoints for a transform."""
        checkpoint_ids = self._by_transform.get(transform_id, [])
        checkpoints = [
            self._checkpoints[cid]
            for cid in checkpoint_ids
            if cid in self._checkpoints
        ]
        checkpoints.sort(key=lambda c: c.metadata.created_at, reverse=True)
        return checkpoints[:limit]

    async def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        if checkpoint_id not in self._checkpoints:
            return False

        checkpoint = self._checkpoints.pop(checkpoint_id)
        if checkpoint.transform_id in self._by_transform:
            self._by_transform[checkpoint.transform_id] = [
                cid for cid in self._by_transform[checkpoint.transform_id]
                if cid != checkpoint_id
            ]
        return True

    async def cleanup(self, transform_id: str, keep_count: int = 5) -> int:
        """Clean up old checkpoints."""
        checkpoints = await self.list(transform_id, limit=1000)
        to_delete = checkpoints[keep_count:]

        deleted = 0
        for checkpoint in to_delete:
            if await self.delete(checkpoint.checkpoint_id):
                deleted += 1

        return deleted


class FileCheckpointStore(CheckpointStore):
    """File-based checkpoint store.

    Stores checkpoints as JSON files in a directory structure.
    """

    def __init__(self, base_path: str | Path) -> None:
        """Initialize the file-based store.

        Args:
            base_path: Base directory for checkpoint storage.
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _checkpoint_path(self, transform_id: str, checkpoint_id: str) -> Path:
        """Get the path for a checkpoint file."""
        transform_dir = self.base_path / transform_id
        transform_dir.mkdir(parents=True, exist_ok=True)
        return transform_dir / f"{checkpoint_id}.json"

    async def save(self, checkpoint: Checkpoint) -> None:
        """Save a checkpoint to file."""
        path = self._checkpoint_path(checkpoint.transform_id, checkpoint.checkpoint_id)
        with open(path, "w") as f:
            json.dump(checkpoint.to_dict(), f, indent=2)

    async def get(self, checkpoint_id: str) -> Checkpoint | None:
        """Get a checkpoint by ID."""
        # Search all transform directories
        for transform_dir in self.base_path.iterdir():
            if not transform_dir.is_dir():
                continue
            path = transform_dir / f"{checkpoint_id}.json"
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
                    return Checkpoint.from_dict(data)
        return None

    async def get_latest(self, transform_id: str) -> Checkpoint | None:
        """Get the latest checkpoint for a transform."""
        transform_dir = self.base_path / transform_id
        if not transform_dir.exists():
            return None

        latest: Checkpoint | None = None
        latest_time: datetime | None = None

        for path in transform_dir.glob("*.json"):
            with open(path) as f:
                data = json.load(f)
                checkpoint = Checkpoint.from_dict(data)
                if latest_time is None or checkpoint.metadata.created_at > latest_time:
                    latest = checkpoint
                    latest_time = checkpoint.metadata.created_at

        return latest

    async def list(self, transform_id: str, limit: int = 10) -> list[Checkpoint]:
        """List checkpoints for a transform."""
        transform_dir = self.base_path / transform_id
        if not transform_dir.exists():
            return []

        checkpoints: list[Checkpoint] = []
        for path in transform_dir.glob("*.json"):
            with open(path) as f:
                data = json.load(f)
                checkpoints.append(Checkpoint.from_dict(data))

        checkpoints.sort(key=lambda c: c.metadata.created_at, reverse=True)
        return checkpoints[:limit]

    async def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        # Search all transform directories
        for transform_dir in self.base_path.iterdir():
            if not transform_dir.is_dir():
                continue
            path = transform_dir / f"{checkpoint_id}.json"
            if path.exists():
                path.unlink()
                return True
        return False

    async def cleanup(self, transform_id: str, keep_count: int = 5) -> int:
        """Clean up old checkpoints."""
        checkpoints = await self.list(transform_id, limit=1000)
        to_delete = checkpoints[keep_count:]

        deleted = 0
        for checkpoint in to_delete:
            path = self._checkpoint_path(transform_id, checkpoint.checkpoint_id)
            if path.exists():
                path.unlink()
                deleted += 1

        return deleted
