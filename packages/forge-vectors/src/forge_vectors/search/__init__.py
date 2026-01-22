"""
Search engine implementations.

This module provides:
- SearchEngine protocol for unified search interface
- k-NN search implementation
- Hybrid keyword + semantic search
- Result reranking
"""

from forge_vectors.search.base import (
    SearchEngine,
    SearchQuery,
    SearchResult,
    SearchMode,
    SearchConfig,
)

__all__ = [
    "SearchEngine",
    "SearchQuery",
    "SearchResult",
    "SearchMode",
    "SearchConfig",
]
