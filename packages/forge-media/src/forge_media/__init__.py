"""
Forge Media - Document extraction, OCR, and image processing for Open Forge.

This package provides media processing capabilities:
- core: MediaSet model and storage integration (uses forge-core storage)
- documents: PDF, DOCX, XLSX extraction with chunking
- vision: OCR (Tesseract, Vision API) and image processing

Note: Video and voice processing are deferred per consolidated architecture.
"""

from forge_media.core.media_set import MediaSet, MediaItem, MediaType, MediaStatus
from forge_media.core.storage import MediaStorageAdapter
from forge_media.documents.extractors.base import (
    DocumentExtractor,
    ExtractedDocument,
    DocumentPage,
    ExtractedTable,
)
from forge_media.documents.chunking import TextChunk, ChunkingStrategy
from forge_media.vision.ocr import OCRProvider, OCRResult

__all__ = [
    # Core
    "MediaSet",
    "MediaItem",
    "MediaType",
    "MediaStatus",
    "MediaStorageAdapter",
    # Documents
    "DocumentExtractor",
    "ExtractedDocument",
    "DocumentPage",
    "ExtractedTable",
    "TextChunk",
    "ChunkingStrategy",
    # Vision
    "OCRProvider",
    "OCRResult",
]

__version__ = "0.1.0"
