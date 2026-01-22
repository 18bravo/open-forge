"""
PostgreSQL with pgvector extension vector store implementation.

This is the primary vector store implementation for forge-vectors,
using PostgreSQL's pgvector extension for vector similarity search.
"""

from datetime import datetime
import json
from typing import Any

from pydantic import BaseModel, Field

from forge_vectors.stores.base import (
    CollectionInfo,
    CollectionNotFoundError,
    DistanceMetric,
    IndexConfig,
    VectorDocument,
    VectorSearchResult,
    VectorStore,
    VectorStoreError,
)


class PgVectorConfig(BaseModel):
    """Configuration for pgvector store."""

    connection_string: str | None = Field(
        default=None,
        description="PostgreSQL connection string (or use individual params)",
    )
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    database: str = Field(default="forge", description="Database name")
    user: str = Field(default="forge", description="Database user")
    password: str | None = Field(default=None, description="Database password")
    schema: str = Field(default="vectors", description="Schema for vector tables")
    pool_min_size: int = Field(default=2, description="Minimum pool size")
    pool_max_size: int = Field(default=10, description="Maximum pool size")


class PgVectorStore:
    """
    PostgreSQL pgvector implementation of VectorStore.

    Uses the pgvector extension for efficient vector similarity search.
    Supports IVFFlat and HNSW indexes for scalable search.

    Example:
        store = PgVectorStore(config=PgVectorConfig(
            host="localhost",
            database="forge",
        ))
        await store.connect()

        await store.create_collection(
            name="documents",
            dimensions=1536,
            distance_metric=DistanceMetric.COSINE,
        )

        await store.upsert("documents", [
            VectorDocument(
                id="doc1",
                vector=[0.1, 0.2, ...],
                content="Hello world",
                metadata={"source": "test"},
            )
        ])

        results = await store.search(
            collection="documents",
            vector=[0.1, 0.2, ...],
            limit=10,
        )
    """

    def __init__(self, config: PgVectorConfig | None = None):
        self.config = config or PgVectorConfig()
        self._pool: Any = None  # asyncpg.Pool

    async def connect(self) -> None:
        """
        Establish connection pool to PostgreSQL.

        Raises:
            VectorStoreError: If connection fails.
        """
        try:
            import asyncpg
        except ImportError as e:
            raise VectorStoreError(
                "asyncpg package required. Install with: pip install asyncpg",
                store="pgvector",
            ) from e

        try:
            if self.config.connection_string:
                dsn = self.config.connection_string
            else:
                dsn = (
                    f"postgresql://{self.config.user}:{self.config.password or ''}"
                    f"@{self.config.host}:{self.config.port}/{self.config.database}"
                )

            self._pool = await asyncpg.create_pool(
                dsn,
                min_size=self.config.pool_min_size,
                max_size=self.config.pool_max_size,
            )

            # Ensure pgvector extension and schema exist
            async with self._pool.acquire() as conn:
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.config.schema}")

        except Exception as e:
            raise VectorStoreError(f"Failed to connect: {e}", store="pgvector") from e

    async def create_collection(
        self,
        name: str,
        dimensions: int,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
        index_config: IndexConfig | None = None,
    ) -> None:
        """
        Create a new vector collection (table).

        Creates a table with id, vector, content, metadata, and timestamps.
        Optionally creates an index based on index_config.
        """
        if not self._pool:
            raise VectorStoreError("Not connected. Call connect() first.", store="pgvector")

        table_name = f"{self.config.schema}.{name}"

        async with self._pool.acquire() as conn:
            # Create table
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id TEXT PRIMARY KEY,
                    vector vector({dimensions}),
                    content TEXT NOT NULL,
                    metadata JSONB DEFAULT '{{}}',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ
                )
            """)

            # Create index if specified
            if index_config:
                await self._create_index(
                    conn, table_name, dimensions, distance_metric, index_config
                )

    async def _create_index(
        self,
        conn: Any,
        table_name: str,
        dimensions: int,
        distance_metric: DistanceMetric,
        index_config: IndexConfig,
    ) -> None:
        """Create vector index on the collection."""
        # Map distance metric to pgvector operator
        ops_map = {
            DistanceMetric.COSINE: "vector_cosine_ops",
            DistanceMetric.EUCLIDEAN: "vector_l2_ops",
            DistanceMetric.DOT_PRODUCT: "vector_ip_ops",
        }
        ops = ops_map[distance_metric]

        index_name = f"{table_name.replace('.', '_')}_vector_idx"

        if index_config.index_type == "ivfflat":
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table_name} USING ivfflat (vector {ops})
                WITH (lists = {index_config.lists})
            """)
        elif index_config.index_type == "hnsw":
            await conn.execute(f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON {table_name} USING hnsw (vector {ops})
                WITH (m = {index_config.m}, ef_construction = {index_config.ef_construction})
            """)

    async def delete_collection(self, name: str) -> bool:
        """Delete a vector collection."""
        if not self._pool:
            raise VectorStoreError("Not connected", store="pgvector")

        table_name = f"{self.config.schema}.{name}"

        async with self._pool.acquire() as conn:
            result = await conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            return "DROP TABLE" in result

    async def list_collections(self) -> list[CollectionInfo]:
        """List all vector collections."""
        if not self._pool:
            raise VectorStoreError("Not connected", store="pgvector")

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT
                    table_name,
                    (SELECT COUNT(*) FROM {self.config.schema}."" || table_name) as count
                FROM information_schema.tables
                WHERE table_schema = $1
            """, self.config.schema)

            collections = []
            for row in rows:
                # TODO: Extract dimensions and distance metric from table definition
                collections.append(
                    CollectionInfo(
                        name=row["table_name"],
                        dimensions=0,  # Would need to inspect column
                        distance_metric=DistanceMetric.COSINE,
                        document_count=row["count"],
                    )
                )
            return collections

    async def collection_exists(self, name: str) -> bool:
        """Check if a collection exists."""
        if not self._pool:
            raise VectorStoreError("Not connected", store="pgvector")

        async with self._pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = $1 AND table_name = $2
                )
            """, self.config.schema, name)
            return result

    async def upsert(
        self,
        collection: str,
        documents: list[VectorDocument],
    ) -> int:
        """Insert or update documents."""
        if not self._pool:
            raise VectorStoreError("Not connected", store="pgvector")

        if not documents:
            return 0

        table_name = f"{self.config.schema}.{collection}"

        async with self._pool.acquire() as conn:
            # Use INSERT ... ON CONFLICT for upsert
            count = 0
            for doc in documents:
                await conn.execute(f"""
                    INSERT INTO {table_name} (id, vector, content, metadata, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id) DO UPDATE SET
                        vector = EXCLUDED.vector,
                        content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                """,
                    doc.id,
                    str(doc.vector),  # pgvector accepts string representation
                    doc.content,
                    json.dumps(doc.metadata),
                    doc.created_at,
                    doc.updated_at,
                )
                count += 1

            return count

    async def delete(
        self,
        collection: str,
        ids: list[str],
    ) -> int:
        """Delete documents by ID."""
        if not self._pool:
            raise VectorStoreError("Not connected", store="pgvector")

        if not ids:
            return 0

        table_name = f"{self.config.schema}.{collection}"

        async with self._pool.acquire() as conn:
            result = await conn.execute(
                f"DELETE FROM {table_name} WHERE id = ANY($1)",
                ids,
            )
            # Parse "DELETE X" to get count
            return int(result.split()[-1]) if result else 0

    async def get(
        self,
        collection: str,
        ids: list[str],
    ) -> list[VectorDocument | None]:
        """Retrieve documents by ID."""
        if not self._pool:
            raise VectorStoreError("Not connected", store="pgvector")

        if not ids:
            return []

        table_name = f"{self.config.schema}.{collection}"

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"SELECT * FROM {table_name} WHERE id = ANY($1)",
                ids,
            )

            # Build lookup dict
            docs_by_id = {}
            for row in rows:
                docs_by_id[row["id"]] = VectorDocument(
                    id=row["id"],
                    vector=list(row["vector"]),
                    content=row["content"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

            return [docs_by_id.get(id_) for id_ in ids]

    async def search(
        self,
        collection: str,
        vector: list[float],
        limit: int = 10,
        filter: dict[str, Any] | None = None,
        include_vectors: bool = False,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
    ) -> list[VectorSearchResult]:
        """
        Search for similar vectors.

        Uses pgvector's distance operators:
        - <=> for cosine distance
        - <-> for L2/euclidean distance
        - <#> for inner product (negative for max similarity)
        """
        if not self._pool:
            raise VectorStoreError("Not connected", store="pgvector")

        table_name = f"{self.config.schema}.{collection}"

        # Select distance operator
        dist_op_map = {
            DistanceMetric.COSINE: "<=>",
            DistanceMetric.EUCLIDEAN: "<->",
            DistanceMetric.DOT_PRODUCT: "<#>",
        }
        dist_op = dist_op_map[distance_metric]

        # Build query
        select_cols = "id, content, metadata, created_at, updated_at"
        if include_vectors:
            select_cols += ", vector"

        query = f"""
            SELECT {select_cols}, vector {dist_op} $1 AS distance
            FROM {table_name}
        """

        # Add metadata filter if specified
        params: list[Any] = [str(vector)]
        if filter:
            conditions = []
            for i, (key, value) in enumerate(filter.items(), start=2):
                conditions.append(f"metadata->>'{key}' = ${i}")
                params.append(str(value))
            query += " WHERE " + " AND ".join(conditions)

        query += f" ORDER BY distance LIMIT {limit}"

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            results = []
            for row in rows:
                doc = VectorDocument(
                    id=row["id"],
                    vector=list(row["vector"]) if include_vectors and "vector" in row else [],
                    content=row["content"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )

                # Convert distance to score (higher is better)
                distance = float(row["distance"])
                if distance_metric == DistanceMetric.COSINE:
                    score = 1 - distance  # Cosine distance is 1 - similarity
                elif distance_metric == DistanceMetric.DOT_PRODUCT:
                    score = -distance  # Negate for similarity
                else:
                    score = 1 / (1 + distance)  # Inverse for euclidean

                results.append(
                    VectorSearchResult(
                        document=doc,
                        score=score,
                        distance=distance,
                    )
                )

            return results

    async def health_check(self) -> bool:
        """Check if the store is healthy."""
        if not self._pool:
            return False

        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def __aenter__(self) -> "PgVectorStore":
        """Support async context manager."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Clean up on context exit."""
        await self.close()
