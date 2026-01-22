# forge-vectors

Vector storage, embeddings, and semantic search for Open Forge.

## Overview

forge-vectors provides the RAG (Retrieval-Augmented Generation) capabilities for the Open Forge platform, including:

- **Embeddings**: Generate and cache vector embeddings from multiple providers
- **Vector Stores**: Store and retrieve vectors efficiently using pgvector or Qdrant
- **Search**: Semantic, keyword, and hybrid search with optional reranking
- **Chunking**: Split documents into optimal chunks for embedding

## Installation

```bash
# Core package
pip install forge-vectors

# With local embeddings (Sentence Transformers)
pip install forge-vectors[local]

# With Qdrant vector store
pip install forge-vectors[qdrant]

# With reranking support
pip install forge-vectors[rerank]

# All optional dependencies
pip install forge-vectors[all]
```

## Quick Start

```python
from forge_vectors import (
    EmbeddingProvider,
    VectorStore,
    SearchEngine,
    ChunkingStrategy,
)
from forge_vectors.embeddings.providers import OpenAIEmbeddings
from forge_vectors.stores.pgvector import PgVectorStore, PgVectorConfig
from forge_vectors.search.hybrid import HybridSearchEngine
from forge_vectors.chunking.base import RecursiveChunker

# Initialize components
embeddings = OpenAIEmbeddings()
store = PgVectorStore(config=PgVectorConfig(
    host="localhost",
    database="forge",
))
await store.connect()

# Create search engine
search = HybridSearchEngine(
    store=store,
    embedding_provider=embeddings,
)

# Chunk and index documents
chunker = RecursiveChunker()
chunks = chunker.chunk("Your document text here...")

# Generate embeddings and store
for chunk in chunks:
    vector = await embeddings.embed_text(chunk.content)
    await store.upsert("documents", [VectorDocument(
        id=f"chunk-{chunk.index}",
        vector=vector,
        content=chunk.content,
    )])

# Search
results = await search.search(SearchQuery(
    text="your search query",
    collection="documents",
    mode=SearchMode.HYBRID,
))
```

## Package Structure

```
forge-vectors/
├── src/forge_vectors/
│   ├── embeddings/       # Embedding providers and caching
│   │   ├── base.py       # EmbeddingProvider protocol
│   │   ├── providers.py  # OpenAI, Sentence Transformers
│   │   └── cache.py      # Embedding cache
│   ├── stores/           # Vector store backends
│   │   ├── base.py       # VectorStore protocol
│   │   ├── pgvector.py   # PostgreSQL pgvector (primary)
│   │   └── qdrant.py     # Qdrant (optional)
│   ├── search/           # Search implementations
│   │   ├── base.py       # SearchEngine protocol
│   │   ├── hybrid.py     # Hybrid search engine
│   │   └── rerank.py     # Reranking models
│   ├── chunking/         # Text chunking strategies
│   │   └── base.py       # Chunking strategies
│   └── api/              # FastAPI routes
│       └── routes.py
└── tests/
    ├── unit/
    └── integration/
```

## Core Interfaces

### EmbeddingProvider Protocol

```python
@runtime_checkable
class EmbeddingProvider(Protocol):
    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse: ...
    async def embed_text(self, text: str, model: str | None = None) -> list[float]: ...
    def supported_models(self) -> list[EmbeddingModel]: ...
    async def health_check(self) -> bool: ...
```

### VectorStore Protocol

```python
@runtime_checkable
class VectorStore(Protocol):
    async def create_collection(self, name: str, dimensions: int, ...) -> None: ...
    async def upsert(self, collection: str, documents: list[VectorDocument]) -> int: ...
    async def search(self, collection: str, vector: list[float], ...) -> list[VectorSearchResult]: ...
    async def delete(self, collection: str, ids: list[str]) -> int: ...
```

### SearchEngine Protocol

```python
@runtime_checkable
class SearchEngine(Protocol):
    async def search(self, query: SearchQuery) -> list[SearchResult]: ...
    async def semantic_search(self, text: str, collection: str, ...) -> list[SearchResult]: ...
    async def hybrid_search(self, text: str, collection: str, ...) -> list[SearchResult]: ...
    async def rerank(self, query: str, results: list[SearchResult], ...) -> list[SearchResult]: ...
```

### ChunkingStrategy ABC

```python
class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, text: str, metadata: dict | None = None) -> list[TextChunk]: ...
    @abstractmethod
    def chunk_documents(self, documents: list[dict], text_key: str = "content") -> list[TextChunk]: ...
```

## Configuration

### pgvector (Primary Store)

```python
from forge_vectors.stores.pgvector import PgVectorConfig

config = PgVectorConfig(
    host="localhost",
    port=5432,
    database="forge",
    user="forge",
    password="secret",
    schema="vectors",
    pool_min_size=2,
    pool_max_size=10,
)
```

### Qdrant (Optional)

```python
from forge_vectors.stores.qdrant import QdrantConfig

config = QdrantConfig(
    host="localhost",
    port=6333,
    api_key="your-api-key",  # For Qdrant Cloud
)
```

## Search Modes

- **SEMANTIC**: Vector similarity search using embeddings
- **KEYWORD**: Full-text search using PostgreSQL tsvector (planned)
- **HYBRID**: Combines semantic and keyword search using Reciprocal Rank Fusion

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Type checking
mypy src/

# Linting
ruff check src/
```

## License

Apache 2.0
