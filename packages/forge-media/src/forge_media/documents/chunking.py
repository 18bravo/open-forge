"""Text chunking strategies for document content."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from forge_media.documents.extractors.base import ExtractedDocument


class TextChunk(BaseModel):
    """
    A chunk of text from a document.

    Attributes:
        text: The chunk content
        start_index: Character offset in the source document
        end_index: End character offset
        metadata: Additional chunk metadata
        page_number: Source page number (if applicable)
        section: Section heading (if detected)
    """

    text: str
    start_index: int
    end_index: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    page_number: int | None = None
    section: str | None = None

    @property
    def length(self) -> int:
        """Character length of the chunk."""
        return len(self.text)


class ChunkingStrategy(ABC):
    """
    Abstract base class for text chunking strategies.

    Chunking strategies split extracted documents into smaller pieces
    suitable for embedding and retrieval.
    """

    @abstractmethod
    def chunk(
        self,
        document: ExtractedDocument,
        config: dict[str, Any] | None = None,
    ) -> list[TextChunk]:
        """
        Split a document into chunks.

        Args:
            document: The extracted document to chunk
            config: Optional strategy-specific configuration

        Returns:
            List of TextChunk objects
        """
        ...


class FixedSizeChunker(ChunkingStrategy):
    """
    Chunk text by fixed character count with overlap.

    This is the simplest chunking strategy, splitting text at fixed
    intervals while trying to break at natural boundaries (newlines).

    Example:
        ```python
        chunker = FixedSizeChunker(chunk_size=1000, overlap=200)
        chunks = chunker.chunk(extracted_doc)
        for chunk in chunks:
            print(f"Chunk: {chunk.length} chars")
        ```
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 200,
        separator: str = "\n",
    ):
        """
        Initialize the fixed-size chunker.

        Args:
            chunk_size: Target size for each chunk in characters
            overlap: Number of characters to overlap between chunks
            separator: Preferred break point character
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.separator = separator

    def chunk(
        self,
        document: ExtractedDocument,
        config: dict[str, Any] | None = None,
    ) -> list[TextChunk]:
        """Split document into fixed-size chunks."""
        text = document.full_text
        chunks: list[TextChunk] = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # Try to break at separator
            if end < len(text):
                break_point = text.rfind(self.separator, start, end)
                if break_point > start:
                    end = break_point + 1

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    TextChunk(
                        text=chunk_text,
                        start_index=start,
                        end_index=end,
                    )
                )

            start = end - self.overlap
            if start <= chunks[-1].start_index if chunks else 0:
                start = end  # Prevent infinite loop

        return chunks


class SemanticChunker(ChunkingStrategy):
    """
    Chunk by semantic boundaries (paragraphs, sections).

    This strategy respects natural document structure by breaking
    at paragraph boundaries and respecting page divisions.

    Example:
        ```python
        chunker = SemanticChunker(max_chunk_size=2000)
        chunks = chunker.chunk(extracted_doc)
        ```
    """

    def __init__(self, max_chunk_size: int = 2000):
        """
        Initialize the semantic chunker.

        Args:
            max_chunk_size: Maximum characters per chunk
        """
        self.max_chunk_size = max_chunk_size

    def chunk(
        self,
        document: ExtractedDocument,
        config: dict[str, Any] | None = None,
    ) -> list[TextChunk]:
        """Split document at semantic boundaries."""
        chunks: list[TextChunk] = []
        current_index = 0

        for page in document.pages:
            # Split page into paragraphs
            paragraphs = page.text.split("\n\n")

            current_chunk: list[str] = []
            current_size = 0
            chunk_start = current_index

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                # Check if adding this paragraph exceeds max size
                if current_size + len(para) > self.max_chunk_size and current_chunk:
                    # Save current chunk
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(
                        TextChunk(
                            text=chunk_text,
                            start_index=chunk_start,
                            end_index=chunk_start + len(chunk_text),
                            page_number=page.page_number,
                        )
                    )
                    chunk_start = current_index
                    current_chunk = []
                    current_size = 0

                current_chunk.append(para)
                current_size += len(para) + 2  # +2 for "\n\n"
                current_index += len(para) + 2

            # Save remaining content from this page
            if current_chunk:
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(
                    TextChunk(
                        text=chunk_text,
                        start_index=chunk_start,
                        end_index=chunk_start + len(chunk_text),
                        page_number=page.page_number,
                    )
                )

        return chunks


class PageChunker(ChunkingStrategy):
    """
    Chunk by document pages.

    Each page becomes a separate chunk. Useful when page boundaries
    are meaningful (e.g., scanned documents, presentations).

    Example:
        ```python
        chunker = PageChunker()
        chunks = chunker.chunk(extracted_doc)
        # One chunk per page
        ```
    """

    def chunk(
        self,
        document: ExtractedDocument,
        config: dict[str, Any] | None = None,
    ) -> list[TextChunk]:
        """Create one chunk per page."""
        chunks: list[TextChunk] = []
        current_index = 0

        for page in document.pages:
            text = page.text.strip()
            if text:
                chunks.append(
                    TextChunk(
                        text=text,
                        start_index=current_index,
                        end_index=current_index + len(text),
                        page_number=page.page_number,
                    )
                )
            current_index += len(text) + 2  # Account for page separator

        return chunks


def get_chunker(strategy: str, **kwargs) -> ChunkingStrategy:
    """
    Factory function to get a chunking strategy by name.

    Args:
        strategy: Strategy name ("fixed", "semantic", or "page")
        **kwargs: Strategy-specific configuration

    Returns:
        ChunkingStrategy instance

    Raises:
        ValueError: If strategy name is unknown
    """
    strategies = {
        "fixed": FixedSizeChunker,
        "semantic": SemanticChunker,
        "page": PageChunker,
    }

    if strategy not in strategies:
        raise ValueError(
            f"Unknown chunking strategy: {strategy}. "
            f"Available: {list(strategies.keys())}"
        )

    return strategies[strategy](**kwargs)
