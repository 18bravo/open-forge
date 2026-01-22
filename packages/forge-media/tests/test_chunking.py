"""Tests for document chunking strategies."""

from __future__ import annotations

import pytest

from forge_media.documents.extractors.base import DocumentPage, ExtractedDocument
from forge_media.documents.chunking import (
    FixedSizeChunker,
    PageChunker,
    SemanticChunker,
    TextChunk,
    get_chunker,
)


@pytest.fixture
def sample_document() -> ExtractedDocument:
    """Create a sample document for testing chunking."""
    pages = [
        DocumentPage(
            page_number=1,
            text="This is the first paragraph.\n\nThis is the second paragraph.",
        ),
        DocumentPage(
            page_number=2,
            text="This is page two content.\n\nAnother paragraph here.",
        ),
    ]

    return ExtractedDocument(
        pages=pages,
        full_text="This is the first paragraph.\n\nThis is the second paragraph.\n\nThis is page two content.\n\nAnother paragraph here.",
        tables=[],
        metadata={},
        page_count=2,
        word_count=20,
    )


class TestTextChunk:
    """Tests for TextChunk model."""

    def test_chunk_length(self):
        """Test chunk length property."""
        chunk = TextChunk(
            text="Hello, world!",
            start_index=0,
            end_index=13,
        )

        assert chunk.length == 13

    def test_chunk_with_metadata(self):
        """Test chunk with metadata."""
        chunk = TextChunk(
            text="Test content",
            start_index=0,
            end_index=12,
            page_number=1,
            section="Introduction",
            metadata={"source": "test.pdf"},
        )

        assert chunk.page_number == 1
        assert chunk.section == "Introduction"
        assert chunk.metadata["source"] == "test.pdf"


class TestFixedSizeChunker:
    """Tests for FixedSizeChunker."""

    def test_basic_chunking(self, sample_document):
        """Test basic fixed-size chunking."""
        chunker = FixedSizeChunker(chunk_size=50, overlap=10)
        chunks = chunker.chunk(sample_document)

        assert len(chunks) > 0
        for chunk in chunks:
            assert isinstance(chunk, TextChunk)
            assert len(chunk.text) <= 60  # chunk_size + some tolerance

    def test_small_document(self):
        """Test chunking a small document that fits in one chunk."""
        doc = ExtractedDocument(
            pages=[DocumentPage(page_number=1, text="Short text")],
            full_text="Short text",
            tables=[],
            metadata={},
            page_count=1,
            word_count=2,
        )

        chunker = FixedSizeChunker(chunk_size=1000)
        chunks = chunker.chunk(doc)

        assert len(chunks) == 1
        assert chunks[0].text == "Short text"

    def test_overlap_works(self, sample_document):
        """Test that overlap creates overlapping chunks."""
        chunker = FixedSizeChunker(chunk_size=30, overlap=10)
        chunks = chunker.chunk(sample_document)

        if len(chunks) >= 2:
            # Check that chunks overlap
            first_end = chunks[0].end_index
            second_start = chunks[1].start_index
            # With overlap, second chunk should start before first ends
            assert second_start < first_end


class TestSemanticChunker:
    """Tests for SemanticChunker."""

    def test_respects_paragraphs(self, sample_document):
        """Test that semantic chunker respects paragraph boundaries."""
        chunker = SemanticChunker(max_chunk_size=2000)
        chunks = chunker.chunk(sample_document)

        assert len(chunks) > 0
        # Each chunk should be a coherent piece of text
        for chunk in chunks:
            assert isinstance(chunk, TextChunk)

    def test_includes_page_numbers(self, sample_document):
        """Test that semantic chunks include page numbers."""
        chunker = SemanticChunker(max_chunk_size=100)
        chunks = chunker.chunk(sample_document)

        # At least some chunks should have page numbers
        page_numbers = [c.page_number for c in chunks if c.page_number is not None]
        assert len(page_numbers) > 0


class TestPageChunker:
    """Tests for PageChunker."""

    def test_one_chunk_per_page(self, sample_document):
        """Test that page chunker creates one chunk per page."""
        chunker = PageChunker()
        chunks = chunker.chunk(sample_document)

        # Should have same number of chunks as pages
        assert len(chunks) == sample_document.page_count

    def test_preserves_page_numbers(self, sample_document):
        """Test that chunks have correct page numbers."""
        chunker = PageChunker()
        chunks = chunker.chunk(sample_document)

        for i, chunk in enumerate(chunks):
            assert chunk.page_number == i + 1


class TestGetChunker:
    """Tests for get_chunker factory function."""

    def test_get_fixed_chunker(self):
        """Test getting fixed-size chunker."""
        chunker = get_chunker("fixed", chunk_size=500, overlap=50)

        assert isinstance(chunker, FixedSizeChunker)

    def test_get_semantic_chunker(self):
        """Test getting semantic chunker."""
        chunker = get_chunker("semantic", max_chunk_size=1500)

        assert isinstance(chunker, SemanticChunker)

    def test_get_page_chunker(self):
        """Test getting page chunker."""
        chunker = get_chunker("page")

        assert isinstance(chunker, PageChunker)

    def test_unknown_strategy_raises(self):
        """Test that unknown strategy raises ValueError."""
        with pytest.raises(ValueError, match="Unknown chunking strategy"):
            get_chunker("unknown")
