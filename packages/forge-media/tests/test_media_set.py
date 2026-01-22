"""Tests for MediaSet and MediaItem models."""

from __future__ import annotations

from datetime import datetime

import pytest

from forge_media.core.media_set import (
    MediaItem,
    MediaSet,
    MediaStatus,
    MediaType,
    ProcessingConfig,
)


class TestMediaItem:
    """Tests for MediaItem model."""

    def test_create_media_item(self):
        """Test creating a basic media item."""
        item = MediaItem(
            id="item-123",
            media_set_id="set-456",
            name="document.pdf",
            media_type=MediaType.DOCUMENT,
            mime_type="application/pdf",
            storage_path="media/set-456/item-123/document.pdf",
            storage_backend="s3",
            size_bytes=1024,
            checksum="abc123",
        )

        assert item.id == "item-123"
        assert item.media_set_id == "set-456"
        assert item.name == "document.pdf"
        assert item.media_type == MediaType.DOCUMENT
        assert item.status == MediaStatus.PENDING
        assert item.size_bytes == 1024

    def test_media_item_defaults(self):
        """Test default values for optional fields."""
        item = MediaItem(
            id="item-123",
            media_set_id="set-456",
            name="image.png",
            media_type=MediaType.IMAGE,
            mime_type="image/png",
            storage_path="path/to/image.png",
            storage_backend="local",
            size_bytes=2048,
            checksum="def456",
        )

        assert item.status == MediaStatus.PENDING
        assert item.metadata == {}
        assert item.extracted_text is None
        assert item.thumbnails == []
        assert item.processing_errors == []
        assert item.ontology_object_id is None

    def test_media_item_with_metadata(self):
        """Test media item with metadata."""
        item = MediaItem(
            id="item-123",
            media_set_id="set-456",
            name="photo.jpg",
            media_type=MediaType.IMAGE,
            mime_type="image/jpeg",
            storage_path="path/to/photo.jpg",
            storage_backend="s3",
            size_bytes=5000,
            checksum="ghi789",
            metadata={"width": 1920, "height": 1080},
        )

        assert item.metadata["width"] == 1920
        assert item.metadata["height"] == 1080


class TestMediaSet:
    """Tests for MediaSet model."""

    def test_create_media_set(self):
        """Test creating a basic media set."""
        media_set = MediaSet(
            id="set-123",
            name="Project Documents",
            owner_id="user-456",
        )

        assert media_set.id == "set-123"
        assert media_set.name == "Project Documents"
        assert media_set.owner_id == "user-456"
        assert media_set.visibility == "private"
        assert media_set.auto_process is True

    def test_media_set_with_config(self):
        """Test media set with custom processing config."""
        config = ProcessingConfig(
            extract_text=True,
            run_ocr=True,
            ocr_languages=["en", "es"],
        )

        media_set = MediaSet(
            id="set-123",
            name="Scanned Documents",
            owner_id="user-456",
            processing_config=config,
        )

        assert media_set.processing_config.run_ocr is True
        assert "es" in media_set.processing_config.ocr_languages

    def test_add_item_updates_stats(self):
        """Test that add_item updates set statistics."""
        media_set = MediaSet(
            id="set-123",
            name="Test Set",
            owner_id="user-456",
        )

        item = MediaItem(
            id="item-123",
            media_set_id="set-123",
            name="doc.pdf",
            media_type=MediaType.DOCUMENT,
            mime_type="application/pdf",
            storage_path="path/doc.pdf",
            storage_backend="s3",
            size_bytes=1000,
            checksum="abc",
        )

        initial_count = media_set.item_count
        initial_size = media_set.total_size_bytes

        media_set.add_item(item)

        assert media_set.item_count == initial_count + 1
        assert media_set.total_size_bytes == initial_size + 1000

    def test_remove_item_updates_stats(self):
        """Test that remove_item updates set statistics."""
        media_set = MediaSet(
            id="set-123",
            name="Test Set",
            owner_id="user-456",
            item_count=5,
            total_size_bytes=5000,
            processed_count=3,
        )

        item = MediaItem(
            id="item-123",
            media_set_id="set-123",
            name="doc.pdf",
            media_type=MediaType.DOCUMENT,
            mime_type="application/pdf",
            storage_path="path/doc.pdf",
            storage_backend="s3",
            size_bytes=1000,
            checksum="abc",
            status=MediaStatus.READY,
        )

        media_set.remove_item(item)

        assert media_set.item_count == 4
        assert media_set.total_size_bytes == 4000
        assert media_set.processed_count == 2


class TestProcessingConfig:
    """Tests for ProcessingConfig model."""

    def test_default_config(self):
        """Test default processing configuration."""
        config = ProcessingConfig()

        assert config.extract_text is True
        assert config.generate_thumbnails is True
        assert config.run_ocr is False
        assert config.embed_content is True
        assert "en" in config.ocr_languages

    def test_custom_thumbnail_sizes(self):
        """Test custom thumbnail size configuration."""
        config = ProcessingConfig(
            thumbnail_sizes=[(64, 64), (128, 128)],
        )

        assert len(config.thumbnail_sizes) == 2
        assert (64, 64) in config.thumbnail_sizes
