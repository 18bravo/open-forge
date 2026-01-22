"""Tests for search engine interfaces."""

import pytest

from forge_vectors.search.base import (
    SearchConfig,
    SearchEngine,
    SearchError,
    SearchMode,
    SearchQuery,
    SearchResult,
)


class TestSearchModels:
    """Tests for search data models."""

    def test_search_query(self):
        """SearchQuery model validation."""
        query = SearchQuery(
            text="How to configure authentication?",
            collection="docs",
            mode=SearchMode.HYBRID,
            limit=20,
            filter={"category": "security"},
        )
        assert query.text == "How to configure authentication?"
        assert query.collection == "docs"
        assert query.mode == SearchMode.HYBRID
        assert query.limit == 20
        assert query.filter["category"] == "security"

    def test_search_query_defaults(self):
        """SearchQuery has sensible defaults."""
        query = SearchQuery(
            text="test query",
            collection="docs",
        )
        assert query.mode == SearchMode.SEMANTIC
        assert query.limit == 10
        assert query.filter is None
        assert query.rerank is False
        assert query.semantic_weight == 0.7
        assert query.keyword_weight == 0.3

    def test_search_result(self):
        """SearchResult model validation."""
        result = SearchResult(
            id="doc-123",
            content="This is the document content",
            metadata={"source": "test"},
            score=0.95,
            semantic_score=0.95,
        )
        assert result.id == "doc-123"
        assert result.score == 0.95
        assert result.semantic_score == 0.95
        assert result.keyword_score is None
        assert result.rerank_score is None

    def test_search_result_hybrid_scores(self):
        """SearchResult can store hybrid scores."""
        result = SearchResult(
            id="doc-123",
            content="Content",
            score=0.85,
            semantic_score=0.9,
            keyword_score=0.7,
            rerank_score=0.95,
        )
        assert result.semantic_score == 0.9
        assert result.keyword_score == 0.7
        assert result.rerank_score == 0.95

    def test_search_config(self):
        """SearchConfig model validation."""
        config = SearchConfig(
            default_limit=20,
            max_limit=200,
            default_mode=SearchMode.HYBRID,
            enable_reranking=True,
            rerank_model="cohere-rerank-v3",
        )
        assert config.default_limit == 20
        assert config.max_limit == 200
        assert config.default_mode == SearchMode.HYBRID
        assert config.enable_reranking is True
        assert config.rerank_model == "cohere-rerank-v3"


class TestSearchModes:
    """Tests for search mode enum."""

    def test_search_modes_defined(self):
        """All expected search modes are defined."""
        assert SearchMode.SEMANTIC == "semantic"
        assert SearchMode.KEYWORD == "keyword"
        assert SearchMode.HYBRID == "hybrid"

    def test_search_mode_values(self):
        """Search mode values are strings."""
        for mode in SearchMode:
            assert isinstance(mode.value, str)


class TestSearchErrors:
    """Tests for search exceptions."""

    def test_search_error(self):
        """SearchError includes query."""
        error = SearchError("Search failed", query="test query")
        assert "Search failed" in str(error)
        assert error.query == "test query"


class TestSearchEngineProtocol:
    """Tests for SearchEngine protocol compliance."""

    def test_protocol_is_runtime_checkable(self):
        """SearchEngine can be checked at runtime."""
        # Protocol should be importable and runtime checkable
        assert hasattr(SearchEngine, "__protocol_attrs__") or hasattr(
            SearchEngine, "_is_protocol"
        )
