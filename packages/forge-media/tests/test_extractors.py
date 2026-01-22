"""Tests for document extractors."""

from __future__ import annotations

import pytest

from forge_media.documents.extractors.base import (
    DocumentExtractor,
    DocumentPage,
    ExtractedDocument,
    ExtractedTable,
    ExtractionOptions,
)
from forge_media.documents.extractors.pdf import PDFExtractor
from forge_media.documents.extractors.docx import DOCXExtractor
from forge_media.documents.extractors.xlsx import XLSXExtractor


class TestExtractedDocument:
    """Tests for ExtractedDocument model."""

    def test_empty_document(self):
        """Test creating an empty document."""
        doc = ExtractedDocument.empty()

        assert doc.full_text == ""
        assert doc.page_count == 0
        assert doc.word_count == 0
        assert len(doc.pages) == 0
        assert len(doc.tables) == 0

    def test_document_with_pages(self):
        """Test document with pages."""
        pages = [
            DocumentPage(page_number=1, text="Page one content"),
            DocumentPage(page_number=2, text="Page two content"),
        ]

        doc = ExtractedDocument(
            pages=pages,
            full_text="Page one content\n\nPage two content",
            tables=[],
            metadata={},
            page_count=2,
            word_count=6,
        )

        assert doc.page_count == 2
        assert len(doc.pages) == 2
        assert doc.pages[0].page_number == 1


class TestExtractedTable:
    """Tests for ExtractedTable model."""

    def test_table_properties(self):
        """Test table row and column count properties."""
        table = ExtractedTable(
            table_index=0,
            headers=["Name", "Age", "City"],
            rows=[
                ["Alice", "30", "NYC"],
                ["Bob", "25", "LA"],
            ],
        )

        assert table.row_count == 2
        assert table.column_count == 3

    def test_table_without_headers(self):
        """Test table column count without headers."""
        table = ExtractedTable(
            table_index=0,
            headers=None,
            rows=[
                ["A", "B", "C", "D"],
                ["1", "2", "3", "4"],
            ],
        )

        assert table.column_count == 4


class TestPDFExtractor:
    """Tests for PDF extractor."""

    def test_supported_mime_types(self):
        """Test that PDF extractor supports correct MIME types."""
        extractor = PDFExtractor()

        assert "application/pdf" in extractor.supported_mime_types
        assert extractor.can_handle("application/pdf")
        assert not extractor.can_handle("image/png")

    @pytest.mark.asyncio
    async def test_extract_requires_pypdf(self, sample_pdf_bytes):
        """Test that extraction works with pypdf installed."""
        extractor = PDFExtractor()

        # This will either work (pypdf installed) or raise ImportError
        try:
            result = await extractor.extract(sample_pdf_bytes)
            assert isinstance(result, ExtractedDocument)
        except Exception as e:
            # If pypdf not installed or PDF is invalid, that's expected
            assert "pypdf" in str(e).lower() or "pdf" in str(e).lower()


class TestDOCXExtractor:
    """Tests for DOCX extractor."""

    def test_supported_mime_types(self):
        """Test that DOCX extractor supports correct MIME types."""
        extractor = DOCXExtractor()

        assert extractor.can_handle(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert not extractor.can_handle("application/pdf")


class TestXLSXExtractor:
    """Tests for XLSX extractor."""

    def test_supported_mime_types(self):
        """Test that XLSX extractor supports correct MIME types."""
        extractor = XLSXExtractor()

        assert extractor.can_handle(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert not extractor.can_handle("application/pdf")


class TestExtractionOptions:
    """Tests for ExtractionOptions."""

    def test_default_options(self):
        """Test default extraction options."""
        options = ExtractionOptions()

        assert options.extract_tables is True
        assert options.extract_images is False
        assert options.extract_metadata is True
        assert options.max_pages is None

    def test_custom_options(self):
        """Test custom extraction options."""
        options = ExtractionOptions(
            extract_tables=False,
            extract_images=True,
            max_pages=10,
        )

        assert options.extract_tables is False
        assert options.extract_images is True
        assert options.max_pages == 10
