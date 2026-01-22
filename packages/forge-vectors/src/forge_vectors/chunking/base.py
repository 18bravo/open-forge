"""
Base chunking types and ChunkingStrategy ABC.

This module defines the core abstractions for text chunking,
used to split documents into smaller pieces for embedding.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ChunkingConfig(BaseModel):
    """Base configuration for chunking strategies."""

    chunk_size: int = Field(
        default=512,
        description="Target chunk size in characters or tokens",
    )
    chunk_overlap: int = Field(
        default=50,
        description="Overlap between consecutive chunks",
    )
    min_chunk_size: int = Field(
        default=100,
        description="Minimum chunk size (avoid tiny fragments)",
    )
    use_tokens: bool = Field(
        default=False,
        description="If True, sizes are in tokens; if False, in characters",
    )


class TextChunk(BaseModel):
    """A chunk of text extracted from a document."""

    content: str = Field(..., description="The chunk text content")
    index: int = Field(..., description="Chunk index within the document")
    start_char: int = Field(..., description="Start character position in source")
    end_char: int = Field(..., description="End character position in source")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (headings, section, etc.)",
    )

    @property
    def char_length(self) -> int:
        """Length of the chunk in characters."""
        return len(self.content)


class ChunkingStrategy(ABC):
    """
    Abstract base class for text chunking strategies.

    Different strategies can be used depending on content type:
    - Fixed size: Simple character/token-based splitting
    - Sentence: Split on sentence boundaries
    - Paragraph: Split on paragraph boundaries
    - Semantic: Use embedding similarity to find natural breaks
    - Recursive: Hierarchically split using multiple separators
    """

    @abstractmethod
    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[TextChunk]:
        """
        Split text into chunks.

        Args:
            text: The text to chunk.
            metadata: Optional metadata to include in all chunks.

        Returns:
            List of TextChunk objects.
        """
        ...

    @abstractmethod
    def chunk_documents(
        self,
        documents: list[dict[str, Any]],
        text_key: str = "content",
    ) -> list[TextChunk]:
        """
        Chunk multiple documents.

        Args:
            documents: List of document dicts with text content.
            text_key: Key to extract text from each document.

        Returns:
            List of TextChunk objects with document metadata.
        """
        ...


class FixedSizeChunker(ChunkingStrategy):
    """
    Fixed-size chunking strategy.

    Splits text into chunks of approximately equal size with optional overlap.
    Simple but effective for many use cases.

    Example:
        chunker = FixedSizeChunker(config=ChunkingConfig(
            chunk_size=500,
            chunk_overlap=50,
        ))
        chunks = chunker.chunk("Long document text...")
    """

    def __init__(self, config: ChunkingConfig | None = None):
        self.config = config or ChunkingConfig()

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[TextChunk]:
        """Split text into fixed-size chunks with overlap."""
        if not text:
            return []

        metadata = metadata or {}
        chunks = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap
        min_size = self.config.min_chunk_size

        start = 0
        index = 0

        while start < len(text):
            # Calculate end position
            end = start + chunk_size

            # If not at the end, try to break at whitespace
            if end < len(text):
                # Look for whitespace to break at
                break_point = text.rfind(" ", start + min_size, end)
                if break_point > start:
                    end = break_point

            # Extract chunk
            chunk_text = text[start:end].strip()

            # Skip empty chunks
            if chunk_text:
                chunks.append(
                    TextChunk(
                        content=chunk_text,
                        index=index,
                        start_char=start,
                        end_char=end,
                        metadata=metadata.copy(),
                    )
                )
                index += 1

            # Move start position (with overlap)
            start = end - overlap
            if start <= chunks[-1].start_char if chunks else 0:
                start = end  # Prevent infinite loop

        return chunks

    def chunk_documents(
        self,
        documents: list[dict[str, Any]],
        text_key: str = "content",
    ) -> list[TextChunk]:
        """Chunk multiple documents, preserving document metadata."""
        all_chunks = []

        for doc_idx, doc in enumerate(documents):
            text = doc.get(text_key, "")
            # Create metadata with document info
            doc_metadata = {
                k: v for k, v in doc.items() if k != text_key
            }
            doc_metadata["_document_index"] = doc_idx

            chunks = self.chunk(text, metadata=doc_metadata)
            all_chunks.extend(chunks)

        return all_chunks


class SentenceChunker(ChunkingStrategy):
    """
    Sentence-based chunking strategy.

    Splits text on sentence boundaries, combining sentences to reach
    target chunk size. Better preserves semantic meaning than fixed-size.

    Example:
        chunker = SentenceChunker(config=ChunkingConfig(
            chunk_size=500,
            chunk_overlap=1,  # Overlap by N sentences
        ))
        chunks = chunker.chunk("Document with sentences. Another sentence.")
    """

    def __init__(self, config: ChunkingConfig | None = None):
        self.config = config or ChunkingConfig()
        # Simple sentence boundary patterns
        self._sentence_endings = [". ", "! ", "? ", ".\n", "!\n", "?\n"]

    def _split_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        sentences = []
        current_start = 0

        i = 0
        while i < len(text):
            # Check for sentence ending
            for ending in self._sentence_endings:
                if text[i:i + len(ending)] == ending:
                    sentence = text[current_start:i + 1].strip()
                    if sentence:
                        sentences.append(sentence)
                    current_start = i + len(ending)
                    i = current_start - 1
                    break
            i += 1

        # Handle remaining text
        remaining = text[current_start:].strip()
        if remaining:
            sentences.append(remaining)

        return sentences

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[TextChunk]:
        """Split text into chunks at sentence boundaries."""
        if not text:
            return []

        metadata = metadata or {}
        sentences = self._split_sentences(text)

        if not sentences:
            return []

        chunks = []
        current_sentences: list[str] = []
        current_length = 0
        chunk_start = 0
        char_pos = 0
        index = 0

        for sentence in sentences:
            sentence_len = len(sentence) + 1  # +1 for space

            # Check if adding this sentence exceeds chunk size
            if current_length + sentence_len > self.config.chunk_size and current_sentences:
                # Create chunk from accumulated sentences
                chunk_text = " ".join(current_sentences)
                chunks.append(
                    TextChunk(
                        content=chunk_text,
                        index=index,
                        start_char=chunk_start,
                        end_char=char_pos,
                        metadata=metadata.copy(),
                    )
                )
                index += 1

                # Handle overlap (keep last N sentences)
                overlap_sentences = self.config.chunk_overlap
                if overlap_sentences > 0 and len(current_sentences) > overlap_sentences:
                    current_sentences = current_sentences[-overlap_sentences:]
                    current_length = sum(len(s) + 1 for s in current_sentences)
                    chunk_start = char_pos - current_length
                else:
                    current_sentences = []
                    current_length = 0
                    chunk_start = char_pos

            current_sentences.append(sentence)
            current_length += sentence_len
            char_pos += sentence_len

        # Handle remaining sentences
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append(
                TextChunk(
                    content=chunk_text,
                    index=index,
                    start_char=chunk_start,
                    end_char=len(text),
                    metadata=metadata.copy(),
                )
            )

        return chunks

    def chunk_documents(
        self,
        documents: list[dict[str, Any]],
        text_key: str = "content",
    ) -> list[TextChunk]:
        """Chunk multiple documents at sentence boundaries."""
        all_chunks = []

        for doc_idx, doc in enumerate(documents):
            text = doc.get(text_key, "")
            doc_metadata = {
                k: v for k, v in doc.items() if k != text_key
            }
            doc_metadata["_document_index"] = doc_idx

            chunks = self.chunk(text, metadata=doc_metadata)
            all_chunks.extend(chunks)

        return all_chunks


class RecursiveChunker(ChunkingStrategy):
    """
    Recursive text chunking strategy.

    Splits text hierarchically using multiple separators, trying larger
    boundaries first (paragraphs, then sentences, then characters).

    Example:
        chunker = RecursiveChunker(config=ChunkingConfig(
            chunk_size=500,
            chunk_overlap=50,
        ))
        chunks = chunker.chunk("Document with\\n\\nparagraphs and sentences.")
    """

    def __init__(
        self,
        config: ChunkingConfig | None = None,
        separators: list[str] | None = None,
    ):
        self.config = config or ChunkingConfig()
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def chunk(self, text: str, metadata: dict[str, Any] | None = None) -> list[TextChunk]:
        """Recursively split text using hierarchical separators."""
        if not text:
            return []

        metadata = metadata or {}
        chunks = self._recursive_split(text, self.separators)

        # Convert to TextChunk objects
        result = []
        char_pos = 0
        for idx, chunk_text in enumerate(chunks):
            start = text.find(chunk_text, char_pos)
            if start == -1:
                start = char_pos
            end = start + len(chunk_text)

            result.append(
                TextChunk(
                    content=chunk_text,
                    index=idx,
                    start_char=start,
                    end_char=end,
                    metadata=metadata.copy(),
                )
            )
            char_pos = end

        return result

    def _recursive_split(
        self,
        text: str,
        separators: list[str],
    ) -> list[str]:
        """Recursively split text, trying separators in order."""
        if not separators:
            return [text] if text else []

        separator = separators[0]
        remaining_separators = separators[1:]

        # Split by current separator
        if separator:
            splits = text.split(separator)
        else:
            # Final fallback: split by characters
            return self._split_by_chars(text)

        # Merge splits to target chunk size
        merged_chunks = []
        current_chunk = ""

        for split in splits:
            # Try adding to current chunk
            test_chunk = current_chunk + separator + split if current_chunk else split

            if len(test_chunk) <= self.config.chunk_size:
                current_chunk = test_chunk
            else:
                # Current chunk is ready
                if current_chunk:
                    # If current chunk is too big, recursively split it
                    if len(current_chunk) > self.config.chunk_size:
                        merged_chunks.extend(
                            self._recursive_split(current_chunk, remaining_separators)
                        )
                    else:
                        merged_chunks.append(current_chunk)

                # Start new chunk
                if len(split) > self.config.chunk_size:
                    # Split is too big, recursively split it
                    merged_chunks.extend(
                        self._recursive_split(split, remaining_separators)
                    )
                    current_chunk = ""
                else:
                    current_chunk = split

        # Handle remaining chunk
        if current_chunk:
            if len(current_chunk) > self.config.chunk_size:
                merged_chunks.extend(
                    self._recursive_split(current_chunk, remaining_separators)
                )
            else:
                merged_chunks.append(current_chunk)

        return merged_chunks

    def _split_by_chars(self, text: str) -> list[str]:
        """Split text by characters when no separator works."""
        chunks = []
        chunk_size = self.config.chunk_size
        overlap = self.config.chunk_overlap

        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start = end - overlap if end < len(text) else end

        return chunks

    def chunk_documents(
        self,
        documents: list[dict[str, Any]],
        text_key: str = "content",
    ) -> list[TextChunk]:
        """Chunk multiple documents recursively."""
        all_chunks = []

        for doc_idx, doc in enumerate(documents):
            text = doc.get(text_key, "")
            doc_metadata = {
                k: v for k, v in doc.items() if k != text_key
            }
            doc_metadata["_document_index"] = doc_idx

            chunks = self.chunk(text, metadata=doc_metadata)
            all_chunks.extend(chunks)

        return all_chunks
