"""Document extraction and chunking for PDF, DOCX, XLSX, and more."""

from forge_media.documents.extractors.base import (
    DocumentExtractor,
    ExtractedDocument,
    DocumentPage,
    ExtractedTable,
    ExtractedImage,
)
from forge_media.documents.extractors.pdf import PDFExtractor
from forge_media.documents.extractors.docx import DOCXExtractor
from forge_media.documents.extractors.xlsx import XLSXExtractor
from forge_media.documents.chunking import (
    TextChunk,
    ChunkingStrategy,
    FixedSizeChunker,
    SemanticChunker,
    PageChunker,
)

__all__ = [
    # Base classes
    "DocumentExtractor",
    "ExtractedDocument",
    "DocumentPage",
    "ExtractedTable",
    "ExtractedImage",
    # Extractors
    "PDFExtractor",
    "DOCXExtractor",
    "XLSXExtractor",
    # Chunking
    "TextChunk",
    "ChunkingStrategy",
    "FixedSizeChunker",
    "SemanticChunker",
    "PageChunker",
]
