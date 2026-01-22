"""MediaSet and MediaItem models for managing media collections."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class MediaType(str, Enum):
    """Supported media types."""

    IMAGE = "image"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"
    # VIDEO and AUDIO deferred per consolidated architecture


class MediaStatus(str, Enum):
    """Processing status for media items."""

    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class MediaItem(BaseModel):
    """
    Represents a single media item in a MediaSet.

    Attributes:
        id: Unique identifier for the media item
        media_set_id: ID of the parent MediaSet
        name: Original filename or display name
        media_type: Type of media (image, document, etc.)
        mime_type: MIME type of the file
        status: Current processing status
        storage_path: Path in storage backend
        storage_backend: Name of storage backend (e.g., "s3", "local")
        size_bytes: File size in bytes
        checksum: SHA-256 checksum of file content
        metadata: Extracted metadata (dimensions, page count, etc.)
        extracted_text: Text content extracted from the media
        thumbnails: List of thumbnail paths
        processing_errors: List of any errors during processing
        ontology_object_id: Optional link to ontology object
    """

    id: str
    media_set_id: str
    name: str
    media_type: MediaType
    mime_type: str
    status: MediaStatus = MediaStatus.PENDING

    # Storage
    storage_path: str
    storage_backend: str
    size_bytes: int
    checksum: str  # SHA-256

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)
    extracted_text: str | None = None
    thumbnails: list[str] = Field(default_factory=list)

    # Processing
    processed_at: datetime | None = None
    processing_errors: list[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Ontology link
    ontology_object_id: str | None = None


class ProcessingConfig(BaseModel):
    """
    Configuration for media processing pipeline.

    Attributes:
        extract_text: Whether to extract text from documents
        generate_thumbnails: Whether to generate image thumbnails
        thumbnail_sizes: List of thumbnail dimensions (width, height)
        run_ocr: Whether to run OCR on images
        ocr_languages: Languages to use for OCR
        extract_entities: Whether to extract named entities from text
        embed_content: Whether to generate vector embeddings
        custom_processors: List of custom processor names to run
    """

    extract_text: bool = True
    generate_thumbnails: bool = True
    thumbnail_sizes: list[tuple[int, int]] = Field(
        default_factory=lambda: [(128, 128), (256, 256), (512, 512)]
    )
    run_ocr: bool = False
    ocr_languages: list[str] = Field(default_factory=lambda: ["en"])
    extract_entities: bool = False
    embed_content: bool = True
    custom_processors: list[str] = Field(default_factory=list)


class MediaSet(BaseModel):
    """
    A collection of related media items.

    MediaSets provide organization and shared processing configuration
    for groups of media items.

    Attributes:
        id: Unique identifier for the media set
        name: Display name for the set
        description: Optional description
        processing_config: Default processing configuration for items
        auto_process: Whether to automatically process uploaded items
        item_count: Number of items in the set
        total_size_bytes: Total size of all items
        processed_count: Number of successfully processed items
        owner_id: ID of the owning user
        visibility: Access level (private, team, public)
    """

    id: str
    name: str
    description: str | None = None

    # Configuration
    processing_config: ProcessingConfig = Field(default_factory=ProcessingConfig)
    auto_process: bool = True

    # Stats
    item_count: int = 0
    total_size_bytes: int = 0
    processed_count: int = 0

    # Access
    owner_id: str
    visibility: Literal["private", "team", "public"] = "private"

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def add_item(self, item: MediaItem) -> None:
        """Update stats when an item is added (for use by repositories)."""
        self.item_count += 1
        self.total_size_bytes += item.size_bytes
        self.updated_at = datetime.utcnow()

    def remove_item(self, item: MediaItem) -> None:
        """Update stats when an item is removed (for use by repositories)."""
        self.item_count = max(0, self.item_count - 1)
        self.total_size_bytes = max(0, self.total_size_bytes - item.size_bytes)
        if item.status == MediaStatus.READY:
            self.processed_count = max(0, self.processed_count - 1)
        self.updated_at = datetime.utcnow()

    def mark_item_processed(self) -> None:
        """Increment processed count (for use by repositories)."""
        self.processed_count += 1
        self.updated_at = datetime.utcnow()
