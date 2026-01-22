"""
Text chunking strategies for document processing.

This module provides:
- ChunkingStrategy ABC for implementing chunking algorithms
- Various chunking implementations (fixed size, sentence, semantic)
"""

from forge_vectors.chunking.base import (
    ChunkingStrategy,
    TextChunk,
    ChunkingConfig,
)

__all__ = [
    "ChunkingStrategy",
    "TextChunk",
    "ChunkingConfig",
]
