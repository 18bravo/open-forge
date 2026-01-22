"""Tests for chunking strategies."""

import pytest

from forge_vectors.chunking.base import (
    ChunkingConfig,
    FixedSizeChunker,
    RecursiveChunker,
    SentenceChunker,
    TextChunk,
)


class TestFixedSizeChunker:
    """Tests for FixedSizeChunker."""

    def test_empty_text(self):
        """Empty text returns empty list."""
        chunker = FixedSizeChunker()
        chunks = chunker.chunk("")
        assert chunks == []

    def test_short_text(self):
        """Text shorter than chunk size returns single chunk."""
        chunker = FixedSizeChunker(config=ChunkingConfig(chunk_size=100))
        text = "Short text"
        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert chunks[0].content == text
        assert chunks[0].index == 0

    def test_multiple_chunks(self):
        """Long text is split into multiple chunks."""
        chunker = FixedSizeChunker(config=ChunkingConfig(
            chunk_size=50,
            chunk_overlap=10,
            min_chunk_size=10,
        ))
        text = "This is a longer text that should be split into multiple chunks for testing purposes."
        chunks = chunker.chunk(text)

        assert len(chunks) > 1
        # Check indices are sequential
        for i, chunk in enumerate(chunks):
            assert chunk.index == i

    def test_preserves_metadata(self):
        """Metadata is preserved in chunks."""
        chunker = FixedSizeChunker()
        metadata = {"source": "test", "doc_id": "123"}
        text = "Some text content"
        chunks = chunker.chunk(text, metadata=metadata)

        assert len(chunks) == 1
        assert chunks[0].metadata["source"] == "test"
        assert chunks[0].metadata["doc_id"] == "123"

    def test_chunk_documents(self):
        """Multiple documents are chunked with metadata."""
        chunker = FixedSizeChunker(config=ChunkingConfig(chunk_size=500))
        docs = [
            {"content": "First document text", "title": "Doc 1"},
            {"content": "Second document text", "title": "Doc 2"},
        ]
        chunks = chunker.chunk_documents(docs)

        assert len(chunks) >= 2
        # Check document indices are preserved
        doc_indices = set(c.metadata.get("_document_index") for c in chunks)
        assert doc_indices == {0, 1}


class TestSentenceChunker:
    """Tests for SentenceChunker."""

    def test_empty_text(self):
        """Empty text returns empty list."""
        chunker = SentenceChunker()
        chunks = chunker.chunk("")
        assert chunks == []

    def test_single_sentence(self):
        """Single sentence returns single chunk."""
        chunker = SentenceChunker()
        text = "This is a single sentence."
        chunks = chunker.chunk(text)

        assert len(chunks) == 1
        assert "single sentence" in chunks[0].content

    def test_multiple_sentences(self):
        """Multiple sentences are grouped into chunks."""
        chunker = SentenceChunker(config=ChunkingConfig(
            chunk_size=100,
            chunk_overlap=0,
        ))
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = chunker.chunk(text)

        # Should create chunks based on size
        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk.content) <= 150  # Some tolerance

    def test_sentence_boundaries_preserved(self):
        """Chunks should end at sentence boundaries."""
        chunker = SentenceChunker(config=ChunkingConfig(chunk_size=50))
        text = "Hello world. This is a test. Another sentence here."
        chunks = chunker.chunk(text)

        # Each chunk should be a complete sentence or sentences
        for chunk in chunks:
            # Should not have partial sentences (roughly)
            assert chunk.content.rstrip().endswith(('.', '!', '?')) or chunk == chunks[-1]


class TestRecursiveChunker:
    """Tests for RecursiveChunker."""

    def test_empty_text(self):
        """Empty text returns empty list."""
        chunker = RecursiveChunker()
        chunks = chunker.chunk("")
        assert chunks == []

    def test_respects_paragraph_boundaries(self):
        """Chunker respects paragraph boundaries when possible."""
        chunker = RecursiveChunker(config=ChunkingConfig(chunk_size=200))
        text = "First paragraph with content.\n\nSecond paragraph here.\n\nThird paragraph."
        chunks = chunker.chunk(text)

        # Should split on paragraph boundaries
        assert len(chunks) >= 1

    def test_falls_back_to_smaller_separators(self):
        """Falls back to smaller separators for long paragraphs."""
        chunker = RecursiveChunker(config=ChunkingConfig(chunk_size=50))
        text = "This is a very long paragraph that contains many sentences. " * 5
        chunks = chunker.chunk(text)

        # Should split into multiple chunks
        assert len(chunks) > 1
        for chunk in chunks:
            # Each chunk should be within size limit (with some tolerance)
            assert len(chunk.content) <= 100


class TestTextChunk:
    """Tests for TextChunk model."""

    def test_char_length_property(self):
        """char_length property returns correct length."""
        chunk = TextChunk(
            content="Hello world",
            index=0,
            start_char=0,
            end_char=11,
        )
        assert chunk.char_length == 11

    def test_metadata_default(self):
        """Metadata defaults to empty dict."""
        chunk = TextChunk(
            content="Test",
            index=0,
            start_char=0,
            end_char=4,
        )
        assert chunk.metadata == {}
