"""Pytest configuration and fixtures for forge-vectors tests."""

import pytest


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (requires external services)",
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow-running",
    )


@pytest.fixture
def sample_texts():
    """Sample texts for testing."""
    return [
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning is a subset of artificial intelligence.",
        "Python is a popular programming language for data science.",
        "Vector databases enable efficient similarity search.",
        "Natural language processing helps computers understand text.",
    ]


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        {
            "id": "doc-1",
            "content": "Introduction to machine learning and AI concepts.",
            "metadata": {"category": "ml", "author": "Alice"},
        },
        {
            "id": "doc-2",
            "content": "Python programming best practices and patterns.",
            "metadata": {"category": "programming", "author": "Bob"},
        },
        {
            "id": "doc-3",
            "content": "Vector similarity search using embeddings.",
            "metadata": {"category": "search", "author": "Charlie"},
        },
    ]


@pytest.fixture
def sample_embeddings():
    """Sample embedding vectors for testing (small dimensions for speed)."""
    import random

    random.seed(42)

    def generate_embedding(dim=128):
        return [random.random() for _ in range(dim)]

    return [
        generate_embedding(),
        generate_embedding(),
        generate_embedding(),
    ]
