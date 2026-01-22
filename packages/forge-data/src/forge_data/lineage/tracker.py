"""
Automatic lineage capture.

Provides collectors for extracting lineage from various sources:
SQL queries, pipelines, and manual annotations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from forge_data.lineage.graph import (
    EdgeType,
    LineageEdge,
    LineageGraph,
    LineageNode,
    NodeType,
    TransformationType,
)


class LineageCollector(ABC):
    """Abstract base class for lineage collectors."""

    @abstractmethod
    async def collect(self, source: Any) -> list[LineageEdge]:
        """
        Collect lineage information from a source.

        Args:
            source: The source to extract lineage from

        Returns:
            List of lineage edges discovered
        """
        ...


class SQLLineageCollector(LineageCollector):
    """
    Extract column-level lineage from SQL queries.

    Uses sqlglot for SQL parsing and lineage extraction.
    This is a stub implementation.
    """

    def __init__(self, dialect: str = "postgres"):
        """
        Initialize the SQL lineage collector.

        Args:
            dialect: SQL dialect for parsing (postgres, mysql, snowflake, etc.)
        """
        self.dialect = dialect

    async def collect(self, source: str) -> list[LineageEdge]:
        """
        Parse SQL and extract lineage relationships.

        Args:
            source: SQL query string

        Returns:
            List of lineage edges from the query

        Note: This is a stub. Full implementation would use sqlglot:
            from sqlglot import parse
            from sqlglot.lineage import lineage
        """
        # Stub implementation
        return []

    def _column_to_id(self, column: str) -> str:
        """Convert a column reference to a node ID."""
        return column.lower().replace(".", "_")


class PipelineLineageCollector(LineageCollector):
    """
    Collect lineage from pipeline runs (Dagster, Airflow, etc.).

    This is a stub implementation.
    """

    def __init__(self, pipeline_type: str = "dagster"):
        """
        Initialize the pipeline lineage collector.

        Args:
            pipeline_type: Type of pipeline (dagster, airflow, etc.)
        """
        self.pipeline_type = pipeline_type

    async def collect(self, source: dict[str, Any]) -> list[LineageEdge]:
        """
        Extract lineage from a pipeline run.

        Args:
            source: Pipeline run metadata

        Returns:
            List of lineage edges from the pipeline

        Note: This is a stub. Full implementation would integrate
        with Dagster's asset lineage or Airflow's data lineage.
        """
        # Stub implementation
        return []


class LineageTracker:
    """
    Central lineage tracking service.

    Coordinates lineage collection from multiple sources and maintains
    the lineage graph.

    Example:
        tracker = LineageTracker()
        tracker.register_collector("sql", SQLLineageCollector())

        # Record lineage from a SQL query
        await tracker.track_sql(
            sql="SELECT a, b FROM source_table",
            output_table="target_table"
        )

        # Get the lineage graph
        graph = tracker.get_graph()
    """

    def __init__(self) -> None:
        self._graph = LineageGraph()
        self._collectors: dict[str, LineageCollector] = {}

    def register_collector(self, name: str, collector: LineageCollector) -> None:
        """Register a lineage collector."""
        self._collectors[name] = collector

    def get_graph(self) -> LineageGraph:
        """Get the current lineage graph."""
        return self._graph

    async def track_sql(
        self,
        sql: str,
        output_table: str,
        output_columns: list[str] | None = None,
    ) -> list[LineageEdge]:
        """
        Track lineage from a SQL query.

        Args:
            sql: The SQL query
            output_table: Table that receives the query output
            output_columns: Columns in the output (optional)

        Returns:
            List of lineage edges created
        """
        collector = self._collectors.get("sql")
        if not collector:
            collector = SQLLineageCollector()

        edges = await collector.collect(sql)

        for edge in edges:
            self._graph.add_edge(edge)

        return edges

    async def track_pipeline_run(
        self,
        pipeline_name: str,
        run_id: str,
        inputs: list[str],
        outputs: list[str],
        metadata: dict[str, Any] | None = None,
    ) -> list[LineageEdge]:
        """
        Track lineage from a pipeline run.

        Args:
            pipeline_name: Name of the pipeline
            run_id: Unique run identifier
            inputs: Input dataset IDs
            outputs: Output dataset IDs
            metadata: Additional metadata

        Returns:
            List of lineage edges created
        """
        edges = []
        now = datetime.utcnow()

        # Create a transform node for the pipeline run
        transform_node = LineageNode(
            id=f"pipeline:{pipeline_name}:{run_id}",
            type=NodeType.PIPELINE,
            name=f"{pipeline_name} run {run_id}",
            qualified_name=f"pipeline.{pipeline_name}.{run_id}",
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )
        self._graph.add_node(transform_node)

        # Create edges from inputs to transform
        for input_id in inputs:
            edge = LineageEdge(
                id=f"{input_id}->{transform_node.id}",
                source_id=input_id,
                target_id=transform_node.id,
                edge_type=EdgeType.CONSUMES,
                created_at=now,
            )
            edges.append(edge)
            self._graph.add_edge(edge)

        # Create edges from transform to outputs
        for output_id in outputs:
            edge = LineageEdge(
                id=f"{transform_node.id}->{output_id}",
                source_id=transform_node.id,
                target_id=output_id,
                edge_type=EdgeType.PRODUCES,
                created_at=now,
            )
            edges.append(edge)
            self._graph.add_edge(edge)

        return edges

    def add_manual_lineage(
        self,
        source_id: str,
        target_id: str,
        transformation: TransformationType = TransformationType.UNKNOWN,
        expression: str | None = None,
    ) -> LineageEdge:
        """
        Add manual lineage annotation.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            transformation: Type of transformation
            expression: Optional transformation expression

        Returns:
            The created lineage edge
        """
        edge = LineageEdge(
            id=f"{source_id}->{target_id}",
            source_id=source_id,
            target_id=target_id,
            edge_type=EdgeType.DERIVES_FROM,
            transformation=transformation,
            expression=expression,
            metadata={"manual": True},
            created_at=datetime.utcnow(),
        )
        self._graph.add_edge(edge)
        return edge
