"""Base classes and protocols for document extraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ExtractedImage(BaseModel):
    """An image extracted from a document."""

    page_number: int
    image_index: int
    image_data: bytes | None = None  # Raw image bytes (optional, may be large)
    mime_type: str = "image/png"
    width: int | None = None
    height: int | None = None
    caption: str | None = None


class ExtractedTable(BaseModel):
    """A table extracted from a document."""

    page_number: int | None = None
    table_index: int
    headers: list[str] | None = None
    rows: list[list[str]]
    confidence: float = 1.0

    @property
    def row_count(self) -> int:
        """Number of data rows (excluding header)."""
        return len(self.rows)

    @property
    def column_count(self) -> int:
        """Number of columns."""
        if self.headers:
            return len(self.headers)
        if self.rows:
            return len(self.rows[0])
        return 0


class DocumentPage(BaseModel):
    """A single page from a document."""

    page_number: int
    text: str
    tables: list[ExtractedTable] = Field(default_factory=list)
    images: list[ExtractedImage] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExtractedDocument(BaseModel):
    """
    Complete extraction result from a document.

    Contains the full text, individual pages, tables, and metadata
    extracted from the document.
    """

    pages: list[DocumentPage]
    full_text: str
    tables: list[ExtractedTable]
    metadata: dict[str, Any]
    page_count: int
    word_count: int

    @classmethod
    def empty(cls) -> ExtractedDocument:
        """Create an empty extraction result."""
        return cls(
            pages=[],
            full_text="",
            tables=[],
            metadata={},
            page_count=0,
            word_count=0,
        )


class ExtractionOptions(BaseModel):
    """Options for document extraction."""

    extract_tables: bool = True
    extract_images: bool = False
    extract_metadata: bool = True
    # OCR is handled separately via vision module
    max_pages: int | None = None  # Limit pages to extract


class DocumentExtractor(ABC):
    """
    Abstract base class for document extractors.

    Implementations should extract text, tables, and metadata from
    specific document formats (PDF, DOCX, XLSX, etc.).

    Example:
        ```python
        class PDFExtractor(DocumentExtractor):
            @property
            def supported_mime_types(self) -> list[str]:
                return ["application/pdf"]

            async def extract(self, data: bytes, options: ExtractionOptions | None = None):
                # Implementation here
                ...
        ```
    """

    @property
    @abstractmethod
    def supported_mime_types(self) -> list[str]:
        """
        List of MIME types this extractor can handle.

        Returns:
            List of MIME type strings (e.g., ["application/pdf"])
        """
        ...

    @abstractmethod
    async def extract(
        self,
        data: bytes,
        options: ExtractionOptions | None = None,
    ) -> ExtractedDocument:
        """
        Extract content from document data.

        Args:
            data: Raw document bytes
            options: Extraction options

        Returns:
            ExtractedDocument containing text, tables, and metadata

        Raises:
            ValueError: If the document format is invalid
            ExtractionError: If extraction fails
        """
        ...

    def can_handle(self, mime_type: str) -> bool:
        """Check if this extractor can handle the given MIME type."""
        return mime_type in self.supported_mime_types


class ExtractionError(Exception):
    """Raised when document extraction fails."""

    def __init__(self, message: str, cause: Exception | None = None):
        super().__init__(message)
        self.cause = cause
